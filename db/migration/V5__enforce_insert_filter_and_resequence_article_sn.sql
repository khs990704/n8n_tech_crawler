ALTER TABLE public.rss_article
  ALTER COLUMN article_sn DROP DEFAULT;

CREATE OR REPLACE FUNCTION public.rss_article_filter_insert()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.categories IS NULL
    OR NEW.categories NOT IN ('{AI산업}', '{AI기술}')
  THEN
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

  IF NEW.article_sn IS NULL THEN
    NEW.article_sn := nextval('public.rss_article_article_sn_seq');
  END IF;

  RETURN NEW;
END;
$$;

DELETE FROM public.rss_article
WHERE categories IS NULL
  OR categories NOT IN ('{AI산업}', '{AI기술}');

DELETE FROM public.rss_article a
USING public.rss_article b
WHERE a.guid IS NOT NULL
  AND b.guid IS NOT NULL
  AND a.guid = b.guid
  AND a.article_sn > b.article_sn;

DO $$
DECLARE
  v_max_sn BIGINT;
  v_is_called BOOLEAN;
BEGIN
  LOCK TABLE public.rss_article IN ACCESS EXCLUSIVE MODE;

  SELECT COALESCE(MAX(article_sn), 0)
    INTO v_max_sn
  FROM public.rss_article;

  IF v_max_sn > 0 THEN
    UPDATE public.rss_article
    SET article_sn = article_sn + v_max_sn;
  END IF;

  WITH renumbered AS (
    SELECT article_sn, row_number() OVER (ORDER BY article_sn) AS new_sn
    FROM public.rss_article
  )
  UPDATE public.rss_article ra
  SET article_sn = r.new_sn
  FROM renumbered r
  WHERE ra.article_sn = r.article_sn;

  SELECT EXISTS (SELECT 1 FROM public.rss_article)
    INTO v_is_called;

  PERFORM setval(
    'public.rss_article_article_sn_seq',
    COALESCE((SELECT MAX(article_sn) FROM public.rss_article), 1),
    v_is_called
  );
END
$$;
