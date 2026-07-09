/*
# Create users table (multi-user, owner-scoped)

1. New Tables
- `users`
  - `user_id` (bigint, primary key, auto-increment)
  - `full_name` (varchar(150), not null)
  - `username` (varchar(50), unique, not null)
  - `email` (varchar(150), unique, not null)
  - `phone` (varchar(20), unique)
  - `password_hash` (varchar(255), not null)
  - `profile_photo` (varchar(500))
  - `role` (varchar(20), default 'user')
  - `account_status` (varchar(20), default 'active')
  - `email_verified` (boolean, default false)
  - `failed_login_attempts` (integer, default 0)
  - `last_login` (timestamp)
  - `created_at` (timestamp, default now())
  - `updated_at` (timestamp, default now())
2. Security
- Enable RLS on `users`.
- Owner-scoped CRUD: each authenticated user can only access their own rows.
3. Notes
- This table stores user profile data. Authentication is handled via JWT tokens issued by the Flask backend.
- The `user_id` is used as the identity in JWT tokens.
*/

CREATE TABLE IF NOT EXISTS users (
  user_id BIGSERIAL PRIMARY KEY,
  full_name VARCHAR(150) NOT NULL,
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(150) UNIQUE NOT NULL,
  phone VARCHAR(20) UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  profile_photo VARCHAR(500),
  role VARCHAR(20) DEFAULT 'user' NOT NULL,
  account_status VARCHAR(20) DEFAULT 'active' NOT NULL,
  email_verified BOOLEAN DEFAULT false NOT NULL,
  failed_login_attempts INTEGER DEFAULT 0 NOT NULL,
  last_login TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_user" ON users;
CREATE POLICY "select_own_user" ON users FOR SELECT
  TO authenticated USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "update_own_user" ON users;
CREATE POLICY "update_own_user" ON users FOR UPDATE
  TO authenticated USING (auth.uid()::text = user_id::text) WITH CHECK (auth.uid()::text = user_id::text);
