from flask_restx import Resource, fields

from . import budgets_api_ns
from . import _API_SERVICE

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


@budgets_api_ns.route("/plans_de_comptes/<int:annee>/<string:nomenclature>")
class PlanDeComptesCtrl(Resource):
    @budgets_api_ns.response(200, "Success", model=api_get_pdc_info_response)
    def get(self, annee: int, nomenclature: str):
        pdc_info = _API_SERVICE.retrieve_pdc_info_nomenclature(annee, nomenclature)
        answer = pdc_info.to_api_answer()
        return answer
