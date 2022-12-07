from pathlib import Path


class ActesMarqueBlancheApiException(Exception):
    def __init__(self, api_message: str):
        self.api_message = api_message


class SolrMarqueBlancheError(ActesMarqueBlancheApiException):
    def __init__(self, message: str):
        # api_message = f"sorl '{etape}' invalide"
        api_message = f"solr '{message}' execption"
        super().__init__(api_message)
