# TOTEM2CSV

Transformer les informations de lignes budgétaires contenues dans un fichier au format
[TOTEM](http://odm-budgetaire.org/) en fichier CSV respectant le schéma tabulaire
du [budget](https://git.opendatafrance.net/scdl/budget)

## Dépendances logicielles

- Python version 3.\*
- [xmlstarlet](http://xmlstar.sourceforge.net/)
- bash

## Installation

Pour installer les dépendances Python3 (de préférence avec un virtualenv)

```bash
pip install -r requirements.txt
```

Pour créer et activer un venv, voici un exemple:

```bash
mkdir ~/venv_datafin
cd ~/venv_datafin
source bin/activate
cd -
```

Pour installer xmlstarlet

```bash
sudo apt-get install xmlstarlet
```

## Utilisation

```bash
./totem2csv.sh <fichiertotem> <fichierplandecompte>
```

Note : le script doit être exécuté à partir du dossier du projet totem2csv

