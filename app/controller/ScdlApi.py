from flask import send_file
from flask_restx import Namespace, Resource

api = Namespace(name='scdl',
                description="API pour exporter au format SCDL les délibérations, budgets et toutes la nature d'actes"
                )

@api.errorhandler(FileNotFoundError)
def handle_not_found(_):
    return 'Not found', 404

@api.route('/budget/<int:siren>/<int:annee>', doc={
    "description": "export les budgets au <a href=\"https://scdl.opendatafrance.net/docs/schemas/budget.html\">format SCDL</a> pour le siren et l'année présent dans l'url"})
class ScdlBudgetCtrl(Resource):
    @api.response(200, 'Success')
    @api.produces(["application/octet-stream"])
    def get(self, siren, annee):
        from app.tasks.datagouv_tasks import generated_scdl_budget

        with generated_scdl_budget(siren=siren, annee=annee) as csv_filepath:
            return send_file(csv_filepath, as_attachment=True)


@api.route('/budget/<int:annee>',doc={
    "description": "export des budgets au <a href=\"https://scdl.opendatafrance.net/docs/schemas/budget.html\">format SCDL</a> pour toutes les entités et l'année présent dans l'url"})
class ScdlBudgetAllCtrl(Resource):
    @api.response(200, 'Success')
    @api.produces(["application/octet-stream"])
    def get(self, annee):
        from app.tasks.datagouv_tasks import generated_scdl_budget

        with generated_scdl_budget(siren="*", annee=annee) as csv_filepath:
            return send_file(csv_filepath, as_attachment=True)


@api.route('/deliberation/<int:siren>/<int:annee>',doc={
    "description": "export les délibérations au <a href=\"https://scdl.opendatafrance.net/docs/schemas/deliberations.html\">format SCDL</a> pour le siren et l'année présent dans l'url"})
class ScdlDeliberationCtrl(Resource):
    @api.response(200, 'Success')
    @api.produces(["application/octet-stream"])
    def get(self, siren, annee):
        from app.tasks.datagouv_tasks import generated_scdl_deliberation

        with generated_scdl_deliberation(siren = siren, annee = annee) as csv_filepath:
            return send_file(csv_filepath, as_attachment=True)


@api.route('/deliberation/<int:annee>',doc={
    "description": "export les délibérations au <a href=\"https://scdl.opendatafrance.net/docs/schemas/deliberations.html\">format SCDL</a>  pour toutes les entités et l'année présent dans l'url"})
class ScdlDeliberationAllCtrl(Resource):
    @api.response(200, 'Success')
    @api.produces(["application/octet-stream"])
    def get(self, annee):
        from app.tasks.datagouv_tasks import generated_scdl_deliberation

        with generated_scdl_deliberation(siren = "*", annee=annee) as csv_filepath:
            return send_file(csv_filepath, as_attachment=True)


@api.route('/actes/<int:siren>/<int:annee>',doc={
    "description": "export de  toutes les natures d'actes dans un format identique au format scdl des déliébrations auquel nous avons ajouté la colonne nature d'acte et date de publication pour le siren et l'année dans l'url"})
class ScdlActeCtrl(Resource):
    @api.response(200, 'Success')
    @api.produces(["application/octet-stream"])
    def get(self, siren, annee):
        from app.tasks.datagouv_tasks import generated_scdl_acte

        with generated_scdl_acte(siren = siren, annee= annee) as csv_filepath:
            return send_file(csv_filepath, as_attachment=True)

# On supprime cette api car pas suffisanment performante, on pourra la réactiver lorqu'on utilisera directement la bdd MariaDb pour générer les SCDL (plus solr)
# @api.route('/actes/<int:annee>')
# class ScdlActeAllCtrl(Resource):
#     @api.response(200, 'Success')
#     @api.produces(["application/octet-stream"])
#     def get(self, annee):
#         from app.tasks.datagouv_tasks import generation_acte
#         from app.tasks.utils import get_or_create_workdir
#         try:
#             return send_from_directory(get_or_create_workdir(), filename=generation_acte('*', annee),
#                                        as_attachment=True)
#         except FileNotFoundError:
#             abort(404)
