class TestSmoke:

    def test_health_check(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200

