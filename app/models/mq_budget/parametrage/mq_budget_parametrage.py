from app import db

from dataclasses import dataclass

@dataclass
class ParametresDefaultVisualisation(db.Model):
    """Représente les paramètres d'une visualisation présente par défaut dans une page de paramétrage"""
    __tablename__ = "mq_budget_parametres_defaultvisualisation"

    id: int = db.Column(db.Integer, primary_key=True)

    localisation: str = db.Column(db.String(100), nullable=False, unique=True)
    """Identifiant fonctionnel, localisation de la visualisation. composé d'une annee-siret-etape-grapheid"""

    titre: str = db.Column(db.String(255), nullable=True)
    """Titre de la visualisation. peut contenir 'default' si le titre doit être calculé par l'application"""
    sous_titre: str = db.Column(db.String(255), nullable=True)
    """Sous-titre de la visualisation. peut contenir 'default' si le sous-titre doit être calculé par l'application"""