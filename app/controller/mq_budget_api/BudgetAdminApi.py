from . import budgets_api_ns

from flask_restx import Resource

from app.service.budget import Totems, TotemsError
from app.service.budget.api import _read_scdl_as_str
from app.service.mq_budget_api_service.budgets_functions import pdc_path_to_api_response

# @budgets_api_ns.route("/admin/cache_info/scdls")
# class CacheInfoSCDLCtrl(Resource):
#     @budgets_api_ns.response(200, 'Success')
#     def get(self):
#         cache_info = _read_scdl_as_str.cache_info()
#         return cache_info._asdict()

@budgets_api_ns.route("/admin/cache_info/pdc")
class CacheInfoPDCCtrl(Resource):
    @budgets_api_ns.response(200, 'Success')
    def get(self):
        cache_info = pdc_path_to_api_response.cache_info()
        return cache_info._asdict()