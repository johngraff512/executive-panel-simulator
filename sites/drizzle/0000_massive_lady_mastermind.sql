CREATE TABLE `documents` (
	`id` text PRIMARY KEY NOT NULL,
	`owner_id` text NOT NULL,
	`object_key` text NOT NULL,
	`filename` text NOT NULL,
	`status` text DEFAULT 'processing' NOT NULL,
	`analysis_json` text,
	`openai_file_id` text,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`expires_at` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `sessions` (
	`id` text PRIMARY KEY NOT NULL,
	`owner_id` text NOT NULL,
	`document_id` text NOT NULL,
	`company_name` text NOT NULL,
	`report_type` text NOT NULL,
	`executives_json` text NOT NULL,
	`question_limit` integer DEFAULT 6 NOT NULL,
	`allow_followups` integer DEFAULT true NOT NULL,
	`current_turn` integer DEFAULT 1 NOT NULL,
	`status` text DEFAULT 'active' NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updated_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE TABLE `turns` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`session_id` text NOT NULL,
	`turn_number` integer NOT NULL,
	`executive` text NOT NULL,
	`question` text NOT NULL,
	`response_text` text,
	`response_type` text,
	`is_followup` integer DEFAULT false NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
