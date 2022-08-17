# __init__.py is a special Python file that allows a directory to become
# a Python package so it can be accessed using the 'import' statement.
import logging

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
migrate = Migrate()

from flask_cors import CORS
from flask_oidc import OpenIDConnect
oidc = OpenIDConnect()


# Instantiate Flask extensions
from app import celeryapp
from app.controller import api

from app.shared.logger_utils import create_or_get_gelf_loghandler

def create_app(extra_config_settings={},oidcEnable=True):
    """Create a Flask application.
    """

    # Logging
    gelf_log_handler = create_or_get_gelf_loghandler()
    if gelf_log_handler:
        logging.getLogger().addHandler(gelf_log_handler)

    # Instantiate Flask
    app = Flask(__name__)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Load common settings
    app.config.from_object('app.settings')
    # Load environment specific settings
    app.config.from_object('app.local_settings')
    # Load extra settings from extra_config_settings param
    app.config.update(extra_config_settings)


    # Setup Flask-SQLAlchemy
    db.init_app(app)

    # Setup Flask-Migrate
    migrate.init_app(app, db)

    # Celery
    celery = celeryapp.create_celery_app(app)
    celeryapp.celery = celery

    # flask_restx
    api.init_app(app)

    #init OIDC client
    if oidcEnable:
        app.config.update({
            'OIDC_CLIENT_SECRETS': 'app/keycloak.json',
            'OIDC_ID_TOKEN_COOKIE_SECURE': False,
            'OIDC_REQUIRE_VERIFIED_EMAIL': False,
            'OIDC_USER_INFO_ENABLED': True,
            'OIDC_OPENID_REALM': 'megalis',
            'OIDC_SCOPES': ['openid', 'email', 'profile'],
            'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret_post'
        })
        oidc.init_app(app)

    return app





