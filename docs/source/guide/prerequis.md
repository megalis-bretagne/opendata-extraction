# Description de la plateforme

Dans la partie installation nous allons décrire comment déployer l'ensemble des briques opendata sur une plateforme type:
- 4 VM de 4VCPU / 8Go RAM / 20go (centos7)
- Un disque 100go volume à monter sur le VM BDD
- Cluster docker swarm composé de 3 noeuds (3 VM)
- 1 VM pour héberger la base de donneés et un volume ssh
- 1 volume sshfs (https://github.com/vieux/docker-volume-sshfs)
- Instance keyclaok


**TODO ajouter un schema ICI pour illuster notre configuration type**



**Mise à jour du système:**

    # Clone the code repository into ~/dev/opendata-extraction
    
    yum update -y 
    cat /etc/redhat-release
    CentOS Linux release 7.7.1908 (Core)

**Installation Docker**

[Suivre la documentation officielle](https://docs.docker.com/engine/install/)


**Initialisation de docker swarm**

Sur la première VM, on initialise notre swarm docker:

    docker swarm init 
    docker swarm join-token manager

    To add a manager to this swarm, run the following command:
    docker swarm join --token SWMTKN-1-5t9pofbsskv6023fw29e7efqexe3seyvsntvp5xldzgwca32x3-4xmhrvrxhe1uklk0aowtjxo3s 10.253.104.104:2377

On ajoute les deux autres VM dans notre swarm:

    docker swarm join --token SWMTKN-1-5t9pofbsskv6023fw29e7efqexe3seyvsntvp5xldzgwca32x3-4xmhrvrxhe1uklk0aowtjxo3s 10.253.104.104:2377


Vérification:

    docker node ls
    ID                            HOSTNAME            STATUS              AVAILABILITY        MANAGER STATUS      ENGINE VERSION
    5qw29uqtuhk35zagfmz3w6fux *   vm1                 Ready               Active              Leader              19.03.8
    hz2lp3fvj6ysg1116e2qmk8cl     vm2                 Ready               Active              Leader              19.03.8
    om2lqc7desf7bh8ywut3mb9ur     vm3                 Ready               Active              Leader              19.03.8


**Création d'un utilisateur**

L’idée est de monter en ssh un volume qui sera sur le serveur de bdd afin de permettre de persister des fihiers,\
Sur l'ensemble des VMs, création du user megalis :

    su - root
    adduser megalis
    passwd password


**Installation du plugin sshfs ( montage de volume ssh)**

Sur les 3 VM : génération d’une clef ssh dans /home/megalis puis diffusion de la clé publique vers la VM BDD

    su - megalis    
    ssh-keygen
    ssh-copy-id megalis@<HOST_BDD>

Sur les 3 VM du cluster swarm:

    su - root
    #1 - Install the plugin
    mkdir -p /var/lib/docker/plugins/
    docker plugin install vieux/sshfs sshkey.source=/home/megalis/.ssh/
    #creation du volume
    docker volume create -d vieux/sshfs -o sshcmd=megalis@<HOST_BDD>:/data/partage/ sshvolume
    #test du volume
    docker run -it -v sshvolume:/sshvolume busybox ls /sshvolume
