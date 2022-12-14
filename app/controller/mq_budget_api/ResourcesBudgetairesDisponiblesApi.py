from flask_restx import Resource, fields

from . import _API_SERVICE

from .modele_commun import etape_model
from . import budgets_api_ns

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

@budgets_api_ns.route("/donnees_budgetaires_disponibles/<int:siren>")
class RessourcesDisponiblesCtrl(Resource):
    @budgets_api_ns.response(200, 'Success', model = api_ressources_budgetaires_disponibles)
    def get(
        self,
        siren: int,
    ):
        disponibles = _API_SERVICE.ressources_budgetaires_disponibles(siren)
        answer = disponibles.to_api_answer()
        return answer