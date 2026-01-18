"""
Test Public Routes (Portal da Transparência)
"""
import pytest


class TestPublicRoutes:
    """Tests for public transparency portal routes"""
    
    @pytest.mark.asyncio
    async def test_public_pacs(self, client):
        """Test public PACs endpoint"""
        response = await client.get("/api/public/pacs")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_public_pacs_geral(self, client):
        """Test public PACs Geral endpoint"""
        response = await client.get("/api/public/pacs-geral")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_public_pacs_obras(self, client):
        """Test public PACs Obras endpoint"""
        response = await client.get("/api/public/pacs-geral-obras")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_public_processos(self, client):
        """Test public processos endpoint"""
        response = await client.get("/api/public/processos")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_public_dashboard_stats(self, client):
        """Test public dashboard statistics"""
        response = await client.get("/api/public/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert "pacs" in data
        assert "processos" in data
        assert "valor_total_geral" in data
    
    @pytest.mark.asyncio
    async def test_public_classificacoes(self, client):
        """Test public classification codes"""
        response = await client.get("/api/public/classificacoes")
        assert response.status_code == 200
        data = response.json()
        assert "339030" in data


class TestDOEMPublic:
    """Tests for public DOEM routes"""
    
    @pytest.mark.asyncio
    async def test_public_doem_edicoes(self, client):
        """Test public DOEM editions endpoint"""
        response = await client.get("/api/public/doem/edicoes")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "data" in data
    
    @pytest.mark.asyncio
    async def test_public_doem_anos(self, client):
        """Test public DOEM years endpoint"""
        response = await client.get("/api/public/doem/anos")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_public_doem_segmentos(self, client):
        """Test public DOEM segments endpoint"""
        response = await client.get("/api/public/doem/segmentos")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
