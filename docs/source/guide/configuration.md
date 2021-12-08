# Configuration

## Présentation
Le projet [opendata-stack](https://github.com/megalis-bretagne/opendata-stack.git) est un projet exemple qui contient l'ensemble des fichiers 
de configuration nécessaire au projet opendata.

_Arborescence du projet template openda-stack_
* config
  * env1
  * env2
* outils
  * solr
* pastell
* stack
  * env1
  * env2

**Le dossier config** contient les fichiers de configuration par environnement\
* _env1/local_settings.py_ fichier de configuration pour l'environnement env1 du projet[opendata-extraction](https://github.com/megalis-bretagne/opendata-extraction.git)
* _env1/keycloak.json_ fichier de configuration keycloak pour l'environnement env1 

**Le dossier outils** contient des dossiers (solr, traefik ...)  contenant les dockerfile que nous avons customisé pour le
besoin du projet. Par exemple, nous avons ajouté dans apache solr notre schéma ainsi que les outils nécessaires pour faire de l'océrisation de fichiers PDF.

**Le dossier stack** contient les fichiers docker-compose pour déployer dans docker swarm



## Déployer la config

Pour installer le projet, il faut déployer (copier) l'ensemble de l'arborescence projet  [opendata-stack](https://github.com/megalis-bretagne/opendata-stack.git) sur 1 noeud de notre swarm docker. 
Ce noeud sera la VM depuis laquelle nous pourrons démarrer les différents services.