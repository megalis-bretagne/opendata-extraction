# This file defines command line commands for manage.py
from flask_script import Command

from app import db
from app.models.publication_model import Publication,Acte,PieceJointe
from app.models.parametrage_model import Parametrage
from app.models.entite_pastell_ag import EntitePastellAG
class InitDbCommand(Command):
    """ Initialize the database."""
    def run(self):
        init_db()
        print('Database has been initialized.')

def init_db():
    """ Initialize the database."""
    db.drop_all()
    db.create_all()

def create_users():
    # Create all tables
    db.create_all()
    # Save to DB
    db.session.commit()

def create_organization():
    # Create all tables
    db.create_all()
    # Save to DB
    db.session.commit()


