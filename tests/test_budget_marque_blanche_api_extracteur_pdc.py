from pathlib import Path
import pytest
from app.service.budget_marque_blanche_api_service._ExtracteurInfoPdc import _ExtracteurInfoPdc


@pytest.fixture
def _pdc_path():
    return Path(__file__).parent / "data" / "exemple_plan_de_compte.xml"

@pytest.fixture
def _extracteur(_pdc_path):
    return _ExtracteurInfoPdc(_pdc_path)

def test_extraction(_extracteur: _ExtracteurInfoPdc):

    nature_chapitres = _extracteur.extraire_chapitres_nature()
    fonction_chapitres = _extracteur.extraire_chapitres_fonction()
    nature_comptes = _extracteur.extraire_comptes_nature()
    fonc_reffonc = _extracteur.extraire_references_fonctionnelles()

    assert len(nature_chapitres) == 47
    assert len(fonction_chapitres) == 39

    assert len(nature_comptes) > 0
    assert "9999" not in nature_comptes
    assert "001" in nature_comptes
    assert nature_comptes["001"].parent_code == None
    assert "10" in nature_comptes
    assert "10229" in nature_comptes
    assert nature_comptes["10229"].parent_code == "1022"
    assert "102298" in nature_comptes
    assert nature_comptes["102298"].parent_code == "10229"

    assert len(fonc_reffonc) == 112
    assert "0" in fonc_reffonc
    assert fonc_reffonc["0"].parent_code == None
    assert "026" in fonc_reffonc
    assert fonc_reffonc["026"].parent_code == "02"
