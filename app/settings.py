# Settings common to all environments (development|staging|production)
# Place environment specific settings in env_settings.py
# development.py
# An example file (env_settings_example.py) can be used as a starting point

import os

# Application settings
APP_NAME = "OpenData-API "
APP_SYSTEM_ERROR_SUBJECT_LINE = APP_NAME + " system error"
TESTING = False

# Flask-SQLAlchemy settings
SQLALCHEMY_TRACK_MODIFICATIONS = False
#By default, MariaDB is configured to have a 600 second timeout.
# This often surfaces hard to debug, production environment only exceptions like 2013: Lost connection to MySQL server during query.
SQLALCHEMY_POOL_RECYCLE=120


# Celery
CELERY_BROKER_URL = 'redis://redis:6379/1'
result_backend = 'redis://redis:6379/0'
CELERY_REDIS_USE_SSL = False
accept_content = ['json']
task_serializer = 'json'
result_serializer = 'json'
redis_max_connections = 5

