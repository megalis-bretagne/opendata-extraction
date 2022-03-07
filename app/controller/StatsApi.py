from flask_restx import Namespace, Resource, abort
from flask import send_from_directory

api = Namespace(name='stats', description='Statistiques de la plateforme')



@api.route('/publications', doc={
    "description": " Retourne un fichier CSV avec les colonnes suivantes:  <ul><li>type d'acte (déliberaion, budget)</li><li>choix dans Pastell (oui, non, ne sais pas)</li><li>état (publié, non publié)</li><li>total</li></ul>"})
class StatsPublications(Resource):
    @api.response(200, 'Success')
    @api.produces(["application/octet-stream"])
    def get(self):
        from sqlalchemy.sql import text
        from app.tasks.utils import get_or_create_workdir, query_result_to_csv
        from app import db
        try:
            request = text("""select case when acte_nature=1 THEN 'deliberation' ELSE  'budget' END as 'nature acte',
                                       case when publication_open_data='0' THEN 'oui' when publication_open_data='1' THEN 'non' when publication_open_data='2' THEN 'ne sais pas' ELSE  publication_open_data END as 'combo pastell',
                                       case when etat=1 THEN 'publié' when etat=0 THEN 'non publié' when etat=2 THEN 'en cours' ELSE  'en erreur' END as 'etat',
                                       count(*) as nombre 
                            from publication group by acte_nature,etat,publication_open_data order by nombre desc;""")

            with db.engine.connect() as con:
                result = con.execute(request);
                filename = "stats_publications.csv"
                query_result_to_csv(filename, result)
                return send_from_directory(get_or_create_workdir(), filename=filename, as_attachment=True)

        except FileNotFoundError:
            abort(404)



@api.route('/tauxNonPublie', doc={
    "description": " Retourne un fichier CSV avec les colonnes suivantes:  <ul><li>siren</li><li>nombre d'actes publiés</li><li>nombre d'actes non publiés</li><li>pourcentage non publié</li><li>total</li></ul>"})
class StatsNonPublie(Resource):
    @api.response(200, 'Success')
    @api.produces(["application/octet-stream"])
    def get(self):
        from sqlalchemy.sql import text
        from app.tasks.utils import get_or_create_workdir, query_result_to_csv
        from app import db
        try:
            request = text("""select t0.siren, nbPublié, nbNonPublié, nbNonPublié *100 / (nbPublié+nbNonPublié) as tauxDeNonPublié
                            from (select distinct(siren) from publication) t0
                                     left join (select siren, count(*) as nbPublié from publication where etat = 1 group by siren) t1 on t0.siren = t1.siren
                                     left join (select siren, count(*) as nbNonPublié from publication where etat = 0 or 2 group by siren) t2 on t0.siren = t2.siren
                            order by tauxDeNonPublié desc;""")

            with db.engine.connect() as con:
                result = con.execute(request);
                filename = "stats_taux.csv"
                query_result_to_csv(filename, result)
                return send_from_directory(get_or_create_workdir(), filename=filename, as_attachment=True)

        except FileNotFoundError:
            abort(404)



@api.route('/serviceDesactive',
           doc={"description": "Retourne la liste des siren qui ont désactivé le service opendata"})
class StatsOpenDataDesactive(Resource):
    @api.response(200, 'Success')
    @api.produces(["application/octet-stream"])
    def get(self):
        from sqlalchemy.sql import text
        from app.tasks.utils import query_result_to_csv, get_or_create_workdir
        from app import db
        try:
            request = text("""select siren, open_data_active from parametrage where open_data_active is false;""")
            with db.engine.connect() as con:
                result = con.execute(request);
                filename = "stats_desactive.csv"
                query_result_to_csv(filename, result)
                return send_from_directory(get_or_create_workdir(), filename=filename, as_attachment=True)

        except FileNotFoundError:
            abort(404)
