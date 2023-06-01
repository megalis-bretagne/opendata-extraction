import pytest
import app.shared.client_api_sirene as api_sirene
from app.shared.client_api_sirene.ClientApiSirene import (
    _ClientApiInseeStrategy,
    _ClientApiEntrepriseStrategy,
    ClientApiSirene,
)

@pytest.fixture(scope="module")
def vcr_config():
    return { "filter_headers": ["authorization"] }

@pytest.fixture()
def client_api_sirene(request):
    list_strategies = request.param

    client = api_sirene.ClientApiSirene(*list_strategies)
    return client


@pytest.fixture()
def siren():
    return "253514491"

@pytest.fixture()
def ccbr_siren():
    return "243500733"

@pytest.mark.vcr
@pytest.mark.parametrize(
    "client_api_sirene",
    [
        (_ClientApiInseeStrategy("clef valide", "secret valide"),),
    ],
    indirect=True,
)
def test_client_api_sirene_etablissements_strategies(client_api_sirene: ClientApiSirene, ccbr_siren):
    lst_etab = client_api_sirene.etablissements(ccbr_siren)

    assert len(lst_etab) == 12

    siege = next(e for e in lst_etab if e.est_siege)
    assert siege.siret == "24350073300114"

    service_assainissement = next(e for e in lst_etab if e.siret == "24350073300049")
    assert not service_assainissement.est_siege
    assert service_assainissement.enseigne == "SERVICE D'ASSAINISSEMENT"

@pytest.mark.vcr
@pytest.mark.parametrize(
    "client_api_sirene",
    [
        (_ClientApiInseeStrategy("clef valide", "secret valide"),),
    ],
    indirect=True,
)
def test_client_api_sirene_strategies(client_api_sirene: ClientApiSirene, siren):
    
    etab_siege = client_api_sirene.etablissement_siege_du_siren(siren)
    assert etab_siege.nic == "00047"
    assert etab_siege.siret == "25351449100047"
    assert etab_siege.denomination_unite_legale == "MEGALIS BRETAGNE"
    assert etab_siege.est_siege == True
    assert etab_siege.enseigne == None


@pytest.mark.vcr
@pytest.mark.parametrize(
    "client_api_sirene",
    [
        (
            _ClientApiInseeStrategy("clef valide", "secret invalide"),
            _ClientApiEntrepriseStrategy(
                "https://entreprise.data.gouv.fr/api/sirene/v3"
            ),
        ),
    ],
    indirect=True,
)
def test_client_api_sirene_fallback(client_api_sirene, siren):

    etab_siege = client_api_sirene.etablissement_siege_du_siren(siren)

    assert etab_siege.nic == "00047"
    assert etab_siege.denomination_unite_legale == "MEGALIS BRETAGNE"


@pytest.mark.vcr
@pytest.mark.parametrize(
    "client_api_sirene",
    [
        (
            _ClientApiInseeStrategy("clef invalide", "secret invalide"),
            _ClientApiEntrepriseStrategy(
                "https://faux.entreprise.data.gouv.fr/api/sirene/v3"
            ),
        ),
    ],
    indirect=True,
)
def test_client_api_sirene_all_fail(client_api_sirene, siren):

    with pytest.raises(api_sirene.ErreurClientApiSirene) as e:
        client_api_sirene.etablissement_siege_du_siren(siren)


@pytest.mark.vcr
@pytest.mark.parametrize(
    "client_api_sirene",
    [
        (_ClientApiInseeStrategy("clef valide", "clef valide"),),
    ],
    indirect=True,
)
def test_client_api_insee_invalid_siren(client_api_sirene):
    siren_invalide = "253514499" # siren inexistant

    with pytest.raises(api_sirene.SireneInvalide) as e:
        client_api_sirene.etablissement_siege_du_siren(siren_invalide)


@pytest.mark.vcr
@pytest.mark.parametrize(
    "client_api_sirene",
    [
        (_ClientApiInseeStrategy("clef valide", "clef valide"),),
        (
            _ClientApiEntrepriseStrategy(
                "https://entreprise.data.gouv.fr/api/sirene/v3"
            ),
        ),
    ],
    indirect=True,
)
def test_client_api_insee_invalid_syntax_siren(client_api_sirene):
    siren_invalide = "253514490_invalid" # siren à la syntaxe invalide

    with pytest.raises(api_sirene.SireneInvalide) as e:
        client_api_sirene.etablissement_siege_du_siren(siren_invalide)
