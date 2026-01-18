"""
Test PAC Routes
"""
import pytest


class TestPACIndividual:
    """Tests for PAC Individual routes"""
    
    def test_get_pacs(self, client, auth_headers):
        """Test listing PACs"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/pacs", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_pacs_paginado(self, client, auth_headers):
        """Test listing PACs with pagination"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/pacs/paginado?page=1&limit=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
    
    def test_get_pacs_anos(self, client, auth_headers):
        """Test getting available years"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/pacs/anos", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_pacs_stats(self, client, auth_headers):
        """Test getting PAC statistics"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/pacs/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_pacs" in data
        assert "valor_total" in data
    
    def test_dashboard_stats(self, client, auth_headers):
        """Test dashboard statistics"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/dashboard/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "pacs" in data
        assert "pacs_geral" in data
        assert "processos" in data


class TestPACGeral:
    """Tests for PAC Geral routes"""
    
    def test_get_pacs_geral(self, client, auth_headers):
        """Test listing PACs Geral"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/pacs-geral", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_pacs_geral_stats(self, client, auth_headers):
        """Test getting PAC Geral statistics"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/pacs-geral/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_pacs" in data


class TestPACObras:
    """Tests for PAC Obras routes"""
    
    def test_get_pacs_obras(self, client, auth_headers):
        """Test listing PACs Obras"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/pacs-geral-obras", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_classificacao_obras(self, client, auth_headers):
        """Test getting obras classification"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/classificacao/obras-servicos", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Should have at least one classification code
        assert len(data) > 0
