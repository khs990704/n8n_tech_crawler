DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relkind = 'S'
      AND n.nspname = 'public'
      AND c.relname = 'rss_article_article_sn_seq'
  ) THEN
    CREATE SEQUENCE public.rss_article_article_sn_seq;
  END IF;
END
$$;

ALTER TABLE public.rss_article
  ALTER COLUMN article_sn SET DEFAULT nextval('public.rss_article_article_sn_seq');

ALTER SEQUENCE public.rss_article_article_sn_seq
  OWNED BY public.rss_article.article_sn;
