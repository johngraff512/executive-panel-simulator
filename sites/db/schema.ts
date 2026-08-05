import { sql } from "drizzle-orm";
import {
  index,
  integer,
  sqliteTable,
  text,
  uniqueIndex,
} from "drizzle-orm/sqlite-core";

export const documents = sqliteTable(
  "documents",
  {
    id: text("id").primaryKey(),
    ownerId: text("owner_id").notNull(),
    objectKey: text("object_key").notNull(),
    filename: text("filename").notNull(),
    status: text("status").notNull().default("processing"),
    analysisJson: text("analysis_json"),
    openaiFileId: text("openai_file_id"),
    createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
    expiresAt: text("expires_at").notNull(),
  },
  (table) => [
    index("idx_documents_owner_created").on(table.ownerId, table.createdAt),
  ],
);

export const sessions = sqliteTable(
  "sessions",
  {
    id: text("id").primaryKey(),
    ownerId: text("owner_id").notNull(),
    documentId: text("document_id").notNull(),
    companyName: text("company_name").notNull(),
    reportType: text("report_type").notNull(),
    executivesJson: text("executives_json").notNull(),
    questionLimit: integer("question_limit").notNull().default(6),
    allowFollowups: integer("allow_followups", { mode: "boolean" })
      .notNull()
      .default(true),
    currentTurn: integer("current_turn").notNull().default(1),
    status: text("status").notNull().default("active"),
    feedbackJson: text("feedback_json"),
    createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
    updatedAt: text("updated_at").notNull().default(sql`CURRENT_TIMESTAMP`),
  },
  (table) => [
    index("idx_sessions_owner_status").on(table.ownerId, table.status),
  ],
);

export const turns = sqliteTable(
  "turns",
  {
    id: integer("id").primaryKey({ autoIncrement: true }),
    sessionId: text("session_id").notNull(),
    turnNumber: integer("turn_number").notNull(),
    executive: text("executive").notNull(),
    question: text("question").notNull(),
    responseText: text("response_text"),
    responseType: text("response_type"),
    isFollowup: integer("is_followup", { mode: "boolean" })
      .notNull()
      .default(false),
    createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
  },
  (table) => [
    uniqueIndex("idx_turns_session_number").on(
      table.sessionId,
      table.turnNumber,
    ),
  ],
);
