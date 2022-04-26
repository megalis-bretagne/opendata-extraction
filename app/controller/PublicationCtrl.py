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

model_publication_list = api.model('PublicationList', {
    'publications': fields.List(fields.Nested(model_publication))
})

arguments_publication_controller = reqparse.RequestParser()
arguments_publication_controller.add_argument('siren', help='siren')

publicationParams_search_controller = reqparse.RequestParser()
publicationParams_search_controller.add_argument('filter', help='filtre de recherche sur le numéro d\'acte')
publicationParams_search_controller.add_argument('sortDirection', help='asc ou desc (desc par defaut)')
publicationParams_search_controller.add_argument('sortField',
                                                 help='champ de tri (numero_de_lacte,publication_open_data,'
                                                      'date_de_lacte,acte_nature,etat,id par defaut')
publicationParams_search_controller.add_argument('pageIndex', help='index de la page, commence par 0')
publicationParams_search_controller.add_argument('pageSize', help='taille de la page')
publicationParams_search_controller.add_argument('siren', help='siren de l\'organisme')
publicationParams_search_controller.add_argument('etat',
                                                 help='etat de la publication (1: publie, 0:non, 2:en-cours,'
                                                      '3:en-erreur)')
publicationParams_search_controller.add_argument('est_masque',
                                                 help='est à publier (0:non, 1:oui)')


@api.route('')
class PublicationAllCtrl(Resource):
    @api.response(200, 'Success', model_publication_list)
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
        from app.tasks.publication_tasks import publier_acte_task
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
        from app.tasks.publication_tasks import depublier_acte_task
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


@api.route('/supprimer/<int:id>')
class PublicationDepublierCtrl(Resource):
    @api.response(200, 'Success', model_publication)
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    def put(self, id):
        from app.models.publication_model import Publication
        from app import db
        from app.tasks.publication_tasks import depublier_acte_task
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

@api.route('/supprimer/<int:id>')
class PublicationSupprimerCtrl(Resource):
    @api.response(200, 'Success', model_publication)
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    def put(self, id):
        from app.models.publication_model import Publication
        from app import db
        try:
            db_sess = db.session
            publication = Publication.query.filter(Publication.id == id).one()
            # 1 => publie, 0:non, 2:en-cours,3:en-erreur
            publication.est_supprime = True
            db_sess.commit()

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


@api.route('/search')
class PublicationSearchCtrl(Resource):
    @api.expect(publicationParams_search_controller)
    @api.response(200, 'Success', model_publication_list)
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    def post(self):
        from app.models.publication_model import Publication, Acte, PieceJointe
        args = publicationParams_search_controller.parse_args()
        siren = args['siren']
        etat = args['etat']
        est_masque = args['est_masque']

        if (args['sortDirection']) == 'asc':
            if (args['sortField']) == 'numero_de_lacte':
                sortField = Publication.numero_de_lacte.asc()
            elif (args['sortField']) == 'publication_open_data':
                sortField = Publication.publication_open_data.asc()
            elif (args['sortField']) == 'date_de_lacte':
                sortField = Publication.date_de_lacte.asc()
            elif (args['sortField']) == 'acte_nature':
                sortField = Publication.acte_nature.asc()
            elif (args['sortField']) == 'etat':
                sortField = Publication.etat.asc()
            else:
                sortField = Publication.id.asc()
        else:
            if (args['sortField']) == 'numero_de_lacte':
                sortField = Publication.numero_de_lacte.desc()
            elif (args['sortField']) == 'publication_open_data':
                sortField = Publication.publication_open_data.desc()
            elif (args['sortField']) == 'date_de_lacte':
                sortField = Publication.date_de_lacte.desc()
            elif (args['sortField']) == 'acte_nature':
                sortField = Publication.acte_nature.desc()
            elif (args['sortField']) == 'etat':
                sortField = Publication.etat.desc()
            else:
                sortField = Publication.id.desc()

        if (args['etat'] != None and args['etat'] != ''):
            if (args['filter'] != None and args['filter'] != ''):
                filter = args['filter']
                searchFilter = "%{}%".format(filter)
                result = Publication.query.filter(
                    or_(Publication.numero_de_lacte.like(searchFilter), Publication.objet.like(searchFilter)),
                    Publication.siren == siren, Publication.etat == etat,Publication.est_supprime == 0,
                    Publication.est_masque == est_masque).order_by(
                    sortField).paginate(int(args['pageIndex']) + 1, per_page=int(args['pageSize']))
            else:
                result = Publication.query.filter(Publication.siren == siren, Publication.etat == etat,
                                                  Publication.est_masque == est_masque,Publication.siren == siren,Publication.est_supprime == 0).order_by(
                    sortField).paginate(int(args['pageIndex']) + 1, per_page=int(args['pageSize']))
        else:
            if (args['filter'] != None and args['filter'] != ''):
                filter = args['filter']
                searchFilter = "%{}%".format(filter)
                result = Publication.query.filter(
                    or_(Publication.numero_de_lacte.like(searchFilter), Publication.objet.like(searchFilter)),
                    Publication.siren == siren,Publication.est_supprime == 0,
                    Publication.est_masque == est_masque,).order_by(
                    sortField).paginate(int(args['pageIndex']) + 1, per_page=int(args['pageSize']))
            else:
                result = Publication.query.filter(Publication.siren == siren, Publication.est_supprime == 0).order_by(
                    sortField).paginate(int(args['pageIndex']) + 1, per_page=int(args['pageSize']))

        return jsonify(
            {"total": result.total, "publications": [i.serialize for i in result.items]}
        )
