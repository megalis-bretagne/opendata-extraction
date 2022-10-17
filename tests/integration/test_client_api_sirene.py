import pytest

from app.shared.client_api_sirene.flask_functions import etablissement_siege_pour_siren, etablissements_pour_siren

@pytest.fixture(scope="module")
def vcr_config():
    return { "filter_headers": ["authorization"] }

without_using_api_insee = dict(
    USE_API_INSEE=False,
    API_SIREN_KEY="clef invalide",
    API_SIREN_SECRET="secret invalide",
    URL_API_ENNTREPRISE="https://entreprise.data.gouv.fr/api/sirene/v3",
)
using_api_insee = dict(
    USE_API_INSEE=True,
    API_SIREN_KEY="clef valide",
    API_SIREN_SECRET="secret valide",
    URL_API_ENNTREPRISE="https://entreprise.data.gouv.fr/api/sirene/v3",
)

using_api_insee_misconfigured = dict(
    USE_API_INSEE=True,
    API_SIREN_KEY="clef invalide",
    API_SIREN_SECRET="secret invalide",
    URL_API_ENNTREPRISE="https://entreprise.data.gouv.fr/api/sirene/v3",
)


@pytest.fixture()
def etablissement_siege_pour_siren_noncache():
    yield etablissement_siege_pour_siren
    etablissement_siege_pour_siren.cache_clear()  # on s'assure de bien supprimer le cache entre les tests

@pytest.fixture()
def etablissements_pour_siren_noncache():
    yield etablissements_pour_siren
    etablissements_pour_siren.cache_clear()  # on s'assure de bien supprimer le cache entre les tests

class TestClientApiSirene:
    @pytest.mark.vcr
    @pytest.mark.parametrize(
        "app",
        [without_using_api_insee, using_api_insee, using_api_insee_misconfigured],
        indirect=True,
    )
    def test_etablissement_siege_call(self, app, etablissement_siege_pour_siren_noncache):

        siren = "253514491"
        etab_siege = etablissement_siege_pour_siren_noncache(siren)

        assert etab_siege.nic == "00047"
        assert etab_siege.denomination_unite_legale == "MEGALIS BRETAGNE"

        print(f"{etab_siege}")


    @pytest.mark.vcr
    @pytest.mark.parametrize(
        "app",
        [without_using_api_insee, using_api_insee, using_api_insee_misconfigured],
        indirect=True,
    )
    def test_etablissements_call(self, app, etablissements_pour_siren_noncache):

        siren = "253514491"
        etablissements = etablissements_pour_siren_noncache(siren)

        assert len(etablissements) == 5

        siege = next(e for e in etablissements if e.est_siege)

        assert siege
        assert siege.nic == "00047"
        assert siege.denomination_unite_legale == "MEGALIS BRETAGNE"