import { env } from "cloudflare:workers";

export type SessionRecord = {
  id: string;
  owner_id: string;
  document_id: string;
  company_name: string;
  report_type: string;
  executives_json: string;
  question_limit: number;
  allow_followups: number;
  current_turn: number;
  status: string;
  analysis_json: string | null;
  feedback_json: string | null;
};

export type TurnRecord = {
  id: number;
  turn_number: number;
  executive: string;
  question: string;
  response_text: string | null;
  response_type: string | null;
  is_followup: number;
};

export type RuntimeBindings = {
  DB?: D1Database;
  FILES?: R2Bucket;
  PORTKEY_API_KEY?: string;
  PORTKEY_VIRTUAL_KEY?: string;
  PORTKEY_PROVIDER?: string;
  PORTKEY_BASE_URL?: string;
  PORTKEY_ENVIRONMENT?: string;
  OPENAI_API_KEY?: string;
  OPENAI_ANALYSIS_MODEL?: string;
  OPENAI_TURN_MODEL?: string;
  OPENAI_TRANSCRIBE_MODEL?: string;
  OPENAI_SPEECH_MODEL?: string;
  OPENAI_FEEDBACK_MODEL?: string;
};

export function bindings(): RuntimeBindings {
  return env as unknown as RuntimeBindings;
}

export async function ensureSchema(): Promise<void> {
  const { DB } = bindings();
  if (!DB) throw new Error("D1 binding DB is unavailable");

  await DB.batch([
    DB.prepare(`CREATE TABLE IF NOT EXISTS documents (
      id TEXT PRIMARY KEY,
      owner_id TEXT NOT NULL,
      object_key TEXT NOT NULL,
      filename TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'processing',
      analysis_json TEXT,
      openai_file_id TEXT,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      expires_at TEXT NOT NULL
    )`),
    DB.prepare(`CREATE TABLE IF NOT EXISTS sessions (
      id TEXT PRIMARY KEY,
      owner_id TEXT NOT NULL,
      document_id TEXT NOT NULL,
      company_name TEXT NOT NULL,
      report_type TEXT NOT NULL,
      executives_json TEXT NOT NULL,
      question_limit INTEGER NOT NULL DEFAULT 6,
      allow_followups INTEGER NOT NULL DEFAULT 1,
      current_turn INTEGER NOT NULL DEFAULT 1,
      status TEXT NOT NULL DEFAULT 'active',
      feedback_json TEXT,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )`),
    DB.prepare(`CREATE TABLE IF NOT EXISTS turns (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT NOT NULL,
      turn_number INTEGER NOT NULL,
      executive TEXT NOT NULL,
      question TEXT NOT NULL,
      response_text TEXT,
      response_type TEXT,
      is_followup INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )`),
    DB.prepare(
      "CREATE INDEX IF NOT EXISTS idx_documents_owner_created ON documents(owner_id, created_at)",
    ),
    DB.prepare(
      "CREATE INDEX IF NOT EXISTS idx_sessions_owner_status ON sessions(owner_id, status)",
    ),
    DB.prepare(
      "CREATE UNIQUE INDEX IF NOT EXISTS idx_turns_session_number ON turns(session_id, turn_number)",
    ),
  ]);
}

export function requestOwnerId(request: Request): string {
  return request.headers.get("oai-authenticated-user-id") ?? "local-preview";
}

export async function ownerSafetyId(ownerId: string): Promise<string> {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(ownerId),
  );
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("")
    .slice(0, 32);
}

export async function getSession(
  sessionId: string,
  ownerId: string,
): Promise<{ session: SessionRecord; turns: TurnRecord[] } | null> {
  const { DB } = bindings();
  if (!DB) throw new Error("D1 binding DB is unavailable");

  const session = await DB.prepare(
    `SELECT s.*, d.analysis_json
     FROM sessions s
     JOIN documents d ON d.id = s.document_id
     WHERE s.id = ? AND s.owner_id = ?`,
  )
    .bind(sessionId, ownerId)
    .first<SessionRecord>();
  if (!session) return null;

  const result = await DB.prepare(
    `SELECT id, turn_number, executive, question, response_text,
            response_type, is_followup
     FROM turns WHERE session_id = ? ORDER BY turn_number ASC`,
  )
    .bind(sessionId)
    .all<TurnRecord>();

  return { session, turns: result.results };
}
