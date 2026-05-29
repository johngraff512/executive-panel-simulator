"""
Database module for Executive Panel Simulator Version 2.

Storage is accessed through SQLAlchemy Core and the backend is chosen at
runtime via the DATABASE_URL environment variable:

  - local dev / Azure pilot : SQLite
        sqlite:///executive_simulator.db            (relative, local dev)
        sqlite:////home/data/executive_simulator.db (absolute, Azure /home mount)
  - future managed database : Postgres  (postgresql+psycopg://user:pass@host/db)
                              Azure SQL (mssql+pyodbc://...?driver=ODBC+Driver+18+for+SQL+Server)

The public function API (signatures and return shapes) is intentionally
identical to the previous sqlite3 implementation, so app_v2.py is unchanged.
Switching to a managed database later is a DATABASE_URL change plus a driver in
requirements.txt -- no query rewrites (the only dialect-divergent spots,
upserts and date math, are handled here).
"""

import json
import os
from contextlib import contextmanager
from datetime import datetime, timedelta

from sqlalchemy import (
    Boolean,
    Column,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    create_engine,
    event,
    func,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import make_url

# ============================================================================
# Engine / connection setup
# ============================================================================

DEFAULT_URL = "sqlite:///executive_simulator.db"
DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_URL)

_url = make_url(DATABASE_URL)
_is_sqlite = _url.get_backend_name() == "sqlite"

# Ensure the SQLite file's directory exists (e.g. /home/data on Azure) before
# we try to open/create the database.
if _is_sqlite and _url.database and os.path.dirname(_url.database):
    os.makedirs(os.path.dirname(_url.database), exist_ok=True)

if _is_sqlite:
    engine = create_engine(
        DATABASE_URL,
        future=True,
        connect_args={"timeout": 30, "check_same_thread": False},
        pool_pre_ping=True,
    )

    @event.listens_for(engine, "connect")
    def _sqlite_on_connect(dbapi_conn, _record):
        # Wait (up to 30s) instead of failing immediately when the file is
        # locked -- important on the SMB-backed Azure Files /home mount.
        #
        # NOTE: Do NOT enable WAL journal mode here. WAL relies on shared
        # memory that is unsafe over Azure Files and can corrupt the database;
        # keep SQLite's default rollback (DELETE) journal.
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA busy_timeout=30000")
        cur.close()
else:
    # Managed databases (Postgres / Azure SQL): real pool with liveness checks.
    engine = create_engine(
        DATABASE_URL,
        future=True,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=1800,  # managed DBs drop idle connections (~30 min)
    )


@contextmanager
def get_db():
    """Transactional connection context manager.

    Commits on success and rolls back on exception -- same contract as the
    previous sqlite3-based helper. Used for writes; reads use engine.connect().
    """
    with engine.begin() as conn:
        yield conn


# ============================================================================
# Schema
# ============================================================================

metadata = MetaData()

# JSON-bearing columns are stored as Text and (de)serialized in Python with
# json.dumps/loads, exactly as before -- this keeps stored bytes and returned
# objects identical across SQLite/Postgres/Azure SQL. Timestamp columns are
# also Text holding ISO strings (see _now_iso), because callers treat
# timestamps as strings (e.g. row["timestamp"].replace("Z", "+00:00")).

sessions = Table(
    "sessions",
    metadata,
    Column("session_id", Text, primary_key=True),
    Column("company_name", Text, nullable=False),
    Column("industry", Text),
    Column("report_type", Text),
    Column("selected_executives", Text),  # JSON array
    Column("report_content", Text),  # full report text/analysis
    Column("key_details", Text),  # JSON array
    Column("used_topics", Text),  # JSON array of indices
    Column("current_question_count", Integer, default=0),
    Column("question_limit", Integer, default=10),
    Column("allow_followups", Boolean, default=False),
    Column("enable_web_research", Boolean, default=False),
    Column("enable_ai_feedback", Boolean, default=False),
    Column("ai_feedback", Text),  # JSON (caller pre-serializes)
    Column("company_research", Text),  # JSON object
    Column("created_at", Text),  # ISO string
    Column("updated_at", Text),  # ISO string
)

