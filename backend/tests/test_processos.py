"""
Test Processos Routes
"""
import pytest


class TestProcessos:
    """Tests for Gestão Processual routes"""
    
    def test_get_processos(self, client, auth_headers):
        """Test listing processos"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/processos", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_processos_paginado(self, client, auth_headers):
        """Test listing processos with pagination"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/processos/paginado?page=1&limit=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert "page" in data
    
    def test_get_processos_anos(self, client, auth_headers):
        """Test getting available years"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/processos/anos", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_processos_stats(self, client, auth_headers):
        """Test getting processos statistics"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/processos/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "por_status" in data
    
    def test_get_modalidades(self, client, auth_headers):
        """Test getting contracting modalities"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/processos/modalidades/lista", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "Pregão Eletrônico" in data
    
    def test_get_status_lista(self, client, auth_headers):
        """Test getting status list"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/processos/status/lista", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "Em Elaboração" in data
