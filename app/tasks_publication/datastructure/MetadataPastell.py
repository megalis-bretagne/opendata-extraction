#fmt: off
classification_actes_dict = dict()
classification_actes_dict[1] = "Commande Publique"
classification_actes_dict[1.1] = "Commande Publique/Marches publics"
classification_actes_dict[1.2] = "Commande Publique/Delegation de service public"
classification_actes_dict[1.3] = "Commande Publique/Conventions de Mandat"
classification_actes_dict[1.4] = "Commande Publique/Autres types de contrats"
classification_actes_dict[1.5] = "Commande Publique/Transactions /protocole d accord transactionnel"
classification_actes_dict[1.6] = "Commande Publique/Actes relatifs a la maitrise d oeuvre"
classification_actes_dict[1.7] = "Commande Publique/Actes speciaux et divers"

classification_actes_dict[2] = "Urbanisme"
classification_actes_dict[2.1] = "Urbanisme/Documents d urbanisme"
classification_actes_dict[2.2] = "Urbanisme/Actes relatifs au droit d occupation ou d utilisation des sols"
classification_actes_dict[2.3] = "Urbanisme/Droit de preemption urbain"

classification_actes_dict[3] = "Domaine et patrimoine"
classification_actes_dict[3.1] = "Domaine et patrimoine/Acquisitions"
classification_actes_dict[3.2] = "Domaine et patrimoine/Alienations"
classification_actes_dict[3.3] = "Domaine et patrimoine/Locations"
classification_actes_dict[3.4] = "Domaine et patrimoine/Limites territoriales"
classification_actes_dict[3.5] = "Domaine et patrimoine/Autres actes de gestion du domaine public"
classification_actes_dict[3.6] = "Domaine et patrimoine/Autres actes de gestion du domaine prive"

classification_actes_dict[4] = "Fonction publique"
classification_actes_dict[4.1] = "Fonction publique/Personnel titulaires et stagiaires de la F.P.T."
classification_actes_dict[4.2] = "Fonction publique/Personnel contractuel"
classification_actes_dict[4.3] = "Fonction publique/Fonction publique hospitaliere"
classification_actes_dict[4.4] = "Fonction publique/Autres categories de personnels"
classification_actes_dict[4.5] = "Fonction publique/Regime indemnitaire"

classification_actes_dict[5] = "Institutions et vie politique"
classification_actes_dict[5.1] = "Institutions et vie politique/Election executif"
classification_actes_dict[5.2] = "Institutions et vie politique/Fonctionnement des assemblees"
classification_actes_dict[5.3] = "Institutions et vie politique/Designation de representants"
classification_actes_dict[5.4] = "Institutions et vie politique/Delegation de fonctions"
classification_actes_dict[5.5] = "Institutions et vie politique/Delegation de signature"
classification_actes_dict[5.6] = "Institutions et vie politique/Exercice des mandats locaux"
classification_actes_dict[5.7] = "Institutions et vie politique/Intercommunalite"
classification_actes_dict[5.8] = "Institutions et vie politique/Decision d ester en justice"

classification_actes_dict[6] = "Libertes publiques et pourvoirs de police"
classification_actes_dict[6.1] = "Libertes publiques et pourvoirs de police/Police municipale"
classification_actes_dict[6.2] = "Libertes publiques et pourvoirs de police/Pouvoir du president du conseil general"
classification_actes_dict[6.3] = "Libertes publiques et pourvoirs de police/Pouvoir du president du conseil regional"
classification_actes_dict[6.4] = "Libertes publiques et pourvoirs de police/Autres actes reglementaires"
classification_actes_dict[6.5] = "Libertes publiques et pourvoirs de police/Actes pris au nom de l Etat et soumis au controle hierarchique"

classification_actes_dict[7] = "Finances locales"
classification_actes_dict[7.1] = "Finances locales/Decisions budgetaires"
classification_actes_dict[7.2] = "Finances locales/Fiscalite"
classification_actes_dict[7.3] = "Finances locales/Emprunts"
classification_actes_dict[7.4] = "Finances locales/Interventions economiques"
classification_actes_dict[7.5] = "Finances locales/Subventions"
classification_actes_dict[7.6] = "Finances locales/Contributions budgetaires"
classification_actes_dict[7.7] = "Finances locales/Avances"
classification_actes_dict[7.8] = "Finances locales/Fonds de concours"
classification_actes_dict[7.9] = "Finances locales/Prise de participation (SEM, etc...)"
classification_actes_dict[7.10] = "Finances locales/Divers"

