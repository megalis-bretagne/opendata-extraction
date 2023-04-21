import logging

from flask import jsonify, current_app
from flask_restx import Namespace, Resource, reqparse

from app import oidc
from app.controller.Decorator import isAdmin

api = Namespace(name='admin', description="API de gestion des services d'administration <b>(API sécurisée)</b>")

arguments_pastell_controller = reqparse.RequestParser()
arguments_pastell_controller.add_argument('id_e',
                                          help="identifiant de l'entitie dans pastell pour lequel on souhaite effectuer l'action")

arguments_udata_controller = reqparse.RequestParser()
arguments_udata_controller.add_argument('annee', help="Année de generation")
arguments_udata_controller.add_argument('siren', help="siren de l'organisme")

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
    def delete(self, id_publication):
        from app.tasks.utils import solr_connexion
        try:
            solr = solr_connexion()
            solr.delete(q="publication_id:" + str(id_publication))
        except Exception as e:
            logging.exception("Erreur lors suppression dans solr de l'id_publication: %s" % id_publication)
            raise e
        return jsonify({"statut": 'ok'})



@api.route('/publier/rejeu')
class AdminPulicationRejeu(Resource):
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.publication import creation_publication_task
        import os
        for entry in os.scandir(current_app.config['DIRECTORY_RELAUNCH']):
            if entry.name.endswith(".zip"):
                creation_publication_task.delay(os.path.join(current_app.config['DIRECTORY_RELAUNCH'], entry.name))

        return jsonify({
            "statut": 'demande de relance des fichiers zip présent dans le dossier de relance  (taches asynchrone)'})

@api.route('/publier/datagouv/deliberation')
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


@api.route('/publier/datagouv/budget')
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


@api.route('/publier/datagouv/decpHisto')
class AdminPulicationDecpHisto(Resource):
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.marches_tasks import generation_marche_histo
        generation_marche_histo.delay()
        return jsonify({
            "statut": "demande de generation et publication du decp des années historique à partir de 2014 (taches asynchrone)"})


@api.route('/publier/datagouv/decpHisto/annee')
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


@api.route('/publier/datagouv/decp')
class AdminPublicationDecp(Resource):
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.marches_tasks import generation_marche
        generation_marche.delay()
        return jsonify(
            {"statut": "demande de generation et publication du decp pour l'année courante (taches asynchrone)"})



@api.route('/publier/udata/decp')
class AdminUdataDecpCtrl(Resource):
    @api.expect(arguments_udata_controller)
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.udata_tasks import publication_udata_decp
        args = arguments_udata_controller.parse_args()
        siren = args['siren']
        annee = args['annee']
        publication_udata_decp.delay(siren, annee)
        return jsonify(
            {"statut": 'demande de déclenchement udata decp (taches asynchrone)'})


@api.route('/publier/udata/budget')
class AdminUdataBudgetCtrl(Resource):
    @api.expect(arguments_udata_controller)
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.udata_tasks import publication_udata_budget
        args = arguments_udata_controller.parse_args()
        siren = args['siren']
        annee = args['annee']
        publication_udata_budget.delay(siren, annee)
        return jsonify(
            {"statut": 'demande de déclenchement udata budget (taches asynchrone)'})


@api.route('/publier/udata/deliberation')
class AdminUdataDeliberationCtrl(Resource):
    @api.expect(arguments_udata_controller)
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.udata_tasks import publication_udata_deliberation
        args = arguments_udata_controller.parse_args()
        siren = args['siren']
        annee = args['annee']
        publication_udata_deliberation.delay(siren, annee)
        return jsonify(
            {"statut": 'demande de déclenchement udata deliberation (taches asynchrone)'})


@api.route('/publier/udata/all')
class AdminUdataAllCtrl(Resource):
    @api.expect(arguments_annee_controller)
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.udata_tasks import publication_udata
        args = arguments_annee_controller.parse_args()
        annee = args['annee']
        publication_udata.delay(annee)
        return jsonify(
            {"statut": 'demande de déclenchement udata budget, deliberation & decp  (taches asynchrone)'})


@api.route('/publier/udata/decpHisto')
class AdminUdataPublicationDecpHisto(Resource):
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.udata_tasks import publication_udata_decp_histo
        publication_udata_decp_histo.delay()
        return jsonify({
            "statut": "demande de generation et publication du decp des années historique à partir de 2014 vers udata (taches asynchrone)"})


@api.route('/publication/republier/all/<int:etat>')
@api.doc(params={'etat': '1 =publie, 0=non, 2=en-cours, 3=en-erreur'})
class PublicationRepublierCtrl(Resource):
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self, etat):
        from app.tasks.publication import republier_all_acte_task
        republier_all_acte_task.delay(etat)
        return jsonify(
            {"statut": "ETAT:" +str(etat)+ '- demande de republication prise en compte (taches asynchrone)'})

@api.route('/publication/republier/<int:siren>/<int:etat>')
@api.doc(params={'etat': '1 =publie, 0=non, 2=en-cours, 3=en-erreur'})
class PublicationRepublierSirenCtrl(Resource):
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self, siren, etat):
        from app.tasks.publication import republier_actes_pour_siren_task
        republier_actes_pour_siren_task.delay(siren, etat)
        return jsonify(
            {"statut": "ETAT:" +str(etat)+ ' SIREN: '+str(siren)+'- demande de republication prise en compte (taches asynchrone)'})


@api.route('/parametrage/valorisation')
class AdminValorisation(Resource):
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def post(self):
        from app.tasks.parametrage_tasks import valorisation_all_nic_denomination
        valorisation_all_nic_denomination.delay()
        return jsonify(
            {"statut": 'Valorisation des nic et denomination'})


@api.route('/test/isAdmin')
class AdminIsAdmin(Resource):
    @api.response(200, 'Success')
    @oidc.accept_token(require_token=True, scopes_required=['openid'])
    @isAdmin
    def get(self):
        return jsonify(
            {"rep": 'Welcome admin'})