questions = Table(
    "questions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("session_id", Text, nullable=False),
    Column("executive", Text, nullable=False),
    Column("executive_name", Text),
    Column("question_text", Text, nullable=False),
    Column("is_followup", Boolean, default=False),
    Column("timestamp", Text),  # ISO string
    Index("idx_questions_session", "session_id"),
)

responses = Table(
    "responses",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("session_id", Text, nullable=False),
    Column("response_text", Text, nullable=False),
    Column("response_type", Text, default="text"),  # 'text' or 'audio'
    Column("timestamp", Text),  # ISO string
    Index("idx_responses_session", "session_id"),
)

progressive_cache = Table(
    "progressive_cache",
    metadata,
    Column("flask_session_id", Text, primary_key=True),
    Column("extraction_data", Text),  # JSON
    Column("ai_analysis_data", Text),  # JSON
    Column("web_research_data", Text),  # JSON
    Column("created_at", Text),  # ISO string
    Column("expires_at", Text),  # ISO string (auto-cleanup after 1 hour)
)

Index("idx_sessions_created", sessions.c.created_at)


def init_database():
    """Create all tables and indexes if they don't exist (idempotent)."""
    metadata.create_all(engine)
    print("✅ Database initialized successfully")


# ============================================================================
# Helpers
# ============================================================================


def _now_iso():
    """Canonical UTC timestamp string for all writes and comparisons.

    Fixed-width ISO ("YYYY-MM-DD HH:MM:SS.ffffff") so lexical ordering equals
    chronological ordering on every engine -- no DB-side date functions needed.
    """
    return datetime.utcnow().isoformat(sep=" ")


def _upsert(conn, table, values, index_elements, update_cols):
    """Portable INSERT ... ON CONFLICT DO UPDATE.

    Reproduces SQLite's INSERT OR REPLACE: callers pass a full value set and
    list every column to refresh in update_cols, so a conflicting row is reset
    to the new values rather than left with stale fields.
    """
    name = conn.dialect.name
    if name == "sqlite":
        stmt = sqlite_insert(table).values(**values)
    elif name == "postgresql":
        stmt = pg_insert(table).values(**values)
    else:
        # Azure SQL / mssql has no ON CONFLICT; implement via MERGE when the
        # managed-DB migration happens. Fail loudly rather than mis-save.
        raise NotImplementedError(f"upsert not implemented for dialect '{name}'")
    stmt = stmt.on_conflict_do_update(
        index_elements=index_elements,
        set_={c: stmt.excluded[c] for c in update_cols},
    )
    conn.execute(stmt)


# ============================================================================
# Sessions
# ============================================================================


def create_session(
    session_id,
    company_name,
    industry,
    report_type,
    selected_executives,
    report_content,
    key_details,
    question_limit,
    allow_followups=False,
    enable_web_research=False,
    enable_ai_feedback=False,
    company_research=None,
):
    """Create a new session (or replace existing if session_id already exists)."""
    now = _now_iso()
    values = {
        "session_id": session_id,
        "company_name": company_name,
        "industry": industry,
        "report_type": report_type,
        "selected_executives": json.dumps(selected_executives),
        "report_content": report_content,
        "key_details": json.dumps(key_details),
        "used_topics": json.dumps([]),  # empty used_topics initially
        "current_question_count": 0,
        "question_limit": question_limit,
        "allow_followups": allow_followups,
        "enable_web_research": enable_web_research,
        "enable_ai_feedback": enable_ai_feedback,
        "ai_feedback": None,
        "company_research": json.dumps(company_research) if company_research else None,
        "created_at": now,
        "updated_at": now,
    }
    # Reset every column on conflict to match INSERT OR REPLACE's fresh-row
    # semantics (so a retried create_session does not keep a stale state).
    with get_db() as conn:
        _upsert(
            conn,
            sessions,
            values,
            index_elements=["session_id"],
            update_cols=[k for k in values if k != "session_id"],
        )


def get_session(session_id):
    """Retrieve session data."""
    with engine.connect() as conn:
        row = conn.execute(select(sessions).where(sessions.c.session_id == session_id)).fetchone()

    if not row:
        return None

    # Convert row to dict and parse JSON fields
    session_data = dict(row._mapping)
    session_data["selected_executives"] = json.loads(session_data["selected_executives"])
    session_data["key_details"] = json.loads(session_data["key_details"])
    session_data["used_topics"] = json.loads(session_data["used_topics"])
    if session_data["company_research"]:
        session_data["company_research"] = json.loads(session_data["company_research"])

    return session_data


