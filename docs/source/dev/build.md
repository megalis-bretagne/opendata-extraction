# Builder

**Prérequis**
Installer `docker`

Le build des trois applications est réalisé avec docker.

Exemple pour le projet opendata-extraction:

    # Clone the code repository into ~/dev/opendata-extraction
    mkdir -p ~/dev
    cd ~/dev
    git clone https://github.com/megalis-bretagne/opendata-extraction.git opendata-extraction

    cd ~/dev/opendata-extraction

    docker build -f Dockerfile -t opendata-extraction .
