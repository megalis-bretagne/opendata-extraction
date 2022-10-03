import pytest

class TestBudgetMarqueBlancheApi:
    api_prefix = "/api/v1/budgets"
    un_siren = "215600461"
    un_faux_siren = "999999991"

    def test_budget_ressources_disponibles(self, client):

        response = client.get(f"{self.api_prefix}/disponibles/{self.un_siren}")
        assert response.status_code == 200
    
    @pytest.mark.skip("Pourra réactiver lorsque l'on saura monter un vrai environement")
    def test_budget_etape_admin(self, client):

        response = client.get(f"{self.api_prefix}/{self.un_siren}/2021/administratif")
        assert response.status_code == 200
    
    #
    # Cas en erreur
    #
    def test_budget_avec_etape_invalide(self, client):

        response = client.get(f"{self.api_prefix}/{self.un_siren}/2022/etape_invalide")
        assert response.status_code == 400

    def test_budget_avec_siren_invalide(self, client):

        response = client.get(f"{self.api_prefix}/{self.un_faux_siren}/2022/administratif")
        assert response.status_code >= 400, response

    def test_budget_avec_vrai_siren_sans_budget(self, client):

        response = client.get(f"{self.api_prefix}/{self.un_siren}/1980/administratif") # Pas de budget pour cette année
        assert response.status_code == 404