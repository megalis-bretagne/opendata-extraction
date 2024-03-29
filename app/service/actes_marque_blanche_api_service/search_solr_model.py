from dataclasses import dataclass
from typing import Optional


@dataclass()
class Annexe:
    """Information sur un établissement donnée"""
    id: str
    url: str
    hash: str
    content_type: str
    resultat_recherche: bool

    @property
    def serialize(self):
        return {
            'id': self.id,
            'url': self.url,
            'hash': self.hash,
            'content_type': self.content_type,
            'resultat_recherche': self.resultat_recherche,
        }


@dataclass()
class Acte:
    """Information sur un établissement donnée"""
    hash: str
    siren: str
    publication_id: str
    id: str
    type: str
    nature_autre_detail: str
    classification_code: str
    classification_libelle: str
    objet: str
    id_publication: str
    date_acte: str
    date_publication: str
    url: str
    typologie: str
    content_type: str
    blockchain_transaction_hash: str
    blockchain_url: str
    resultat_recherche: Optional[bool]
    annexes: Optional[list[Annexe]]

    @property
    def serialize(self):
        return {
            'hash': self.hash,
            'siren': self.siren,
            'publication_id': self.publication_id,
            'id': self.id,
            'type': self.type,
            'nature_autre_detail': self.nature_autre_detail,
            'classification_code': self.classification_code,
            'classification_libelle': self.classification_libelle,
            'objet': self.objet,
            'id_publication': self.id_publication,
            'date_acte': self.date_acte,
            'date_publication': self.date_publication,
            'url': self.url,
            'typologie': self.typologie,
            'content_type': self.content_type,
            'blockchain_transaction_hash': self.blockchain_transaction_hash,
            'blockchain_url': self.blockchain_url,
            'resultat_recherche': self.resultat_recherche,
            'annexes': [item.serialize for item in self.annexes]
        }


@dataclass()
class Page:
    """Information sur un établissement donnée"""
    nb_resultats: int
    page_suivante: str
    resultats: list[Acte]

    @property
    def serialize(self):
        return {
            'nb_resultats': self.nb_resultats,
            'resultats': [item.serialize for item in self.resultats],
            'page_suivante': self.page_suivante
        }
