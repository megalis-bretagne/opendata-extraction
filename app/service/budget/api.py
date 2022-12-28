import csv
import functools

from pathlib import Path
from typing import Optional
from yatotem2scdl import EtapeBudgetaire, ConvertisseurTotemBudget, Options


from .functions import (
    TotemMetadataTuple,
    _liste_totem_with_metadata,
    _budget_metadata_predicate,
    make_or_get_budget_convertisseur,
    _get_or_make_scdl_from_totem,
)


class TotemsError(Exception):
    @staticmethod
    def wrap_fn(f):
        @functools.wraps(f)
        def inner(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except TotemsError as e:
                raise e
            except Exception as e:
                raise TotemsError("Erreur inconnue") from e

        return inner


class Totems:
    def __init__(self, siren: str) -> None:
        self._siren = siren
        self._siret: Optional[str] = None
        self._annee: Optional[int] = None
        self._etape: EtapeBudgetaire = None

    def siren(self, siren: str):
        self._siren = siren
        return self

    def annee(self, annee: int):
        self._annee = annee
        return self

    def siret(self, siret: str):
        self._siret = siret
        return self

    def etape(self, etape: EtapeBudgetaire):
        self._etape = etape
        return self

    @TotemsError.wrap_fn
    def request(self):
        totem_x_metadata = _liste_totem_with_metadata(self._siren)
        pred = _budget_metadata_predicate(
            annee=self._annee, siret=self._siret, etape=self._etape
        )
        totems_and_metadata = { x for x in totem_x_metadata if pred(x.metadata) }

        return ListedTotems(totems_and_metadata)


class ListedTotems:
    def __init__(self, totem_x_metadata: set[TotemMetadataTuple]) -> None:
        self._totem_x_metadata = totem_x_metadata
        self.convertisseur = make_or_get_budget_convertisseur()

    @functools.cached_property
    def _pdcs(self):
        _pdcs = {x.metadata.plan_de_compte for x in self._totem_x_metadata}
        return frozenset(_pdcs)

    def ensure_has_unique_pdc(self):
        """S'assure qu'il n'y ait qu'un seul plan de comptes pour les fichiers totems correspondant
        Raises:
            TotemsError: en cas de PDC non unique
        """

        nb_pdcs = len(self._pdcs)
        if nb_pdcs != 1:
            nb_totems = len(self._totem_x_metadata)
            raise TotemsError(
                f"Il y a {nb_pdcs} plans de comptes pour les fichiers {nb_totems} totems."
            )

        return self

    @property
    def pdcs(self):
        return self._pdcs

    @property
    def first_pdc(self):
        return next(iter(self._pdcs))

    @property
    def liste(self):
        return self._totem_x_metadata

    @TotemsError.wrap_fn
    def vers_scdl_rows(self) -> list[dict]:
        """Transforme les fichiers totems en lignes SCDL"""

        totems_and_metadata = self._totem_x_metadata

        rows = []
        for (xml, _) in totems_and_metadata:
            reader = _to_scdl_csv_reader(self.convertisseur, xml)
            for _, row in enumerate(reader):
                rows.append(row)

        return rows


def _read_scdl_as_str(xml_fp: Path):
    scdl_fp = _get_or_make_scdl_from_totem(xml_fp)
    scdl = scdl_fp.read_text()
    return scdl


def _to_scdl_csv_reader(convertisseur: ConvertisseurTotemBudget, xml_fp: Path):

    entetes_seq = convertisseur.budget_scdl_entetes().split(",")
    scdl = _read_scdl_as_str(xml_fp)
    return csv.DictReader(scdl.splitlines(), entetes_seq)
