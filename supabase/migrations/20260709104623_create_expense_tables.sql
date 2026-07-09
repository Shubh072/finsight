/*
# Create accounts, expense_categories, and expenses tables

1. New Tables
- `accounts`
  - `id` (bigint, primary key, auto-increment)
  - `user_id` (bigint, FK to users.user_id, not null)
  - `name` (varchar(120), not null)
  - `account_type` (varchar(50))
  - `created_at`, `updated_at`, `is_deleted`, `deleted_at` (audit fields)

- `expense_categories`
  - `id` (bigint, primary key, auto-increment)
  - `user_id` (bigint, FK to users.user_id, not null)
  - `name` (varchar(80), not null)
  - `icon` (varchar(120))
  - `color` (varchar(50))
  - `category_image` (varchar(500))
  - `created_at`, `updated_at`, `is_deleted`, `deleted_at` (audit fields)

- `expenses`
  - `id` (bigint, primary key, auto-increment)
  - `user_id` (bigint, FK to users.user_id, not null)
  - `title` (varchar(200), not null)
  - `category` (varchar(80), not null)
  - `sub_category` (varchar(80))
  - `amount` (numeric(18,2), not null)
  - `expense_date` (date, not null)
  - `payment_method` (varchar(60), not null)
  - `account_id` (bigint, FK to accounts.id)
  - `merchant_name` (varchar(180))
  - `location` (varchar(180))
  - `description` (text)
  - `tags_json` (jsonb)
  - `recurring` (boolean, default false)
  - `recurring_frequency` (varchar(20))
  - `currency` (varchar(10), default 'USD')
  - `priority` (integer)
  - `mood` (varchar(80))
  - `status` (varchar(30), default 'active')
  - `normalized_title` (varchar(255))
  - `fingerprint` (varchar(64))
  - `receipt_filename` (varchar(255))
  - `receipt_url` (varchar(500))
  - `receipt_mime` (varchar(120))
  - `receipt_size` (bigint)
  - `receipt_ocr_text` (text)
  - `receipt_ocr_confidence` (numeric(5,2))
  - `ocr_ready` (boolean, default false)
  - `tax_included` (numeric(18,2))
  - `invoice_number` (varchar(100))
  - `receipt_number` (varchar(100))
  - `gst` (varchar(50))
  - `budget_id` (bigint)
  - `notes` (text)
  - `created_at`, `updated_at`, `is_deleted`, `deleted_at` (audit fields)

2. Indexes
- Indexes on user_id, category, expense_date, status, merchant_name, normalized_title, fingerprint, is_deleted for fast queries

3. Security
- Enable RLS on all tables.
- Owner-scoped CRUD via user_id checks.
*/

CREATE TABLE IF NOT EXISTS accounts (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  name VARCHAR(120) NOT NULL,
  account_type VARCHAR(50),
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  is_deleted BOOLEAN DEFAULT false NOT NULL,
  deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts(user_id);

ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_accounts" ON accounts;
CREATE POLICY "select_own_accounts" ON accounts FOR SELECT
  TO authenticated USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "insert_own_accounts" ON accounts;
CREATE POLICY "insert_own_accounts" ON accounts FOR INSERT
  TO authenticated WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "update_own_accounts" ON accounts;
CREATE POLICY "update_own_accounts" ON accounts FOR UPDATE
  TO authenticated USING (auth.uid()::text = user_id::text) WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "delete_own_accounts" ON accounts;
CREATE POLICY "delete_own_accounts" ON accounts FOR DELETE
  TO authenticated USING (auth.uid()::text = user_id::text);


CREATE TABLE IF NOT EXISTS expense_categories (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  name VARCHAR(80) NOT NULL,
  icon VARCHAR(120),
  color VARCHAR(50),
  category_image VARCHAR(500),
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  is_deleted BOOLEAN DEFAULT false NOT NULL,
  deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_expense_categories_user_id ON expense_categories(user_id);

ALTER TABLE expense_categories ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_expense_categories" ON expense_categories;
CREATE POLICY "select_own_expense_categories" ON expense_categories FOR SELECT
  TO authenticated USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "insert_own_expense_categories" ON expense_categories;
CREATE POLICY "insert_own_expense_categories" ON expense_categories FOR INSERT
  TO authenticated WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "update_own_expense_categories" ON expense_categories;
CREATE POLICY "update_own_expense_categories" ON expense_categories FOR UPDATE
  TO authenticated USING (auth.uid()::text = user_id::text) WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "delete_own_expense_categories" ON expense_categories;
CREATE POLICY "delete_own_expense_categories" ON expense_categories FOR DELETE
  TO authenticated USING (auth.uid()::text = user_id::text);


CREATE TABLE IF NOT EXISTS expenses (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  title VARCHAR(200) NOT NULL,
  category VARCHAR(80) NOT NULL,
  sub_category VARCHAR(80),
  amount NUMERIC(18,2) NOT NULL,
  expense_date DATE NOT NULL,
  payment_method VARCHAR(60) NOT NULL,
  account_id BIGINT REFERENCES accounts(id) ON DELETE SET NULL,
  merchant_name VARCHAR(180),
  location VARCHAR(180),
  description TEXT,
  tags_json JSONB,
  recurring BOOLEAN DEFAULT false NOT NULL,
  recurring_frequency VARCHAR(20),
  currency VARCHAR(10) DEFAULT 'USD',
  priority INTEGER,
  mood VARCHAR(80),
  status VARCHAR(30) DEFAULT 'active' NOT NULL,
  normalized_title VARCHAR(255),
  fingerprint VARCHAR(64),
  receipt_filename VARCHAR(255),
  receipt_url VARCHAR(500),
  receipt_mime VARCHAR(120),
  receipt_size BIGINT,
  receipt_ocr_text TEXT,
  receipt_ocr_confidence NUMERIC(5,2),
  ocr_ready BOOLEAN DEFAULT false NOT NULL,
  tax_included NUMERIC(18,2),
  invoice_number VARCHAR(100),
  receipt_number VARCHAR(100),
  gst VARCHAR(50),
  budget_id BIGINT,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  is_deleted BOOLEAN DEFAULT false NOT NULL,
  deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_expenses_user_id ON expenses(user_id);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);
CREATE INDEX IF NOT EXISTS idx_expenses_expense_date ON expenses(expense_date);
CREATE INDEX IF NOT EXISTS idx_expenses_status ON expenses(status);
CREATE INDEX IF NOT EXISTS idx_expenses_merchant_name ON expenses(merchant_name);
CREATE INDEX IF NOT EXISTS idx_expenses_normalized_title ON expenses(normalized_title);
CREATE INDEX IF NOT EXISTS idx_expenses_fingerprint ON expenses(fingerprint);
CREATE INDEX IF NOT EXISTS idx_expenses_is_deleted ON expenses(is_deleted);

ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_expenses" ON expenses;
CREATE POLICY "select_own_expenses" ON expenses FOR SELECT
  TO authenticated USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "insert_own_expenses" ON expenses;
CREATE POLICY "insert_own_expenses" ON expenses FOR INSERT
  TO authenticated WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "update_own_expenses" ON expenses;
CREATE POLICY "update_own_expenses" ON expenses FOR UPDATE
  TO authenticated USING (auth.uid()::text = user_id::text) WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "delete_own_expenses" ON expenses;
CREATE POLICY "delete_own_expenses" ON expenses FOR DELETE
  TO authenticated USING (auth.uid()::text = user_id::text);
