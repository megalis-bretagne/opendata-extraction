from flask import jsonify,current_app
from flask_restx import Namespace, Resource


api = Namespace(name='health',description='Les publications sont une réprésentation des actes reçus depuis Pastell')


@api.route('')
class HealthCtrl(Resource):
    @api.response(200, 'Success')
    def get(self):
        return jsonify({"statut": 'ok'})


@api.route('/solr')
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

@api.route('/apiInsee')
class HealthInseeCtrl(Resource):
    @api.response(200, 'Success')
    def get(self):
        from app.tasks.utils import api_insee_call
        # on tente de récupérer les infos sur le siren de megalis avec l'api insee
        siren = "253514491"
        result = api_insee_call(siren)
        if result['header']['statut'] == 200:
            return jsonify(
                    {
                        "statut": 'ok',
                        "denominationUniteLegale": result['etablissements'][0]['uniteLegale']['denominationUniteLegale'],
                        "libelleCommuneEtablissement": result['etablissements'][0]['adresseEtablissement']['libelleCommuneEtablissement']
                    })
        else:
            return jsonify(
                {
                    "statut": 'down',
                })