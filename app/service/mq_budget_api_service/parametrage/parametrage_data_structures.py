from dataclasses import dataclass, asdict
from typing import Optional

from ..type_aliases import Annee, Siret, VisualisationGrapheId
from yatotem2scdl import EtapeBudgetaire

from .parametrage_exceptions import (
    DefaultVisualisationLocalisationParsingError,
    ParametresDefaultVisualisationParsingError,
)

from app.models.mq_budget.parametrage import ParametresDefaultVisualisation as Model


@dataclass
class DefaultVisualisationLocalisation:
    annee: Annee
    siret: Siret
    etape: str
    graphe_id: VisualisationGrapheId

    def __init__(
        self, annee: Annee, siret: Siret, etape: str, graphe_id=VisualisationGrapheId
    ) -> None:

        EtapeBudgetaire.from_str(etape)  # Pour la gestion d'erreurs
        self.annee = annee
        self.siret = siret
        self.etape = etape
        self.graphe_id = graphe_id

    def etape_budgetaire(self):
        return EtapeBudgetaire.from_str(self.etape)

    def to_model_str(self) -> str:
        return f"1-{self.annee}-{self.siret}-{self.etape}-{self.graphe_id}"

    @staticmethod
    def from_model_str(model: str):

        if not model.startswith("1-"):
            raise DefaultVisualisationLocalisationParsingError(model)

        try:
            splitted = model.split("-")

            annee: Annee = int(splitted[1])
            siret: Siret = splitted[2]
            etape_str: str = splitted[3]
            graphe_id: VisualisationGrapheId = splitted[4]

            return DefaultVisualisationLocalisation(annee, siret, etape_str, graphe_id)

        except Exception as err:
            raise DefaultVisualisationLocalisationParsingError(model) from err


@dataclass
class ParametresDefaultVisualisation:

    localisation: DefaultVisualisationLocalisation
    titre: Optional[str] = None
    sous_titre: Optional[str] = None

    def to_api_answer(self):
        return asdict(self)

    def to_model(self):
        model = Model()
        model.localisation = self.localisation.to_model_str()
        model.titre = self.titre
        model.sous_titre = self.sous_titre
        return model

    @staticmethod
    def from_model(model: Model):

        try:
            localisation = DefaultVisualisationLocalisation.from_model_str(
                model.localisation
            )

            return ParametresDefaultVisualisation(
                localisation, model.titre, model.sous_titre
            )

        except Exception as err:
            raise ParametresDefaultVisualisationParsingError() from err
