DELETE FROM public.rss_extract_source a
USING public.rss_extract_source b
WHERE a.sn > b.sn
  AND a.src = b.src;

ALTER TABLE public.rss_extract_source
  ADD CONSTRAINT rss_extract_source_src_uniq UNIQUE (src);
