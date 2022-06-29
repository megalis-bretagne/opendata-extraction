ALTER TABLE acte ADD COLUMN hash varchar(65);
ALTER TABLE pj_acte ADD COLUMN hash varchar(65);

ALTER TABLE parametrage ADD CONSTRAINT parametrage_UN_siren UNIQUE KEY (siren);
ALTER TABLE acte MODIFY COLUMN name varchar(300) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL;

ALTER TABLE parametrage ADD nic varchar(5) DEFAULT "00000" NOT NULL;
ALTER TABLE parametrage ADD denomination varchar(256) DEFAULT "" NOT NULL;