def update_session(session_id, **kwargs):
    """Update session fields."""
    # Whitelist real columns (and never allow updating the PK or created_at).
    allowed = {c.name for c in sessions.columns} - {"session_id", "created_at"}

    values = {}
    for key, value in kwargs.items():
        if key not in allowed:
            raise ValueError(f"Illegal session update column: {key}")
        # Serialize lists/dicts to JSON
        values[key] = json.dumps(value) if isinstance(value, list | dict) else value

    values["updated_at"] = _now_iso()

    with get_db() as conn:
        conn.execute(sessions.update().where(sessions.c.session_id == session_id).values(**values))


# ============================================================================
# Questions & responses
# ============================================================================


def add_question(session_id, executive, executive_name, question_text, is_followup=False):
    """Add a question to the session."""
    with get_db() as conn:
        result = conn.execute(
            questions.insert().values(
                session_id=session_id,
                executive=executive,
                executive_name=executive_name,
                question_text=question_text,
                is_followup=is_followup,
                timestamp=_now_iso(),
            )
        )
        return result.inserted_primary_key[0]


def get_questions(session_id):
    """Get all questions for a session."""
    with engine.connect() as conn:
        rows = conn.execute(
            select(questions).where(questions.c.session_id == session_id).order_by(questions.c.id.asc())
        ).fetchall()
    return [dict(row._mapping) for row in rows]


def add_response(session_id, response_text, response_type="text"):
    """Add a response to the session."""
    with get_db() as conn:
        result = conn.execute(
            responses.insert().values(
                session_id=session_id,
                response_text=response_text,
                response_type=response_type,
                timestamp=_now_iso(),
            )
        )
        return result.inserted_primary_key[0]


def get_responses(session_id):
    """Get all responses for a session."""
    with engine.connect() as conn:
        rows = conn.execute(
            select(responses).where(responses.c.session_id == session_id).order_by(responses.c.id.asc())
        ).fetchall()
    return [dict(row._mapping) for row in rows]


def get_conversation_history(session_id, limit=5):
    """Get recent conversation history (Q&A pairs) for context

    Args:
        session_id: Session identifier
        limit: Number of recent Q&A pairs to retrieve (default 5)

    Returns:
        List of dicts with 'question', 'executive', and 'response' keys
    """
    # Kept as raw SQL (named params) to preserve the exact LEFT JOIN matching
    # semantics. Portable to SQLite/Postgres; LIMIT must become TOP/OFFSET-FETCH
    # for Azure SQL at migration time.
    sql = text(
        """
        SELECT
            q.executive,
            q.executive_name,
            q.question_text,
            q.timestamp AS question_time,
            r.response_text,
            r.timestamp AS response_time
        FROM questions q
        LEFT JOIN responses r ON q.session_id = r.session_id
            AND r.id = (
                SELECT MIN(r2.id)
                FROM responses r2
                WHERE r2.session_id = q.session_id
                AND r2.timestamp > q.timestamp
            )
        WHERE q.session_id = :sid
        ORDER BY q.id DESC
        LIMIT :lim
        """
    )

    with engine.connect() as conn:
        rows = conn.execute(sql, {"sid": session_id, "lim": limit}).fetchall()

    history = []
    for row in rows:
        m = row._mapping
        history.append(
            {
                "executive": m["executive"],
                "executive_name": m["executive_name"],
                "question": m["question_text"],
                "response": m["response_text"] if m["response_text"] else "[No response yet]",
            }
        )

    # Return in chronological order (oldest first)
    return list(reversed(history))


def delete_session(session_id):
    """Delete a session and all related data"""
    with get_db() as conn:
        conn.execute(responses.delete().where(responses.c.session_id == session_id))
        conn.execute(questions.delete().where(questions.c.session_id == session_id))
        conn.execute(sessions.delete().where(sessions.c.session_id == session_id))


def cleanup_old_sessions(days=7):
    """Delete sessions older than specified days"""
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat(sep=" ")
    with get_db() as conn:
        old_ids = select(sessions.c.session_id).where(sessions.c.created_at < cutoff)
        conn.execute(responses.delete().where(responses.c.session_id.in_(old_ids)))
        conn.execute(questions.delete().where(questions.c.session_id.in_(old_ids)))
        result = conn.execute(sessions.delete().where(sessions.c.created_at < cutoff))
        return result.rowcount


