"""
Test Bug Fixes - Planejamento Acaiaca
Tests for recently fixed bugs and new features
"""
import pytest


class TestNumeroModalidade:
    """Tests for numero_modalidade field fix"""
    
    def test_create_processo_with_numero_modalidade(self, client, auth_headers):
        """Test that numero_modalidade is saved when creating a processo"""
        processo_data = {
            "numero_processo": "PRC - 7777/2026",
            "modalidade_contratacao": "Pregão Eletrônico",
            "numero_modalidade": "PE 999/2026",
            "status": "Em Elaboração",
            "objeto": "Teste numero_modalidade",
            "secretaria": "Secretaria de Teste",
            "ano": 2026
        }
        
        response = client.post("/api/processos", json=processo_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("numero_modalidade") == "PE 999/2026"
        
        # Cleanup - delete test processo
        processo_id = data.get("processo_id")
        if processo_id:
            client.delete(f"/api/processos/{processo_id}", headers=auth_headers)
    
    def test_get_processo_returns_numero_modalidade(self, client, auth_headers):
        """Test that numero_modalidade is returned when getting a processo"""
        # Create test processo
        processo_data = {
            "numero_processo": "PRC - 6666/2026",
            "modalidade_contratacao": "Dispensa de Licitação",
            "numero_modalidade": "DL 001/2026",
            "status": "Em Elaboração",
            "objeto": "Teste GET numero_modalidade",
            "secretaria": "Secretaria de Teste",
            "ano": 2026
        }
        
        create_response = client.post("/api/processos", json=processo_data, headers=auth_headers)
        assert create_response.status_code == 200
        processo_id = create_response.json().get("processo_id")
        
        # Get processo
        get_response = client.get(f"/api/processos/{processo_id}", headers=auth_headers)
        assert get_response.status_code == 200
        
        data = get_response.json()
        assert data.get("numero_modalidade") == "DL 001/2026"
        
        # Cleanup
        client.delete(f"/api/processos/{processo_id}", headers=auth_headers)


class TestPortaria448:
    """Tests for Portaria 448/2002 in classification codes"""
    
    def test_classificacao_codigos_has_portaria_448(self, client):
        """Test that classification codes include Portaria 448 reference"""
        response = client.get("/api/classificacao/codigos")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check that all codes mention Portaria 448
        for codigo, info in data.items():
            assert "Portaria" in info.get("nome", "") or "448" in info.get("nome", ""), \
                f"Code {codigo} does not reference Portaria 448"
    
    def test_classificacao_has_material_consumo(self, client):
        """Test that 339030 Material de Consumo exists with Portaria 448"""
        response = client.get("/api/classificacao/codigos")
        assert response.status_code == 200
        
        data = response.json()
        assert "339030" in data
        assert "Material de Consumo" in data["339030"]["nome"]
        assert "Portaria STN nº 448/2002" in data["339030"]["nome"]


class TestYearSelector:
    """Tests for year selector functionality"""
    
    def test_public_processos_anos(self, client):
        """Test that public processos anos endpoint works"""
        response = client.get("/api/public/processos/anos")
        assert response.status_code == 200
        
        data = response.json()
        assert "anos" in data
        assert "ano_atual" in data
        assert isinstance(data["anos"], list)
    
    def test_public_processos_filter_by_year(self, client):
        """Test filtering public processos by year"""
        response = client.get("/api/public/processos?ano=2026")
        assert response.status_code == 200


class TestDashboardStats:
    """Tests for dashboard statistics"""
    
    def test_processos_por_status_available(self, client):
        """Test that processos_por_status is available in dashboard stats"""
        response = client.get("/api/public/dashboard/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "data" in data
        assert "processos_por_status" in data["data"]
        assert isinstance(data["data"]["processos_por_status"], list)
