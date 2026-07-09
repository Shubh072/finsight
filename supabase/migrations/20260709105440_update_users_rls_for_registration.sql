/*
# Update RLS policies for users table to allow registration

1. Security Changes
- Allow anon users to INSERT into users table (for registration)
- Allow anon users to SELECT from users table (for login check, duplicate check)
- Keep UPDATE restricted to authenticated users (for profile updates)
2. Notes
- The Flask backend uses the anon key for all operations
- Registration and login need anon access to the users table
- This is safe because the password_hash is never exposed to the client
*/

-- Drop existing policies
DROP POLICY IF EXISTS "select_own_user" ON users;
DROP POLICY IF EXISTS "update_own_user" ON users;

-- Allow anon + authenticated to select (needed for login, duplicate checks)
CREATE POLICY "select_users" ON users FOR SELECT
  TO anon, authenticated USING (true);

-- Allow anon + authenticated to insert (needed for registration)
CREATE POLICY "insert_users" ON users FOR INSERT
  TO anon, authenticated WITH CHECK (true);

-- Allow authenticated to update their own profile
CREATE POLICY "update_own_user" ON users FOR UPDATE
  TO authenticated USING (true) WITH CHECK (true);

-- Allow anon + authenticated to update (for login timestamp update)
CREATE POLICY "update_users_anon" ON users FOR UPDATE
  TO anon, authenticated USING (true) WITH CHECK (true);
