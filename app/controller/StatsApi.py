import io

from flask_restx import Namespace, Resource, reqparse
from flask import make_response, jsonify

import csv
api = Namespace(name='stats', description='Statistiques de la plateforme')

arguments_publications = reqparse.RequestParser()
arguments_publications.add_argument('startDate', help="Filtre les publications les plus jeunes depuis la date donnée sur la date de publication. Sous le Format \"2022-01-13\"")
arguments_publications.add_argument('endDate', help="Filtre les publications les plus vielles depuis la date donnée sur la date de publication. Sous le Format \"2022-09-17\"")
arguments_publications.add_argument('mode', help="CSV ou json (CSV par défaut)", required=False )


arguments_mode_csv_json  = reqparse.RequestParser()
arguments_mode_csv_json.add_argument('mode', help="CSV ou json (CSV par défaut)", required=False )


@api.route('/publications', doc={
    "description": " Retourne un fichier CSV avec les colonnes suivantes:  <ul><li>type d'acte (déliberaion,Actes réglementaires,Actes individuels,Contrats,conventions et avenants, budget,Autres)</li><li>choix dans Pastell (oui, non, ne sais pas)</li><li>état (publié, non publié)</li><li>total</li></ul>"})
class StatsPublications(Resource):
    @api.expect(arguments_publications)
    @api.response(200, 'Success')
    def get(self):
        from sqlalchemy.sql import text
        from app import db

        args = arguments_publications.parse_args()
        start_date = args['startDate']
        end_date = args['endDate']
        mode = 'csv' if args['mode'] is None else args['mode']
        array_condition = []
        condition = ""
        if start_date is not None:
            array_condition.append("date_publication >= '"+start_date+"'")
        if end_date is not None:
            array_condition.append("date_publication <= '"+end_date+"'")
        if len(array_condition) > 0:
            condition = "where " + " and ".join(array_condition)

        request = text("""select case when acte_nature=1 THEN 'déliberation' when acte_nature=2 THEN 'Actes réglementaires' when acte_nature=3 THEN 'Actes individuels' when acte_nature=4 THEN 'Contrats,conventions et avenants' when acte_nature=5 THEN 'budget' ELSE  'Autres' END as 'nature acte',
                                       case when publication_open_data='3' THEN 'oui' when publication_open_data='1' THEN 'non' when publication_open_data='2' THEN 'ne sais pas' ELSE  publication_open_data END as 'combo pastell',
                                       case when etat=1 THEN 'publié' when etat=0 THEN 'non publié' when etat=2 THEN 'en cours' ELSE  'en erreur' END as 'etat',
                                       count(*) as nombre 
                            from publication """ + condition + """ group by acte_nature,etat,publication_open_data order by nombre desc;""")

        with db.engine.connect() as con:
            result = con.execute(request)

            if mode.lower() == 'json' :
                return self._to_json(result)
            else :
                return to_csv(result,"stats_publications.csv")

    def _to_json(self, result):
        rows = result.fetchall()
        object_list = []
        for row in rows:
            object_list.append({"nature acte": row[0], "combo pastell": row[1], "etat": row[2], "nombre":row[3]})
        return jsonify(object_list)


@api.route('/tauxNonPublie', doc={
    "description": " Retourne un fichier CSV avec les colonnes suivantes:  <ul><li>siren</li><li>nombre d'actes publiés</li><li>nombre d'actes non publiés</li><li>pourcentage non publié</li><li>total</li></ul>"})
