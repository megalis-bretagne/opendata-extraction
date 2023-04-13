import logging
from typing import Mapping

from app import db

from .exceptions import (
    BadRequestforPublicationPiecesJointesApi,
    PublicationPiecesJointesApiError,
)

from app.models.publication_model import PieceJointe, Publication

logger = logging.getLogger(__name__)


class PublicationPiecesJointesApiService:
    def publie_depublie_piecesjointes(self, payload: Mapping[str, bool]):

        logger.info(f"Requête de publicaiton des annexes.")
        logger.debug(f"Avec les instructions suivantes: {payload}")
        publication_id = self._check_payload_is_about_only_one_publication(payload)

        if publication_id is None:
            logger.warning(f"Requête de publication de pièce jointes vide.")
            return

        publication = Publication.query.get(publication_id)
        if publication.etat == "0":  # Si la publication est en état 'non publiée'
            raise BadRequestforPublicationPiecesJointesApi(
                "On ne peut changer l'état de publication des pièces jointes"
                " uniquement pour les publications 'publiées'"
            )

        for id, publie in payload.items():
            pj: PieceJointe = PieceJointe.query.get(id)
            if pj is None:
                raise PublicationPiecesJointesApiError(f"Annexe {id} introuvable.")
            pj.publie = publie

        db.session.commit()

        try:
            from app.tasks.publication import publier_acte_task

            publication.etat = "2"
            task = publier_acte_task.delay(publication_id)
            return {
                "task_id": task.id,
                "status": task.status,
            }
        except Exception as e:
            raise PublicationPiecesJointesApiError(str(e)) from e

    def _check_payload_is_about_only_one_publication(
        self,
        payload: Mapping[str, bool],
    ) -> int | None:
        ids = payload.keys()
        filter = PieceJointe.id.in_(ids)  # type: ignore
        pjs = PieceJointe.query.filter(filter).all()

        publication_id = None
        for pj in pjs:
            if publication_id is not None and pj.publication_id != publication_id:
                raise BadRequestforPublicationPiecesJointesApi(
                    "Une commande de publication / dépublication de pièces jointes"
                    " doit concerné une seule publication"
                )

            publication_id = pj.publication_id

        return publication_id
