import dataclasses

# fmt: off
classification_actes_dict = dict()
classification_actes_dict["1"] = "Commande Publique"
classification_actes_dict["1.1"] = "Commande Publique/Marches publics"
classification_actes_dict["1.2"] = "Commande Publique/Delegation de service public"
classification_actes_dict["1.3"] = "Commande Publique/Conventions de Mandat"
classification_actes_dict["1.4"] = "Commande Publique/Autres types de contrats"
classification_actes_dict["1.5"] = "Commande Publique/Transactions /protocole d accord transactionnel"
classification_actes_dict["1.6"] = "Commande Publique/Actes relatifs a la maitrise d oeuvre"
classification_actes_dict["1.7"] = "Commande Publique/Actes speciaux et divers"

classification_actes_dict["2"] = "Urbanisme"
classification_actes_dict["2.1"] = "Urbanisme/Documents d urbanisme"
classification_actes_dict["2.2"] = "Urbanisme/Actes relatifs au droit d occupation ou d utilisation des sols"
classification_actes_dict["2.3"] = "Urbanisme/Droit de preemption urbain"

classification_actes_dict["3"] = "Domaine et patrimoine"
classification_actes_dict["3.1"] = "Domaine et patrimoine/Acquisitions"
classification_actes_dict["3.2"] = "Domaine et patrimoine/Alienations"
classification_actes_dict["3.3"] = "Domaine et patrimoine/Locations"
classification_actes_dict["3.4"] = "Domaine et patrimoine/Limites territoriales"
classification_actes_dict["3.5"] = "Domaine et patrimoine/Autres actes de gestion du domaine public"
classification_actes_dict["3.6"] = "Domaine et patrimoine/Autres actes de gestion du domaine prive"

classification_actes_dict["4"] = "Fonction publique"
classification_actes_dict["4.1"] = "Fonction publique/Personnel titulaires et stagiaires de la F.P.T."
classification_actes_dict["4.2"] = "Fonction publique/Personnel contractuel"
classification_actes_dict["4.3"] = "Fonction publique/Fonction publique hospitaliere"
classification_actes_dict["4.4"] = "Fonction publique/Autres categories de personnels"
classification_actes_dict["4.5"] = "Fonction publique/Regime indemnitaire"

classification_actes_dict["5"] = "Institutions et vie politique"
classification_actes_dict["5.1"] = "Institutions et vie politique/Election executif"
classification_actes_dict["5.2"] = "Institutions et vie politique/Fonctionnement des assemblees"
classification_actes_dict["5.3"] = "Institutions et vie politique/Designation de representants"
classification_actes_dict["5.4"] = "Institutions et vie politique/Delegation de fonctions"
classification_actes_dict["5.5"] = "Institutions et vie politique/Delegation de signature"
classification_actes_dict["5.6"] = "Institutions et vie politique/Exercice des mandats locaux"
classification_actes_dict["5.7"] = "Institutions et vie politique/Intercommunalite"
classification_actes_dict["5.8"] = "Institutions et vie politique/Decision d ester en justice"

classification_actes_dict["6"] = "Libertes publiques et pourvoirs de police"
classification_actes_dict["6.1"] = "Libertes publiques et pourvoirs de police/Police municipale"
classification_actes_dict["6.2"] = "Libertes publiques et pourvoirs de police/Pouvoir du president du conseil general"
classification_actes_dict["6.3"] = "Libertes publiques et pourvoirs de police/Pouvoir du president du conseil regional"
classification_actes_dict["6.4"] = "Libertes publiques et pourvoirs de police/Autres actes reglementaires"
classification_actes_dict["6.5"] = "Libertes publiques et pourvoirs de police/Actes pris au nom de l Etat et soumis au controle hierarchique"

classification_actes_dict["7"] = "Finances locales"
classification_actes_dict["7.1"] = "Finances locales/Decisions budgetaires"
classification_actes_dict["7.2"] = "Finances locales/Fiscalite"
classification_actes_dict["7.3"] = "Finances locales/Emprunts"
classification_actes_dict["7.4"] = "Finances locales/Interventions economiques"
classification_actes_dict["7.5"] = "Finances locales/Subventions"
classification_actes_dict["7.6"] = "Finances locales/Contributions budgetaires"
classification_actes_dict["7.7"] = "Finances locales/Avances"
classification_actes_dict["7.8"] = "Finances locales/Fonds de concours"
classification_actes_dict["7.9"] = "Finances locales/Prise de participation (SEM, etc...)"
classification_actes_dict["7.10"] = "Finances locales/Divers"

classification_actes_dict["8"] = "Domaines de competences par themes"
classification_actes_dict["8.1"] = "Domaines de competences par themes/Enseignement"
classification_actes_dict["8.2"] = "Domaines de competences par themes/Aide sociale"
classification_actes_dict["8.3"] = "Domaines de competences par themes/Voirie"
classification_actes_dict["8.4"] = "Domaines de competences par themes/Amenagement du territoire"
classification_actes_dict["8.5"] = "Domaines de competences par themes/Politique de la ville-habitat-logement"
classification_actes_dict["8.6"] = "Domaines de competences par themes/Emploi-formation professionnelle"
classification_actes_dict["8.7"] = "Domaines de competences par themes/Transports"
classification_actes_dict["8.8"] = "Domaines de competences par themes/Environnement"
classification_actes_dict["8.9"] = "Domaines de competences par themes/Culture"

classification_actes_dict["9"] = "Autres domaines de competences"
classification_actes_dict["9.1"] = "Autres domaines de competences/Autres domaines de competences des communes"
classification_actes_dict["9.2"] = "Autres domaines de competences/Autres domaines de competences des departements"
classification_actes_dict["9.3"] = "Autres domaines de competences/Autres domaines de competences des regions"
classification_actes_dict["9.4"] = "Autres domaines de competences/Voeux et motions"
# fmt: on


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

        classification_nom = classification_actes_dict[_code]

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
        return dataclasses.replace(
            self,
            objet=_force_latin1(self.objet)
        )