class StatsNonPublie(Resource):
    @api.expect(arguments_mode_csv_json)
    @api.response(200, 'Success')
    def get(self):
        from sqlalchemy.sql import text
        from app import db
        args = arguments_publications.parse_args()
        mode = 'csv' if args['mode'] is None else args['mode']
        request = text("""select siren, nbPublié, nbNonPublié, nbNonPublié*100 / (nbPublié + nbNonPublié) as tauxDeNonPublié
                              from 
                              (select distinct(t0.siren), IFNULL(t1.publié, 0) as nbPublié, IFNULL(t2.nonPublié, 0) as nbNonPublié from publication t0
                                  left join (select siren, count(*) as publié from publication where etat =  1 group by siren) t1 on t0.siren = t1.siren
                                  left join (select siren, count(*) as nonPublié from publication where etat <> 1 group by siren) t2 on t0.siren = t2.siren) t3
                              order by tauxDeNonPublié desc;""")

        with db.engine.connect() as con:
            result = con.execute(request)
            if mode.lower() == 'json':
                return self._to_json(result)
            else:
                return to_csv(result,"stats_taux.csv")

    @api.route('/documentScanne', doc={
        "description": "Statistiques sur les documents scannés et non scannés. "
                       "Retourne un json avec les statistiques suivantes: "
                       "<ul>"
                       "<li>pourcentageDocumentScanne : pourcentage des documents de type image sur la plateforme</li>"
                       "<li>nombreTotalDeDocument: nombre total de documents</li>"
                       "<li>nombreDocumentScanne: nombre de documents <strong>scanné</strong></li>"
                       "<li>nombreDocumentNotScanne: nombre de documents <strong>non scanné</strong></li></li>"
                       "<li>tailleMoyenneDocumentScanne: taille moyenne des documents <strong>scanné</strong> en octet</li>"
                       "<li>tailleMinDocumentScanne: taille min des documents <strong>scanné</strong> en octet</li>"
                       "<li>tailleMaxDocumentScanne: taille max des documents <strong>scanné</strong> en octet</li>"
                       "<li>tailleMoyenneDocumentNotScanne: taille moyenne des documents <strong>non scanné</strong> en octet</li>"
                       "<li>tailleMinDocumentNotScanne: taille min des documents <strong>non scanné</strong> en octet</li>"
                       "<li>tailleMaxDocumentNotScanne: taille max des documents <strong>non scanné</strong> en octet</li></ul>"})
    class StatsScan(Resource):
        @api.response(200, 'Success')
        def get(self):
            from app.tasks import solr_connexion
            solr = solr_connexion()

            resultImage = \
                solr.search(q='*:*',
                            **{
                                'start': '0',
                                'rows': '0',
                                'fq': 'pdf_charsperpage:0 AND -pdf_charsperpage:[1 TO *]',
                                'stats': 'true',
                                'stats.field': 'stream_size'
                            })

            resultNotImage = \
                solr.search(q='*:*',
                            **{
                                'start': '0',
                                'rows': '0',
                                'fq': '-pdf_charsperpage:0 AND pdf_charsperpage:[* TO *]',
                                'stats': 'true',
                                'stats.field': 'stream_size'
                            })


            resutatotal = \
                {
                    'pourcentageDocumentScanne': (resultImage.stats['stats_fields']['stream_size']['count'] / (resultImage.stats['stats_fields']['stream_size']['count'] + resultNotImage.stats['stats_fields']['stream_size']['count'])) * 100,
                    'nombreTotalDeDocument': resultImage.stats['stats_fields']['stream_size']['count'] + resultNotImage.stats['stats_fields']['stream_size']['count'],
                    'nombreDocumentScanne': resultImage.stats['stats_fields']['stream_size']['count'],
                    'nombreDocumentNotScanne': resultNotImage.stats['stats_fields']['stream_size']['count'],
                    'tailleMoyenneDocumentScanne': resultImage.stats['stats_fields']['stream_size']['mean'],
                    'tailleMinDocumentScanne': resultImage.stats['stats_fields']['stream_size']['min'],
                    'tailleMaxDocumentScanne': resultImage.stats['stats_fields']['stream_size']['max'],
                    'tailleMoyenneDocumentNotScanne': resultNotImage.stats['stats_fields']['stream_size']['mean'],
                    'tailleMinDocumentNotScanne': resultNotImage.stats['stats_fields']['stream_size']['min'],
                    'tailleMaxDocumentNotScanne': resultNotImage.stats['stats_fields']['stream_size']['max']

                }

            return jsonify(resutatotal)


@api.route('/serviceDesactive',
           doc={"description": "Retourne la liste des siren qui ont désactivé le service opendata"})
class StatsOpenDataDesactive(Resource):
    @api.response(200, 'Success')
    @api.expect(arguments_mode_csv_json)
    def get(self):
        from sqlalchemy.sql import text
        from app import db
        args = arguments_publications.parse_args()
        mode = 'csv' if args['mode'] is None else args['mode']
        request = text("""select siren, open_data_active from parametrage where open_data_active is false;""")
        with db.engine.connect() as con:
            result = con.execute(request)
            if mode.lower() == 'json':
                return self._to_json(result)
            else:
                return to_csv(result, "stats_desactive.csv")

    def _to_json(self,result):
        rows = result.fetchall()
        object_list = []
        for row in rows:
            object_list.append({"siren": row[0], "open_data_active": str(row[1])})
        return jsonify(object_list)

## Export en csv des resultats
def to_csv(result, filename):
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow([row[0] for row in result.cursor.description])
    writer.writerows(result.cursor.fetchall())
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename="+filename
    response.headers["Content-type"] = "text/csv"
    return response