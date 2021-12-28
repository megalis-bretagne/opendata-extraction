from flask import send_from_directory
from flask_restx import Namespace, Resource, abort

api = Namespace(name='scdl', description='budget et deliberation au format scdl')


@api.route('/budget/<int:siren>/<int:annee>')
class ScdlBudgetCtrl(Resource):
    @api.response(200, 'Success')
    @api.produces(["application/octet-stream"])
    def get(self, siren, annee):
        from app.tasks.datagouv_tasks import generation_budget
        from app.tasks.utils import get_or_create_workdir
        try:
            return send_from_directory(get_or_create_workdir(), filename=generation_budget(siren, annee),
                                       as_attachment=True)
        except FileNotFoundError:
            abort(404)


@api.route('/budget/<int:annee>')
class ScdlBudgetAllCtrl(Resource):
    @api.response(200, 'Success')
    @api.produces(["application/octet-stream"])
    def get(self, annee):
        from app.tasks.datagouv_tasks import generation_budget
        from app.tasks.utils import get_or_create_workdir
        try:
            return send_from_directory(get_or_create_workdir(), filename=generation_budget('*', annee),
                                       as_attachment=True)
        except FileNotFoundError:
            abort(404)


@api.route('/deliberation/<int:siren>/<int:annee>')
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


@api.route('/deliberation/<int:annee>')
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
