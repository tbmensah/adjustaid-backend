-- company optional (was NOT NULL in initial schema)

ALTER TABLE public.users ALTER COLUMN company DROP NOT NULL;
