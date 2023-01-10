import dataclasses

from .classification_actes import _classification_actes_dict

def _compute_publication_opendata(acte_nature: str):

    if acte_nature == "1" or acte_nature == "2" or acte_nature == "5":
        publication_open_data = (
            "3"  # delib, actes réglementaires et budgets oui par défaut
        )
    elif acte_nature == "3" or acte_nature == "6":
        publication_open_data = "1"  # actes individuels et autres non par defaut
    else:
        publication_open_data = "2"  # le reste à ne sais pas

    return publication_open_data


def _force_latin1(s: str):
    return s.encode("latin-1", "ignore").decode("latin-1")


@dataclasses.dataclass
class MetadataPastell:
    numero_de_lacte: str
    date_de_lacte: str
    objet: str
    siren: str
    acte_nature: str

    envoi_depot: str

    nature_autre_detail: str
    liste_arrete: list[str]
    liste_acte_tamponne: list[str]

    liste_autre_document_attache: list[str]

    type_piece: str

    classification: str
    classification_code: str
    classification_nom: str

    publication_open_data: str

    @staticmethod
    def parse(json):

        acte_nature = json["acte_nature"]
        envoi_depot = json.get("envoi_depot", "checked")
        nature_autre_detail = json.get("nature_autre_detail", "")
        liste_arrete = json.get("arrete", [])
        acte_tamponne = json.get("acte_tamponne", [])
        liste_autre_document_attache = json.get("autre_document_attache", [])
        type_piece = json.get("type_piece", "")
        classification = json.get("classification", "9.2")
        key = "publication_open_data"
        publication_open_data = (
            _compute_publication_opendata(acte_nature)
            if key not in json or not json[key]
            else json[key]
        )


        classification_code = classification.split(" ", 1)[0]

        _classification_code_split = classification_code.split(".", -1)
        _code = ".".join(_classification_code_split[0:2])

        classification_nom = _classification_actes_dict[_code]

        return MetadataPastell(
            numero_de_lacte=json["numero_de_lacte"],
            date_de_lacte=json["date_de_lacte"],
            objet=json["objet"],
            siren=json["siren"],
            acte_nature=acte_nature,
            envoi_depot=envoi_depot,
            nature_autre_detail=nature_autre_detail,
            liste_arrete=liste_arrete,
            liste_acte_tamponne=acte_tamponne,
            liste_autre_document_attache=liste_autre_document_attache,
            type_piece=type_piece,
            classification=classification,
            classification_code=classification_code,
            classification_nom=classification_nom,
            publication_open_data=publication_open_data,
        )

    def sanitize_for_db(self):
        return dataclasses.replace(self, objet=_force_latin1(self.objet))
