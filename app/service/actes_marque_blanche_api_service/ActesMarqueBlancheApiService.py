import logging

from pysolr import SolrError

from app.service.actes_marque_blanche_api_service.search_solr_model import Page, Annexe, Acte
from .exceptions import SolrMarqueBlancheError,ActesMarqueBlancheApiException
from .functions import _wrap_in_acte_marque_blanche_api_ex



class ActesMarqueBlancheApiService:

    def __init__(self):
        self.__logger = logging.getLogger(self.__class__.__name__)

    @_wrap_in_acte_marque_blanche_api_ex
    def search(self,searchParams):
        from app.tasks import solr_connexion

        filterQuery, query, lignes, cursorMark = self.gestion_arguments(searchParams)
        self.__logger.info(f"query sorl {query}")
        self.__logger.info(f"Filtre sorl {filterQuery}")

        solr = solr_connexion()

        results = self.callSolr(filterQuery, query, cursorMark, solr)

        # utilisé pour dédoublonner
        dict_Acte = {}
        # utilisé pour creer la réponse
        liste_acte = []
        termine = True
        if len(results.docs) > 0:
            termine = False

        while not termine:

            for doc in results.docs:

                _typologie = doc['typology'][0]
                _publication_id = doc['publication_id'][0]
                if 'score' in doc:
                    self.__logger.info(f"id document {str(_publication_id)} score: {str(doc['score'])}")

                if _publication_id in dict_Acte:
                    self.__logger.info(f"deja présent {str(_publication_id)} - {_typologie}")
                    if _typologie != 'PJ':
                        dict_Acte[_publication_id].resultat_recherche = True
                        self.__logger.info(f"   flag acte resultat_recherche=true - {str(_publication_id)} - {dict_Acte[_publication_id].hash}")
                    else:
                        for annexe in dict_Acte[_publication_id].annexes:
                            if annexe.hash == doc['hash'][0]:
                                self.__logger.info(
                                    f"   flag annexe resultat_recherche=true - {str(_publication_id)} - {annexe.hash}")
                                annexe.resultat_recherche = True
                                break
                else:
                    self.__logger.info(f"AJOUT  - {str(_publication_id)} - {_typologie}")
                    if _typologie != 'PJ':

                        # C'est un acte ACTE
                        _hash = doc['hash'][0]
                        _siren = doc['siren']
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

                        _acte = Acte(hash=_hash, siren=_siren, publication_id=_publication_id, id=_id, type=_type,
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
                        _content_type_annexe = doc['content_type'][0]
                        _annexe = Annexe(hash=_hash_annexe, url=_url_annexe, id=_id_annexe,
                                         content_type=_content_type_annexe, resultat_recherche=True)
                        _acte.annexes.append(_annexe)
                        liste_acte.append(_acte)
                        self.completer_annexes(_acte, solr, _id_annexe)

                    dict_Acte[_publication_id] = _acte

            if (cursorMark == results.nextCursorMark):
                termine = True
            else:
                if len(liste_acte) >= int(lignes):
                    termine = True
                cursorMark = results.nextCursorMark
                results = self.callSolr(filterQuery, query, results.nextCursorMark, solr)

        if results.nextCursorMark == '*' or cursorMark == results.nextCursorMark:
            _page_suivante = ''
        else:
            _page_suivante = results.nextCursorMark

        return Page(nb_resultats=results.hits, resultats=liste_acte, page_suivante=_page_suivante)



    def callSolr(self, filterQuery, query, cursorMark, solr):

        try:
            if query == '*:*':
                results = solr.search(q=query, **{
                    'fq': filterQuery,
                    'rows': 1,
                    'cursorMark': cursorMark,
                    'sort': 'date_de_publication desc,id desc',
                    'fl': 'hash,publication_id,id,documenttype,classification_code,classification_nom,description,'
                          'publication_id,date,date_de_publication,filepath,typology,content_type,type_autre_detail,'
                          'blockchain_transaction_hash,blockchain_url,siren,score'

                })
            else:
                results = solr.search(q=query, **{
                    'defType': 'edismax',
                    'fq': filterQuery,
                    'qf': 'documentidentifier^10 description^5 _text_^2 classification_nom',
                    'rows': 1,
                    'cursorMark': cursorMark,
                    'sort': 'score desc,id desc',
                    'fl': 'hash,publication_id,id,documenttype,classification_code,classification_nom,description,'
                          'publication_id,date,date_de_publication,filepath,typology,content_type,type_autre_detail,'
                          'blockchain_transaction_hash,blockchain_url,siren,score'

                })

            return results
        except SolrError as err:
            logging.exception(err)
            raise SolrMarqueBlancheError(message="requete invalide")

    def gestion_arguments(self, searchParams):
        args = searchParams.parse_args()

        if args['query'] is None or args['query'] == '':
            query = '*:*'
        else:
            query = args['query']
        filterQuery = 'est_publie:true'

        if args['siren'] is not None:
            siren = args['siren']
            filterQuery = filterQuery + ' AND siren:' + siren

        if args['types_actes'] is not None:
            liste_type_acte = args['types_actes'].split(',', 8)
            first = True
            type_actes_filter = ''
            for nature in liste_type_acte:
                if first:
                    type_actes_filter = '(documenttype:' + nature
                    first = False
                else:
                    type_actes_filter = type_actes_filter + ' OR documenttype:' + nature
            filterQuery = filterQuery + ' AND ' + type_actes_filter + ')'

        if args['classifications'] is not None:
            liste_classification = args['classifications'].split(',', 10)
            first = True
            classification_filter = ''
            for classification in liste_classification:
                if first:
                    classification_filter = '(classification_code:' + classification + '*'
                    first = False
                else:
                    classification_filter = classification_filter + ' OR classification_code:' + classification + '*'
            filterQuery = filterQuery + ' AND ' + classification_filter + ')'

        if args['date_debut'] == None:
            date_debut = '*'
        else:
            # add to fq
            date_debut = args['date_debut']

        if args['date_fin'] == None:
            date_fin = 'NOW'
        else:
            # add to fq
            date_fin = args['date_fin']
        filterQuery = filterQuery + ' AND date_de_publication:[' + date_debut + ' TO ' + date_fin + ']'

        if args['lignes'] == None:
            # valeur par defaut
            lignes = 10
        else:
            lignes = args['lignes']

        if args['page_suivante'] == None:
            # valeur par defaut
            cursorMark = '*'
        else:
            cursorMark = args['page_suivante']

        return filterQuery, query, lignes, cursorMark

    def completer_annexes(self, acte, solr, idAnnexeAignorer=0):
        result_annexes = solr.search(q='publication_id:' + str(acte.id_publication), **{
            'rows': 100,
            'start': 0,
            'fq': 'typology:PJ AND est_publie:true AND NOT id:' + str(idAnnexeAignorer),
            'fl': 'hash,id,documenttype,filepath,content_type'
        })
        for docA in result_annexes.docs:
            _url_annexe = docA['filepath'][0]
            _hash_annexe = docA['hash'][0]
            _id_annexe = docA['id']
            _content_type = docA['content_type'][0]
            _annexe = Annexe(hash=_hash_annexe, url=_url_annexe, id=_id_annexe, resultat_recherche=False,
                             content_type=_content_type)
            acte.annexes.append(_annexe)

    def recuperer_acte(self, id_pub, solr):
        result_annexes = solr.search(q='publication_id:' + id_pub, **{
            'rows': 1,
            'start': 0,
            'fq': 'NOT typology:PJ AND est_publie:true',
            'fl': 'hash,publication_id,id,documenttype,classification_code,classification_nom,description,'
                  'publication_id,date,date_de_publication,filepath,typology,content_type,type_autre_detail,'
                  'blockchain_transaction_hash,blockchain_url,siren,score'
        })
        for doc in result_annexes.docs:
            _hash = doc['hash'][0]
            _siren = doc['siren']
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

            _acte = Acte(hash=_hash, siren=_siren, publication_id=_publication_id, id=_id, type=_type,
                         type_autre_detail=_type_autre_detail, classification_code=_classification_code,
                         classification_libelle=_classification_libelle, objet=_objet, id_publication=_id_publication,
                         date_acte=_date_acte, date_publication=_date_publication, url=_url, typologie=_typologie,
                         content_type=_content_type, blockchain_transaction_hash=_blockchain_transaction_hash,
                         blockchain_url=_blockchain_url, resultat_recherche=_resultat_recherche, annexes=[])
            return _acte
