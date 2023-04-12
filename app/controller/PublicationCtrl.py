from flask import jsonify
from flask_restx import Namespace, reqparse, fields, Resource
from sqlalchemy import or_
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from app import oidc
from app.controller.Decorator import isAdmin

api = Namespace(name='publication', description='API de gestion des publications <b>(API sécurisée)</b>')

model_acte = api.model('acte', {
    'id': fields.Integer,
    'url': fields.String,
    'name': fields.String,
    'publication_id': fields.Integer
})

model_piece_jointe = api.model('piece_jointe', {
    'id': fields.Integer,
    'url': fields.String,
    'name': fields.String,
    'publication_id': fields.Integer
})

model_publication = api.model(
    'publication', {
        'id': fields.Integer,
        'numero_de_lacte': fields.String,
        'objet': fields.String,
        'siren': fields.String,
        'publication_open_data': fields.String,
        'etat': fields.String,
        'date_de_lacte': fields.DateTime,
        'classification_code': fields.String,
        'classification_nom': fields.String,
        'acte_nature': fields.String,
        'actes': fields.List(fields.Nested(model_acte)),
        'pieces_jointe': fields.List(fields.Nested(model_piece_jointe)),
    })

model_publication_light = api.model(
    'publication', {
        'id': fields.Integer,
        'numero_de_lacte': fields.String,
        'siren': fields.String,
        'date_de_lacte': fields.DateTime,
        'create_at': fields.DateTime,
        'est_supprime': fields.Boolean,
        'nb_pj': fields.Integer

    })
model_publication_light_list = api.model('PublicationLightList', {
    'publicationsLight': fields.List(fields.Nested(model_publication_light))
})

model_publication_list = api.model('PublicationList', {
    'publications': fields.List(fields.Nested(model_publication))
})

arguments_publication_controller = reqparse.RequestParser()
arguments_publication_controller.add_argument('siren', help='siren')

arguments_publication_modifier_controller = reqparse.RequestParser()
arguments_publication_modifier_controller.add_argument('objet', help="objet de l\'acte")

publicationParams_search_controller = reqparse.RequestParser()
publicationParams_search_controller.add_argument('filter', help='filtre de recherche sur le numéro d\'acte ou bien l\'objet')
publicationParams_search_controller.add_argument('sortDirection', help='asc ou desc (desc par defaut)')
publicationParams_search_controller.add_argument('sortField',
                                                 help='champ de tri (numero_de_lacte,publication_open_data,'
                                                      'date_de_lacte,acte_nature,etat,id par defaut')
publicationParams_search_controller.add_argument('pageIndex', help='index de la page, commence par 0', required=True)
publicationParams_search_controller.add_argument('pageSize', type=int, help='taille de la page', required=True)
publicationParams_search_controller.add_argument('siren', help='siren de l\'organisme')
publicationParams_search_controller.add_argument('etat',
                                                 help='etat de la publication (1: publie, 0:non, 2:en-cours,'
                                                      '3:en-erreur)')
publicationParams_search_controller.add_argument('est_masque',
                                                 help='est à publier (0:non, 1:oui)')

publicationLightParams_search_controller = reqparse.RequestParser()
publicationLightParams_search_controller.add_argument('filter', help='filtre de recherche sur le numéro d\'acte ou bien l\'objet')
publicationLightParams_search_controller.add_argument('siren', help='siren de l\'organisme')
publicationLightParams_search_controller.add_argument('pastell_id_d', help='L\'id du document interne à pastell')
publicationLightParams_search_controller.add_argument('sortDirection', help='asc ou desc (desc par defaut)')
publicationLightParams_search_controller.add_argument('sortField',
                                                      help='champ de tri (numero_de_lacte,publication_open_data,'
                                                           'date_de_lacte,acte_nature,etat,id par defaut')
publicationLightParams_search_controller.add_argument('pageIndex', help='index de la page, commence par 0',
                                                      required=True)
publicationLightParams_search_controller.add_argument('pageSize', help='taille de la page', required=True)


