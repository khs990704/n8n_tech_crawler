ALTER TABLE public.rss_article
  ADD COLUMN IF NOT EXISTS src TEXT;
