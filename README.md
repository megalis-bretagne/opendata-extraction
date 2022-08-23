# Extraction open data megalis
[![Documentation Status](https://readthedocs.org/projects/opendata-megalis/badge/?version=latest)](https://opendata-megalis.readthedocs.io/fr/latest/?badge=latest)

L'application permet de gérer les publications opendata de Megalis Bretagne. 

En fonction du mode de lancement l'application:
* Expose une API REST (mode runserver)
* Déclenche des tâches périodiques (mode beat)
* Exécute des tâches (mode worker)
* Scrute un répertoire (mode watcher)


La documentation est disponible ici : https://opendata-megalis.readthedocs.io/fr/latest/

## Variables d'environnement

### Envoyer les logs au format GELF

| Nom de la variable | Exemple         | Description |
| ------------------ | --------------- | ----------- |
| GELF_HOST          | logstash.domain |             |
| GELF_PORT          | 12201           |             |
| GELF_PROTO         | UDP             |             |