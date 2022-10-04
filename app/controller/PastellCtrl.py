from flask import jsonify
from flask_restx import Namespace, Resource, reqparse
from app import oidc
from app.controller.Decorator import isAdmin

api = Namespace(name='pastell', description="API de création du paramétrage pastell <b>(API sécurisée)</b>")

arguments_pastell_controller = reqparse.RequestParser()
arguments_pastell_controller.add_argument('id_e',
                                          help="identifiant de l'entitie dans pastell pour lequel on souhaite effectuer l'action")

@api.route('/creation/all')
class AdminPastellAllCtrl(Resource):
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.pastell_tasks import creation_et_association_all
        creation_et_association_all.delay()
        return jsonify(
            {"statut": "demande de mise en place du paramétrage pastell pour tous les id_e présent dans pastell (taches asynchrone)"})



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
            {"statut": "id_e:" +id_e + 'demande de mise en place du paramétrage pastell pour l\'id_e en paramètre (taches asynchrone)'})



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
            {"statut": "id_e:" +id_e + 'demande de deblocage_ged_pastell pour l\'id_e en paramètre (taches asynchrone)'})