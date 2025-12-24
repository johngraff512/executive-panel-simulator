"""
SQLite database module for Executive Panel Simulator Version 2
Handles persistent storage of sessions, responses, and company research
"""

import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager
import os

DB_PATH = 'executive_simulator.db'

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_database():
    """Initialize database tables"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                industry TEXT,
                report_type TEXT,
                selected_executives TEXT,  -- JSON array
                report_content TEXT,  -- Full report text/analysis
                key_details TEXT,  -- JSON array
                used_topics TEXT,  -- JSON array of indices
                current_question_count INTEGER DEFAULT 0,
                question_limit INTEGER DEFAULT 10,
                allow_followups BOOLEAN DEFAULT 0,
                enable_web_research BOOLEAN DEFAULT 0,
                company_research TEXT,  -- JSON object with research data
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Questions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                executive TEXT NOT NULL,
                executive_name TEXT,
                question_text TEXT NOT NULL,
                is_followup BOOLEAN DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        ''')

        # Responses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                response_text TEXT NOT NULL,
                response_type TEXT DEFAULT 'text',  -- 'text' or 'audio'
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        ''')

        # Create indices for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_questions_session ON questions(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_responses_session ON responses(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at)')

        print("✅ Database initialized successfully")

def create_session(session_id, company_name, industry, report_type,
                  selected_executives, report_content, key_details,
                  question_limit, allow_followups=False, enable_web_research=False,
                  company_research=None):
    """Create a new session"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sessions
            (session_id, company_name, industry, report_type, selected_executives,
             report_content, key_details, question_limit, allow_followups,
             enable_web_research, company_research, used_topics)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            company_name,
            industry,
            report_type,
            json.dumps(selected_executives),
            report_content,
            json.dumps(key_details),
            question_limit,
            allow_followups,
            enable_web_research,
            json.dumps(company_research) if company_research else None,
            json.dumps([])  # Empty used_topics initially
        ))

def get_session(session_id):
    """Retrieve session data"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
        row = cursor.fetchone()

        if not row:
            return None

        # Convert row to dict and parse JSON fields
        session_data = dict(row)
        session_data['selected_executives'] = json.loads(session_data['selected_executives'])
        session_data['key_details'] = json.loads(session_data['key_details'])
        session_data['used_topics'] = json.loads(session_data['used_topics'])
        if session_data['company_research']:
            session_data['company_research'] = json.loads(session_data['company_research'])

        return session_data

def update_session(session_id, **kwargs):
    """Update session fields"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Build dynamic UPDATE query
        set_clauses = []
        values = []

        for key, value in kwargs.items():
            set_clauses.append(f"{key} = ?")
            # Serialize lists/dicts to JSON
            if isinstance(value, (list, dict)):
                values.append(json.dumps(value))
            else:
                values.append(value)

        # Add updated_at timestamp
        set_clauses.append("updated_at = ?")
        values.append(datetime.now().isoformat())

        values.append(session_id)

        query = f"UPDATE sessions SET {', '.join(set_clauses)} WHERE session_id = ?"
        cursor.execute(query, values)

def add_question(session_id, executive, executive_name, question_text, is_followup=False):
    """Add a question to the session"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO questions
            (session_id, executive, executive_name, question_text, is_followup)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, executive, executive_name, question_text, is_followup))
        return cursor.lastrowid

def get_questions(session_id):
    """Get all questions for a session"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM questions
            WHERE session_id = ?
            ORDER BY id ASC
        ''', (session_id,))
        return [dict(row) for row in cursor.fetchall()]

def add_response(session_id, response_text, response_type='text'):
    """Add a response to the session"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO responses
            (session_id, response_text, response_type)
            VALUES (?, ?, ?)
        ''', (session_id, response_text, response_type))
        return cursor.lastrowid

def get_responses(session_id):
    """Get all responses for a session"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM responses
            WHERE session_id = ?
            ORDER BY id ASC
        ''', (session_id,))
        return [dict(row) for row in cursor.fetchall()]

def delete_session(session_id):
    """Delete a session and all related data"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM responses WHERE session_id = ?', (session_id,))
        cursor.execute('DELETE FROM questions WHERE session_id = ?', (session_id,))
        cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))

def cleanup_old_sessions(days=7):
    """Delete sessions older than specified days"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM responses WHERE session_id IN (
                SELECT session_id FROM sessions
                WHERE created_at < datetime('now', '-' || ? || ' days')
            )
        ''', (days,))
        cursor.execute('''
            DELETE FROM questions WHERE session_id IN (
                SELECT session_id FROM sessions
                WHERE created_at < datetime('now', '-' || ? || ' days')
            )
        ''', (days,))
        cursor.execute('''
            DELETE FROM sessions
            WHERE created_at < datetime('now', '-' || ? || ' days')
        ''', (days,))
        return cursor.rowcount

def get_session_stats():
    """Get database statistics"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM sessions')
        total_sessions = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM questions')
        total_questions = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM responses')
        total_responses = cursor.fetchone()['count']

        return {
            'total_sessions': total_sessions,
            'total_questions': total_questions,
            'total_responses': total_responses
        }

# Initialize database when module is imported
if __name__ != '__main__':
    init_database()
