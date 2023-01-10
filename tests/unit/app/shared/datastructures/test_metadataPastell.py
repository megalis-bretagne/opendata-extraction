import pytest
import json
import pickle

from pathlib import Path

from app.shared.datastructures import MetadataPastell
from app.shared.datastructures.classification_actes import _classification_actes_dict


@pytest.fixture
def _data() -> dict:
    p = Path(__file__).parent / "_data" / "metadata_ex1.json"
    with p.open("r") as f:
        return json.load(f)


def test_smoke_parse(_data):
    metadata = MetadataPastell.parse(_data)

def test_sanitize_for_db(_data):

    _data["objet"] = "toto"
    metadata = MetadataPastell.parse(_data)
    sanitized_for_db = metadata.sanitize_for_db()

    assert id(metadata) != id(sanitized_for_db)
    serialized_metadata = pickle.dumps(metadata)
    serialized_sanitized = pickle.dumps(sanitized_for_db)

    assert serialized_metadata == serialized_sanitized

    

@pytest.mark.parametrize(
    "testDesc",
    [
        { "classification": "9.2", "classification_code": "9.2", "classification_nom": _classification_actes_dict["9.2"], "raises": False },
        { "classification": "9.2.3 toto tata", "classification_code": "9.2.3", "classification_nom": _classification_actes_dict["9.2"], "raises": False },
        { "classification": "10 toto tata", "classification_code": "10", "raises": True },
    ]
)
def test_parse_classficiation(_data, testDesc):
    _data["classification"] = testDesc["classification"]

    try:
        metadata = MetadataPastell.parse(_data)

        if testDesc["raises"]:
            assert False, "Le parsing de la classification aurait du planter"
    except Exception:
        if testDesc["raises"]:
            return

    assert metadata.classification_code == testDesc["classification_code"]
    assert metadata.classification_nom == testDesc["classification_nom"]


@pytest.mark.parametrize(
    "testDesc",
    [
        { "publication_open_data": 'toto', "acte_nature": '1', "result_publication_open_data": 'toto' },
        { "publication_open_data": '', "acte_nature": '1', "result_publication_open_data": '3' },

        { "acte_nature": '1', "result_publication_open_data": '3' },
        { "acte_nature": '2', "result_publication_open_data": '3' },
        { "acte_nature": '5', "result_publication_open_data": '3' },

        { "acte_nature": '3', "result_publication_open_data": '1' },
        { "acte_nature": '6', "result_publication_open_data": '1' },

        { "acte_nature": 'inconnu', "result_publication_open_data": '2' },
    ],
)
def test_publication_opendata(_data, testDesc):

    if not "publication_open_data" in testDesc:
        _del(_data, "publication_open_data")
    else:
        _data["publication_open_data"] = testDesc["publication_open_data"]

    _data["acte_nature"] = testDesc["acte_nature"]

    metadata = MetadataPastell.parse(_data)

    assert metadata.publication_open_data == testDesc["result_publication_open_data"]

def test_parse_params(_data):
    _test_parse_param(_data, "envoi_depot", valeur_si_non_present="checked")
    _test_parse_param(_data, "nature_autre_detail")

    _test_parse_param(_data, "arrete", "liste_arrete", parse_error_si_non_present=True)

    _test_parse_param(
        _data,
        "acte_tamponne",
        "liste_acte_tamponne",
        valeur_a_renseigner=["toto"],
        valeur_si_non_present=[],
    )
    _test_parse_param(
        _data,
        "autre_document_attache",
        "liste_autre_document_attache",
        valeur_a_renseigner=["toto"],
        valeur_si_non_present=[],
    )
    _test_parse_param(_data, "type_piece")
    _test_parse_param(
        _data, "classification", valeur_si_non_present="9.2", valeur_a_renseigner="1"
    )


def _test_parse_param(
    _data,
    key_json,
    key_attrib=None,
    valeur_a_renseigner="toto",
    valeur_si_non_present="",
    parse_error_si_non_present=False,
):

    if key_attrib is None:
        key_attrib = key_json

    # Parametre vide
    _del(_data, key_json)

    if parse_error_si_non_present:
        try:
            metadata = MetadataPastell.parse(_data)
            assert False, f"On devrait avoir une exception lors du parsing"
        except Exception:
            pass
    else:
        metadata = MetadataPastell.parse(_data)

        if valeur_si_non_present == "attrib_error":
            try:
                valeur_si_non_present == getattr(metadata, key_attrib)
                assert (
                    False
                ), f"Le metadata pastell ne devrait pas avoir d'attribut nommé {key_attrib}"
            except AttributeError:
                pass
        else:
            assert valeur_si_non_present == getattr(metadata, key_attrib)

    # Parametre non vide
    _data[key_json] = valeur_a_renseigner
    metadata = MetadataPastell.parse(_data)
    assert valeur_a_renseigner == getattr(metadata, key_attrib)


def _silently(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(e)

    return inner


@_silently
def _del(_data, key):
    del _data[key]
