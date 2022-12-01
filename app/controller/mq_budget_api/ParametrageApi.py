from app import oidc

from flask_restx import Resource, Namespace
from flask_restx import reqparse

from app.service.mq_budget_api_service import Annee, Siret
from app.service.mq_budget_api_service.parametrage import (
    DefaultVisualisationLocalisation,
)

from . import _PARAM_API_SERVICE

from . import budgets_api

parametrage_ns = Namespace(
    name="parametrage",
    path="/parametrage",
    description=(
        "API de parametrage des données de budgets pour la marque blanche. "
        "<b>C'est une API privée pour le frontend et elle peut changer à tout moment</b>"
    ),
)

put_parametrages_req_parser = reqparse.RequestParser()
put_parametrages_req_parser.add_argument("titre", type=str, location="form")
put_parametrages_req_parser.add_argument("sous_titre", type=str, location="form")


@parametrage_ns.route(
    "/default_visualisation/<int:annee>/<string:siret>/<string:etape_str>/<string:graphe_id>"
)
class ParametrageVisualisationParDefaut(Resource):
    def get(self, annee: Annee, siret: Siret, etape_str: str, graphe_id: str):

        localisation = DefaultVisualisationLocalisation(
            annee, siret, etape_str, graphe_id
        )
        parametrage = _PARAM_API_SERVICE.get_parametre_defaultvisualisation(
            localisation
        )

        return parametrage.to_api_answer()

    @parametrage_ns.expect(put_parametrages_req_parser)
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    def put(self, annee: Annee, siret: Siret, etape_str: str, graphe_id: str):

        args = put_parametrages_req_parser.parse_args()

        titre = args["titre"]
        sous_titre = args["sous_titre"]

        localisation = DefaultVisualisationLocalisation(
            annee, siret, etape_str, graphe_id
        )

        _PARAM_API_SERVICE.set_parametre_defaultvisualisation(
            localisation, titre, sous_titre
        )


budgets_api.add_namespace(parametrage_ns)
