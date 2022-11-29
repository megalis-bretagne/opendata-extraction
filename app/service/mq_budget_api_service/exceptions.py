from pathlib import Path


class BudgetMarqueBlancheApiException(Exception):
    def __init__(self, api_message: str):
        self.api_message = api_message


class EtapeInvalideError(BudgetMarqueBlancheApiException):
    def __init__(self, etape: str):
        api_message = f"Étape '{etape}' invalide"
        super().__init__(api_message)


class ImpossibleDextraireEtabInfoError(BudgetMarqueBlancheApiException):
    def __init__(self, siren: str):
        api_message = f"Impossible de déterminer l'établissement du siège social correspondant au siren {siren}"
        super().__init__(api_message=api_message)

class AucuneDonneeBudgetError(BudgetMarqueBlancheApiException):
    def __init__(self):
        super().__init__("Aucune données budget pour cette requête")

class ImpossibleDexploiterBudgetError(BudgetMarqueBlancheApiException):
    def __init__(self, budget_fp: Path, detail: str):
        self.budget_fp = budget_fp
        self.details = detail
        api_message = (
            f"Impossible d'exploiter les données budgets pour cette requête.\n"
        )
        super().__init__(api_message)


class _ImpossibleParserLigne(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