@api.route('')
class PublicationAllCtrl(Resource):
    @api.response(200, 'Success', model_publication)
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def get(self):
        from app.models.publication_model import Publication
        result = Publication.query.all()
        return jsonify({"publications": [i.serialize for i in result]})


@api.route('/publier/<int:id>')
class PublicationPublierCtrl(Resource):
    @api.response(200, 'Success', model_publication)
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    def put(self, id):
        from app.models.publication_model import Publication
        from app import db
        from app.tasks.publication import publier_acte_task
        try:
            db_sess = db.session
            publication = Publication.query.filter(Publication.id == id).one()
            # 1 => publie, 0:non, 2:en-cours,3:en-erreur
            publication.etat = 2
            db_sess.commit()
            task = publier_acte_task.delay(publication.id)
            return jsonify(publication.serialize)

        except MultipleResultsFound as e:
            print(e)
            api.abort(500, 'MultipleResultsFound')
        except NoResultFound as e:
            print(e)
            api.abort(404, 'Not found')


@api.route('/depublier/<int:id>')
class PublicationDepublierCtrl(Resource):
    @api.response(200, 'Success', model_publication)
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    def put(self, id):
        from app.models.publication_model import Publication
        from app import db
        from app.tasks.publication import depublier_acte_task
        try:
            db_sess = db.session
            publication = Publication.query.filter(Publication.id == id).one()
            # 1 => publie, 0:non, 2:en-cours,3:en-erreur
            publication.etat = 2
            publication.est_masque = True
            db_sess.commit()
            task = depublier_acte_task.delay(publication.id)
            return jsonify(publication.serialize)

        except MultipleResultsFound as e:
            print(e)
            api.abort(500, 'MultipleResultsFound')
        except NoResultFound as e:
            print(e)
            api.abort(404, 'Not found')


@api.route('/modifier/<int:id>')
class PublicationModifierCtrl(Resource):
    @api.expect(arguments_publication_modifier_controller)
    @api.response(200, 'Success', model_publication)
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    def put(self, id):
        from app.models.publication_model import Publication
        from app import db
        from app.tasks.publication import modifier_acte_task
        try:
            db_sess = db.session
            publication = Publication.query.filter(Publication.id == id).one()
            args = arguments_publication_modifier_controller.parse_args()
            objet = args['objet']

            print(model_publication)
            publication.objet = objet
            db_sess.commit()

            task = modifier_acte_task.delay(publication.id)
            return jsonify(publication.serialize)

        except MultipleResultsFound as e:
            print(e)
            api.abort(500, 'MultipleResultsFound')
        except NoResultFound as e:
            print(e)
            api.abort(404, 'Not found')


@api.route('/masquer/<int:id>')
class PublicationMasquerCtrl(Resource):
    @api.response(200, 'Success', model_publication)
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    def put(self, id):
        from app.models.publication_model import Publication
        from app import db
        try:
            db_sess = db.session
            publication = Publication.query.filter(Publication.id == id).one()
            # 1 => publie, 0:non, 2:en-cours,3:en-erreur
            publication.est_masque = True
            db_sess.commit()

            return jsonify(publication.serialize)

        except MultipleResultsFound as e:
            print(e)
            api.abort(500, 'MultipleResultsFound')
        except NoResultFound as e:
            print(e)
            api.abort(404, 'Not found')


@api.route('/demasquer/<int:id>')
class PublicationDemasquerCtrl(Resource):
    @api.response(200, 'Success', model_publication)
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    def put(self, id):
        from app.models.publication_model import Publication
        from app import db
        try:
            db_sess = db.session
            publication = Publication.query.filter(Publication.id == id).one()
            publication.est_masque = False
            db_sess.commit()
            return jsonify(publication.serialize)

        except MultipleResultsFound as e:
            print(e)
            api.abort(500, 'MultipleResultsFound')
        except NoResultFound as e:
            print(e)
            api.abort(404, 'Not found')


