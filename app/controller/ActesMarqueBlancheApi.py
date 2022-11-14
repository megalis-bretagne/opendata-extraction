from flask import Blueprint, jsonify
from flask_restx import Api, Namespace, Resource, fields, reqparse

from app.models.search_solr_model import Acte, Page, Annexe

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
    'debut': fields.Integer,
    'resultats': fields.List(fields.Nested(Acte)),

})

searchParams = reqparse.RequestParser()
searchParams.add_argument('query', help='filtre de recherche sur le numéro d\'acte')
searchParams.add_argument('date_debut', help='date au format iso')
searchParams.add_argument('date_fin', help='date au format iso')
searchParams.add_argument('classifications', help='asc ou desc (desc par defaut)')
searchParams.add_argument('types_actes', help='asc ou desc (desc par defaut)')
searchParams.add_argument('pageSuivante', help='page suivante')
searchParams.add_argument('lignes', help='asc ou desc (desc par defaut)')


@actes_api_ns.route('/search')
class PublicationSearchCtrl(Resource):
    @actes_api_ns.expect(searchParams)
    # @actes_api_ns.marshal_with(page, code=200)
    def get(self):
        from app.tasks.utils import solr_connexion
        solr = solr_connexion()
        args = searchParams.parse_args()
        query = args['query']

        if args['date_debut'] == None:
            date_debut = '*'
        else:
            # add to fq
            date_debut = args['date_debut']
        if args['date_fin'] == None:
            date_fin = 'NOW'
        else:
            # add to fq
            date_fin = args['date_debut']
        if args['date_fin'] is not None:
            # add to fq
            date_fin = args['date_fin']

        classifications = args['classifications']
        types_actes = args['types_actes']

        if args['lignes'] == None:
            # valeur par defaut
            lignes = 10
        else:
            lignes = args['lignes']
        if args['pageSuivante'] == None:
            # valeur par defaut
            cursorMark='*'
        else:
            cursorMark = args['pageSuivante']

        filterQuery = 'est_publie:true'
        filterQuery = filterQuery + ' AND date:[' + date_debut + ' TO ' + date_fin + ']'

        results = self.callSolr(filterQuery, query, cursorMark, solr)

        termine = True
        dict_Acte = {}
        liste_acte = []

        if len(results.docs) > 0:
            termine = False

        while not termine:
            print(filterQuery)
            for doc in results.docs:

                _typologie = doc['typology'][0]
                _publication_id = doc['publication_id'][0]

                if 'score' in doc:
                    print('score= ' + str(doc['score']) + ' - ' + str(_publication_id) + ' - ' + _typologie)

                if _publication_id in dict_Acte:
                    # print('deja présent ' + str(_publication_id) + ' - ' + _typologie)
                    if _typologie != 'PJ':
                        dict_Acte[_publication_id].resultat_recherche = True
                        # print('   flag acte resultat_recherche=true :' + str(_publication_id) + ' - ' + dict_Acte[_publication_id].hash)
                    else:
                        for annexe in dict_Acte[_publication_id].annexes:
                            if annexe.hash == doc['hash'][0]:
                                # print('   flag annexe resultat_recherche=true :' + str(_publication_id) + ' - ' + annexe.hash)
                                # print('   flag annexe resultat_recherche=true :' + str(_publication_id) + ' - ' + annexe.hash)
                                annexe.resultat_recherche = True
                                break
                else:
                    # print('ADD ' + str(_publication_id) + ' - ' + _typologie)
                    if _typologie != 'PJ':
                        # C'est un acte ACTE
                        _hash = doc['hash'][0]
                        _id = doc['id']
                        _type = doc['documenttype'][0]
                        _classification_code = doc['classification_code']
                        _classification_libelle = doc['classification_nom']
                        _objet = doc['description'][0]
                        _id_publication = doc['publication_id'][0]
                        _date_acte = doc['date'][0]
                        _date_publication = doc['date_de_publication'][0]
                        _url = doc['filepath'][0]
                        _content_type = doc['content_type'][0]
                        _type_autre_detail = doc['type_autre_detail'] if 'type_autre_detail' in doc else ""
                        _blockchain_transaction_hash = doc[
                            'blockchain_transaction_hash'] if 'blockchain_transaction_hash' in doc else ""
                        _blockchain_url = doc['blockchain_url'] if 'blockchain_url' in doc else ""
                        _resultat_recherche = True

                        _acte = Acte(hash=_hash, publication_id=_publication_id, id=_id, type=_type,
                                     type_autre_detail=_type_autre_detail, classification_code=_classification_code,
                                     classification_libelle=_classification_libelle, objet=_objet,
                                     id_publication=_id_publication,
                                     date_acte=_date_acte, date_publication=_date_publication, url=_url,
                                     typologie=_typologie,
                                     content_type=_content_type,
                                     blockchain_transaction_hash=_blockchain_transaction_hash,
                                     blockchain_url=_blockchain_url, resultat_recherche=_resultat_recherche, annexes=[])
                        liste_acte.append(_acte)

                        self.completer_annexes(_acte, solr)

                    else:
                        _publication_id = doc['publication_id'][0]
                        _acte = self.recuperer_acte(str(_publication_id), solr)
                        _url_annexe = doc['filepath'][0]
                        _hash_annexe = doc['hash'][0]
                        _id_annexe = doc['id']
                        _annexe = Annexe(hash=_hash_annexe, url=_url_annexe, id=_id_annexe, resultat_recherche=True)
                        try:
                            _acte.annexes.append(_annexe)
                        except Exception as e:
                            print(e)
                        liste_acte.append(_acte)
                        self.completer_annexes(_acte, solr, _id_annexe)

                    dict_Acte[_publication_id] = _acte

            if (cursorMark == results.nextCursorMark):
                termine = True
            else:
                if len(liste_acte) >= int(lignes):
                    termine = True
                cursorMark=results.nextCursorMark
                results = self.callSolr(filterQuery, query, results.nextCursorMark, solr)

        reponse = Page(nb_resultats=results.hits, debut=1, resultats=liste_acte,pageSuivante=results.nextCursorMark)
        return jsonify(reponse.serialize)

    def callSolr(self, filterQuery,query,cursorMark, solr):
        results = solr.search(q=query, **{
            'defType': 'edismax',
            'fq': filterQuery,
            'qf': 'documentidentifier^10 description^5 _text_^2 classification_nom',
            'rows': 1,
            'cursorMark': cursorMark,
            'sort': 'score desc,id desc',
            'fl': 'hash,publication_id,id,documenttype,classification_code,classification_nom,description,'
                  'publication_id,date,date_de_publication,filepath,typology,content_type,type_autre_detail,'
                  'blockchain_transaction_hash,blockchain_url,score'

        })
        return results

    def completer_annexes(self, acte, solr, idAnnexeAignorer=0):
        result_annexes = solr.search(q='publication_id:' + str(acte.id_publication), **{
            'rows': 100,
            'start': 0,
            'fq': 'typology:PJ AND est_publie:true AND NOT id:' + str(idAnnexeAignorer),
            'fl': 'hash,id,documenttype,filepath'
        })
        for docA in result_annexes.docs:
            print("   completer les annexes dans la publication: " + str(acte.id_publication))
            _url_annexe = docA['filepath'][0]
            _hash_annexe = docA['hash'][0]
            _id_annexe = docA['id']
            _annexe = Annexe(hash=_hash_annexe, url=_url_annexe, id=_id_annexe, resultat_recherche=False)
            acte.annexes.append(_annexe)

    def recuperer_acte(self, id_pub, solr):
        result_annexes = solr.search(q='publication_id:' + id_pub, **{
            'rows': 1,
            'start': 0,
            'fq': 'NOT typology:PJ AND est_publie:true',
            'fl': 'hash,publication_id,id,documenttype,classification_code,classification_nom,description,'
                  'publication_id,date,date_de_publication,filepath,typology,content_type,type_autre_detail,'
                  'blockchain_transaction_hash,blockchain_url'
        })
        for doc in result_annexes.docs:
            print("   Récupérer l'acte dans la publication: " + str(id_pub))
            _hash = doc['hash'][0]
            _publication_id = doc['publication_id'][0]
            _id = doc['id']
            _type = doc['documenttype'][0]
            _classification_code = doc['classification_code']
            _classification_libelle = doc['classification_nom']
            _objet = doc['description'][0]
            _id_publication = doc['publication_id'][0]
            _date_acte = doc['date'][0]
            _date_publication = doc['date_de_publication'][0]
            _url = doc['filepath'][0]
            _typologie = doc['typology'][0]
            _content_type = doc['content_type'][0]
            _type_autre_detail = doc['type_autre_detail'] if 'type_autre_detail' in doc else ""
            _blockchain_transaction_hash = doc[
                'blockchain_transaction_hash'] if 'blockchain_transaction_hash' in doc else ""
            _blockchain_url = doc['blockchain_url'] if 'blockchain_url' in doc else ""
            _resultat_recherche = False

            _acte = Acte(hash=_hash, publication_id=_publication_id, id=_id, type=_type,
                         type_autre_detail=_type_autre_detail, classification_code=_classification_code,
                         classification_libelle=_classification_libelle, objet=_objet, id_publication=_id_publication,
                         date_acte=_date_acte, date_publication=_date_publication, url=_url, typologie=_typologie,
                         content_type=_content_type, blockchain_transaction_hash=_blockchain_transaction_hash,
                         blockchain_url=_blockchain_url, resultat_recherche=_resultat_recherche, annexes=[])
            return _acte