def get_session_stats():
    """Get database statistics"""
    with engine.connect() as conn:
        total_sessions = conn.execute(select(func.count()).select_from(sessions)).scalar_one()
        total_questions = conn.execute(select(func.count()).select_from(questions)).scalar_one()
        total_responses = conn.execute(select(func.count()).select_from(responses)).scalar_one()

    return {
        "total_sessions": total_sessions,
        "total_questions": total_questions,
        "total_responses": total_responses,
    }


# ============================================================================
# PROGRESSIVE CACHE FUNCTIONS (Database-backed for multi-worker support)
# ============================================================================


def save_progressive_cache_extraction(flask_session_id, extraction_data):
    """Save extraction data to database for progressive analysis"""
    # Expiration 1 hour from now. On conflict, also reset analysis/research to
    # NULL so the row starts fresh (matching the old INSERT OR REPLACE).
    expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat(sep=" ")
    values = {
        "flask_session_id": flask_session_id,
        "extraction_data": json.dumps(extraction_data),
        "ai_analysis_data": None,
        "web_research_data": None,
        "created_at": _now_iso(),
        "expires_at": expires_at,
    }
    with get_db() as conn:
        _upsert(
            conn,
            progressive_cache,
            values,
            index_elements=["flask_session_id"],
            update_cols=["extraction_data", "ai_analysis_data", "web_research_data", "created_at", "expires_at"],
        )

    print(f"💾 Saved extraction to database cache for session {flask_session_id[:20]}...")


def save_progressive_cache_analysis(flask_session_id, analysis_data):
    """Save AI analysis data to database for progressive analysis"""
    with get_db() as conn:
        conn.execute(
            progressive_cache.update()
            .where(progressive_cache.c.flask_session_id == flask_session_id)
            .values(ai_analysis_data=json.dumps(analysis_data))
        )

    print(f"💾 Saved AI analysis to database cache for session {flask_session_id[:20]}...")


def save_progressive_cache_research(flask_session_id, research_data):
    """Save web research data to database for progressive analysis"""
    with get_db() as conn:
        conn.execute(
            progressive_cache.update()
            .where(progressive_cache.c.flask_session_id == flask_session_id)
            .values(web_research_data=json.dumps(research_data))
        )

    print(f"💾 Saved web research to database cache for session {flask_session_id[:20]}...")


def get_progressive_cache(flask_session_id):
    """Retrieve progressive cache data from database"""
    with engine.connect() as conn:
        row = conn.execute(
            select(
                progressive_cache.c.extraction_data,
                progressive_cache.c.ai_analysis_data,
                progressive_cache.c.web_research_data,
            ).where(
                (progressive_cache.c.flask_session_id == flask_session_id)
                & ((progressive_cache.c.expires_at.is_(None)) | (progressive_cache.c.expires_at > _now_iso()))
            )
        ).fetchone()

    if not row:
        print(f"❌ No cache found for session {flask_session_id[:20]}...")
        return {}

    m = row._mapping
    cache = {}

    if m["extraction_data"]:
        cache["extraction"] = json.loads(m["extraction_data"])

    if m["ai_analysis_data"]:
        cache["ai_analysis"] = json.loads(m["ai_analysis_data"])

    if m["web_research_data"]:
        cache["web_research"] = json.loads(m["web_research_data"])

    print(f"✅ Retrieved cache from database: {list(cache.keys())}")
    return cache


def delete_progressive_cache(flask_session_id):
    """Delete progressive cache data after session is created"""
    with get_db() as conn:
        conn.execute(progressive_cache.delete().where(progressive_cache.c.flask_session_id == flask_session_id))

    print(f"🗑️ Deleted progressive cache for session {flask_session_id[:20]}...")


def cleanup_expired_progressive_cache():
    """Clean up expired progressive cache entries"""
    with get_db() as conn:
        result = conn.execute(progressive_cache.delete().where(progressive_cache.c.expires_at < _now_iso()))
        deleted = result.rowcount

    if deleted > 0:
        print(f"🗑️ Cleaned up {deleted} expired progressive cache entries")
    return deleted


# ============================================================================

# Initialize database when module is imported
if __name__ != "__main__":
    init_database()
