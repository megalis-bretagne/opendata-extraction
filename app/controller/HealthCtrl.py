import logging
from flask import jsonify,current_app
from flask_restx import Namespace, Resource

api = Namespace(name='health',description='Les publications sont une réprésentation des actes reçus depuis Pastell')

@api.route('',doc={
    "description": "healthcheck des API opendata"})
class HealthCtrl(Resource):
    @api.response(200, 'Success')
    def get(self):
        return jsonify({"statut": 'ok'})


@api.route('/solr',doc={
    "description": "healthcheck du moteur de recherche sorl"})
class HealthSolrCtrl(Resource):
    @api.response(200, 'Success')
    def get(self):
        from app.tasks.utils import solr_connexion
        solr = solr_connexion()
        if solr.verify:
            return jsonify(
                    {
                        "statut": 'ok',
                        "url": current_app.config['URL_SOLR']

                    })
        else:
            return jsonify(
                {
                    "statut": 'down',
                    "url": current_app.config['URL_SOLR']

                })

@api.route('/apiSirene',doc={
    "description": "healthcheck des api sirene (insee et entreprise)"})
class HealthInseeCtrl(Resource):
    @api.response(200, 'Success')
    def get(self):
        from app.shared.client_api_sirene.flask_functions import etablissement_siege_pour_siren

        # siren de megalis
        siren = "253514491"

        try:
            etab_siege = etablissement_siege_pour_siren(siren)
            return jsonify(
                    {
                        "statut": 'ok',
                        "denomination_unite_legale": etab_siege.denomination_unite_legale,
                    }
            )
        except Exception as e:
            logging.exception(e)
            return jsonify(
                {
                    "statut": 'down',
                }
            )