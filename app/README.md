# app directory

This directory contains the Flask application code.

The code has been organized into the following sub-directories:

    # Sub-directories
    commands     # Commands made available to manage.py
    models       # Database Models
    shared       # external code
    tasks        # celery task
    controller   # REST api endpoint




select siren, open_data_active from parametrage where open_data_active is false;
select * from publication where siren in (select siren from parametrage where open_data_active is false);


select count(distinct(siren)), acte_nature, count(*) from publication group by acte_nature;
select count(distinct(siren)), acte_nature from publication group by acte_nature;

select * from user where username like '%mohon%';

select 
DECODE_ORACLE(acte_nature, 1, 'Délibérations', 5, 'Budgets') as 'Document', 
DECODE_ORACLE(publication_open_data, 0, 'oui', 1, 'non', 2, 'ne sais pas') as 'Choix-pastel', 
DECODE_ORACLE(etat, 1, 'publié', 0, 'non publié', 3, 'en erreur') as 'Etat', 
count(*) as nb from publication  where created_at < '2022-02-01' group by publication_open_data, acte_nature, etat order by nb desc;

select t0.siren, nbOui, nbNon, nbNeSaisPas, nbNon *100 / (nbOui+nbNon) as tauxDeNonPublié
from (select distinct(siren) from publication) t0
left join (select siren, count(*) as nbOui from publication where publication_open_data = 0 group by siren) t1 on t0.siren = t1.siren
left join (select siren, count(*) as nbNon from publication where publication_open_data = 1 group by siren) t2 on t0.siren = t2.siren 
left join (select siren, count(*) as nbNeSaisPas from publication where publication_open_data = 2 group by siren) t3 on t0.siren = t3.siren 
order by tauxDeNonPublié desc;

select t0.siren, nbOui, nbNon, nbNeSaisPas, nbNon *100 / (nbOui+nbNon) as tauxDeNonPublié
from (select distinct(siren) from publication) t0
left join (select siren, count(*) as nbOui from publication where publication_open_data = 0 group by siren) t1 on t0.siren = t1.siren
left join (select siren, count(*) as nbNon from publication where publication_open_data = 1 group by siren) t2 on t0.siren = t2.siren 
left join (select siren, count(*) as nbNeSaisPas from publication where publication_open_data = 2 group by siren) t3 on t0.siren = t3.siren 
order by tauxDeNonPublié desc;

select siren, count(*) as nbNon from publication where publication_open_data = 1 group by siren order by nbNon desc;

select est_masque, count(*) from publication group by est_masque;


select distinct(siren) from publication;

select DATE_FORMAT(created_at, '%w'), count(*) as nb  from publication group by DATE_FORMAT(created_at, '%w') order by nb desc;
select DATE_FORMAT(created_at, '%k'), count(*) as nb  from publication group by DATE_FORMAT(created_at, '%k') order by nb desc;

select * from publication;

select siren, count(*) as nbOui from publication where publication_open_data = 0 group by siren;
select siren, count(*) as nbOui from publication where publication_open_data = 1 group by siren;