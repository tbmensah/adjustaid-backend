-- App session stamp. Nullable: existing users stay NULL until POST /session/start.

ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS last_login_at timestamptz DEFAULT NULL;