@api.route('/<int:id>')
class PublicationCtrl(Resource):
    @api.response(200, 'Success', model_publication)
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    def get(self, id):
        from app.models.publication_model import Publication
        try:
            publication = Publication.query.filter(Publication.id == id).one()
            return jsonify(publication.serialize)
        except MultipleResultsFound as e:
            print(e)
            api.abort(500, 'MultipleResultsFound')
        except NoResultFound as e:
            print(e)
            api.abort(404, 'Not found')

    @api.response(200, 'Success', model_publication)
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    def delete(self, id):
        from app.models.publication_model import Publication
        from app import db
        from app.tasks.publication import depublier_acte_task
        try:
            db_sess = db.session
            publication = Publication.query.filter(Publication.id == id).one()
            publication.est_supprime = True

            # 1 => publie, 0:non, 2:en-cours,3:en-erreur
            publication.etat = 2
            publication.est_masque = True
            db_sess.commit()

            # Dépublication des actes supprimés
            task = depublier_acte_task.delay(publication.id)
            return jsonify(publication.serialize)

        except MultipleResultsFound as e:
            print(e)
            api.abort(500, 'MultipleResultsFound')
        except NoResultFound as e:
            print(e)
            api.abort(404, 'Not found')


# Consommée par le front data publication
@api.route('/search')
class PublicationSearchCtrl(Resource):
    @api.expect(publicationParams_search_controller)
    @api.response(200, 'Success', model_publication_list)
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    def post(self):
        args = publicationParams_search_controller.parse_args()
        return _search(
            args, 
            serializeFn=lambda x: x.serialize, 
            est_supprime=0, est_masque=0,
        )

# Consommée par API
@api.route('/search/light')
class PublicationLightSearchCtrl(Resource):
    @api.expect(publicationLightParams_search_controller)
    @api.response(200, 'Success', model_publication_light_list)
    def post(self):
        args = publicationLightParams_search_controller.parse_args()
        return _search(
            args,
            serializeFn=lambda x: x.serializeLight,
        )


def _is_blank(s: str):
    return not (s and s.strip())


def _search(args, serializeFn, est_supprime=None, est_masque=None):
    from app.models.publication_model import Publication

    siren = args.get('siren')
    if args.get('est_masque') == 'True':
        est_masque = 1

    sortField = args.get('sortField')
    if (sortField) == 'numero_de_lacte':
        sortField = Publication.numero_de_lacte
    elif (sortField) == 'publication_open_data':
        sortField = Publication.publication_open_data
    elif (sortField) == 'date_de_lacte':
        sortField = Publication.date_de_lacte
    elif (sortField) == 'acte_nature':
        sortField = Publication.acte_nature
    elif (sortField) == 'etat':
        sortField = Publication.etat
    else:
        sortField = Publication.id

    if (args.get('sortDirection')) == 'asc':
        sortField = sortField.asc()
    else:
        sortField = sortField.desc()
    
    filters = []
    if not _is_blank(args.get('etat')):
        etat = str(args.get('etat'))
        op = Publication.etat == etat
        filters.append(op)
    if not _is_blank(args.get('filter')):
        filter = str(args.get('filter'))
        searchFilter = "%{}%".format(filter)
        op = or_(Publication.numero_de_lacte.like(searchFilter), Publication.objet.like(searchFilter))
        filters.append(op)
    if not _is_blank(args.get('siren')):
        siren = str(args.get('siren'))
        op = Publication.siren == siren
        filters.append(op)
    if not _is_blank(args.get('pastell_id_d')):
        pastell_id_d = str(args.get('pastell_id_d'))
        op = Publication.pastell_id_d == pastell_id_d
        filters.append(op)
    
    if est_supprime:
        filters.append(Publication.est_supprime == est_supprime)
    if est_masque:
        filters.append(Publication.est_masque == est_masque)

    page = int(args.get('pageIndex')) + 1
    per_page = int(args.get('pageSize'))

    query = Publication.query.filter(*filters)
    query = query.order_by(sortField)
    query = query.paginate(page, per_page=per_page)
    result = query

    return jsonify(
        {"total": result.total, "publications": [serializeFn(i) for i in result.items]}
    )