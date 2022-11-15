from .exceptions import (
    ActesMarqueBlancheApiException, SolrMarqueBlancheError
)


def _wrap_in_acte_marque_blanche_api_ex(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ActesMarqueBlancheApiException as err:
            raise err
        except Exception as err:
            raise ActesMarqueBlancheApiException("Erreur inconnue") from err

    return inner
