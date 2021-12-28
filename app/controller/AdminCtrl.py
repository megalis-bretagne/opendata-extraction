import logging

from flask import jsonify
from flask_restx import Namespace, Resource, reqparse
from sqlalchemy.exc import NoResultFound

from app import oidc
from app.controller.Decorator import isAdmin

api = Namespace(name='admin', description="API de gestion des services d'administration <b>(API sécurisée)</b>")

arguments_pastell_controller = reqparse.RequestParser()
arguments_pastell_controller.add_argument('id_e',
                                          help="identifiant de l'entitie dans pastell pour lequel on souhaite effectuer l'action")

arguments_annee_controller = reqparse.RequestParser()
arguments_annee_controller.add_argument('annee', help="Année de generation")


@api.route('/solr/clear')
class AdminCtrl(Resource):
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def get(self):
        from app.tasks.utils import solr_clear_all
        solr_clear_all()
        return jsonify({"statut": 'ok'})

@api.route('/solr/delete/<int:idPublication>')
class AdminSolrDeleteCtrl(Resource):
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def delete(self, idPublication):
        from app.tasks.utils import solr_connexion
        try:
            solr = solr_connexion()
            solr.delete(q="publication_id:" + str(idPublication))
        except Exception as e:
            logging.exception("Erreur lors suppression dans solr de l'idPublicaion: %s" % idPublication)
            raise e
        return jsonify({"statut": 'ok'})


@api.route('/publier/scdl/deliberation')
class AdminPulicationDelibSCDL(Resource):
    @api.expect(arguments_annee_controller)
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.datagouv_tasks import generation_and_publication_scdl
        args = arguments_annee_controller.parse_args()
        annee = args['annee']
        generation_and_publication_scdl.delay('1', annee)
        return jsonify({
                           "statut": 'demande de generation et publication du SCDL deliberation sur data gouv effectuée (taches asynchrone)'})


@api.route('/publier/scdl/budget')
class AdminPulicationBudgetSCDL(Resource):
    @api.expect(arguments_annee_controller)
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.datagouv_tasks import generation_and_publication_scdl
        args = arguments_annee_controller.parse_args()
        annee = args['annee']
        generation_and_publication_scdl.delay('5', annee)
        return jsonify({
                           "statut": 'demande de generation et publication du SCDL budget sur data gouv effectuée (taches asynchrone)'})


@api.route('/publier/decpHisto')
class AdminPulicationDecpHisto(Resource):
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.marches_tasks import generation_marche_histo
        generation_marche_histo.delay()
        return jsonify({
                           "statut": "demande de generation et publication du decp des années historique à partir de 2014 (taches asynchrone)"})

@api.route('/publier/decpHisto/annee')
class AdminPulicationDecpHistoAnnee(Resource):
    @api.expect(arguments_annee_controller)
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.marches_tasks import generation_marche_annee
        args = arguments_annee_controller.parse_args()
        annee = args['annee']
        generation_marche_annee.delay(str(annee))
        return jsonify(
            {"statut": "demande de generation et publication du decp pour l'année en parametre (taches asynchrone)"})

@api.route('/publier/decp')
class AdminPulicationDecp(Resource):
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.marches_tasks import generation_marche
        generation_marche.delay()
        return jsonify(
            {"statut": "demande de generation et publication du decp pour l'année courante (taches asynchrone)"})

@api.route('/pastell/creation/all')
class AdminPastellAllCtrl(Resource):
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.pastell_tasks import creation_et_association_all
        creation_et_association_all.delay()
        return jsonify(
            {"statut": "demande de generation et publication du decp de l'année courante (taches asynchrone)"})

@api.route('/pastell/declencher')
class AdminPastellDeclencherCtrl(Resource):
    @api.expect(arguments_pastell_controller)
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.pastell_tasks import delecher_pastell_task
        args = arguments_pastell_controller.parse_args()
        id_e = args['id_e']
        delecher_pastell_task.delay(id_e)
        return jsonify(
            {"statut": 'demande de déclenchement pastell realisée (taches asynchrone)'})

@api.route('/pastell/declencherAG')
class AdminPastellDeclencherAGCtrl(Resource):
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.pastell_tasks import delecher_pastell_all_AG_task
        delecher_pastell_all_AG_task.delay()
        return jsonify(
            {"statut": 'demande de déclenchement des actes generique dans pastell realisée (taches asynchrone)'})


@api.route('/pastell/creation/ged-megalis-opendata')
class AdminPastellGedPastellCtrl(Resource):
    @api.expect(arguments_pastell_controller)
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.pastell_tasks import creation_et_association_connecteur_ged_pastell_budget_task
        from app.tasks.pastell_tasks import creation_et_association_connecteur_ged_pastell_delib_task
        from app.tasks.pastell_tasks import creation_et_association_connecteur_ged_pastell_AG_task
        args = arguments_pastell_controller.parse_args()
        id_e = args['id_e']
        creation_et_association_connecteur_ged_pastell_AG_task.delay(id_e)
        creation_et_association_connecteur_ged_pastell_budget_task.delay(id_e)
        creation_et_association_connecteur_ged_pastell_delib_task.delay(id_e)
        return jsonify(
            {"statut": 'demande de creation et association du connecteur ged_pastell réalisée (taches asynchrone)'})

@api.route('/publication/republier/all/<int:etat>')
@api.doc(params={'etat': '1 =publie, 0=non, 2=en-cours, 3=en-erreur'})
class PublicationRepublierCtrl(Resource):
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self, etat):
        from app.models.publication_model import Publication
        from app import db
        from app.tasks.publication_tasks import publier_acte_task
        try:
            db_sess = db.session
            #etat =3: en - erreur
            liste_publication = Publication.query.filter(Publication.etat == etat)
            for publication in liste_publication:
                # 1 => publie, 0:non, 2:en-cours,3:en-erreur
                publication.etat = 2
                db_sess.commit()
                publier_acte_task.delay(publication.id)
            return "ok"
        except NoResultFound as e:
            print(e)
            api.abort(404, 'Not found')


@api.route('/pastell/creation/ged_sftp-opendata')
class AdminPastellGedSdtpCtrl(Resource):
    @api.expect(arguments_pastell_controller)
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.pastell_tasks import creation_et_association_connecteur_ged_sftp_task
        args = arguments_pastell_controller.parse_args()
        id_e = args['id_e']
        creation_et_association_connecteur_ged_sftp_task.delay(id_e)
        return jsonify(
            {"statut": 'demande de creation et association du connecteur ged_pastell réalisée ( taches asynchrone)'})


@api.route('/test/isAdmin')
class AdminIsAdmin(Resource):
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def get(self):
        return jsonify(
            {"rep": 'Welcome admin'})




