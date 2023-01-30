import dataclasses
from pathlib import Path

from . import logger

class InZipFileParseError(Exception):
    pass

@dataclasses.dataclass
class InZipFileParser:
    """Représente le zip que l'on reçoit en entrée de la création de publication.
    Ne pas construire via constructeur. Passer par `from_pastell_ged`"""
    path: Path

    separators = ["-", "_"]

    def dirname(self):
        return str(self.path.parent)
    
    def filename(self):
        return str(self.path.name)
    
    def id_d(self):
        """Renvoit l'id_d. Cela se base sur la convention de nommage. Pas une garantie forte."""
        probable_id_d = self.filename().removesuffix('.zip')

        for sep in self.separators:
            probable_id_d = probable_id_d.replace(sep, " ")
        probable_id_d = probable_id_d.split()[0]

        if len(probable_id_d) != 7:
            logger.warning(f"Le nom du fichier représente-t-il l'id_d de pastell? ({probable_id_d})")

        return probable_id_d

    @staticmethod
    def from_pastell_ged(s_path: str):
        """Construit un InZipFile depuis un chemin valide
        Vérifie que le fichier a un nom cohérent.

        Raises:
            InZipInvalidError: Si le fichier n'est pas cohérent. (nom trop long, ne finit pas par '.zip')

        Returns:
            InZip: Un InZip avec un chemin valide
        """

        try:
            p = Path(s_path).resolve()
        except Exception as e:
            raise InZipFileParseError from e 
        
        if not p.is_file():
            raise InZipFileParseError(f"{s_path} n'est pas un fichier.")
        
        #
        # Le fichier doit avoir le format
        # ID_D.zip
        # oú id_d est une chaine de 7 caractères.
        # XXX: Pour avoir de la flexibilité sur les rejeux, 
        # on ne vérifie qu'une longueur max pour le nom de fichier.
        #
        filename = p.name
        if not filename.endswith(".zip"):
            raise InZipFileParseError(f"Le nom du fichier {s_path} doit terminer par '.zip'.")
        
        wout_suffix = filename.removesuffix('.zip')
        max_char = 50
        if len(wout_suffix) > max_char:
            raise InZipFileParseError(f"Le nom du fichier {s_path} ne doit pas dépasser les {max_char} caractères.")

        return InZipFileParser(p)
    
