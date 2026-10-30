CREATE TABLE `tv_reports` (
	`id` text PRIMARY KEY NOT NULL,
	`created_at` integer NOT NULL,
	`report` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `tv_reports_created_at` ON `tv_reports` (`created_at`);