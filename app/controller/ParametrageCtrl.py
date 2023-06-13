from datetime import datetime
import logging
from flask import jsonify
from flask_restx import Namespace, reqparse, fields, Resource
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from app import oidc
from app.models.parametrage_model import Parametrage
from app.shared.client_api_sirene.data_structures import Etablissement

api = Namespace(name='parametrage', description='API de gestion du paramétrage')

logger = logging.getLogger(__name__)

model_parametrage = api.model('parametrage', {
    'id': fields.Integer,
    'siren': fields.String,
    'nic': fields.String,
    'denomination': fields.String,
    'open_data_active': fields.Boolean,
    'publication_des_annexes': fields.Boolean,
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
arguments_parametrage_controller.add_argument('open_data_active', help='service open data actif.', type=bool)
arguments_parametrage_controller.add_argument('publication_des_annexes', help='Publication des annexes pour l\'organisation.', type=bool)
arguments_parametrage_controller.add_argument('publication_data_gouv_active',
                                              help='service publication data gouv actif', type=bool)
arguments_parametrage_controller.add_argument('publication_udata_active',
                                              help='service publication udata actif', type=bool)
arguments_parametrage_controller.add_argument('uid_data_gouv', help='uid organisme sur data gouv')
arguments_parametrage_controller.add_argument('api_key_data_gouv', help='api key pour publication sur data gouv')


@api.route('/<siren>')
@api.param('siren', 'siren')
@api.doc(security=['bearer'])
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
                    "publication_des_annexes": True,
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
        from app.tasks.publication import gestion_activation_open_data, republier_actes_pour_siren_task
        from app.shared.client_api_sirene.flask_functions import etablissement_siege_pour_siren
        from app import db
        ctrl_args = arguments_parametrage_controller.parse_args()
        args = { k: v for k,v in ctrl_args.items() if v is not None }

        try:
            etablissement = etablissement_siege_pour_siren(siren)
        except Exception as e:
            logger.exception(e)
            api.abort(400, 'etablissement not found in URL_API_ENNTREPRISE')

        try:
            parametrage = Parametrage.query.filter(Parametrage.siren == siren).one()
        except NoResultFound as e:
            logger.debug(f"Le paramétrage pour le {siren} n'existe pas. Création d'un paramétrage par défaut.")
            parametrage = _new_parametrage(siren, etablissement)
            db.session.add(parametrage)
            db.session.commit()
        except MultipleResultsFound as e:
            logger.exception(e)
            api.abort(500, str(e))

        logger.info(f"Mise à jour du paramétrage pour siren {siren}.")
        parametrage.nic = etablissement.nic
        parametrage.denomination = etablissement.denomination_unite_legale
        parametrage.publication_data_gouv_active = args.get('publication_data_gouv_active', False)
        parametrage.publication_udata_active = True
        parametrage.uid_data_gouv = args.get('uid_data_gouv', '')
        parametrage.api_key_data_gouv = args.get('api_key_data_gouv', '')
        parametrage.modified_at = datetime.now()

        open_data_active = args['open_data_active']
        do_maj_open_data_active = False
        if 'open_data_active' in args and open_data_active != parametrage.open_data_active:
            logger.info(f"Changement du paramètre open_data_active vers {open_data_active}")
            do_maj_open_data_active = True
            parametrage.open_data_active = open_data_active
        
        publication_des_annexes = args['publication_des_annexes']
        do_maj_publication_annexes = False
        if 'publication_des_annexes' in args and publication_des_annexes != parametrage.publication_annexes:
            logger.info(f"Changement du paramètre publication_des_annexes vers {publication_des_annexes}")
            do_maj_publication_annexes = True
            parametrage.publication_annexes = publication_des_annexes

        db.session.add(parametrage)
        db.session.commit()

        if do_maj_open_data_active:
            logger.debug(f"Mise à jour de SOLR pour le paramètre open_data_active")
            gestion_activation_open_data.delay(siren, args['open_data_active'])

        if do_maj_publication_annexes:
            logger.debug(f"Mise à jour de l'historique pour la publication des annexes du siren {siren}")
            republier_actes_pour_siren_task.delay(siren, '1') # On republie tous les actes du siren qui sont déjà publiés

        return jsonify(parametrage.serialize)

def _new_parametrage(siren, etablissement: Etablissement):
    new_parametrage = Parametrage(
        created_at=datetime.now(),
        modified_at=datetime.now(),
        siren=siren,
        nic=etablissement.nic,
        denomination = etablissement.denomination_unite_legale,
    )
    return new_parametrage
