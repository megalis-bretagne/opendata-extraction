from datetime import datetime
from flask import jsonify
from flask_restx import Namespace, reqparse, fields, Resource
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from app import oidc

api = Namespace(name='parametrage', description='API de gestion du paramétrage <b>(API sécurisée)</b>')

model_parametrage = api.model('parametrage', {
    'id': fields.Integer,
    'siren': fields.String,
    'nic': fields.String,
    'denomination': fields.String,
    'open_data_active': fields.Boolean,
    'publication_data_gouv_active': fields.Boolean,
    'publication_udata_active': fields.Boolean,
    'uid_data_gouv': fields.String,
    'api_key_data_gouv': fields.String
})

model_parametrage_list = api.model('ParametrageList', {
    'parametrages': fields.List(fields.Nested(model_parametrage))
})

arguments_parametrage_controller = reqparse.RequestParser()

arguments_parametrage_controller.add_argument('id', help='id parametrage')
arguments_parametrage_controller.add_argument('open_data_active', help='service open data actif', type=bool)
arguments_parametrage_controller.add_argument('publication_data_gouv_active',
                                              help='service publication data gouv actif', type=bool)
arguments_parametrage_controller.add_argument('publication_udata_active',
                                              help='service publication udata actif', type=bool)
arguments_parametrage_controller.add_argument('uid_data_gouv', help='uid organisme sur data gouv')
arguments_parametrage_controller.add_argument('api_key_data_gouv', help='api key pour publication sur data gouv')


@api.route('/<siren>')
@api.param('siren', 'siren')
class ParametrageCtrl(Resource):
    @api.response(200, 'Success', model_parametrage)
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    def get(self, siren):
        from app.models.parametrage_model import Parametrage
        try:
            parametrage = Parametrage.query.filter(Parametrage.siren == siren).one()
            return jsonify(parametrage.serialize)
        except MultipleResultsFound:
            api.abort(500, 'MultipleResultsFound')
        except NoResultFound:
            # on retourne un parametrage par defaut
            return jsonify(
                {
                    "id": '0',
                    "siren": siren,
                    "nic": "",
                    "denomination": "",
                    "open_data_active": False,
                    "publication_data_gouv_active": False,
                    "publication_udata_active": False,
                    "uid_data_gouv": "",
                    "api_key_data_gouv": ""
                }
            )

    @api.expect(arguments_parametrage_controller)
    @api.response(200, 'Success', model_parametrage)
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    def post(self, siren):
        from app.models.parametrage_model import Parametrage
        from app.tasks.publication import gestion_activation_open_data
        from app.shared.client_api_sirene.flask_functions import etablissement_siege_pour_siren
        from app import db
        args = arguments_parametrage_controller.parse_args()

        try:
            etablissement = etablissement_siege_pour_siren(siren)
        except Exception:
            api.abort(400, 'etablissement not found in URL_API_ENNTREPRISE')

        try:
            parametrage = Parametrage.query.filter(Parametrage.siren == siren).one()
            parametrage.nic = etablissement.nic
            parametrage.denomination = etablissement.denomination_unite_legale
            parametrage.open_data_active = args['open_data_active'] or False
            parametrage.publication_data_gouv_active = args['publication_data_gouv_active'] or False
            # parametrage.publication_udata_active = args['publication_udata_active']
            parametrage.publication_udata_active = True
            parametrage.uid_data_gouv = args['uid_data_gouv']
            parametrage.api_key_data_gouv = args['api_key_data_gouv']
            parametrage.modified_at = datetime.now()
            db_sess = db.session
            db_sess.add(parametrage)
            db_sess.commit()
            gestion_activation_open_data.delay(siren, args['open_data_active'])

        except MultipleResultsFound as e:
            print(e)
            api.abort(500, 'MultipleResultsFound')

        except NoResultFound as e:
            # on ajoute l'organisme dans notre bdd
            db_sess = db.session
            new_parametrage = Parametrage(created_at=datetime.now(),
                                          modified_at=datetime.now(),
                                          siren=siren,
                                          nic=etablissement.nic,
                                          denomination=etablissement.denomination_unite_legale,
                                          open_data_active=args['open_data_active'] or False,
                                          publication_data_gouv_active=args['publication_data_gouv_active'] or False,
                                          # publication_udata_active=args['publication_udata_active'],
                                          publication_udata_active=True,
                                          uid_data_gouv=args['uid_data_gouv'],
                                          api_key_data_gouv=args['api_key_data_gouv']
                                          )
            db_sess.add(new_parametrage)
            db_sess.commit()
            parametrage = new_parametrage

        return jsonify(parametrage.serialize)
