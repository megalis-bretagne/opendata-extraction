import logging
from flask import Blueprint
from app.service.mq_budget_api_service import BudgetsApiService
from app.service.mq_budget_api_service.parametrage import ParametrageApiService

from flask_restx import Api, Namespace

logger = logging.getLogger(__name__)

_API_SERVICE = BudgetsApiService()
_PARAM_API_SERVICE = ParametrageApiService()

budgets_api_bp = Blueprint("mq_budgets", __name__)

budgets_api = Api(
    budgets_api_bp, doc="/doc", title="API marque blanche budgets", prefix="/v1"
)
budgets_api_ns = Namespace(
    name="budgets",
    path="/",
    description=(
        "API de consultation des données de budgets pour la marque blanche. "
        "<b>C'est une API privée pour le frontend et elle peut changer à tout moment</b>"
    ),
)
budgets_api.add_namespace(budgets_api_ns)

from . import ResourcesBudgetairesDisponiblesApi
from . import DonneesBudgetairesApi
from . import PlansDeComptesApi
from . import ParametrageApi