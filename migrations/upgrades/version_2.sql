ALTER TABLE athlete ADD COLUMN auth_code TEXT NOT NULL DEFAULT '';
--adding new version with "auth" column


UPDATE db_version SET version = 2;
