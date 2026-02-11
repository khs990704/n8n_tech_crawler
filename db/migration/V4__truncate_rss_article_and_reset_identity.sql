TRUNCATE TABLE public.rss_article RESTART IDENTITY;

CREATE OR REPLACE FUNCTION public.rss_article_filter_insert()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.categories NOT IN ('{AI산업}', '{AI기술}') THEN
    RETURN NULL;
  END IF;

  IF NEW.guid IS NOT NULL
    AND EXISTS (
      SELECT 1
      FROM public.rss_article ra
      WHERE ra.guid = NEW.guid
    )
  THEN
    RETURN NULL;
  END IF;

  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_rss_article_filter_insert ON public.rss_article;

CREATE TRIGGER trg_rss_article_filter_insert
BEFORE INSERT ON public.rss_article
FOR EACH ROW
EXECUTE FUNCTION public.rss_article_filter_insert();
