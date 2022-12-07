from typing import Optional
from app import db

from .parametrage_data_structures import DefaultVisualisationLocalisation

from app.models.mq_budget.parametrage import (
    ParametresDefaultVisualisation as ModelParametresDefaultVisualisation,
)
from app.service.mq_budget_api_service.parametrage import ParametresDefaultVisualisation

from ..type_aliases import Annee, Siret
from yatotem2scdl import EtapeBudgetaire


class ParametrageApiService:
    def get_parametre_defaultvisualisation(
        self,
        localisation: DefaultVisualisationLocalisation,
    ) -> ParametresDefaultVisualisation:

        localisation_str = localisation.to_model_str()

        db_parametres = ModelParametresDefaultVisualisation.query.filter_by(
            localisation=localisation_str
        ).first()

        answer: ParametresDefaultVisualisation
        if db_parametres is None:
            default_answer = ParametresDefaultVisualisation(localisation=localisation)
            answer = default_answer
        else:
            answer = ParametresDefaultVisualisation.from_model(db_parametres)

        return answer

    def search_parametres_defaultvisualisation(
        self, annee: Annee, siret: Siret, etape_str: str
    ) -> list[DefaultVisualisationLocalisation]:

        etape = EtapeBudgetaire.from_str(etape_str)
        begin_str = DefaultVisualisationLocalisation.to_localisation_begin_str(
            annee, siret, etape
        )

        db_parametres = (
            ModelParametresDefaultVisualisation.query.filter(
                ModelParametresDefaultVisualisation.localisation.startswith(begin_str)
            )
            .limit(100)
            .all()
        )

        return [ParametresDefaultVisualisation.from_model(x) for x in db_parametres]

    def set_parametre_defaultvisualisation(
        self,
        localisation: DefaultVisualisationLocalisation,
        titre: Optional[str],
        sous_titre: Optional[str],
    ) -> ParametresDefaultVisualisation:

        localisation_model_str = localisation.to_model_str()
        model = ModelParametresDefaultVisualisation.query.filter_by(
            localisation=localisation_model_str
        ).first()

        if model is None:
            model = ModelParametresDefaultVisualisation()
            model.localisation = localisation_model_str

        model.titre = titre
        model.sous_titre = sous_titre

        db.session.add(model)
        db.session.commit()

        return ParametresDefaultVisualisation.from_model(model)
