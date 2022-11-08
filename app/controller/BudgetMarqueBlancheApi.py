import logging
from flask import Blueprint
from flask_restx import Api, Namespace, Resource, fields
import app.service.budget_marque_blanche_api_service as api_service

_API_SERVICE = api_service.BudgetMarqueBlancheApiService()

budgets_api_bp = Blueprint("mq_budgets", __name__)
budgets_api = Api(
    budgets_api_bp, doc="/doc", title="API marque blanche budgets", prefix="/v1"
)
budgets_api_ns = Namespace(
    name="budgets",
    path="/",
    description=(
        "API de consultation des données de budgets pour la marque blanche. "
        "<b>C'est une API privée pour le frontend et elle peut changer à tout moment</b>"
    ),
)
budgets_api.add_namespace(budgets_api_ns)

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
    budgets_api_ns.model(
        "_dict_nic_etapes",
        {"*": _ls_etapes_wildcard},
    )
)

_nic_etapes_wildcard = fields.Wildcard(disp_nested_nic_x_etape)
disp_nested_annee_x_nic = fields.Nested(
    budgets_api_ns.model("_dict_annee_nics", {"*": _nic_etapes_wildcard})
)

_infos_etablissement_model = budgets_api_ns.model(
    "InfosEtablissement",
    {
        "denomination": fields.String(
            description="Denomination de l'unité légale rattachée", required=True
        ),
        "siret": fields.String(description="Siret de l'établissement", required=True),
        "enseigne": fields.String(
            description="Enseigne de l'établissement", required=False
        ),
        "est_siege": fields.Boolean(
            description="Si l'établissement est l'établissement siège", required=True
        ),
    },
    skip_none=True,
)
_nested_infos_etablissement = fields.Nested(_infos_etablissement_model, skip_none=True)
_denomination_entites_wildcard = fields.Wildcard(_nested_infos_etablissement)

api_ressources_budgetaires_disponibles = budgets_api_ns.model(
    "RessourcesDisponibles",
    {
        "siren": fields.String(description="Siren concerné", required=True),
        "ressources_disponibles": fields.Nested(
            budgets_api_ns.model("nic_annee", {"*": _nic_etapes_wildcard}),
            skip_none=True,
        ),
        "infos_etablissements": fields.Nested(
            budgets_api_ns.model(
                "_dict_denomination_entites", {"*": _denomination_entites_wildcard}
            ),
            skip_none=True,
        ),
    },
)

#
# Ressources budgetaires itself
#
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

api_element_nomenclature_pdc = budgets_api_ns.model(
    "ElementNomenclaturePdc",
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
            required=False,
            skip_none=True,
        ),
    },
)

ref_fonc_wildcard = fields.Wildcard(
    fields.Nested(api_element_nomenclature_pdc, skip_none=True), required=False
)
comptes_nature_wildcard = fields.Wildcard(
    fields.Nested(api_element_nomenclature_pdc, skip_none=True), required=False
)

api_get_pdc_info_response = budgets_api_ns.model(
    "InformationPdc",
    {
        "references_fonctionnelles": fields.Nested(
            budgets_api_ns.model(
                "_dict_code_references_fonctionnelles",
                {"*": ref_fonc_wildcard},
            ),
            description="Références fonctionnelles du plan de comptes",
            required=False,
            skip_none=True,
        ),
        "comptes_nature": fields.Nested(
            budgets_api_ns.model(
                "_dict_code_comptes_nature",
                {"*": comptes_nature_wildcard},
            ),
            description="Comptes nature du plan du comptes",
            required=True,
            skip_none=True,
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


@budgets_api_ns.errorhandler(api_service.EtapeInvalideError)
def handle_bad_request_errors(error):
    logging.exception(error)
    return {"message": error.api_message}, 400


@budgets_api_ns.errorhandler(api_service.AucuneDonneeBudgetError)
def handle_not_found(error):
    logging.exception(error)
    return {"message": error.api_message}, 404


@budgets_api_ns.errorhandler(api_service.BudgetMarqueBlancheApiException)
@budgets_api_ns.errorhandler(api_service.ImpossibleDextraireEtabInfoError)
@budgets_api_ns.errorhandler(api_service.ImpossibleDexploiterBudgetError)
def handle_ise_errors(error):
    logging.exception(error)
    return {"message": error.api_message}, 500


@budgets_api_ns.route("/donnees_budgetaires/<int:annee>/<int:siret>/<string:etape>")
class DonneesBudgetCtrl(Resource):
    @budgets_api_ns.marshal_with(api_get_donnees_response, code=200)
    def get(
        self,
        siret: int,
        annee: int,
        etape: str,
    ) -> api_service.GetBudgetMarqueBlancheApiResponse:
        response = _API_SERVICE.retrieve_budget_info(annee, siret, etape)
        return response


@budgets_api_ns.route("/plans_de_comptes/<int:annee>/<int:siret>")
class PlanDeComptesCtrl(Resource):
    @budgets_api_ns.marshal_with(api_get_pdc_info_response, code=200)
    def get(self, siret: int, annee: int):
        response = _API_SERVICE.retrieve_pdc_info(annee, siret)
        return response


@budgets_api_ns.route("/donnees_budgetaires_disponibles/<int:siren>")
class RessourcesDisponiblesCtrl(Resource):
    @budgets_api_ns.marshal_with(api_ressources_budgetaires_disponibles, code=200)
    def get(
        self,
        siren: int,
    ):
        return _API_SERVICE.ressources_budgetaires_disponibles(siren)
