from flask import url_for
from flask import Blueprint

from flask_restx import Api
from app.controller.PublicationCtrl import api as publicationApi
from app.controller.ParametrageCtrl import api as parametrageApi
from app.controller.HealthCtrl import api as healthApi
from app.controller.AdminCtrl import api as adminApi
from app.controller.DecpApi import api as decpApi
from app.controller.ScdlApi import api as scdlApi
from app.controller.StatsApi import api as statsApi
from app.controller.PastellCtrl import api as pastellCtrl

# Fix of returning swagger.json on HTTP
@property
def specs_url(self):
    """
    The Swagger specifications absolute url (ie. `swagger.json`)

    :rtype: str
    """
    return url_for(self.endpoint("specs"), _external=False)


Api.specs_url = specs_url

api_v1_bp = Blueprint("OpenDataAPI", __name__)
api = Api(
    api_v1_bp,
    version="1.0",
    title="API Open DATA",
    description="API de mise à disposition des données ouvertes de Megalis Bretagne",
    prefix="/api/v1",
    doc="/doc/",
)

private_api_v1_bp = Blueprint("API privées OpenData", __name__)
private_api = Api(
    private_api_v1_bp,
    version="1.0",
    title="API privées Open DATA",
    description="API privées pour le projet OpenData",
    prefix="/v1",
    doc="/doc/",
)


api.add_namespace(decpApi)
api.add_namespace(scdlApi)
api.add_namespace(statsApi)
api.add_namespace(healthApi)

private_api.add_namespace(publicationApi)
private_api.add_namespace(parametrageApi)
private_api.add_namespace(adminApi)
private_api.add_namespace(pastellCtrl)
