from flask import send_file
from flask_restx import Namespace, Resource, abort

api = Namespace(name='decp', description='Les données essentielles de la commande publique provenant de la salle des marchés de Megalis Bretagne : <a href="https://marches.megalis.bretagne.bzh">https://marches.megalis.bretagne.bzh</a>')

@api.route('/<int:siren>/<int:annee>')
class DecpCtrl(Resource):
    @api.doc('Retourne un fichier au format decp xml')
    @api.response(200, 'Success')
    @api.response(404, 'Not found')
    @api.produces(["application/octet-stream"])
    def get(self, siren, annee):
        from app.tasks.marches_tasks import generated_decp

        with generated_decp(annee=annee, siren=siren) as decp_filepath:
            if decp_filepath is None:
                abort(404)
            return send_file(decp_filepath, as_attachment=True)
