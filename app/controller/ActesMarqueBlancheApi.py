import json

from flask import Blueprint, jsonify
from flask_restx import Api, Namespace, Resource, fields, reqparse

from app.models.search_solr_model import Acte,Page

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
    'name': fields.String
})

acte = actes_api.model(
    'acte', {
        'hash': fields.String,
        'publication_id': fields.Integer,
        'id': fields.String,
        'type': fields.String,
        'type_autre_detail': fields.String,
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
        'annexes': fields.List(fields.Nested(annexe)),
        'resultat_recherche': fields.Boolean,

    })

page = actes_api.model('page', {
    'nb_resultats': fields.Integer,
    'debut' : fields.Integer,
    'resultats' : fields.List(fields.Nested(Acte)),

})

searchParams = reqparse.RequestParser()
searchParams.add_argument('query', help='filtre de recherche sur le numéro d\'acte')
searchParams.add_argument('date_debut', help='date au format iso')
searchParams.add_argument('date_fin', help='date au format iso')
searchParams.add_argument('classifications', help='asc ou desc (desc par defaut)')
searchParams.add_argument('types_actes', help='asc ou desc (desc par defaut)')
searchParams.add_argument('debut', help='asc ou desc (desc par defaut)')
searchParams.add_argument('lignes', help='asc ou desc (desc par defaut)')


@actes_api_ns.route('/search')
class PublicationSearchCtrl(Resource):
    @actes_api_ns.expect(searchParams)
    # @actes_api_ns.marshal_with(page, code=200)
    def get(self):
        # args = searchParams.parse_args()
        from app.tasks.utils import solr_connexion
        solr = solr_connexion()

        # Setup a Solr instance. The trailing slash is optional.
        # solr = pysolr.Solr('http://localhost:8983/solr/core_0/', search_handler='/autocomplete', use_qt_param=False)
        results = solr.search('piscine', **{
            'defType': 'edismax',
            'fq': 'NOT typology:PJ AND est_publie:true',
            'qf': 'documentidentifier^10 description^5 _text_^2 classification_nom '

        })

        liste_acte =[]
        for doc in results.docs:
            _hash = doc['hash']
            _publication_id = doc['publication_id']
            _id = doc['id']
            _type = doc['documenttype'][0]
             'type_autre_detail' in doc _type_autre_detail = doc['type_autre_detail']
            _classification_code = doc['classification_code ']
            _classification_libelle = doc['classification_libell']
            _objet = doc['objet']
            _id_publication = doc['id_publication']
            _date_acte = doc['date_acte']
            _date_publication = doc['date_publication']
            _url = doc['url']
            _typologie = doc['typologie']
            _content_type = doc['content_type']
            _blockchain_transaction_hash = doc['blockchain_transaction_hash']
            _blockchain_url = doc['blockchain_url']
            # _annexes: list[Annexe]
            # _resultat_recherche: bool

            _acte = Acte(hash=_hash, publication_id=_publication_id, id=_id, type=_type,
                         type_autre_detail=_type_autre_detail, classification_code=_classification_code,
                         classification_libelle=_classification_libelle, objet=_objet, id_publication=_id_publication,
                         date_acte=_date_acte, date_publication=_date_publication, url=_url, typologie=_typologie,
                         content_type=_content_type, blockchain_transaction_hash=_blockchain_transaction_hash,
                         blockchain_url=_blockchain_url,resultat_recherche=False,annexes=[])

            liste_acte.append(_acte)


        reponse = Page(nb_resultats=results.hits,debut=1,resultats=liste_acte)
        return jsonify(reponse.serialize)

