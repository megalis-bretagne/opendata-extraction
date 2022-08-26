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

api_ligne_budget = api.model(
    "Ligne budgetaire",
    {
        "fonction_code": fields.String(
            description="Code de la fonction de la ligne.", required=False
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

api_reference_fonctionnelle = api.model(
    "Référence fonctionnelle d'un plan de compte",
    {
        "code": fields.String(
            description="Code de la réference fonctionnelle du plan de compte",
            required=True,
        ),
        "libelle": fields.String(
            description="Libellé de la réference fonctionnelle du plan de compte",
            required=True,
        ),
        "parent_code": fields.String(
            description="Code de la réference fonctionnelle parente",
            required=False, skip_none=True,
        ),
    },
)

api_compte_nature = api.model(
    "Compte nature d'un plan de compte",
    {
        "code": fields.String(
            description="Code de la réference fonctionnelle du plan de compte",
            required=True,
        ),
        "libelle": fields.String(
            description="Libellé de la réference fonctionnelle du plan de compte",
            required=True,
        ),
        "parent_code": fields.String(
            description="Code de la réference fonctionnelle parente",
            required=False, skip_none=True,
        ),
    },
)

ref_fonc_wildcard = fields.Wildcard(fields.Nested(api_reference_fonctionnelle, skip_none=True), required=False)
comptes_nature_wildcard = fields.Wildcard(fields.Nested(api_compte_nature, skip_none=True), required=False)

api_get_pdc_info_response = api.model(
    "Information plan de comptes",
    {
        "references_fonctionnelles": fields.Nested(
            api.model(
                "references_fonctionnelles",
                {"*": ref_fonc_wildcard },
            ),
            description = "Références fonctionnelles du plan de comptes",
            required=False, skip_none=True,
        ),
        "comptes_nature": fields.Nested(
            api.model(
                "comptes_nature",
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
        "etape": fields.String(
            description="Etape budgetaire concernée",
            enum=[
                "budget primitif",
                "budget supplémentaire",
                "décision modificative",
                "compte administratif",
            ],
            required=True,
        ),
        "annee": fields.Integer(description="Année de l'exerice.", required=True),
        "siren": fields.Integer(description="Numéro SIREN", required=False),
        "siret_siege": fields.Integer(
            description="Numéro SIRET de l'établissement siège", required=False
        ),
        "denomination_siege": fields.String(
            description="Nom de l'établissement public concerné.", required=True
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
        response = _API_SERVICE.retrieve_info_budget(siren, annee, etape)
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

@api.route("/<int:siren>/annees_disponibles")
class AnneesDisponiblesCtrl(Resource):
    @api.response(200, "Success")
    def get(self, siren: int) -> list[str]:
        return _API_SERVICE.annees_disponibles(siren)
