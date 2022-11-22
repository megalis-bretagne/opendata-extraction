from pathlib import Path
from flask import send_from_directory
from flask_restx import Namespace, Resource, abort

import app.shared.workdir_utils as workdir_utils

api = Namespace(name='scdl',
                description="API pour exporter au format SCDL les délibérations, budgets et toutes la nature d'actes"
                )

@api.route('/budget/<int:siren>/<int:annee>', doc={
    "description": "export les budgets au <a href=\"https://scdl.opendatafrance.net/docs/schemas/budget.html\">format SCDL</a> pour le siren et l'année présent dans l'url"})
class ScdlBudgetCtrl(Resource):
    @api.response(200, 'Success')
    @api.produces(["application/octet-stream"])
    def get(self, siren, annee):
        from app.tasks.datagouv_tasks import generation_budget

        with workdir_utils.temporary_workdir() as tmp_dir:
            try:
                csv_filepath = generation_budget(Path(tmp_dir), siren, annee)
                return send_from_directory(tmp_dir, filename=csv_filepath.name,
                                           as_attachment=True)
            except FileNotFoundError:
                abort(404)


@api.route('/budget/<int:annee>',doc={
    "description": "export des budgets au <a href=\"https://scdl.opendatafrance.net/docs/schemas/budget.html\">format SCDL</a> pour toutes les entités et l'année présent dans l'url"})
class ScdlBudgetAllCtrl(Resource):
    @api.response(200, 'Success')
    @api.produces(["application/octet-stream"])
    def get(self, annee):
        from app.tasks.datagouv_tasks import generation_budget

        with workdir_utils.temporary_workdir() as tmp_dir:
            try:
                csv_filepath = generation_budget(Path(tmp_dir), "*", annee)
                return send_from_directory(tmp_dir, filename=csv_filepath.name,
                                           as_attachment=True)
            except FileNotFoundError:
                abort(404)


@api.route('/deliberation/<int:siren>/<int:annee>',doc={
    "description": "export les délibérations au <a href=\"https://scdl.opendatafrance.net/docs/schemas/deliberations.html\">format SCDL</a> pour le siren et l'année présent dans l'url"})
class ScdlDeliberationCtrl(Resource):
    @api.response(200, 'Success')
    @api.produces(["application/octet-stream"])
    def get(self, siren, annee):
        from app.tasks.datagouv_tasks import generation_deliberation
        from app.tasks.utils import get_or_create_workdir
        try:
            return send_from_directory(get_or_create_workdir(), filename=generation_deliberation(siren, annee),
                                       as_attachment=True)
        except FileNotFoundError:
            abort(404)


@api.route('/deliberation/<int:annee>',doc={
    "description": "export les délibérations au <a href=\"https://scdl.opendatafrance.net/docs/schemas/deliberations.html\">format SCDL</a>  pour toutes les entités et l'année présent dans l'url"})
class ScdlDeliberationAllCtrl(Resource):
    @api.response(200, 'Success')
    @api.produces(["application/octet-stream"])
    def get(self, annee):
        from app.tasks.datagouv_tasks import generation_deliberation
        from app.tasks.utils import get_or_create_workdir
        try:
            return send_from_directory(get_or_create_workdir(), filename=generation_deliberation('*', annee),
                                       as_attachment=True)
        except FileNotFoundError:
            abort(404)


@api.route('/actes/<int:siren>/<int:annee>',doc={
    "description": "export de  toutes les natures d'actes dans un format identique au format scdl des déliébrations auquel nous avons ajouté la colonne nature d'acte et date de publication pour le siren et l'année dans l'url"})
class ScdlActeCtrl(Resource):
    @api.response(200, 'Success')
    @api.produces(["application/octet-stream"])
    def get(self, siren, annee):
        from app.tasks.datagouv_tasks import generation_acte
        from app.tasks.utils import get_or_create_workdir
        try:
            return send_from_directory(get_or_create_workdir(), filename=generation_acte(siren, annee),
                                       as_attachment=True)
        except FileNotFoundError:
            abort(404)

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
