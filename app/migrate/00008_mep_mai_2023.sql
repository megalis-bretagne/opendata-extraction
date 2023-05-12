ALTER TABLE data_extraction.parametrage ADD publication_annexes BOOL DEFAULT true NOT NULL;
ALTER TABLE data_extraction.pj_acte ADD publie BOOL NULL;
-- Feature 38 - dates arrêtés.
ALTER TABLE data_extraction.publication ADD date_ar DATETIME NULL;
