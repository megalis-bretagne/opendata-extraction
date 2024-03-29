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
| /mq_apis/actes/v1   | /mq_apis/actes/doc   | API privée pour le frontend marque blanche délibérations                 |

## Variables d'environnement

### Envoyer les logs au format GELF

| Nom de la variable | Exemple         | Description |
| ------------------ | --------------- | ----------- |
| GELF_HOST          | logstash.domain |             |
| GELF_PORT          | 12201           |             |
| GELF_PROTO         | UDP             |             |

## Pour les développeurs

### Les dépendances

Les dépendances sont gérées par [pip-tools](https://github.com/jazzband/pip-tools).

```bash
# Dans votre environnement virtuel
pip install pip-tools
```

#### Pin les dépendances

Supprimer les fichiers [requirements.txt](./requirements.txt) et [dev-requirements.txt](./dev-requirements.txt) pour pin de nouvelles versions.

```bash
pip-compile
pip-compile dev-requirements.in
```

#### Installer les dépendances locallement

```bash
pip-sync # Pour installer iso runtime
pip-sync requirements.txt dev-requirements.txt # Pour également tirer les dépendances de dev
```
