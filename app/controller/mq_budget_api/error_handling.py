import app.service.mq_budget_api_service as service
from . import budgets_api_ns
from . import logger


@budgets_api_ns.errorhandler(service.EtapeInvalideError)
def handle_bad_request_errors(error):
    logger.exception(error)
    return {"message": error.api_message}, 400


@budgets_api_ns.errorhandler(service.AucuneDonneeBudgetError)
def handle_not_found(error):
    logger.exception(error)
    return {"message": error.api_message}, 404


@budgets_api_ns.errorhandler(service.BudgetMarqueBlancheApiException)
@budgets_api_ns.errorhandler(service.ImpossibleDextraireEtabInfoError)
@budgets_api_ns.errorhandler(service.ImpossibleDexploiterBudgetError)
def handle_ise_errors(error):
    logger.exception(error)
    return {"message": error.api_message}, 500