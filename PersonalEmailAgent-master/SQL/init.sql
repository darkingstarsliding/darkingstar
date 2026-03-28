-- ============================================================
-- PersonalEmailAgent 数据库初始化脚本
--
-- 说明：
-- 本脚本包含 4 个核心表：
--    - public.emails               （邮件主表）
--    - public.email_tag_values     （邮件标签结果）
--    - public.tag_definitions      （标签定义）
--    - public.data_agent_memories  （向量记忆/RAG）

-- 安装 pgvector（若已安装会自动跳过）
CREATE EXTENSION IF NOT EXISTS vector;

-- ------------------------------------------------------------
-- 表：public.emails
-- 用途：
--   邮件主表，保存原始邮件、处理摘要、回复草稿与处理时间。
-- 关键字段：
--   id            主键（内部数据库 ID）
--   email_id      外部邮件唯一 ID（用于幂等去重）
--   title/content 邮件标题与正文
--   sender_email  发件人邮箱
--   summary       模型提炼摘要
--   response      模型生成的回复草稿
--   received_at   接收时间
--   classified_at 分类完成时间
--   replied_at    已回复时间
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "public"."emails" (
  "id" bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "email_id" varchar(128) NOT NULL,
  "title" varchar(512) NOT NULL,
  "content" text NOT NULL,
  "sender_email" varchar(255) NOT NULL,
  "sender" varchar(255),
  "summary" text,
  "response" text,
  "received_at" timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "classified_at" timestamp(6),
  "replied_at" timestamp(6),
  "created_at" timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "emails_email_id_key" UNIQUE ("email_id")
);

ALTER TABLE "public"."emails"
  OWNER TO "postgres";

-- 常用查询索引：按接收时间排序、按发件人过滤
CREATE INDEX IF NOT EXISTS "idx_received_at"
ON "public"."emails" ("received_at");

CREATE INDEX IF NOT EXISTS "idx_sender_email"
ON "public"."emails" ("sender_email");

-- ------------------------------------------------------------
-- 表：public.email_tag_values
-- 用途：
--   保存每封邮件的标签结果。
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "public"."email_tag_values" (
  "id" bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "email_db_id" bigint NOT NULL,
  "tag_name" varchar(64) NOT NULL,
  "tag_value" varchar(128) NOT NULL,
  "source" varchar(16) NOT NULL DEFAULT 'model',
  "confidence" numeric(5,4),
  "rationale" text,
  "created_at" timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "fk_email_tag_email"
    FOREIGN KEY ("email_db_id")
    REFERENCES "public"."emails" ("id")
    ON DELETE CASCADE,
  CONSTRAINT "uq_email_tag" UNIQUE ("email_db_id", "tag_name"),
  CONSTRAINT "email_tag_values_source_check"
    CHECK ("source" IN ('model', 'manual'))
);

ALTER TABLE "public"."email_tag_values"
  OWNER TO "postgres";

CREATE INDEX IF NOT EXISTS "idx_tag_name_value"
ON "public"."email_tag_values" ("tag_name", "tag_value");

-- ------------------------------------------------------------
-- 表：public.tag_definitions
-- 用途：
--   定义系统可用标签、候选值范围与语义说明。
-- 字段：
--   name         标签名（唯一）
--   values_json  该标签允许的值（jsonb）
--   description  标签语义描述
--   enabled      是否启用该标签
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "public"."tag_definitions" (
  "id" bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "name" varchar(64) NOT NULL UNIQUE,
  "values_json" jsonb NOT NULL,
  "description" text NOT NULL,
  "enabled" bool NOT NULL DEFAULT true,
  "created_at" timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE "public"."tag_definitions"
  OWNER TO "postgres";

-- ------------------------------------------------------------
-- 表：public.data_agent_memories
-- 用途：
--   存储 Agent 的长期记忆文本与向量，用于语义检索（RAG）。
-- 字段：
--   id         主键
--   text       记忆原文
--   metadata_  JSON 元数据（如 agent_id、timestamp、type）
--   node_id    外部节点/文档 ID（可选）
--   embedding  向量列，维度 1024
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "public"."data_agent_memories" (
  "id" bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "text" varchar NOT NULL,
  "metadata_" json,
  "node_id" varchar,
  "embedding" vector(1024)
);

ALTER TABLE "public"."data_agent_memories"
  OWNER TO "postgres";

-- 仅在 metadata_ 中使用 ref_doc_id 过滤时生效
CREATE INDEX IF NOT EXISTS "agent_memories_idx_1"
ON "public"."data_agent_memories"
USING btree ((metadata_ ->> 'ref_doc_id'));
