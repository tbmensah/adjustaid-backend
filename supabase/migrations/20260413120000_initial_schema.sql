-- Initial schema: enums + public tables aligned with app SQLAlchemy models.
-- Idempotent: safe to re-run when objects already exist.
--
-- Requires Supabase Auth: `auth.users` must exist (provided by Supabase).
-- Apply: `supabase db push` or SQL Editor.

-- -----------------------------------------------------------------------------
-- Enums (names must match SQLAlchemy pg_enum(..., name="...") definitions)
-- -----------------------------------------------------------------------------

DO $$
BEGIN
  CREATE TYPE public.token_type_enum AS ENUM ('ee', 'ff');
EXCEPTION
  WHEN duplicate_object THEN NULL;
END;
$$;

DO $$
BEGIN
  CREATE TYPE public.transaction_reason_enum AS ENUM (
    'purchase',
    'job_deduct',
    'refund',
    'manual_adjustment'
  );
EXCEPTION
  WHEN duplicate_object THEN NULL;
END;
$$;

DO $$
BEGIN
  CREATE TYPE public.stripe_status_enum AS ENUM (
    'pending',
    'completed',
    'refunded',
    'failed'
  );
EXCEPTION
  WHEN duplicate_object THEN NULL;
END;
$$;

DO $$
BEGIN
  CREATE TYPE public.job_type_enum AS ENUM ('ee', 'ff');
EXCEPTION
  WHEN duplicate_object THEN NULL;
END;
$$;

DO $$
BEGIN
  CREATE TYPE public.job_status_enum AS ENUM (
    'draft',
    'confirmed',
    'queued',
    'processing',
    'completed',
    'failed',
    'refunded'
  );
EXCEPTION
  WHEN duplicate_object THEN NULL;
END;
$$;

DO $$
BEGIN
  CREATE TYPE public.ff_pdf_type_enum AS ENUM (
    'NFIP_proof_of_loss',
    'preliminary_report',
    'xact_contents_export',
    'flood_damage_assessment'
  );
EXCEPTION
  WHEN duplicate_object THEN NULL;
END;
$$;

-- -----------------------------------------------------------------------------
-- Tables (public.users links to Supabase Auth)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  auth_id uuid NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
  email text NOT NULL,
  full_name text NOT NULL,
  company text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES public.users (id) ON DELETE CASCADE,
  job_type public.job_type_enum NOT NULL,
  status public.job_status_enum NOT NULL,
  original_filename text,
  celery_task_id text,
  picked_up_at timestamptz,
  completed_at timestamptz,
  error_message text,
  retry_count integer NOT NULL DEFAULT 0,
  max_retries integer NOT NULL DEFAULT 3,
  refunded_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.token_wallets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES public.users (id) ON DELETE CASCADE,
  ee_balance integer NOT NULL DEFAULT 0,
  ff_balance integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_token_wallets_user_id UNIQUE (user_id)
);

CREATE TABLE IF NOT EXISTS public.token_transactions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES public.users (id) ON DELETE CASCADE,
  job_id uuid REFERENCES public.jobs (id) ON DELETE SET NULL,
  token_type public.token_type_enum NOT NULL,
  amount integer NOT NULL,
  reason public.transaction_reason_enum NOT NULL,
  stripe_payment_intent_id text,
  notes text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.stripe_purchases (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES public.users (id) ON DELETE CASCADE,
  stripe_payment_intent_id text NOT NULL UNIQUE,
  stripe_session_id text NOT NULL UNIQUE,
  token_type public.token_type_enum NOT NULL,
  tokens_purchased integer NOT NULL,
  amount_cents integer NOT NULL,
  currency text NOT NULL DEFAULT 'usd',
  status public.stripe_status_enum NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.job_details_ee (
  job_id uuid PRIMARY KEY REFERENCES public.jobs (id) ON DELETE CASCADE,
  payload jsonb NOT NULL,
  output_file_key text,
  output_expires_at timestamptz
);

CREATE TABLE IF NOT EXISTS public.job_details_ff (
  job_id uuid PRIMARY KEY REFERENCES public.jobs (id) ON DELETE CASCADE,
  ff_pdf_type public.ff_pdf_type_enum NOT NULL,
  pdf_file_key text,
  esx_file_key text,
  output_file_key text,
  output_expires_at timestamptz
);

CREATE TABLE IF NOT EXISTS public.job_status_history (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id uuid NOT NULL REFERENCES public.jobs (id) ON DELETE CASCADE,
  from_status public.job_status_enum,
  to_status public.job_status_enum NOT NULL,
  celery_task_id text,
  note text,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- Indexes (names match SQLAlchemy Index definitions)
-- -----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS ix_jobs_user_id ON public.jobs (user_id);

CREATE INDEX IF NOT EXISTS ix_jobs_status ON public.jobs (status);

CREATE INDEX IF NOT EXISTS ix_jobs_status_created_at ON public.jobs (status, created_at);

CREATE INDEX IF NOT EXISTS ix_token_transactions_user_id ON public.token_transactions (user_id);

CREATE INDEX IF NOT EXISTS ix_token_transactions_job_id ON public.token_transactions (job_id);

CREATE INDEX IF NOT EXISTS ix_stripe_purchases_user_id ON public.stripe_purchases (user_id);

CREATE INDEX IF NOT EXISTS ix_job_status_history_job_id ON public.job_status_history (job_id);

-- -----------------------------------------------------------------------------
-- updated_at triggers (Postgres does not auto-maintain updated_at on UPDATE)
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_users_set_updated_at ON public.users;

CREATE TRIGGER trg_users_set_updated_at
  BEFORE UPDATE ON public.users
  FOR EACH ROW
  EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS trg_token_wallets_set_updated_at ON public.token_wallets;

CREATE TRIGGER trg_token_wallets_set_updated_at
  BEFORE UPDATE ON public.token_wallets
  FOR EACH ROW
  EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS trg_jobs_set_updated_at ON public.jobs;

CREATE TRIGGER trg_jobs_set_updated_at
  BEFORE UPDATE ON public.jobs
  FOR EACH ROW
  EXECUTE FUNCTION public.set_updated_at();
