"""
Test suite for Bug Fixes:
1. Year selector in Portal Público (/) for Processos
2. Process creation with all fields (secretaria, secretario, responsavel)
3. Portaria 448 classification codes API
4. /portal-publico route
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

# Get base URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "cristiano.abdo@acaiaca.mg.gov.br",
        "password": "Cris@820906"
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Authentication failed - skipping authenticated tests")

@pytest.fixture
def authenticated_headers(auth_token):
    """Return headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


# ==============================================================================
# TEST 1: Year selector in public portal - processos/anos endpoint
# ==============================================================================

class TestPublicProcessosAnos:
    """Tests for /api/public/processos/anos endpoint - Year selector in Portal Público"""
    
    def test_public_processos_anos_endpoint_exists(self):
        """Test that the public processos anos endpoint exists and returns years"""
        response = requests.get(f"{BASE_URL}/api/public/processos/anos")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "anos" in data, "Response should contain 'anos' key"
        assert "ano_atual" in data, "Response should contain 'ano_atual' key"
        assert isinstance(data["anos"], list), "'anos' should be a list"
        
        # Current year should be in the list
        ano_atual = datetime.now().year
        assert ano_atual in data["anos"], f"Current year {ano_atual} should be in the list"
        
        print(f"✓ Available years: {data['anos']}")
        print(f"✓ Current year: {data['ano_atual']}")
    
    def test_public_processos_filter_by_year(self):
        """Test filtering public processos by year"""
        ano = 2025
        response = requests.get(f"{BASE_URL}/api/public/processos?ano={ano}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "data" in data or isinstance(data, list), "Response should contain data"
        
        print(f"✓ Public processos endpoint working with year filter (ano={ano})")


# ==============================================================================
# TEST 2: Portaria 448 Classification Codes API
# ==============================================================================

class TestPortaria448Codes:
    """Tests for /api/classificacao/codigos endpoint - Portaria 448 codes"""
    
    def test_classificacao_codigos_contains_portaria_448(self):
        """Test that classification codes include Portaria 448 reference"""
        response = requests.get(f"{BASE_URL}/api/classificacao/codigos")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Check that we have the main codes
        expected_codes = ["339030", "339036", "339039", "449052"]
        for code in expected_codes:
            assert code in data, f"Code {code} should be in classification codes"
        
        # Check that Portaria 448 is mentioned in the names
        portaria_found = False
        for code, info in data.items():
            if "nome" in info and "448" in info["nome"]:
                portaria_found = True
                print(f"✓ Code {code}: {info['nome']}")
                assert "subitens" in info, f"Code {code} should have subitens"
                print(f"  └── {len(info['subitens'])} subitens available")
        
        assert portaria_found, "At least one code should reference Portaria 448"
        print("✓ Portaria 448 reference found in classification codes")


# ==============================================================================
# TEST 3: Process creation with all fields (secretaria, secretario, responsavel)
# ==============================================================================

class TestProcessoCreation:
    """Tests for process creation with all fields"""
    
    def test_create_processo_with_all_fields(self, authenticated_headers):
        """Test creating a process with secretaria, secretario, responsavel fields"""
        unique_id = uuid.uuid4().hex[:8]
        
        processo_data = {
            "numero_processo": f"TEST-{unique_id}/2025",
            "modalidade_contratacao": "Pregão Eletrônico",
            "status": "Em Elaboração",
            "objeto": "Teste de criação de processo com todos os campos",
            "secretaria": "Secretaria de Administração",
            "secretario": "João da Silva",
            "responsavel": "Maria de Souza",
            "ano": 2025,
            "observacoes": "Processo de teste"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/processos",
            json=processo_data,
            headers=authenticated_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        created = response.json()
        
        # Verify all fields were saved
        assert created.get("secretaria") == processo_data["secretaria"], \
            f"Secretaria not saved correctly. Expected: {processo_data['secretaria']}, Got: {created.get('secretaria')}"
        
        assert created.get("secretario") == processo_data["secretario"], \
            f"Secretario not saved correctly. Expected: {processo_data['secretario']}, Got: {created.get('secretario')}"
        
        assert created.get("responsavel") == processo_data["responsavel"], \
            f"Responsavel not saved correctly. Expected: {processo_data['responsavel']}, Got: {created.get('responsavel')}"
        
        print(f"✓ Processo created with ID: {created.get('processo_id')}")
        print(f"  └── secretaria: {created.get('secretaria')}")
        print(f"  └── secretario: {created.get('secretario')}")
        print(f"  └── responsavel: {created.get('responsavel')}")
        
        # Verify via GET
        processo_id = created.get("processo_id")
        get_response = requests.get(
            f"{BASE_URL}/api/processos/{processo_id}",
            headers=authenticated_headers
        )
        
        assert get_response.status_code == 200, f"GET failed with status {get_response.status_code}"
        
        fetched = get_response.json()
        assert fetched.get("secretaria") == processo_data["secretaria"], "Secretaria not persisted"
        assert fetched.get("secretario") == processo_data["secretario"], "Secretario not persisted"
        assert fetched.get("responsavel") == processo_data["responsavel"], "Responsavel not persisted"
        
        print("✓ All fields persisted correctly (verified via GET)")
        
        # Cleanup - delete test processo
        delete_response = requests.delete(
            f"{BASE_URL}/api/processos/{processo_id}",
            headers=authenticated_headers
        )
        if delete_response.status_code in [200, 204]:
            print(f"✓ Test processo cleaned up")


# ==============================================================================
# TEST 4: Frontend route /portal-publico
# ==============================================================================

class TestPortalPublicoRoute:
    """Tests for /portal-publico route"""
    
    def test_portal_publico_route_loads(self):
        """Test that /portal-publico route returns HTML"""
        response = requests.get(f"{BASE_URL}/portal-publico")
        
        # Should return 200 and HTML content
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "text/html" in response.headers.get("Content-Type", ""), \
            "Expected HTML content type"
        
        print("✓ /portal-publico route loads correctly")
    
    def test_transparencia_route_loads(self):
        """Test that /transparencia route also works (alias)"""
        response = requests.get(f"{BASE_URL}/transparencia")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ /transparencia route loads correctly")
    
    def test_root_route_loads_portal(self):
        """Test that / (root) loads the public portal"""
        response = requests.get(f"{BASE_URL}/")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ / (root) route loads correctly")


# ==============================================================================
# TEST 5: Public processos endpoint
# ==============================================================================

class TestPublicProcessos:
    """Tests for public processos endpoint"""
    
    def test_public_processos_endpoint(self):
        """Test public processos endpoint without authentication"""
        response = requests.get(f"{BASE_URL}/api/public/processos")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "data" in data or isinstance(data, list), "Response should contain data"
        
        print(f"✓ Public processos endpoint working")
        
        if "data" in data:
            print(f"  └── Found {len(data['data'])} processos")
        elif isinstance(data, list):
            print(f"  └── Found {len(data)} processos")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
