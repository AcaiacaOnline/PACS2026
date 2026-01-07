"""
Test suite for DOEM Público and Gestão Processual Dashboard features
- DOEM Público: Public access without login, navigation buttons
- Gestão Processual: Dashboard with KPIs and charts, toggle functionality
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDOEMPublicoEndpoints:
    """Test public DOEM endpoints - no authentication required"""
    
    def test_public_doem_anos(self):
        """Test GET /api/public/doem/anos - returns available years"""
        response = requests.get(f"{BASE_URL}/api/public/doem/anos")
        assert response.status_code == 200
        data = response.json()
        assert "anos" in data
        assert isinstance(data["anos"], list)
        print(f"Available years: {data['anos']}")
    
    def test_public_doem_edicoes(self):
        """Test GET /api/public/doem/edicoes - returns published editions"""
        response = requests.get(f"{BASE_URL}/api/public/doem/edicoes?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            # Verify edition structure
            edition = data[0]
            assert "edicao_id" in edition
            assert "numero_edicao" in edition
            assert "ano" in edition
            assert "data_publicacao" in edition
            assert "status" in edition
            print(f"Found {len(data)} editions")
    
    def test_public_doem_busca(self):
        """Test GET /api/public/doem/busca - search functionality"""
        response = requests.get(f"{BASE_URL}/api/public/doem/busca?q=decreto")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "resultados" in data
        print(f"Search results: {data['total']} found")
    
    def test_public_doem_no_auth_required(self):
        """Verify public endpoints work without authentication"""
        # Test without any auth header
        endpoints = [
            "/api/public/doem/anos",
            "/api/public/doem/edicoes?limit=5"
        ]
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            assert response.status_code == 200, f"Endpoint {endpoint} should not require auth"
            print(f"✓ {endpoint} accessible without auth")


class TestProcessosStatsEndpoint:
    """Test processos stats endpoint - requires authentication"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "cristiano.abdo@acaiaca.mg.gov.br",
            "password": "Cris@820906"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_processos_stats_requires_auth(self):
        """Test that /api/processos/stats requires authentication"""
        response = requests.get(f"{BASE_URL}/api/processos/stats")
        assert response.status_code == 401 or response.status_code == 403
        print("✓ Stats endpoint correctly requires authentication")
    
    def test_processos_stats_with_auth(self, auth_token):
        """Test GET /api/processos/stats with authentication"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/processos/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify KPI fields
        assert "total_processos" in data
        assert "total_concluidos" in data or "stats_by_status" in data
        assert "stats_by_status" in data
        assert "stats_by_modalidade" in data
        
        print(f"Total processos: {data['total_processos']}")
        print(f"Stats by status: {len(data['stats_by_status'])} categories")
        print(f"Stats by modalidade: {len(data['stats_by_modalidade'])} categories")
    
    def test_processos_stats_structure(self, auth_token):
        """Verify stats response structure for dashboard"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/processos/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify stats_by_status structure
        if data.get("stats_by_status"):
            for item in data["stats_by_status"]:
                assert "status" in item
                assert "quantidade" in item
        
        # Verify stats_by_modalidade structure
        if data.get("stats_by_modalidade"):
            for item in data["stats_by_modalidade"]:
                assert "modalidade" in item
                assert "quantidade" in item
        
        print("✓ Stats structure validated for dashboard rendering")


class TestProcessosPaginatedEndpoint:
    """Test processos paginated endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "cristiano.abdo@acaiaca.mg.gov.br",
            "password": "Cris@820906"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_processos_paginado(self, auth_token):
        """Test GET /api/processos/paginado"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/processos/paginado?page=1&page_size=10", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        print(f"Paginated processos: {len(data['items'])} items, {data['total']} total")
    
    def test_processos_anos(self, auth_token):
        """Test GET /api/processos/anos"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/processos/anos", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "anos" in data
        print(f"Available years for processos: {data['anos']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
