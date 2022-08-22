"""Compare la generation de données budgets entre deux versions de l'API"""

import pytest
import requests
import hashlib
import tempfile
from pathlib import Path

API_CURRENT = "http://localhost:8080/api/v1"
OLD_API = "http://localhost:8081/api/v1"


@pytest.mark.skip(reason="Tests manuels")
@pytest.mark.parametrize(
    "siren,annee",
    [
        ("215600461", "2022"),
        ("215600461", "2021"),
        ("212201941", "2022"),
        ("212201941", "2021"),
    ]
)
def test_budget_siren_annee(siren, annee):
    current = _get_budets_siren_annee(API_CURRENT, siren, annee)
    previous = _get_budets_siren_annee(OLD_API, siren, annee)

    compare_csvs(
        f"budg-{siren}-{annee}-current.csv",
        current.content,
        f"budg-{siren}-{annee}-previous.csv",
        previous.content,
    )

@pytest.mark.skip(reason="Tests manuels")
@pytest.mark.parametrize(
    "annee",
    [
        "2022",
        "2021",
    ]
)
def test_budget_annee(annee):
    annee = "2022"
    current = _get_budgets_annee(API_CURRENT, annee)
    previous = _get_budgets_annee(OLD_API, annee)

    compare_csvs(
        f"budg-{annee}-current.csv",
        current.content,
        f"budg-{annee}-previous.csv",
        previous.content,
    )


def _get_budets_siren_annee(api_prefix, siren, annee):
    url = f"{api_prefix}/scdl/budget/{siren}/{annee}"
    response = requests.get(url)
    return response


def _get_budgets_annee(api_prefix, annee):
    url = f"{api_prefix}/scdl/budget/{annee}"
    response = requests.get(url)
    return response


def compare_csvs(current_suffix, current, previous_suffix, previous):

    d = Path("/tmp/api-tests")
    _, current_f_s = tempfile.mkstemp(suffix=current_suffix, dir=d)
    _, previous_f_s = tempfile.mkstemp(suffix=previous_suffix, dir=d)

    with open(current_f_s, "wb") as current_f, open(previous_f_s, "wb") as previous_f:
        current_f.write(current)
        previous_f.write(previous)

    hexd_one = hashlib.md5(current).hexdigest()
    hexd_two = hashlib.md5(previous).hexdigest()

    assert (
        hexd_one == hexd_two
    ), f"Les réponses devraient être les mêmes\n \
        Les fichiers pour comparaisons sont: {current_f_s} et {previous_f_s}"
