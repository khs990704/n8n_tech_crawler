ALTER TABLE public.rss_article_keyword
  ADD COLUMN IF NOT EXISTS article_sn BIGINT;
