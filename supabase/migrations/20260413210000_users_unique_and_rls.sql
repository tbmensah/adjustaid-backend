-- Users: unique auth_id + email. RLS for authenticated PostgREST clients.
-- Backend connections using postgres/service_role bypass RLS (default Supabase behavior).

-- -----------------------------------------------------------------------------
-- Unique constraints (idempotent)
-- -----------------------------------------------------------------------------

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'users_auth_id_key'
  ) THEN
    ALTER TABLE public.users ADD CONSTRAINT users_auth_id_key UNIQUE (auth_id);
  END IF;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'users_email_key'
  ) THEN
    ALTER TABLE public.users ADD CONSTRAINT users_email_key UNIQUE (email);
  END IF;
END;
$$;

-- -----------------------------------------------------------------------------
-- Row Level Security (authenticated role only; service_role / postgres bypass)
-- -----------------------------------------------------------------------------

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.token_wallets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.token_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.stripe_purchases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_details_ee ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_details_ff ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_status_history ENABLE ROW LEVEL SECURITY;

-- public.users: one profile per auth user
DROP POLICY IF EXISTS "users_select_own" ON public.users;
CREATE POLICY "users_select_own"
  ON public.users FOR SELECT TO authenticated
  USING (auth_id = auth.uid());

DROP POLICY IF EXISTS "users_insert_own" ON public.users;
CREATE POLICY "users_insert_own"
  ON public.users FOR INSERT TO authenticated
  WITH CHECK (auth_id = auth.uid());

DROP POLICY IF EXISTS "users_update_own" ON public.users;
CREATE POLICY "users_update_own"
  ON public.users FOR UPDATE TO authenticated
  USING (auth_id = auth.uid())
  WITH CHECK (auth_id = auth.uid());

DROP POLICY IF EXISTS "users_delete_own" ON public.users;
CREATE POLICY "users_delete_own"
  ON public.users FOR DELETE TO authenticated
  USING (auth_id = auth.uid());

-- Helper expression: rows belonging to current auth user (via public.users.id)
-- jobs
DROP POLICY IF EXISTS "jobs_all_own" ON public.jobs;
CREATE POLICY "jobs_all_own"
  ON public.jobs FOR ALL TO authenticated
  USING (
    user_id IN (SELECT u.id FROM public.users u WHERE u.auth_id = auth.uid())
  )
  WITH CHECK (
    user_id IN (SELECT u.id FROM public.users u WHERE u.auth_id = auth.uid())
  );

-- token_wallets
DROP POLICY IF EXISTS "token_wallets_all_own" ON public.token_wallets;
CREATE POLICY "token_wallets_all_own"
  ON public.token_wallets FOR ALL TO authenticated
  USING (
    user_id IN (SELECT u.id FROM public.users u WHERE u.auth_id = auth.uid())
  )
  WITH CHECK (
    user_id IN (SELECT u.id FROM public.users u WHERE u.auth_id = auth.uid())
  );

-- token_transactions
DROP POLICY IF EXISTS "token_transactions_all_own" ON public.token_transactions;
CREATE POLICY "token_transactions_all_own"
  ON public.token_transactions FOR ALL TO authenticated
  USING (
    user_id IN (SELECT u.id FROM public.users u WHERE u.auth_id = auth.uid())
  )
  WITH CHECK (
    user_id IN (SELECT u.id FROM public.users u WHERE u.auth_id = auth.uid())
  );

-- stripe_purchases
DROP POLICY IF EXISTS "stripe_purchases_all_own" ON public.stripe_purchases;
CREATE POLICY "stripe_purchases_all_own"
  ON public.stripe_purchases FOR ALL TO authenticated
  USING (
    user_id IN (SELECT u.id FROM public.users u WHERE u.auth_id = auth.uid())
  )
  WITH CHECK (
    user_id IN (SELECT u.id FROM public.users u WHERE u.auth_id = auth.uid())
  );

-- job_details_ee (scoped via job ownership)
DROP POLICY IF EXISTS "job_details_ee_all_own" ON public.job_details_ee;
CREATE POLICY "job_details_ee_all_own"
  ON public.job_details_ee FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1
      FROM public.jobs j
      INNER JOIN public.users u ON u.id = j.user_id
      WHERE j.id = job_id AND u.auth_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1
      FROM public.jobs j
      INNER JOIN public.users u ON u.id = j.user_id
      WHERE j.id = job_id AND u.auth_id = auth.uid()
    )
  );

-- job_details_ff
DROP POLICY IF EXISTS "job_details_ff_all_own" ON public.job_details_ff;
CREATE POLICY "job_details_ff_all_own"
  ON public.job_details_ff FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1
      FROM public.jobs j
      INNER JOIN public.users u ON u.id = j.user_id
      WHERE j.id = job_id AND u.auth_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1
      FROM public.jobs j
      INNER JOIN public.users u ON u.id = j.user_id
      WHERE j.id = job_id AND u.auth_id = auth.uid()
    )
  );

-- job_status_history
DROP POLICY IF EXISTS "job_status_history_all_own" ON public.job_status_history;
CREATE POLICY "job_status_history_all_own"
  ON public.job_status_history FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1
      FROM public.jobs j
      INNER JOIN public.users u ON u.id = j.user_id
      WHERE j.id = job_id AND u.auth_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1
      FROM public.jobs j
      INNER JOIN public.users u ON u.id = j.user_id
      WHERE j.id = job_id AND u.auth_id = auth.uid()
    )
  );
