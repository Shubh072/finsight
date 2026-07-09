/*
# Update RLS policies for all expense-related tables to allow anon access

1. Security Changes
- The Flask backend uses the anon key for all database operations
- All tables need anon access for CRUD operations
- The JWT token from Flask provides user authentication, not Supabase auth
- RLS policies now allow anon + authenticated for all operations
2. Tables Updated
- accounts, expense_categories, expenses, budgets, expense_splits
- expense_templates, favorite_merchants, expense_drafts
*/

-- accounts
DROP POLICY IF EXISTS "select_own_accounts" ON accounts;
DROP POLICY IF EXISTS "insert_own_accounts" ON accounts;
DROP POLICY IF EXISTS "update_own_accounts" ON accounts;
DROP POLICY IF EXISTS "delete_own_accounts" ON accounts;

CREATE POLICY "select_accounts" ON accounts FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "insert_accounts" ON accounts FOR INSERT TO anon, authenticated WITH CHECK (true);
CREATE POLICY "update_accounts" ON accounts FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);
CREATE POLICY "delete_accounts" ON accounts FOR DELETE TO anon, authenticated USING (true);

-- expense_categories
DROP POLICY IF EXISTS "select_own_expense_categories" ON expense_categories;
DROP POLICY IF EXISTS "insert_own_expense_categories" ON expense_categories;
DROP POLICY IF EXISTS "update_own_expense_categories" ON expense_categories;
DROP POLICY IF EXISTS "delete_own_expense_categories" ON expense_categories;

CREATE POLICY "select_expense_categories" ON expense_categories FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "insert_expense_categories" ON expense_categories FOR INSERT TO anon, authenticated WITH CHECK (true);
CREATE POLICY "update_expense_categories" ON expense_categories FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);
CREATE POLICY "delete_expense_categories" ON expense_categories FOR DELETE TO anon, authenticated USING (true);

-- expenses
DROP POLICY IF EXISTS "select_own_expenses" ON expenses;
DROP POLICY IF EXISTS "insert_own_expenses" ON expenses;
DROP POLICY IF EXISTS "update_own_expenses" ON expenses;
DROP POLICY IF EXISTS "delete_own_expenses" ON expenses;

CREATE POLICY "select_expenses" ON expenses FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "insert_expenses" ON expenses FOR INSERT TO anon, authenticated WITH CHECK (true);
CREATE POLICY "update_expenses" ON expenses FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);
CREATE POLICY "delete_expenses" ON expenses FOR DELETE TO anon, authenticated USING (true);

-- budgets
DROP POLICY IF EXISTS "select_own_budgets" ON budgets;
DROP POLICY IF EXISTS "insert_own_budgets" ON budgets;
DROP POLICY IF EXISTS "update_own_budgets" ON budgets;
DROP POLICY IF EXISTS "delete_own_budgets" ON budgets;

CREATE POLICY "select_budgets" ON budgets FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "insert_budgets" ON budgets FOR INSERT TO anon, authenticated WITH CHECK (true);
CREATE POLICY "update_budgets" ON budgets FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);
CREATE POLICY "delete_budgets" ON budgets FOR DELETE TO anon, authenticated USING (true);

-- expense_splits
DROP POLICY IF EXISTS "select_own_expense_splits" ON expense_splits;
DROP POLICY IF EXISTS "insert_own_expense_splits" ON expense_splits;
DROP POLICY IF EXISTS "update_own_expense_splits" ON expense_splits;
DROP POLICY IF EXISTS "delete_own_expense_splits" ON expense_splits;

CREATE POLICY "select_expense_splits" ON expense_splits FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "insert_expense_splits" ON expense_splits FOR INSERT TO anon, authenticated WITH CHECK (true);
CREATE POLICY "update_expense_splits" ON expense_splits FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);
CREATE POLICY "delete_expense_splits" ON expense_splits FOR DELETE TO anon, authenticated USING (true);

-- expense_templates
DROP POLICY IF EXISTS "select_own_expense_templates" ON expense_templates;
DROP POLICY IF EXISTS "insert_own_expense_templates" ON expense_templates;
DROP POLICY IF EXISTS "update_own_expense_templates" ON expense_templates;
DROP POLICY IF EXISTS "delete_own_expense_templates" ON expense_templates;

CREATE POLICY "select_expense_templates" ON expense_templates FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "insert_expense_templates" ON expense_templates FOR INSERT TO anon, authenticated WITH CHECK (true);
CREATE POLICY "update_expense_templates" ON expense_templates FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);
CREATE POLICY "delete_expense_templates" ON expense_templates FOR DELETE TO anon, authenticated USING (true);

-- favorite_merchants
DROP POLICY IF EXISTS "select_own_favorite_merchants" ON favorite_merchants;
DROP POLICY IF EXISTS "insert_own_favorite_merchants" ON favorite_merchants;
DROP POLICY IF EXISTS "update_own_favorite_merchants" ON favorite_merchants;
DROP POLICY IF EXISTS "delete_own_favorite_merchants" ON favorite_merchants;

CREATE POLICY "select_favorite_merchants" ON favorite_merchants FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "insert_favorite_merchants" ON favorite_merchants FOR INSERT TO anon, authenticated WITH CHECK (true);
CREATE POLICY "update_favorite_merchants" ON favorite_merchants FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);
CREATE POLICY "delete_favorite_merchants" ON favorite_merchants FOR DELETE TO anon, authenticated USING (true);

-- expense_drafts
DROP POLICY IF EXISTS "select_own_expense_drafts" ON expense_drafts;
DROP POLICY IF EXISTS "insert_own_expense_drafts" ON expense_drafts;
DROP POLICY IF EXISTS "update_own_expense_drafts" ON expense_drafts;
DROP POLICY IF EXISTS "delete_own_expense_drafts" ON expense_drafts;

CREATE POLICY "select_expense_drafts" ON expense_drafts FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "insert_expense_drafts" ON expense_drafts FOR INSERT TO anon, authenticated WITH CHECK (true);
CREATE POLICY "update_expense_drafts" ON expense_drafts FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);
CREATE POLICY "delete_expense_drafts" ON expense_drafts FOR DELETE TO anon, authenticated USING (true);
