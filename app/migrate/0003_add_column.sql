ALTER TABLE acte ADD COLUMN hash varchar(65);
ALTER TABLE pj_acte ADD COLUMN hash varchar(65);

ALTER TABLE parametrage ADD CONSTRAINT parametrage_UN_siren UNIQUE KEY (siren);
