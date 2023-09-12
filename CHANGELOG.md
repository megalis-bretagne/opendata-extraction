# Changelog

Tous changements importants seront journalisés dans ce fichier.

Basé sur [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Corrections

- Chemin des zip archivés corrigé, les jours et les mois sont sur deux digits
- Correction du chemin des publications dans `/private/publications`
- Fix bug de collision de nom dans les URL publics de fichier lors d'une publication / depublication de plusieurs actes ayant des documents identiques
- Mise à jour de python vers 3.11.5
- fix de l'export csv des déliberations et des actes.

## [2.0.21]

### Hotfix

- Technique: nettoyage des tâches persistées au bout de 7 jours.

## [2.0.20]

### Corrections

- fix execution des tests unitaires.

## [2.0.19]

### Ajouts

- Upgrade python to 3.11.3

### Changements

- Changement de la manière de déclarer les dépendances. voir [README](./README.md)
- Nettoyage dans les dépendances actuelles.
- Ajout d'une authentification de type 'apiKey' dans les interface swagger pour les endpoints concernés.

### Corrections

- Support du format ISO 8601 abregé pour `date_de_lacte` (grâce à l'upgrade vers python 3.11)

### Changement techniques

- Ajout de l'option [`result_extended`](https://docs.celeryq.dev/en/latest/userguide/configuration.html#result-extended) pour celery.

## [2.0.18] - 2023-05-16

### Important

- Migration bdd: [00008_mep_mai_2023.sql](./app/migrate/00008_mep_mai_2023.sql)

### Ajouts

- Utilisation de l'information de `date_ar`.
- Alimentation de `DATE_PREF` pour les SCDL deliberation à partir de `date_ar`
- Upgrade python to 3.10.8
- Feature publication des annexes ([issue](https://https://github.com/megalis-bretagne/opendata-marqueblanche/issues/3))
  - Ajout d'une API pour prendre en compte les commandes de publications de pièces jointes dans `/private_api/private_api/v1/publication/pieces_jointes/`
  - Ajout d'un flag `publication_des_annexes` au sein du parametrage
  - Ajout d'un champ `publie` au modèle des `pieces_jointes`

### Changements

- Divers refactoring
- Refactoring search publication
- Ajout du filtre `pastell_id_d` sur le search light
- Force la declaration xml lors de l'export des decp

## [2.0.17] - 2023-04-11

### Fixed

- MEGALIS-304 - R-168370 Erreur de publication opendata malgré script de rejeu
- déclaration incorrecte d'encodage des fichiers xml  [issue github ](https://github.com/megalis-bretagne/opendata-extraction/issues/16)


## [2.0.16] - 2023-02-07

### Fixed

- Le watcher gère le cas ou le fichier reçu est supprimé par un acteur externe.

### Changed

- Lors de la lecture des actes (`watcher/in`). Rend plus robueste l'extraction de l'`id_d`.
- [BUDGET] Niveau de log warn pour les resources budgetaires exclues car non trouvées dans l'api entreprise

## [2.0.14] - 2023-01-24

### Fixed

- [BUDGETS] bug dans comparaisons de date de scellement


## [2.0.13] - 2023-01-18

### Changed

- API MQ budgets: Ajout des plans de comptes pour l'année 2023
- API MQ actes: Ajout de robustesse lors de la recherche, si pas d'actes lié à l'annexe alors on ignore l'annexe 
- publication task: Correction des recherches solr, utilisation du mode cursor lors des recherches- https://dev.sib.fr/bts/browse/MEGALIS-294

## [2.0.12] - 2023-01-10

### Added

- Ajout de métriques prometheus.
- BDD: Ajout d'un champ `pastell_id_d` dans la table `publication` [sql migration](./app/migrate/00007_add_pastell_id_d_column.sql)


### Changed

- API MQ budgets: Au cas ou on a plusieurs documents pour BP ou CA. On prend le plus récent par date de scellement.
- API MQ budgets: La lecture de données budgetaires génère l'écriture du scdl sur disque dans `private/publications`
- API MQ Delibs: les annexes renvoient leurs content-type
- Au sein de solr, documenttype plus précis pour les documents hors prefecture. Documents à réindexer.
- S'assure que le champ `objet` des metadata pastell est bien encodé en `latin-1`
- Désormais, les archives/erreurs suivent cette nomenclature:
  - `watcher/archives/ANNEE/MOIS/JOUR/ID_D-TASK_DI.zip`
  - `watcher/erreurs/ID_D-TASK_DI.zip`
- [gh-29](https://https://github.com/megalis-bretagne/opendata-extraction/issues/29) Ajout de l'ID_D dans la table de publication
- Les tests unitaires sont uniquement joués pour la branche `master`
- On désactive les warning de waitress concernant sa task queue

## [2.0.11] - 2022-12-07

### Added 

- BDD: Table [mq_budget_parametres_defaultvisualisation](./app/migrate/0005_create_table.sql)
- Configuration: `LOG_LEVEL`
- Configuration: `TEMP_WORKDIR_PARENT`
- Technique: module `app.shared.workdir_utils`
- Technique: mise en place du dossier [./migrations/](./migrations/) en vue d'une utilisation de flask-migrate (pas encore utilisé en prod).
- API MQ budgets: support initial pour les BP et DM
- API MQ budgets: changement de titres pour les visualisations
- API /private_api/v1/publication/search/light: Création d'une API pour rechercher les publications, dans le but de les comparer aux documents pastell via leurs api et ainsi detecter les docs non reçu.

### Changed

- Dans `creation_publication_task`, une erreur dans l'extraction du zipfile créee aussi un fichier dans `watcher/erreurs`
- Le watcher s'assure maintenant que les fichiers reçus soient bel et bien des fichiers zip.
- La publication vers le catalogue regionnal prend en compte le parametre d'activation de la publication de l'opendata
- Technique: Les dossiers temporaires utilisés dans les tâches de budget n'utilisent plus le `WORKDIR`

### Fixed

- Technique: refactoring des tâches de generation decp et scdl pour utiliser des repertoires temporaires

## [2.0.10] - 2022-11-22

### Fixed

- bugfix qui empêchait de traiter les fichiers zip dans certaines circonstances
- Technique: `clear_wordir` bugfix lorsqu'elle rencontre un dossier.
