from datetime import datetime
from flask import jsonify
from flask_restx import Namespace, reqparse, fields, Resource
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from app import oidc

api = Namespace(name='parametrage', description='API de gestion du paramétrage <b>(API sécurisée)</b>')

model_parametrage = api.model('parametrage', {
    'id': fields.Integer,
    'siren': fields.String,
    'open_data_active': fields.Boolean,
    'publication_data_gouv_active': fields.Boolean,
    'uid_data_gouv': fields.String,
    'api_key_data_gouv': fields.String
})

model_parametrage_list = api.model('ParametrageList', {
    'parametrages': fields.List(fields.Nested(model_parametrage))
})

arguments_parametrage_controller = reqparse.RequestParser()
arguments_parametrage_controller.add_argument('id', help='id parametrage')
arguments_parametrage_controller.add_argument('siren', help='siren')
arguments_parametrage_controller.add_argument('open_data_active', help='service open data actif',type=bool)
arguments_parametrage_controller.add_argument('publication_data_gouv_active',
                                              help='service publication data gouv actif',type=bool)
arguments_parametrage_controller.add_argument('uid_data_gouv', help='uid organisme sur data gouv')
arguments_parametrage_controller.add_argument('api_key_data_gouv', help='api key pour publication sur data gouv')


@api.route('/<siren>')
class ParametrageCtrl(Resource):
    @api.response(200, 'Success', model_parametrage)
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    def get(self, siren):
        from app.models.parametrage_model import Parametrage
        try:
            parametrage = Parametrage.query.filter(Parametrage.siren == siren).one()
            return jsonify(parametrage.serialize)
        except MultipleResultsFound as e:
            api.abort(500, 'MultipleResultsFound')
        except NoResultFound as e:
            # on retourne un parametrage par defaut
            return jsonify(
                {
                    "id": '0',
                    "siren": siren,
                    "open_data_active": False,
                    "publication_data_gouv_active": False,
                    "uid_data_gouv": "",
                    "api_key_data_gouv": ""
                }
            )

    @api.expect(arguments_parametrage_controller)
    @api.response(200, 'Success', model_parametrage)
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    def post(self,siren):
        from app.models.parametrage_model import Parametrage
        from app.tasks.publication_tasks import gestion_activation_open_data
        from app import db
        args = arguments_parametrage_controller.parse_args()
        try:
            parametrage = Parametrage.query.filter(Parametrage.siren == args['siren']).one()
            parametrage.open_data_active = args['open_data_active']
            parametrage.publication_data_gouv_active = args['publication_data_gouv_active']
            parametrage.uid_data_gouv = args['uid_data_gouv']
            parametrage.api_key_data_gouv = args['api_key_data_gouv']
            parametrage.modified_at = datetime.now()
            db_sess = db.session
            db_sess.add(parametrage)
            db_sess.commit()
            gestion_activation_open_data.delay( args['siren'], args['open_data_active'])

        except MultipleResultsFound as e:
            print(e)
            api.abort(500, 'MultipleResultsFound')

        except NoResultFound as e:
            # on ajoute l'organisme dans notre bdd
            db_sess = db.session
            newParametrage = Parametrage(created_at=datetime.now(),
                                         modified_at=datetime.now(),
                                         siren=args['siren'],
                                         open_data_active=args['open_data_active'],
                                         publication_data_gouv_active=args['publication_data_gouv_active'],
                                         uid_data_gouv=args['uid_data_gouv'],
                                         api_key_data_gouv=args['api_key_data_gouv']
                                         )
            db_sess.add(newParametrage)
            db_sess.commit()
            parametrage = newParametrage

        return jsonify(parametrage.serialize)
