from flask_restx import Resource,fields

import app.service.mq_budget_api_service as service

from .modele_commun import etape_model
from . import budgets_api_ns
from . import _API_SERVICE

api_ligne_budget = budgets_api_ns.model(
    "LigneBudgetaire",
    {
        "fonction_code": fields.String(
            description="Code de la fonction de la ligne.",
            required=False,
        ),
        "compte_nature_code": fields.String(
            description="Code de la nature de la ligne.",
            required=True,
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

api_get_donnees_response = budgets_api_ns.model(
    "DonneesBudget",
    {
        "etape": etape_model,
        "annee": fields.Integer(description="Année de l'exerice.", required=True),
        "siret": fields.Integer(
            description="Numéro SIRET de l'établissement", required=False
        ),
        "lignes": fields.List(fields.Nested(api_ligne_budget)),
    },
)


@budgets_api_ns.route("/donnees_budgetaires/<int:annee>/<int:siret>/<string:etape>")
class DonneesBudgetCtrl(Resource):
    @budgets_api_ns.marshal_with(api_get_donnees_response, code=200)
    def get(
        self,
        siret: int,
        annee: int,
        etape: str,
    ) -> service.GetBudgetMarqueBlancheApiResponse:
        response = _API_SERVICE.retrieve_budget_info(annee, siret, etape)
        return response
