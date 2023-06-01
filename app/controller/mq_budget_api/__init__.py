import logging
from flask import Blueprint
from app.service.mq_budget_api_service import BudgetsApiService
from app.service.mq_budget_api_service.parametrage import ParametrageApiService

from flask_restx import Api, Namespace

logger = logging.getLogger(__name__)

_API_SERVICE = BudgetsApiService()
_PARAM_API_SERVICE = ParametrageApiService()

budgets_api_bp = Blueprint("mq_budgets", __name__)

budgets_api_authorizations = {
    'bearer': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "Ajout d'un header 'Authorization'. Saisissez 'Bearer JWT'",
    },
}
budgets_api = Api(
    budgets_api_bp, 
    doc="/doc", 
    title="API marque blanche budgets", 
    description="<b>Ce sont des APIs privées et peuvent changer à tout moment.</b>",
    prefix="/v1",
    authorizations=budgets_api_authorizations,
)
budgets_api_ns = Namespace(
    name="budgets",
    path="/",
    description="API de consultation des données de budgets pour la marque blanche.",
)
budgets_api.add_namespace(budgets_api_ns)

from . import error_handling
from . import ResourcesBudgetairesDisponiblesApi
from . import DonneesBudgetairesApi
from . import PlansDeComptesApi
from . import ParametrageApi
from . import BudgetAdminApi