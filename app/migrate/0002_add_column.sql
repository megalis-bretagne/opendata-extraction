ALTER TABLE publication ADD COLUMN date_publication DATETIME;
UPDATE publication SET date_publication=modified_at where etat = 1