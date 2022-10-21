class TestBudgetMarqueBlancheApi:
    api_prefix = "/api/v1/budgets"
    un_siren = "215600461"
    un_siret = "21560046100010"
    un_faux_siret = "21560046199999"
    un_faux_siren = "999999991"

    def test_budget_ressources_disponibles(self, client):

        response = client.get(f"{self.api_prefix}/donnees_budgetaires_disponibles/{self.un_siren}")
        assert response.status_code == 200
        
    #
    # Cas en erreur
    #
    def test_budget_avec_etape_invalide(self, client):

        response = client.get(f"{self.api_prefix}/donnees_budgetaires/2022/{self.un_siret}/etape_invalide")
        assert response.status_code == 400

    def test_budget_avec_siren_invalide(self, client):

        response = client.get(f"{self.api_prefix}/donnees_budgetaires/2022/{self.un_faux_siret}/administratif")
        assert response.status_code >= 400, response

    def test_budget_avec_vrai_siren_sans_budget(self, client):

        response = client.get(f"{self.api_prefix}/donnees_budgetaires/1980/{self.un_siret}/administratif") # Pas de budget pour cette année
        assert response.status_code == 404