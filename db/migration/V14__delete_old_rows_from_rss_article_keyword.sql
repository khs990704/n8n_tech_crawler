DELETE FROM public.rss_article_keyword
WHERE date < (CURRENT_DATE - INTERVAL '30 day');
