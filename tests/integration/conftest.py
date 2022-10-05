# This file contains pytest 'fixtures'.
# If a test functions specifies the name of a fixture function as a parameter,
# the fixture function is called and its result is passed to the test function.
#
# Copyright 2014 SolidBuilds.com. All rights reserved
#
# Authors: Ling Thio <ling.thio@gmail.com>

import shutil
import pytest
import tempfile

from pathlib import Path
from testcontainers.core.generic import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
from app import create_app, db as the_db

@pytest.fixture(scope="class")
def redis() -> DockerContainer:
    print("Crée un conteneur redis")
    with DockerContainer("redis:7.0.4-alpine").with_exposed_ports(6379) as redis:
        yield redis

@pytest.fixture(scope="class")
def mariadb(request) -> DockerContainer:

    data_dir = Path(__file__).parent.resolve() / "data"
    init_db_dir = data_dir / "mariadb" / "initdb.d"
    ddl_fp = init_db_dir / "001-ddl-db.sql"
    data_fp = init_db_dir / "002-empty.sql"

    node = request.node
    marker = node.get_closest_marker('jeu_de_donnees')
    if marker is not None and str(marker.args[0]) == "donnees_variees_de_prod":
        data_fp  = init_db_dir / "010-various-data-from-prod.sql"

    print(f"Initialisation de la base avec le jeu de données {data_fp}")

    with DockerContainer("mariadb:5.5") \
        .with_exposed_ports(3306) \
        .with_env("MYSQL_ROOT_PASSWORD", "password") \
        .with_env("MYSQL_DATABASE", "data_extraction") \
        .with_env("MYSQL_USER", "datauser") \
        .with_env("MYSQL_PASSWORD", "password") \
        .with_volume_mapping(str(ddl_fp), "/docker-entrypoint-initdb.d/001-ddl.sql") \
        .with_volume_mapping(str(data_fp), "/docker-entrypoint-initdb.d/002-data.sql") as database:

        wait_for_logs(database, "port: 3306")
        yield database

@pytest.fixture(scope="class")
def solr(request) -> DockerContainer:
    solr_volumes_dir = Path(__file__).parent.resolve() / "data" / "solr" / "volumes"

    node = request.node
    marker = node.get_closest_marker('jeu_de_donnees')
    
    # Gestion du jeu de donnees
    var_solr_dp = None
    if marker is not None and str(marker.args[0]) == "donnees_variees_de_prod":
        var_solr_dp  = solr_volumes_dir / "donnees_variees_de_prod" / "var" / "solr"
    #

    container = DockerContainer("registry.csm.ovh:443/csm/open-data/solr/develop:latest")
    container = container.with_exposed_ports("8983") \
        .with_command("solr-precreate publication_core server/solr/configsets/publication_config/")
    
    with tempfile.TemporaryDirectory("it_solr_tempdir") as tmp_dir:
        
        if var_solr_dp is not None:
            print(f"Utilisation de solr avec un jeu de données: {var_solr_dp}")
            vol_dp = shutil.copytree(var_solr_dp, Path(tmp_dir) / "var_lib_solr")
            container = container.with_volume_mapping(str(vol_dp), "/var/solr", "rw")
        else:
            print(f"Utilisation de solr sans jeu de données")
        
        with container as solr_container:
            wait_for_logs(solr_container, "SolrCore [publication_core]", 60)
            yield solr_container


@pytest.fixture(scope="class")
def app(redis, mariadb, solr):
    """ Makes the 'app' parameter available to test functions. """

    redis_port = redis.get_exposed_port(6379)
    mariadb_port = mariadb.get_exposed_port(3306)
    solr_port = solr.get_exposed_port(8983)

    # Initialize the Flask-App with test-specific settings
    the_app = create_app(dict(
        TESTING=True,  # Propagate exceptions
        LOGIN_DISABLED=False,  # Enable @register_required
        MAIL_SUPPRESS_SEND=True,  # Disable Flask-Mail send

        SERVER_NAME='localhost',  # Enable url_for() without request context
        SQLALCHEMY_DATABASE_URI= f"mysql+pymysql://datauser:password@127.0.0.1:{mariadb_port}/data_extraction?charset=utf8",
        WTF_CSRF_ENABLED=False,  # Disable CSRF form validation

        CELERY_BROKER_URL = f"redis://localhost:{redis_port}/1",
        result_backend = f"redis://localhost:{redis_port}/0",

        #apche solr
        USER_SOLR='solr',
        PASSWORD_SOLR='SolrRocks',
        URL_SOLR=f"http://localhost:{solr_port}/solr/",
        INDEX_DELIB_SOLR='publication_core',

        SECRET_KEY = "test-secret-key",
        CELERY_CRON={},
    ))

    # Setup an application context (since the tests run outside of the webserver context)
    the_app.app_context().push()

    return the_app


@pytest.fixture(scope="class")
def db():
    """ Makes the 'db' parameter available to test functions. """
    return the_db

@pytest.fixture(scope="class")
def session(db, request):
    """Creates a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)

    db.session = session

    def teardown():
        transaction.rollback()
        connection.close()
        session.remove()

    request.addfinalizer(teardown)
    return session

@pytest.fixture
def client(app):
    return app.test_client()

