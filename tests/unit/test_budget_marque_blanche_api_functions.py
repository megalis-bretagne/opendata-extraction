
import pytest
from app.service.mq_budget_api_service.functions import extraire_siren

def test_siren_integer():
    siren = extraire_siren(21560094100011)
    assert type(siren) == int
    assert siren == 215600941

def test_siren_str():
    siren = extraire_siren("21560094100011")
    assert type(siren) == str
    assert siren == "215600941"

def test_siren_error():
    with pytest.raises(ValueError):
        extraire_siren("2156009410001.0")
    with pytest.raises(TypeError):
        extraire_siren(3.14)
    with pytest.raises(TypeError):
        extraire_siren(False)