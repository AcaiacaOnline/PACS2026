"""
Test MROSC Routes
"""
import pytest


class TestMROSC:
    """Tests for MROSC (Prestação de Contas) routes"""
    
    @pytest.mark.asyncio
    async def test_get_naturezas_despesa(self, client, auth_headers):
        """Test getting expense natures"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = await client.get("/api/mrosc/naturezas-despesa", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "339030" in data
        assert "339039" in data
    
    @pytest.mark.asyncio
    async def test_get_projetos(self, client, auth_headers):
        """Test listing MROSC projects"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = await client.get("/api/mrosc/projetos", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_create_and_delete_projeto(self, client, auth_headers, sample_mrosc_projeto_data):
        """Test creating and deleting a MROSC project"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        # Create
        response = await client.post("/api/mrosc/projetos", json=sample_mrosc_projeto_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "projeto_id" in data
        projeto_id = data["projeto_id"]
        
        # Get
        response = await client.get(f"/api/mrosc/projetos/{projeto_id}", headers=auth_headers)
        assert response.status_code == 200
        
        # Get resumo
        response = await client.get(f"/api/mrosc/projetos/{projeto_id}/resumo", headers=auth_headers)
        assert response.status_code == 200
        resumo = response.json()
        assert "projeto" in resumo
        assert "resumo_rh" in resumo
        assert "resumo_despesas" in resumo
        
        # Delete
        response = await client.delete(f"/api/mrosc/projetos/{projeto_id}", headers=auth_headers)
        assert response.status_code == 200
        
        # Verify deleted
        response = await client.get(f"/api/mrosc/projetos/{projeto_id}", headers=auth_headers)
        assert response.status_code == 404


class TestPublicMROSC:
    """Tests for public MROSC routes"""
    
    @pytest.mark.asyncio
    async def test_public_mrosc_projetos(self, client):
        """Test public MROSC projects endpoint"""
        response = await client.get("/api/public/mrosc/projetos")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_public_mrosc_estatisticas(self, client):
        """Test public MROSC statistics endpoint"""
        response = await client.get("/api/public/mrosc/estatisticas")
        assert response.status_code == 200
        data = response.json()
        assert "total_projetos" in data
        assert "por_status" in data
