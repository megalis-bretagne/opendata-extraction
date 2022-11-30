# __init__.py is a special Python file that allows a directory to become
# a Python package so it can be accessed using the 'import' statement.
import logging

from flask import Flask

from app.models.flask_sqlalchemy import db
from app.models.flask_migrate import migrate

from flask_cors import CORS
from flask_oidc import OpenIDConnect
oidc = OpenIDConnect()


# Instantiate Flask extensions
from app import celeryapp
from app.controller import api_v1_bp
from app.controller import private_api_v1_bp
from app.controller.BudgetMarqueBlancheApi import budgets_api_bp
from app.controller.ActesMarqueBlancheApi import actes_api_bp

import app.shared.logger_utils as logger_utils

def create_app(extra_config_settings={},oidcEnable=True):
    """Create a Flask application.
    """

    # Instantiate Flask
    app = Flask(__name__)

    CORS(app, resources={
        r"/api/*": {"origins": "*"},
        r"/private_api/*": {"origins": "*"},
        r"/mq_apis/*": {"origins": "*"}
    })

    # Load common settings
    app.config.from_object('app.settings')
    # Load environment specific settings
    app.config.from_object('app.local_settings')
    # Load extra settings from extra_config_settings param
    app.config.update(extra_config_settings)

    # Log level
    logging.basicConfig()
    log_level_name = app.config.get("LOG_LEVEL", "WARN")
    logger_utils.setup_loggerlevel_from_levelname(log_level_name, logging.getLogger())

    # GELF logging
    gelf_log_handler = logger_utils.create_or_get_gelf_loghandler()
    if gelf_log_handler:
        logging.getLogger().addHandler(gelf_log_handler)

    # Setup Flask-SQLAlchemy
    db.init_app(app)

    # Setup Flask-Migrate
    migrate.init_app(app, db)

    # Celery
    celery = celeryapp.create_celery_app(app)
    celeryapp.celery = celery

    # flask_restx
    app.register_blueprint(api_v1_bp, url_prefix='/')
    app.register_blueprint(private_api_v1_bp, url_prefix='/private_api')
    app.register_blueprint(budgets_api_bp, url_prefix='/mq_apis/budgets')
    app.register_blueprint(actes_api_bp, url_prefix='/mq_apis/actes')

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





