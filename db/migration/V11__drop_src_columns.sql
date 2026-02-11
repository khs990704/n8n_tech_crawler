ALTER TABLE public.rss_extract_source
  DROP CONSTRAINT IF EXISTS rss_extract_source_src_uniq;

ALTER TABLE public.rss_article
  DROP COLUMN IF EXISTS src;

ALTER TABLE public.rss_extract_source
  DROP COLUMN IF EXISTS src;

ALTER TABLE IF EXISTS public.rss_extract_source
  RENAME TO schedule_logs;

ALTER TABLE IF EXISTS public.schedule_logs
  ADD COLUMN IF NOT EXISTS service TEXT;
