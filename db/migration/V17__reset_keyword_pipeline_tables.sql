TRUNCATE TABLE public.keyword_info RESTART IDENTITY;

TRUNCATE TABLE public.rss_article_keyword RESTART IDENTITY;

DELETE FROM public.schedule_logs
WHERE service = 'RSS';
