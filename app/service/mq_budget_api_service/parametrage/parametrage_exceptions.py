class ParametrageApiException(Exception):
    """Root exception for mq_budget parametrage api"""

    pass


class DefaultVisualisationLocalisationParsingError(ParametrageApiException):
    def __init__(self, serialized: str) -> None:
        self.serialized = serialized
        super().__init__(f"Impossible de parser la localisation `{serialized}`")


class ParametresDefaultVisualisationParsingError(ParametrageApiException):
    pass
