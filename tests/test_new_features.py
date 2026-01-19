"""
Test Suite for PAC System - New Features
Tests for:
1. Year filter endpoints for PAC, PAC Geral, and Processos
2. DOEM module (create, publish, download PDF)
3. Public DOEM portal
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://planning-system-2.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "cristiano.abdo@acaiaca.mg.gov.br"
TEST_PASSWORD = "Cris@820906"


class TestYearFilters:
    """Tests for year filter endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Authentication failed")
    
    def test_pacs_anos_endpoint(self):
        """Test /api/pacs/anos endpoint returns list of years"""
        response = self.session.get(f"{BASE_URL}/api/pacs/anos")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "anos" in data, "Response should contain 'anos' key"
        assert "ano_atual" in data, "Response should contain 'ano_atual' key"
        assert isinstance(data["anos"], list), "anos should be a list"
        assert len(data["anos"]) > 0, "anos list should not be empty"
        print(f"PAC anos: {data['anos']}, ano_atual: {data['ano_atual']}")
    
    def test_pacs_geral_anos_endpoint(self):
        """Test /api/pacs-geral/anos endpoint returns list of years"""
        response = self.session.get(f"{BASE_URL}/api/pacs-geral/anos")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "anos" in data, "Response should contain 'anos' key"
        assert "ano_atual" in data, "Response should contain 'ano_atual' key"
        assert isinstance(data["anos"], list), "anos should be a list"
        print(f"PAC Geral anos: {data['anos']}, ano_atual: {data['ano_atual']}")
    
    def test_processos_anos_endpoint(self):
        """Test /api/processos/anos endpoint returns list of years"""
        response = self.session.get(f"{BASE_URL}/api/processos/anos")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "anos" in data, "Response should contain 'anos' key"
        assert "ano_atual" in data, "Response should contain 'ano_atual' key"
        assert isinstance(data["anos"], list), "anos should be a list"
        print(f"Processos anos: {data['anos']}, ano_atual: {data['ano_atual']}")
    
    def test_pacs_filter_by_year(self):
        """Test filtering PACs by year"""
        # First get available years
        anos_response = self.session.get(f"{BASE_URL}/api/pacs/anos")
        anos_data = anos_response.json()
        
        if anos_data["anos"]:
            year = anos_data["anos"][0]
            response = self.session.get(f"{BASE_URL}/api/pacs?ano={year}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert isinstance(data, list), "Response should be a list"
            print(f"PACs for year {year}: {len(data)} records")
    
    def test_pacs_geral_filter_by_year(self):
        """Test filtering PAC Geral by year"""
        # First get available years
        anos_response = self.session.get(f"{BASE_URL}/api/pacs-geral/anos")
        anos_data = anos_response.json()
        
        if anos_data["anos"]:
            year = anos_data["anos"][0]
            response = self.session.get(f"{BASE_URL}/api/pacs-geral?ano={year}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert isinstance(data, list), "Response should be a list"
            print(f"PAC Geral for year {year}: {len(data)} records")
    
    def test_processos_filter_by_year(self):
        """Test filtering Processos by year"""
        # First get available years
        anos_response = self.session.get(f"{BASE_URL}/api/processos/anos")
        anos_data = anos_response.json()
        
        if anos_data["anos"]:
            year = anos_data["anos"][0]
            response = self.session.get(f"{BASE_URL}/api/processos?ano={year}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert isinstance(data, list), "Response should be a list"
            print(f"Processos for year {year}: {len(data)} records")


class TestDOEMModule:
    """Tests for DOEM (Diário Oficial Eletrônico Municipal) module"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Authentication failed")
    
    def test_doem_config_endpoint(self):
        """Test DOEM config endpoint"""
        response = self.session.get(f"{BASE_URL}/api/doem/config")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "nome_municipio" in data, "Config should have nome_municipio"
        print(f"DOEM Config: {data}")
    
    def test_doem_edicoes_anos_endpoint(self):
        """Test DOEM anos endpoint"""
        response = self.session.get(f"{BASE_URL}/api/doem/edicoes/anos")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "anos" in data, "Response should contain 'anos' key"
        print(f"DOEM anos: {data['anos']}")
    
    def test_doem_list_edicoes(self):
        """Test listing DOEM editions"""
        response = self.session.get(f"{BASE_URL}/api/doem/edicoes")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"DOEM editions count: {len(data)}")
        
        if len(data) > 0:
            edicao = data[0]
            assert "edicao_id" in edicao, "Edition should have edicao_id"
            assert "numero_edicao" in edicao, "Edition should have numero_edicao"
            assert "status" in edicao, "Edition should have status"
            print(f"First edition: {edicao['numero_edicao']}, status: {edicao['status']}")
    
    def test_doem_create_edicao(self):
        """Test creating a new DOEM edition"""
        tomorrow = datetime.now().strftime("%Y-%m-%dT12:00:00")
        
        payload = {
            "data_publicacao": tomorrow,
            "publicacoes": [
                {
                    "titulo": "TEST_DECRETO Nº 001/2026",
                    "texto": "Este é um decreto de teste para validação do sistema DOEM.",
                    "secretaria": "Gabinete do Prefeito",
                    "tipo": "Decreto",
                    "ordem": 1
                }
            ]
        }
        
        response = self.session.post(f"{BASE_URL}/api/doem/edicoes", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "edicao_id" in data, "Response should contain edicao_id"
        assert data["status"] == "rascunho", "New edition should be in 'rascunho' status"
        print(f"Created DOEM edition: {data['edicao_id']}, numero: {data['numero_edicao']}")
        
        # Store for cleanup
        self.created_edicao_id = data["edicao_id"]
        return data["edicao_id"]
    
    def test_doem_get_edicao(self):
        """Test getting a specific DOEM edition"""
        # First list editions to get an ID
        list_response = self.session.get(f"{BASE_URL}/api/doem/edicoes")
        edicoes = list_response.json()
        
        if len(edicoes) > 0:
            edicao_id = edicoes[0]["edicao_id"]
            response = self.session.get(f"{BASE_URL}/api/doem/edicoes/{edicao_id}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert data["edicao_id"] == edicao_id
            print(f"Got edition: {data['numero_edicao']}")
        else:
            pytest.skip("No editions available to test")
    
    def test_doem_download_pdf(self):
        """Test downloading DOEM PDF"""
        # First list editions to get an ID
        list_response = self.session.get(f"{BASE_URL}/api/doem/edicoes")
        edicoes = list_response.json()
        
        if len(edicoes) > 0:
            edicao_id = edicoes[0]["edicao_id"]
            response = self.session.get(f"{BASE_URL}/api/doem/edicoes/{edicao_id}/pdf")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert "application/pdf" in response.headers.get("content-type", ""), "Response should be PDF"
            print(f"PDF downloaded successfully, size: {len(response.content)} bytes")
        else:
            pytest.skip("No editions available to test")


class TestDOEMPublicPortal:
    """Tests for public DOEM portal endpoints"""
    
    def setup_method(self):
        """Setup for each test"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_public_doem_anos(self):
        """Test public DOEM anos endpoint"""
        response = self.session.get(f"{BASE_URL}/api/public/doem/anos")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "anos" in data, "Response should contain 'anos' key"
        print(f"Public DOEM anos: {data['anos']}")
    
    def test_public_doem_edicoes(self):
        """Test public DOEM editions list"""
        response = self.session.get(f"{BASE_URL}/api/public/doem/edicoes")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Public endpoint should only return published editions
        for edicao in data:
            assert edicao["status"] == "publicado", f"Public portal should only show published editions, got: {edicao['status']}"
        
        print(f"Public DOEM editions (published): {len(data)}")
    
    def test_public_doem_busca(self):
        """Test public DOEM search"""
        response = self.session.get(f"{BASE_URL}/api/public/doem/busca?q=decreto")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "total" in data, "Response should contain 'total' key"
        assert "resultados" in data, "Response should contain 'resultados' key"
        print(f"Search results for 'decreto': {data['total']} found")
    
    def test_public_doem_pdf_download(self):
        """Test public PDF download for published edition"""
        # First get published editions
        list_response = self.session.get(f"{BASE_URL}/api/public/doem/edicoes")
        edicoes = list_response.json()
        
        if len(edicoes) > 0:
            edicao_id = edicoes[0]["edicao_id"]
            response = self.session.get(f"{BASE_URL}/api/public/doem/edicoes/{edicao_id}/pdf")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert "application/pdf" in response.headers.get("content-type", ""), "Response should be PDF"
            print(f"Public PDF downloaded successfully, size: {len(response.content)} bytes")
        else:
            pytest.skip("No published editions available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
