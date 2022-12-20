import json

import requests

from flask import jsonify,current_app
from flask_restx import Namespace, Resource, reqparse
from requests.auth import HTTPBasicAuth
from sqlalchemy import create_engine, text

from app import oidc
from app.controller.Decorator import isAdmin, token_required

api = Namespace(name='pastell', description="API de création du paramétrage pastell <b>(API sécurisée)</b>")

arguments_pastell_controller = reqparse.RequestParser()
arguments_pastell_controller.add_argument('id_e',
                                          help="identifiant de l'entitie dans pastell pour lequel on souhaite effectuer l'action")

arguments_pastell_rejeu_controller = reqparse.RequestParser()
arguments_pastell_rejeu_controller.add_argument('id_d',help="identifiant du document pastell à rejouer",required=True)


@api.route('/creation/all')
class AdminPastellAllCtrl(Resource):
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.pastell_tasks import creation_et_association_all
        creation_et_association_all.delay()
        return jsonify(
            {
                "statut": "demande de mise en place du paramétrage pastell pour tous les id_e présent dans pastell (taches asynchrone)"})


@api.route('/creation/parametrage')
class AdminPastellGedPastellCtrl(Resource):
    @api.expect(arguments_pastell_controller)
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.pastell_tasks import mise_en_place_config_pastell
        args = arguments_pastell_controller.parse_args()
        id_e = args['id_e']
        mise_en_place_config_pastell.delay(id_e)
        return jsonify(
            {
                "statut": "id_e:" + id_e + 'demande de mise en place du paramétrage pastell pour l\'id_e en paramètre (taches asynchrone)'})


@api.route('/routine/parametrage')
class AdminPastellRoutineCtrl(Resource):
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.pastell_tasks import routine_parametrage_pastell
        routine_parametrage_pastell.delay()
        return jsonify(
            {"statut": "routine paramétrage pastell (taches asynchrone)"})


@api.route('/deblocage')
class AdminPastellDeblocageCtrl(Resource):
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.pastell_tasks import deblocage_ged_pastell
        args = arguments_pastell_controller.parse_args()
        id_e = args['id_e']
        deblocage_ged_pastell.delay(id_e)
        return jsonify(
            {
                "statut": "id_e:" + id_e + 'demande de deblocage_ged_pastell pour l\'id_e en paramètre (taches asynchrone)'})


@api.route('/rejeu_doc')
class AdminPastellRejeuDocCtrl(Resource):
    @api.response(200, 'Success')
    @api.expect(arguments_pastell_rejeu_controller)
    @token_required
    def post(self):

        args = arguments_pastell_rejeu_controller.parse_args()
        id_d = args['id_d']

        URL_API_PASTELL = current_app.config['API_PASTELL_URL']
        API_PASTELL_VERSION = current_app.config['API_PASTELL_VERSION']
        auth_pastell = HTTPBasicAuth(current_app.config['API_PASTELL_USER'],
                                     current_app.config['API_PASTELL_PASSWORD'])

        rejeuDemande = False
        acte_declenche = False

        engine = create_engine(current_app.config['SQLALCHEMY_PASTELL_URI'])
        request = text("""select id_a,id_e,id_d,action,date from document_action where id_d = :x order by date desc limit 1""")

        with engine.connect() as con_pastell:
            result = con_pastell.execute(request, x=id_d)
            if result.rowcount ==0:
                motif=f"Pas de document dans pastell pour l'id_d={id_d}"

            for row in result:
                result_id_a =row[0]
                result_id_e = row[1]
                result_id_d = row[2]
                result_action=row[3]

                if result_action == 'termine':

                    doc_detail_reponse = requests.get(
                        URL_API_PASTELL + API_PASTELL_VERSION + "/entite/" + str(result_id_e) + "/document/" +  str(result_id_d),
                        auth=auth_pastell)
                    if doc_detail_reponse.status_code == 200:
                        doc_detail = json.loads(doc_detail_reponse.text)

                        if 'info' in doc_detail and 'type' in doc_detail['info'] and doc_detail['info']['type'] == 'ged-megalis-opendata':
                            rejeuDemande = True
                            # on modidie l'etat de la derniere action dans pastell dans la table document_action termine => creation
                            request_update = text(
                                """UPDATE document_action set action='modification' where id_a = :y """)
                            result_update = con_pastell.execute(request_update, y=result_id_a)
                            result_update.close()
                            print(
                                f"passage à l'état creation de l'action id_a={result_id_a} pour l'id_d={result_id_d} et id_e={result_id_e}")

                            # Déclenchement etape orientation
                            orientation1_ged_reponse = requests.post(
                                URL_API_PASTELL + API_PASTELL_VERSION + "/entite/" + str(result_id_e)  + "/document/" +
                                str(result_id_d) + "/action/orientation",
                                auth=auth_pastell)
                            if orientation1_ged_reponse.status_code == 201:
                                acte_declenche = True
                                break;
                    else:
                        motif = f"le document n'est pas de type= ged-megalis-opendata/ l'id_d={result_id_d} / id_e={result_id_e}"
                else:
                    motif= f"pas de rejeu car l'état de la derniere action n'est pas terminée pour id_a={result_id_a} / l'id_d={result_id_d} / id_e={result_id_e}"
            result.close()

        if not rejeuDemande:
            return jsonify({"rejeuDemande": 'non', "motif" : motif})
        else:
            return jsonify({"rejeuDemande": 'oui',"declenche": str(acte_declenche)})



