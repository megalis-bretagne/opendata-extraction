# Extraction open data megalis
[![Documentation Status](https://readthedocs.org/projects/opendata-megalis/badge/?version=latest)](https://opendata-megalis.readthedocs.io/fr/latest/?badge=latest)

L'application permet de gérer les publications opendata de Megalis Bretagne. 

En fonction du mode de lancement l'application:
* Expose une API REST (mode runserver)
* Déclenche des tâches périodiques (mode beat)
* Exécute des tâches (mode worker)
* Scrute un répertoire (mode watcher)


La documentation est disponible ici : https://opendata-megalis.readthedocs.io/fr/latest/

## APIs

Plusieurs APIs sont disponibles (mode runserver)

| Emplacement         | documentation        | Description                                                              |
| ------------------- | -------------------- | ------------------------------------------------------------------------ |
| /api/v1             | /doc                 | API publique exposant les statiques, le format SCDL, les données DECP... |
| /private_api/v1     | /private_api/doc     | API privée d'administration de la plateforme                             |
| /mq_apis/budgets/v1 | /mq_apis/budgets/doc | API privée pour le frontend marque blanche budgets                       |

## Variables d'environnement

### Envoyer les logs au format GELF

| Nom de la variable | Exemple         | Description |
| ------------------ | --------------- | ----------- |
| GELF_HOST          | logstash.domain |             |
| GELF_PORT          | 12201           |             |
| GELF_PROTO         | UDP             |             |