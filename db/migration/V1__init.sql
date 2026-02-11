CREATE TABLE IF NOT EXISTS rss_article (
  article_sn BIGSERIAL PRIMARY KEY,
  creator TEXT DEFAULT NULL,
  title TEXT DEFAULT NULL,
  link TEXT DEFAULT NULL,
  pubdate TIMESTAMPTZ DEFAULT NULL,
  encoded TEXT DEFAULT NULL,
  encoded_snippet TEXT DEFAULT NULL,
  content TEXT DEFAULT NULL,
  snippet TEXT DEFAULT NULL,
  guid TEXT DEFAULT NULL,
  categories TEXT DEFAULT NULL,
  isodate TIMESTAMPTZ DEFAULT NULL
);

COMMENT ON COLUMN rss_article.article_sn IS '기사순번';
COMMENT ON COLUMN rss_article.creator IS '제작자';
COMMENT ON COLUMN rss_article.title IS '기사 제목';
COMMENT ON COLUMN rss_article.link IS '원문';
COMMENT ON COLUMN rss_article.pubdate IS '발행일자';
COMMENT ON COLUMN rss_article.encoded IS '원문인코딩';
COMMENT ON COLUMN rss_article.encoded_snippet IS '요약인코딩';
COMMENT ON COLUMN rss_article.content IS '원문';
COMMENT ON COLUMN rss_article.snippet IS '요약';
COMMENT ON COLUMN rss_article.guid IS '고유값';
COMMENT ON COLUMN rss_article.categories IS '카테고리';
COMMENT ON COLUMN rss_article.isodate IS '표준시';
