ALTER TABLE rss_article
  ADD CONSTRAINT rss_article_guid_uniq UNIQUE (guid);
