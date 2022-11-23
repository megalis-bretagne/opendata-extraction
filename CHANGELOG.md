# Changelog

Tous changements importants seront journalisés dans ce fichier.

Basé sur [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added 

- Configuration: `TEMP_WORKDIR_PARENT`
- Technique: module `app.shared.workdir_utils`

### Changed

- La publication vers le catalogue regionnal prend en compte le parametre d'activation de la publication de l'opendata
- Technique: Les dossiers temporaires utilisés dans les tâches de budget n'utilisent plus le `WORKDIR`

### Fixed

- Technique: refactoring des tâches de generation decp et scdl pour utiliser des repertoires temporaires

## [2.0.10] - 2022-11-22

### Fixed

- bugfix qui empêchait de traiter les fichiers zip dans certaines circonstances
- Technique: `clear_wordir` bugfix lorsqu'elle rencontre un dossier.