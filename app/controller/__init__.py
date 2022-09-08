from flask import url_for

from flask_restx import Api
from app.controller.PublicationCtrl import api as publicationApi
from app.controller.ParametrageCtrl import api as parametrageApi
from app.controller.HealthCtrl import api as healthApi
from app.controller.AdminCtrl import api as adminApi
from app.controller.DecpApi import api as decpApi
from app.controller.ScdlApi import api as scdlApi
from app.controller.StatsApi import api as statsApi
from app.controller.BudgetMarqueBlancheApi import api as budgetMarqueBlancheApi

# Fix of returning swagger.json on HTTP
@property
def specs_url(self):
    """
    The Swagger specifications absolute url (ie. `swagger.json`)

    :rtype: str
    """
    return url_for(self.endpoint('specs'), _external=False)


Api.specs_url = specs_url

api = Api(version="1.0", title="API Open DATA",
          description="API de mise à disposition des données ouvertes de Megalis Bretagne",
          prefix="/api/v1", doc='/doc/')

api.add_namespace(decpApi)
api.add_namespace(scdlApi)
api.add_namespace(statsApi)
api.add_namespace(healthApi)
api.add_namespace(publicationApi)
api.add_namespace(parametrageApi)
api.add_namespace(adminApi)
api.add_namespace(budgetMarqueBlancheApi)
