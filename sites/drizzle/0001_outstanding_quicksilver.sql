CREATE INDEX `idx_documents_owner_created` ON `documents` (`owner_id`,`created_at`);--> statement-breakpoint
CREATE INDEX `idx_sessions_owner_status` ON `sessions` (`owner_id`,`status`);--> statement-breakpoint
CREATE UNIQUE INDEX `idx_turns_session_number` ON `turns` (`session_id`,`turn_number`);