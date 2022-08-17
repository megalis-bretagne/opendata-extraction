import logging
from flask_restx import Namespace, Resource, fields
import app.service.budget_marque_blanche_api_service as api_service

_API_SERVICE = api_service.BudgetMarqueBlancheApiService()

# API definition
api = Namespace(
    name="budgets",
    description="API de consultation des données de budgets pour la marque blanche.",
)

get_budget_api_response_ligne = api.model(
    "budget_api_response_ligne",
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

get_budget_api_ref_fonctionnelle = api.model(
    "budget_api_response_ref_fonctionnelle",
    {
        "code": fields.String(
            description="Code de la réference fonctionnelle du plan de compte",
            required=True,
        ),
        "libelle": fields.String(
            description="Libellé de la réference fonctionnelle du plan de compte",
            required=True,
        ),
    },
)

ref_fonc_wildcard = fields.Wildcard(fields.Nested(get_budget_api_ref_fonctionnelle, skip_none=True), required=False)
get_budget_api_response = api.model(
    "budget_api_response",
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
        "references_fonctionnelles": fields.Nested(
            api.model(
                "references_fonctionnelles",
                {"*": ref_fonc_wildcard },
            ),
            required=False, skip_none=True,
        ),
        "lignes": fields.List(fields.Nested(get_budget_api_response_ligne)),
    },
)


# Error handlers
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

#


@api.route("/<int:siren>/<int:annee>/<string:etape>")
class BudgetMarqueBlancheSirenCtrl(Resource):
    @api.marshal_with(get_budget_api_response, code=200)
    def get(
        self, etape: str, siren: int, annee: int
    ) -> api_service.GetBudgetMarqueBlancheApiResponse:
        response = _API_SERVICE.retrieve_info_budget(etape, annee, siren)
        return response


@api.route("/<int:siren>/annees_disponibles")
class BudgetMarqueBlancheAnneesDisponiblesCtrl(Resource):
    @api.response(200, "Success")
    def get(self, siren: int) -> list[str]:
        return _API_SERVICE.annees_disponibles(siren)
