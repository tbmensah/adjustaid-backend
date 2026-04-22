-- App user role: customer (default) vs back_office (operators). Managed in DB; promote via UPDATE.

DO $$
BEGIN
  CREATE TYPE public.user_type_enum AS ENUM ('customer', 'back_office');
EXCEPTION
  WHEN duplicate_object THEN NULL;
END;
$$;

ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS user_type public.user_type_enum NOT NULL DEFAULT 'customer';
