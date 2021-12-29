from flask import send_from_directory
from flask_restx import Namespace, Resource, abort

api = Namespace(name='decp', description='Les données essentielles de la commande publique provenant de la salle des marchés de Megalis Bretagne : <a href="https://marches.megalis.bretagne.bzh">https://marches.megalis.bretagne.bzh</a>')

@api.route('/<int:siren>/<int:annee>')
class DecpCtrl(Resource):
    @api.doc('Retourne un fichier au format decp xml')
    @api.response(200, 'Success')
    @api.produces(["application/octet-stream"])
    def get(self, siren, annee):
        from app.tasks.marches_tasks import generation_decp
        from app.tasks.utils import get_or_create_workdir
        filename = generation_decp(annee, siren)
        if filename is None:
            abort(404)
        return send_from_directory(get_or_create_workdir(), filename=generation_decp(annee, siren), as_attachment=True)
