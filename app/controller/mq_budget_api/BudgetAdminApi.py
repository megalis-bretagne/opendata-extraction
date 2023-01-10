from . import budgets_api_ns

from flask_restx import Resource

from app.service.mq_budget_api_service.budgets_functions import pdc_path_to_api_response


@budgets_api_ns.route("/admin/cache_info/pdc")
class CacheInfoPDCCtrl(Resource):
    @budgets_api_ns.response(200, "Success")
    def get(self):
        cache_info = pdc_path_to_api_response.cache_info()
        return cache_info._asdict()
