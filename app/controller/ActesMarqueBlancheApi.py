from flask import Blueprint, jsonify
from flask_restx import Api, Namespace, Resource, fields, reqparse
import app.service.actes_marque_blanche_api_service.ActesMarqueBlancheApiService as api_service


_API_SERVICE = api_service.ActesMarqueBlancheApiService()

actes_api_bp = Blueprint("mq_actes", __name__)
actes_api = Api(
    actes_api_bp, doc="/doc", title="API marque blanche actes", prefix="/v1"
)
actes_api_ns = Namespace(
    name="actes",
    path="/",
    description=(
        "API de recherche des actes "
        "<b>C'est une API privée pour le frontend et elle peut changer à tout moment</b>"
    ),
)
actes_api.add_namespace(actes_api_ns)

annexe = actes_api.model('annexe', {
    'id': fields.Integer,
    'url': fields.String,
    'hash': fields.String,
    'content_type': fields.String,
    'resultat_recherche': fields.Boolean
})
acte = actes_api.model(
    'acte', {
        'hash': fields.String,
        'siren': fields.String,
        'publication_id': fields.Integer,
        'id': fields.String,
        'type': fields.String,
        'nature_autre_detail': fields.String,
        'classification_code': fields.String,
        'classification_libelle': fields.String,
        'objet': fields.DateTime,
        'id_publication': fields.String,
        'date_acte': fields.String,
        'date_publication': fields.String,
        'url': fields.String,
        'typologie': fields.String,
        'content_type': fields.String,
        'blockchain_transaction_hash': fields.String,
        'blockchain_url': fields.String,
        'resultat_recherche': fields.Boolean,
        'annexes': fields.List(fields.Nested(annexe))
    })

page = actes_api.model('page', {
    'nb_resultats': fields.Integer,
    'resultats': fields.List(fields.Nested(acte)),
    'page_suivante': fields.String
})

searchParams = reqparse.RequestParser()
searchParams.add_argument('query', help='recherche multi champs')
searchParams.add_argument('siren', help='filtre de recherche sur le siren')
searchParams.add_argument('date_debut', help='filtre de recherche sur la date de l\'acte au format iso')
searchParams.add_argument('date_fin', help='filtre de recherche sur la date de l\'acte au format iso')
searchParams.add_argument('classifications', help='filtre de recherche sur la classification')
searchParams.add_argument('types_actes', help='filtre de recherche sur la nature de l\'acte')
searchParams.add_argument('lignes', help='nombre de ligne à retourner')
searchParams.add_argument('page_suivante', help='page suivante')


@actes_api_ns.errorhandler(api_service.SolrMarqueBlancheError)
@actes_api_ns.errorhandler(api_service.ActesMarqueBlancheApiException)
def handle_ise_errors(error):
    return {"message": error.api_message}, 500

@actes_api_ns.route('/search')
class PublicationSearchCtrl(Resource):
    @actes_api_ns.expect(searchParams)
    @actes_api_ns.response(200, 'Success', page)
    def get(self):
        return jsonify(_API_SERVICE.search(searchParams).serialize)