# Changelog

Tous changements importants seront journalisés dans ce fichier.

Basé sur [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added 

- BDD: Table [mq_budget_parametres_defaultvisualisation](./app/migrate/0005_create_table.sql)
- Configuration: `LOG_LEVEL`
- Configuration: `TEMP_WORKDIR_PARENT`
- Technique: module `app.shared.workdir_utils`
- Technique: mise en place du dossier [./migrations/](./migrations/) en vue d'une utilisation de flask-migrate (pas encore utilisé en prod).
- API MQ budgets: support initial pour les BP et DM
- API MQ budgets: changement de titres pour les visualisations

### Changed

- Dans `creation_publication_task`, une erreur dans l'extraction du zipfile créee aussi un fichier dans `watcher/erreurs`
- La publication vers le catalogue regionnal prend en compte le parametre d'activation de la publication de l'opendata
- Technique: Les dossiers temporaires utilisés dans les tâches de budget n'utilisent plus le `WORKDIR`

### Fixed

- Technique: refactoring des tâches de generation decp et scdl pour utiliser des repertoires temporaires

## [2.0.10] - 2022-11-22

### Fixed

- bugfix qui empêchait de traiter les fichiers zip dans certaines circonstances
- Technique: `clear_wordir` bugfix lorsqu'elle rencontre un dossier.