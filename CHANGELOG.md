# Changelog

Tous changements importants seront journalisés dans ce fichier.

Basé sur [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Changed

- API MQ Delibs: les annexes renvoient leurs content-type

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