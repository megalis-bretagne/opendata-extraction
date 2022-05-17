ALTER TABLE publication ADD COLUMN est_supprime TINYINT(1) DEFAULT 0;
ALTER TABLE parametrage ADD COLUMN publication_udata_active TINYINT(1) DEFAULT 0;