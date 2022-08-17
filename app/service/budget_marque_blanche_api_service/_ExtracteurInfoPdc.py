
from dataclasses import dataclass
import logging
from pathlib import Path
from xml.etree.ElementTree import ElementTree

from lxml import etree

from .data_structures import RefFonctionnelleBudgetMarqueBlancheApi

@dataclass()
class _Chapitre():
    code: str
    libelle: str
    libelle_court: str

@dataclass()
class _Compte():
    code: str
    libelle: str
    libelle_court: str

class _ExtracteurInfoPdc():
    """Extracteur d'information d'un plan de compte pour l'API budget marque blanche"""
    def __init__(self, pdc: Path) -> None:
        self.pdc = pdc
        self._processed = False
        self.__logger = logging.getLogger(self.__class__.__name__)
    
    def extraire_chapitres_nature(self) -> dict[str, _Chapitre]:
        if not self._processed:
            self._process()
        chapitres = self.data["Chapitres"]["Nature"]
        return self._to_dict(chapitres)
    
    def extraire_chapitres_fonction(self) -> dict[str, _Chapitre]:
        if not self._processed:
            self._process()
        fonctions = self.data["Chapitres"]["Fonction"]
        return self._to_dict(fonctions)

    def extraire_comptes_nature(self) -> dict[str, _Compte]:
        if not self._processed:
            self._process()
        comptes = self.data["Comptes"]["Nature"]
        return self._to_dict(comptes)
    
    def extraire_references_fonctionnelles(self) -> dict[str, RefFonctionnelleBudgetMarqueBlancheApi]:
        if not self._processed:
            self._process()
        references = self.data["RefFonctionnelles"]
        return self._to_dict(references)
    
    def _process(self):

        self.tree: ElementTree = etree.parse(self.pdc)
        self.data = {}
        self.data["Chapitres"] = {}
        self.data["Comptes"] = {}
        self.data["RefFonctionnelles"] = []
        assert self.tree

        for s in ["Nature", "Fonction"]:
            self.__logger.debug(f"Extraction des chapitres de {s} depuis {self.pdc}")
            chapitres = []
            _xpath_nature_chapitre = f".//{s}/Chapitres/Chapitre"
            chapitres_trees = self.tree.findall(_xpath_nature_chapitre)
            for chapitre_tree in chapitres_trees:
                chapitre = self._extract_nature_chapitre(chapitre_tree)
                chapitres.append(chapitre)
            self.data["Chapitres"][s] = chapitres
        
        comptes = []
        _xpath_nature_compte = ".//Nature/Comptes//Compte"
        nature_compte_trees = self.tree.findall(_xpath_nature_compte)
        for nature_compte_tree in nature_compte_trees:
            compte = self._extract_nature_compte(nature_compte_tree)
            comptes.append(compte)
        self.data["Comptes"]["Nature"] = comptes

        reffoncs = []
        _xpath_nature_compte = ".//Fonction/RefFonctionnelles//RefFonc"
        nature_compte_trees = self.tree.findall(_xpath_nature_compte)
        for nature_compte_tree in nature_compte_trees:
            reffonc = self._extract_reffonc(nature_compte_tree)
            reffoncs.append(reffonc)
        self.data["RefFonctionnelles"] = reffoncs

        self._processed = True
    
    def _extract_nature_chapitre(self, chapitre: ElementTree) -> _Chapitre:
        code = chapitre.attrib.get("Code") # type: ignore
        libelle = chapitre.attrib.get("Libelle") # type: ignore
        libelle_court = chapitre.attrib.get("Lib_court") # type: ignore
        return _Chapitre(code, libelle, libelle_court)

    def _extract_nature_compte(self, compte: ElementTree) -> _Compte:
        code = compte.attrib.get("Code") # type: ignore
        libelle = compte.attrib.get("Libelle") # type: ignore
        libelle_court = compte.attrib.get("Lib_court") # type: ignore
        return _Compte(code, libelle, libelle_court)

    def _extract_reffonc(self, reffonc: ElementTree) -> RefFonctionnelleBudgetMarqueBlancheApi:
        code = reffonc.attrib.get("Code") # type: ignore
        libelle = reffonc.attrib.get("Libelle") # type: ignore
        return RefFonctionnelleBudgetMarqueBlancheApi(code, libelle)
    
    def _to_dict(self, structure_with_code):
        return { x.code: x for x in structure_with_code }

    