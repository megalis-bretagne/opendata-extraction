# Présentation du projet

## Résumé
Le projet à pour but d'automatiser la publication et la gestion de différents jeux de données en open data depuis la plateforme de services de Mégalis Bretagne.

Actuellement, il permet la génération et la publication des jeux de données suivants:
* les délibérations ([fichier annuel au format SCDL délibération](https://scdl.opendatafrance.net/docs/schemas/deliberations.html)  et fichier PDF sur marque blanche)
* les budgets ([fichier annuel au format SCDL budget](https://scdl.opendatafrance.net/docs/schemas/budget.html) et fichier PDF sur marque blanche)
* les marchés publiques ([fichier annuel format-commande-publique](https://github.com/139bercy/format-commande-publique))

Une IHM permet aux utilisateurs de gérér leurs publications et des APIs sont disponibles pour automatiser différentes actions.

Enfin, une réutilisation de [la marque blanche de gironde numérique](https://gitlab.adullact.net/gironde-numerique/data-search-engine) est possible.


##Schéma d'architecture
![architecture](img/img.png)

## Les projets

### Projet : opendata-extraction
Repo : https://github.com/megalis-bretagne/opendata-extraction.git

**Les Technologies utilisées**
* Python 3.9
* Flask
* Celery
* SQLAlchemy
* Apache Solr
* Mysql

### Projet : opendata-frontapp
Repo : https://github.com/megalis-bretagne/opendata-frontapp.git

**Les Technologies utilisées**
* Angular 11
* Angular Material
* NGRX

### Projet : marque blanche
Repo : https://github.com/megalis-bretagne/opendata-marque-blanche.git
**Les Technologies utilisées**
* PHP > 7.2
* Extension Apache Solr
* Apache Solr



