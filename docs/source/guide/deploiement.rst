**********
Déploiement
**********

.. note:: Les commandes de déploiement doivent être réalisée depuis la VM ou les fichiers de configuration ont été déposés et se positionner dans le répertoire de configuration pour effectuer les commandes.


opendata-extraction
===================

.. code-block:: bash

  docker stack deploy -c stack/prod/solr.yml data
  docker stack deploy -c stack/prod/extraction-data.yml data


opendata-marqueblanche
===================

.. code-block:: bash

  docker stack deploy -c stack/prod/marqueblanche.yml data


opendata-front
===================


.. code-block:: bash

  docker stack deploy -c stack/prod/front-data.yml data