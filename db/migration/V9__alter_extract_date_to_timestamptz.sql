ALTER TABLE public.rss_extract_source
  ALTER COLUMN extract_date TYPE TIMESTAMPTZ
  USING extract_date::timestamptz;

ALTER TABLE public.rss_extract_source
  ALTER COLUMN extract_date SET DEFAULT CURRENT_TIMESTAMP;
