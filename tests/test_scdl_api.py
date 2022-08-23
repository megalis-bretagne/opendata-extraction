#
#@pytest.mark.jeu_de_donnees("donnees_variees_de_prod")
#
class TestScdlApi:

    api_prefix = "/api/v1/scdl"

    def test_scdl_budget_pour_2022(self, client):
        response = client.get(f"{self.api_prefix}/budget/2022")
        assert response.status_code == 200

