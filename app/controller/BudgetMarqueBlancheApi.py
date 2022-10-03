import logging
from flask_restx import Namespace, Resource, fields
import app.service.budget_marque_blanche_api_service as api_service

_API_SERVICE = api_service.BudgetMarqueBlancheApiService()

# API definition
api = Namespace(
    name="budgets",
    description=( 
        "API de consultation des données de budgets pour la marque blanche. " 
        "<b>C'est une API privée pour le frontend et peut changer à tout moment</b>" 
    ),
)

etape_model = fields.String(
    description="Etape budgetaire",
    enum=[
        "budget primitif",
        "budget supplémentaire",
        "décision modificative",
        "compte administratif",
    ],
    required=True,
)

#
# Resources budgetaires disponibles 
#
_ls_etapes_wildcard = fields.Wildcard(fields.List(etape_model))
disp_nested_nic_x_etape = fields.Nested(
    api.model(
        "_dict_nic_etapes",
        { "*": _ls_etapes_wildcard },
    )
)

_nic_etapes_wildcard = fields.Wildcard(disp_nested_nic_x_etape)
disp_nested_annee_x_nic = fields.Nested(
    api.model(
        "_dict_annee_nics",
        { "*": _nic_etapes_wildcard }
    )
)

_infos_etablissement_model = api.model(
    "InfosEtablissement",
    {
        "denomination": fields.String(description="Denomination de l'unité légale rattachée", required=True),
        "siret": fields.String(description="Siret de l'établissement", required=True),
        "enseigne": fields.String(description="Enseigne de l'établissement", required=False),
        "est_siege": fields.Boolean(description="Si l'établissement est l'établissement siège", required=True)
    },
    skip_none=True
)
_nested_infos_etablissement = fields.Nested(_infos_etablissement_model, skip_none=True)
_denomination_entites_wildcard = fields.Wildcard(_nested_infos_etablissement)

api_ressources_budgetaires_disponibles = api.model(
    "Ressources budgetaires disponibles pour un siren donnée",
    {
        "siren": fields.String(description = "Siren concerné", required = True),
        "ressources_disponibles": fields.Nested(
            api.model(
                "nic_annee",
                { "*": _nic_etapes_wildcard }
            ),
            skip_none=True,
        ),
        "infos_etablissements": fields.Nested(
            api.model(
                "_dict_denomination_entites",
                { 
                    "*": _denomination_entites_wildcard
                }
            ),
            skip_none = True,
        )
    }
)

#
# Ressources budgetaires itself
#
api_ligne_budget = api.model(
    "Ligne budgetaire",
    {
        "fonction_code": fields.String(
            description="Code de la fonction de la ligne.", required=False,
        ),
        "compte_nature_code": fields.String(
            description="Code de la nature de la ligne.", required=True,
        ),
        "recette": fields.Boolean(
            description="Si la ligne représente une recette. Si non, elle représente une dépense",
            required=True,
        ),
        "montant": fields.Float(
            description="Montant que la ligne représente", required=True
        ),
    },
)

api_element_nomenclature_pdc = api.model(
    "Element de nomenclature d'un plan de compte",
    {
        "code": fields.String(
            description="Code de l'élément de nomenclature",
            required=True,
        ),
        "libelle": fields.String(
            description="Libellé de l'élément de nomenclature",
            required=True,
        ),
        "parent_code": fields.String(
            description="Code de l'élément de nomenclature parent",
            required=False, skip_none=True,
        ),
    },
)

ref_fonc_wildcard = fields.Wildcard(fields.Nested(api_element_nomenclature_pdc, skip_none=True), required=False)
comptes_nature_wildcard = fields.Wildcard(fields.Nested(api_element_nomenclature_pdc, skip_none=True), required=False)

api_get_pdc_info_response = api.model(
    "Information plan de comptes",
    {
        "references_fonctionnelles": fields.Nested(
            api.model(
                "_dict_code_references_fonctionnelles",
                {"*": ref_fonc_wildcard },
            ),
            description = "Références fonctionnelles du plan de comptes",
            required=False, skip_none=True,
        ),
        "comptes_nature": fields.Nested(
            api.model(
                "_dict_code_comptes_nature",
                {"*": comptes_nature_wildcard},
            ),
            description = "Comptes nature du plan du comptes",
            required=True, skip_none=True,
        )
    }
)

api_get_donnees_response = api.model(
    "Données de document budgetaire",
    {
        "etape": etape_model,
        "annee": fields.Integer(description="Année de l'exerice.", required=True),
        "siren": fields.Integer(description="Numéro SIREN", required=False),
        "siret": fields.Integer(
            description="Numéro SIRET de l'établissement", required=False
        ),
        "denomination_siege": fields.String(
            description="Dénomination de l'unité légale.", required=True
        ),
        "lignes": fields.List(fields.Nested(api_ligne_budget)),
    },
)

@api.errorhandler(api_service.EtapeInvalideError)
def handle_bad_request_errors(error):
    logging.exception(error)
    return {"message": error.api_message}, 400


@api.errorhandler(api_service.AucuneDonneeBudgetError)
def handle_not_found(error):
    logging.exception(error)
    return {"message": error.api_message}, 404


@api.errorhandler(api_service.BudgetMarqueBlancheApiException)
@api.errorhandler(api_service.ImpossibleDextraireEtabInfoError)
@api.errorhandler(api_service.ImpossibleDexploiterBudgetError)
def handle_ise_errors(error):
    logging.exception(error)
    return {"message": error.api_message}, 500

@api.route("/<int:siren>/<int:annee>/<string:etape>")
class DonneesBudgetCtrl(Resource):
    @api.marshal_with(api_get_donnees_response, code=200)
    def get(
        self,
        siren: int,
        annee: int,
        etape: str,
    ) -> api_service.GetBudgetMarqueBlancheApiResponse:
        response = _API_SERVICE.retrieve_budget_info(siren, annee, etape)
        return response

@api.route("/<int:siren>/<int:annee>/pdc")
class PlanDeComptesCtrl(Resource):
    @api.marshal_with(api_get_pdc_info_response, code=200)
    def get(
        self,
        siren: int, annee: int
        ):
        response = _API_SERVICE.retrieve_pdc_info(siren, annee)
        return response

@api.route("/disponibles/<int:siren>")
class RessourcesDisponiblesCtrl(Resource):
    @api.marshal_with(api_ressources_budgetaires_disponibles, code=200)
    def get(
        self,
        siren: int,
    ):
        return _API_SERVICE.ressources_budgetaires_disponibles(siren)