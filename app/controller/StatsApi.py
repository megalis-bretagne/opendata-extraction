from flask_restx import Namespace, Resource, abort
from flask import send_from_directory

api = Namespace(name='stats', description='Statistiques de la plateforme')


@api.route('/publications')
class StatsPublications(Resource):
    @api.response(200, 'Success')
    @api.produces(["application/octet-stream"])
    def get(self):
        from sqlalchemy.sql import text
        from app.tasks.utils import get_or_create_workdir
        from app import db
        import csv
        try:
            request = text("""select case when acte_nature=1 THEN 'deliberation' ELSE  'budget' END as 'nature acte',
                                       case when publication_open_data='0' THEN 'oui' when publication_open_data='1' THEN 'non' when publication_open_data='2' THEN 'ne sais pas' ELSE  publication_open_data END as 'combo pastell',
                                       case when etat=1 THEN 'publié' when etat=0 THEN 'non publié' when etat=2 THEN 'en cours' ELSE  'en erreur' END as 'etat',
                                       count(*) as nombre 
                            from publication group by acte_nature,etat,publication_open_data order by nombre desc;""")

            with db.engine.connect() as con:
                result = con.execute(request);
                filename = "stats_publications.csv"
                outfile = open(get_or_create_workdir() + filename, "w")
                outcsv = csv.writer(outfile, lineterminator="\n")
                entete = ""
                for x in result.cursor.description:
                    if entete != "":
                        entete += "," + str(x[0])
                    else:
                        entete = str(x[0])
                outfile.write(entete+'\n')
                outcsv.writerows(result.cursor.fetchall())
                outfile.close()
                return send_from_directory(get_or_create_workdir(), filename=filename, as_attachment=True)

        except FileNotFoundError:
            abort(404)


@api.route('/tauxNonPublie')
class StatsNonPublie(Resource):
    @api.response(200, 'Success')
    @api.produces(["application/octet-stream"])
    def get(self):
        from sqlalchemy.sql import text
        from app.tasks.utils import get_or_create_workdir
        from app import db
        import csv
        try:
            request = text("""select t0.siren, nbOui, nbNon, nbNeSaisPas, nbNon *100 / (nbOui+nbNon) as tauxDeNonPublié
                                from (select distinct(siren) from publication) t0
                                         left join (select siren, count(*) as nbOui from publication where publication_open_data = 0 group by siren) t1 on t0.siren = t1.siren
                                         left join (select siren, count(*) as nbNon from publication where publication_open_data = 1 group by siren) t2 on t0.siren = t2.siren
                                         left join (select siren, count(*) as nbNeSaisPas from publication where publication_open_data = 2 group by siren) t3 on t0.siren = t3.siren
                                order by tauxDeNonPublié desc""")

            with db.engine.connect() as con:
                result = con.execute(request);
                filename = "stats_taux.csv"
                outfile = open(get_or_create_workdir() + filename, "w")
                outcsv = csv.writer(outfile, lineterminator="\n")
                entete = ""
                for x in result.cursor.description:
                    if entete != "":
                        entete += "," + str(x[0])
                    else:
                        entete = str(x[0])
                outfile.write(entete+'\n')
                outcsv.writerows(result.cursor.fetchall())
                outfile.close()
                return send_from_directory(get_or_create_workdir(), filename=filename, as_attachment=True)

        except FileNotFoundError:
            abort(404)

@api.route('/serviceDesactive')
class StatsOpenDataDesactive(Resource):
    @api.response(200, 'Success')
    @api.produces(["application/octet-stream"])
    def get(self):
        from sqlalchemy.sql import text
        from app.tasks.utils import get_or_create_workdir
        from app import db
        import csv
        try:
            request = text("""select siren, count(*) as nbNon from publication where publication_open_data = 1 group by siren order by nbNon desc;""")

            with db.engine.connect() as con:
                result = con.execute(request);
                filename = "stats_desactive.csv"
                outfile = open(get_or_create_workdir() + filename, "w")
                outcsv = csv.writer(outfile, lineterminator="\n")
                entete = ""
                for x in result.cursor.description:
                    if entete != "":
                        entete += "," + str(x[0])
                    else:
                        entete = str(x[0])
                outfile.write(entete+'\n')
                outcsv.writerows(result.cursor.fetchall())
                outfile.close()
                return send_from_directory(get_or_create_workdir(), filename=filename, as_attachment=True)

        except FileNotFoundError:
            abort(404)