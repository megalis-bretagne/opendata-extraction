"""
Point d'entrée de l'application API

waitress-serve --port=80 app.api_app.api_serve:app
"""
import logging
from app import create_app

logging.basicConfig(level=logging.WARN)

app = create_app()