classification_actes_dict[8] = "Domaines de competences par themes"
classification_actes_dict[8.1] = "Domaines de competences par themes/Enseignement"
classification_actes_dict[8.2] = "Domaines de competences par themes/Aide sociale"
classification_actes_dict[8.3] = "Domaines de competences par themes/Voirie"
classification_actes_dict[8.4] = "Domaines de competences par themes/Amenagement du territoire"
classification_actes_dict[8.5] = "Domaines de competences par themes/Politique de la ville-habitat-logement"
classification_actes_dict[8.6] = "Domaines de competences par themes/Emploi-formation professionnelle"
classification_actes_dict[8.7] = "Domaines de competences par themes/Transports"
classification_actes_dict[8.8] = "Domaines de competences par themes/Environnement"
classification_actes_dict[8.9] = "Domaines de competences par themes/Culture"

classification_actes_dict[9] = "Autres domaines de competences"
classification_actes_dict[9.1] = "Autres domaines de competences/Autres domaines de competences des communes"
classification_actes_dict[9.2] = "Autres domaines de competences/Autres domaines de competences des departements"
classification_actes_dict[9.3] = "Autres domaines de competences/Autres domaines de competences des regions"
classification_actes_dict[9.4] = "Autres domaines de competences/Voeux et motions"
#fmt: on

class MetadataPastell:

    @staticmethod
    def parse(json):
        return MetadataPastell(json)
    
    def sanitize_for_db(self):
        return self

    def __init__(self, metajson):
        self.numero_de_lacte = metajson['numero_de_lacte']
        self.date_de_lacte = metajson['date_de_lacte']
        self.objet = metajson['objet']
        self.siren = metajson['siren']
        self.acte_nature = metajson['acte_nature']

        if 'envoi_depot' in metajson:
            self.envoi_depot = metajson['envoi_depot']
        else:
            self.envoi_depot = 'checked'

        if 'nature_autre_detail' in metajson:
            self.nature_autre_detail = metajson['nature_autre_detail']
        else:
            self.nature_autre_detail = ''

        # liste de fichier arrete
        self.liste_arrete = metajson['arrete']
        # liste de fichier arrete tamponne
        if 'acte_tamponne' in metajson:
            self.liste_acte_tamponne = metajson['acte_tamponne']
        else:
            self.liste_acte_tamponne = []

        # liste de d'annexe
        if 'autre_document_attache' in metajson:
            self.liste_autre_document_attache = metajson['autre_document_attache']
        else:
            self.liste_autre_document_attache = []

        if 'type_piece' in metajson:
            self.type_piece = metajson['type_piece']
        else:
            self.type_piece = ''

        if 'classification' in metajson:
            self.classification = metajson['classification']
        else:
            self.classification = '9.2'

        if 'publication_open_data' in metajson:
            if len(metajson['publication_open_data']) == 0:
                # valeur par défaut si dans le fichier metadata publication_open_data n'est pas présent
                if self.acte_nature == '1' or self.acte_nature == '2' or self.acte_nature == '5'  or self.acte_nature == '7':
                    # délib, actes réglementaires et budget oui par defaut
                    self.publication_open_data = '3'
                elif self.acte_nature == '3' or self.acte_nature == '6':
                    # actes individuels et autres non par defaut
                    self.publication_open_data = '1'
                else:
                    # le reste à ne sais pas
                    self.publication_open_data = '2'
            else:
                self.publication_open_data = metajson['publication_open_data']
        else:
            # valeur par défaut si dans le fichier metadata publication_open_data n'est pas présent
            if self.acte_nature == '1' or self.acte_nature == '2' or self.acte_nature == '5':
                # délib, actes réglementaires et budget oui par defaut
                self.publication_open_data = '3'
            elif self.acte_nature == '3' or self.acte_nature == '6':
                # actes individuels et autres non par defaut
                self.publication_open_data = '1'
            else:
                # le reste à ne sais pas
                self.publication_open_data = '2'

        x = self.classification.split(" ", 1)
        # valeur par defaut
        self.classification_code = 9.2
        if len(x) == 2:
            self.classification_code = x[0]
        elif len(x) == 1:
            self.classification_code = x[0]

        classification_code_split = self.classification_code.split(".", -1)
        if len(classification_code_split) > 2:
            self.classification_nom = classification_actes_dict[
                float(classification_code_split[0] + '.' + classification_code_split[1])]
        else:
            self.classification_nom = classification_actes_dict[float(self.classification_code)]