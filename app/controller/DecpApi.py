from flask import send_from_directory
from flask_restx import Namespace, Resource, abort

api = Namespace(name='decp', description='Les données essentielles de la commande publique provenant de la salle des marchés de Megalis Bretagne : <a href="https://marches.megalis.bretagne.bzh">https://marches.megalis.bretagne.bzh</a>')

@api.route('/<int:siren>/<int:annee>')
class DecpCtrl(Resource):
    @api.doc('Retourne un fichier au format decp xml')
    @api.response(200, 'Success')
    @api.produces(["application/octet-stream"])
    def get(self,siren,annee):
        from app.tasks.marches_tasks import recuperer_decp
        from app.tasks.utils import clear_wordir, get_or_create_workdir
        clear_wordir()
        response =recuperer_decp(annee, siren)
        filename = f"decp-{siren}{annee}.xml"
        try:
            text_file = open(get_or_create_workdir()+filename, "w")
            text_file.write(response.text)
            text_file.close()
            return send_from_directory(get_or_create_workdir(), filename=filename, as_attachment=True)
        except FileNotFoundError:
            abort(404)