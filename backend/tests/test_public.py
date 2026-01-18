"""
Test Public Routes - Updated to match actual API response structure
"""
import pytest


class TestPublicRoutes:
    """Tests for public transparency portal routes"""
    
    def test_public_pacs(self, client):
        """Test public PACs endpoint"""
        response = client.get("/api/public/pacs")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or isinstance(data, list)
    
    def test_public_pacs_geral(self, client):
        """Test public PACs Geral endpoint"""
        response = client.get("/api/public/pacs-geral")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or isinstance(data, list)
    
    def test_public_pacs_obras(self, client):
        """Test public PACs Obras endpoint"""
        response = client.get("/api/public/pacs-geral-obras")
        assert response.status_code == 200
        data = response.json()
        # API returns object with 'data' key
        assert isinstance(data, list) or "data" in data
    
    def test_public_processos(self, client):
        """Test public processos endpoint"""
        response = client.get("/api/public/processos")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or isinstance(data, list)
    
    def test_public_dashboard_stats(self, client):
        """Test public dashboard statistics"""
        response = client.get("/api/public/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestPublicMROSC:
    """Tests for public MROSC routes"""
    
    def test_public_mrosc_projetos(self, client):
        """Test public MROSC projects endpoint"""
        response = client.get("/api/public/mrosc/projetos")
        assert response.status_code == 200
        data = response.json()
        # API returns object with 'data' key
        assert isinstance(data, list) or "data" in data
    
    def test_public_mrosc_estatisticas(self, client):
        """Test public MROSC statistics endpoint"""
        response = client.get("/api/public/mrosc/estatisticas")
        assert response.status_code == 200
        data = response.json()
        # API may wrap data in 'data' key
        if "data" in data:
            assert "total_projetos" in data["data"]
        else:
            assert "total_projetos" in data


class TestAnalytics:
    """Tests for analytics routes"""
    
    def test_analytics_dashboard(self, client, auth_headers):
        """Test analytics dashboard"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/analytics/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_analytics_realtime(self, client, auth_headers):
        """Test realtime analytics"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/analytics/realtime", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "uso_por_secretaria" in data
        assert "atividade_por_horario" in data
        assert "tendencia_gastos" in data
        assert "metricas_desempenho" in data
        assert "status_modulos" in data
