DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'schedule_logs'
      AND column_name = 'extract_date'
  ) THEN
    ALTER TABLE public.schedule_logs
      RENAME COLUMN extract_date TO latest_date;
  END IF;
END
$$;
