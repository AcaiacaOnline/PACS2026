"""
Test MROSC Routes
"""
import pytest


class TestMROSC:
    """Tests for MROSC (Prestação de Contas) routes"""
    
    def test_get_naturezas_despesa(self, client, auth_headers):
        """Test getting expense natures"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/mrosc/naturezas-despesa", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "339030" in data
        assert "339039" in data
    
    def test_get_projetos(self, client, auth_headers):
        """Test listing MROSC projects"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/mrosc/projetos", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
