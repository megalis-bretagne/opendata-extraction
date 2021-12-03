Paramétrage Keycloak
===========================

.. warning:: Le projet nécessite de disposer d'un serveur d'authentification keycloak

Creation des clients Keycloak
--------------------

Creation des clients (application) dans l'IHM d'administration keycloak.


Client pour le projet opendata-extraction: **bearer only** (cf screen ci-dessous)

.. image:: img/keycloak-back.png


Client pour le projet opendata-front: **public** (cf screen ci-dessous)

.. image:: img/keycloak-front.png


Pas de client pour le projet  **opendata-marqueblanche** car pas de besoin d'authentification