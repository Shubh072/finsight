/*
# Create budgets, expense_splits, expense_templates, favorite_merchants, expense_drafts tables

1. New Tables
- `budgets`
  - `id` (bigint, primary key)
  - `user_id` (bigint, FK to users)
  - `category` (varchar(80), not null)
  - `limit_amount` (numeric(18,2), not null)
  - `period` (varchar(20), default 'monthly')
  - `start_date` (date)
  - `end_date` (date)
  - `created_at`, `updated_at`, `is_deleted`, `deleted_at`

- `expense_splits`
  - `id` (bigint, primary key)
  - `expense_id` (bigint, FK to expenses)
  - `user_id` (bigint, FK to users)
  - `split_with_name` (varchar(150), not null)
  - `split_type` (varchar(20): 'friends', 'family', 'office', 'custom')
  - `split_method` (varchar(20): 'equal', 'percentage', 'custom')
  - `amount` (numeric(18,2), not null)
  - `percentage` (numeric(5,2))
  - `created_at`

- `expense_templates`
  - `id` (bigint, primary key)
  - `user_id` (bigint, FK to users)
  - `name` (varchar(150), not null)
  - `template_data` (jsonb, not null)
  - `created_at`, `updated_at`

- `favorite_merchants`
  - `id` (bigint, primary key)
  - `user_id` (bigint, FK to users)
  - `merchant_name` (varchar(180), not null)
  - `category` (varchar(80))
  - `default_payment_method` (varchar(60))
  - `default_account_id` (bigint)
  - `usage_count` (integer, default 0)
  - `created_at`

- `expense_drafts`
  - `id` (bigint, primary key)
  - `user_id` (bigint, FK to users)
  - `draft_data` (jsonb, not null)
  - `created_at`, `updated_at`

2. Security
- Enable RLS on all tables.
- Owner-scoped CRUD via user_id checks.
*/

CREATE TABLE IF NOT EXISTS budgets (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  category VARCHAR(80) NOT NULL,
  limit_amount NUMERIC(18,2) NOT NULL,
  period VARCHAR(20) DEFAULT 'monthly' NOT NULL,
  start_date DATE,
  end_date DATE,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  is_deleted BOOLEAN DEFAULT false NOT NULL,
  deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_budgets_user_id ON budgets(user_id);
CREATE INDEX IF NOT EXISTS idx_budgets_category ON budgets(category);

ALTER TABLE budgets ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_budgets" ON budgets;
CREATE POLICY "select_own_budgets" ON budgets FOR SELECT
  TO authenticated USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "insert_own_budgets" ON budgets;
CREATE POLICY "insert_own_budgets" ON budgets FOR INSERT
  TO authenticated WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "update_own_budgets" ON budgets;
CREATE POLICY "update_own_budgets" ON budgets FOR UPDATE
  TO authenticated USING (auth.uid()::text = user_id::text) WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "delete_own_budgets" ON budgets;
CREATE POLICY "delete_own_budgets" ON budgets FOR DELETE
  TO authenticated USING (auth.uid()::text = user_id::text);


CREATE TABLE IF NOT EXISTS expense_splits (
  id BIGSERIAL PRIMARY KEY,
  expense_id BIGINT NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
  user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  split_with_name VARCHAR(150) NOT NULL,
  split_type VARCHAR(20) DEFAULT 'custom',
  split_method VARCHAR(20) DEFAULT 'equal',
  amount NUMERIC(18,2) NOT NULL,
  percentage NUMERIC(5,2),
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_expense_splits_expense_id ON expense_splits(expense_id);
CREATE INDEX IF NOT EXISTS idx_expense_splits_user_id ON expense_splits(user_id);

ALTER TABLE expense_splits ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_expense_splits" ON expense_splits;
CREATE POLICY "select_own_expense_splits" ON expense_splits FOR SELECT
  TO authenticated USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "insert_own_expense_splits" ON expense_splits;
CREATE POLICY "insert_own_expense_splits" ON expense_splits FOR INSERT
  TO authenticated WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "update_own_expense_splits" ON expense_splits;
CREATE POLICY "update_own_expense_splits" ON expense_splits FOR UPDATE
  TO authenticated USING (auth.uid()::text = user_id::text) WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "delete_own_expense_splits" ON expense_splits;
CREATE POLICY "delete_own_expense_splits" ON expense_splits FOR DELETE
  TO authenticated USING (auth.uid()::text = user_id::text);


CREATE TABLE IF NOT EXISTS expense_templates (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  name VARCHAR(150) NOT NULL,
  template_data JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_expense_templates_user_id ON expense_templates(user_id);

ALTER TABLE expense_templates ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_expense_templates" ON expense_templates;
CREATE POLICY "select_own_expense_templates" ON expense_templates FOR SELECT
  TO authenticated USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "insert_own_expense_templates" ON expense_templates;
CREATE POLICY "insert_own_expense_templates" ON expense_templates FOR INSERT
  TO authenticated WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "update_own_expense_templates" ON expense_templates;
CREATE POLICY "update_own_expense_templates" ON expense_templates FOR UPDATE
  TO authenticated USING (auth.uid()::text = user_id::text) WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "delete_own_expense_templates" ON expense_templates;
CREATE POLICY "delete_own_expense_templates" ON expense_templates FOR DELETE
  TO authenticated USING (auth.uid()::text = user_id::text);


CREATE TABLE IF NOT EXISTS favorite_merchants (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  merchant_name VARCHAR(180) NOT NULL,
  category VARCHAR(80),
  default_payment_method VARCHAR(60),
  default_account_id BIGINT,
  usage_count INTEGER DEFAULT 0 NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_favorite_merchants_user_id ON favorite_merchants(user_id);

ALTER TABLE favorite_merchants ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_favorite_merchants" ON favorite_merchants;
CREATE POLICY "select_own_favorite_merchants" ON favorite_merchants FOR SELECT
  TO authenticated USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "insert_own_favorite_merchants" ON favorite_merchants;
CREATE POLICY "insert_own_favorite_merchants" ON favorite_merchants FOR INSERT
  TO authenticated WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "update_own_favorite_merchants" ON favorite_merchants;
CREATE POLICY "update_own_favorite_merchants" ON favorite_merchants FOR UPDATE
  TO authenticated USING (auth.uid()::text = user_id::text) WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "delete_own_favorite_merchants" ON favorite_merchants;
CREATE POLICY "delete_own_favorite_merchants" ON favorite_merchants FOR DELETE
  TO authenticated USING (auth.uid()::text = user_id::text);


CREATE TABLE IF NOT EXISTS expense_drafts (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  draft_data JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_expense_drafts_user_id ON expense_drafts(user_id);

ALTER TABLE expense_drafts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_expense_drafts" ON expense_drafts;
CREATE POLICY "select_own_expense_drafts" ON expense_drafts FOR SELECT
  TO authenticated USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "insert_own_expense_drafts" ON expense_drafts;
CREATE POLICY "insert_own_expense_drafts" ON expense_drafts FOR INSERT
  TO authenticated WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "update_own_expense_drafts" ON expense_drafts;
CREATE POLICY "update_own_expense_drafts" ON expense_drafts FOR UPDATE
  TO authenticated USING (auth.uid()::text = user_id::text) WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "delete_own_expense_drafts" ON expense_drafts;
CREATE POLICY "delete_own_expense_drafts" ON expense_drafts FOR DELETE
  TO authenticated USING (auth.uid()::text = user_id::text);
