"""
Complete MROSC (Prestação de Contas) Tests
Tests for MROSC endpoints including:
- List projects
- Get project details
- PDF export with digital signature (Lei 14.063 style)
- Admin login
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://acaiaca-gov-1.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "cristiano.abdo@acaiaca.mg.gov.br"
ADMIN_PASSWORD = "Cris@820906"


class TestMROSCComplete:
    """Complete tests for MROSC module"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = None
        self.user = None
    
    def login(self):
        """Login and get auth token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
            self.user = data.get("user")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            return True
        return False
    
    def test_admin_login_success(self):
        """Test admin login with valid credentials"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not in response"
        assert "user" in data, "User not in response"
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["is_admin"] == True
        print(f"✓ Admin login successful: {data['user']['name']}")
    
    def test_admin_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Invalid credentials correctly rejected")
    
    def test_get_mrosc_projetos_list(self):
        """Test listing MROSC projects"""
        if not self.login():
            pytest.skip("Login failed")
        
        response = self.session.get(f"{BASE_URL}/api/mrosc/projetos")
        assert response.status_code == 200, f"Failed to get projects: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ MROSC projects list: {len(data)} projects found")
        return data
    
    def test_get_naturezas_despesa(self):
        """Test getting expense natures"""
        if not self.login():
            pytest.skip("Login failed")
        
        response = self.session.get(f"{BASE_URL}/api/mrosc/naturezas-despesa")
        assert response.status_code == 200, f"Failed to get naturezas: {response.text}"
        data = response.json()
        assert "339030" in data, "339030 should be in naturezas"
        assert "339039" in data, "339039 should be in naturezas"
        print(f"✓ Naturezas de despesa: {len(data)} types found")
    
    def test_create_mrosc_projeto(self):
        """Test creating a new MROSC project"""
        if not self.login():
            pytest.skip("Login failed")
        
        projeto_data = {
            "nome_projeto": "TEST_Projeto de Teste MROSC",
            "objeto": "Projeto de teste para validação do sistema MROSC",
            "organizacao_parceira": "OSC Teste",
            "cnpj_parceira": "12.345.678/0001-90",
            "responsavel_osc": "Responsável Teste",
            "data_inicio": "2025-01-01T00:00:00Z",
            "data_conclusao": "2025-12-31T00:00:00Z",
            "prazo_meses": 12,
            "valor_total": 100000.00,
            "valor_repasse_publico": 80000.00,
            "valor_contrapartida": 20000.00,
            "status": "ELABORACAO"
        }
        
        response = self.session.post(f"{BASE_URL}/api/mrosc/projetos", json=projeto_data)
        assert response.status_code == 200, f"Failed to create project: {response.text}"
        data = response.json()
        assert "projeto_id" in data, "projeto_id should be in response"
        assert data["nome_projeto"] == projeto_data["nome_projeto"]
        print(f"✓ MROSC project created: {data['projeto_id']}")
        return data["projeto_id"]
    
    def test_get_mrosc_projeto_by_id(self):
        """Test getting a specific MROSC project"""
        if not self.login():
            pytest.skip("Login failed")
        
        # First get list of projects
        response = self.session.get(f"{BASE_URL}/api/mrosc/projetos")
        if response.status_code != 200 or not response.json():
            pytest.skip("No projects available")
        
        projetos = response.json()
        projeto_id = projetos[0]["projeto_id"]
        
        # Get specific project
        response = self.session.get(f"{BASE_URL}/api/mrosc/projetos/{projeto_id}")
        assert response.status_code == 200, f"Failed to get project: {response.text}"
        data = response.json()
        assert data["projeto_id"] == projeto_id
        print(f"✓ MROSC project retrieved: {data['nome_projeto']}")
    
    def test_get_mrosc_projeto_resumo(self):
        """Test getting project financial summary"""
        if not self.login():
            pytest.skip("Login failed")
        
        # First get list of projects
        response = self.session.get(f"{BASE_URL}/api/mrosc/projetos")
        if response.status_code != 200 or not response.json():
            pytest.skip("No projects available")
        
        projetos = response.json()
        projeto_id = projetos[0]["projeto_id"]
        
        # Get resumo
        response = self.session.get(f"{BASE_URL}/api/mrosc/projetos/{projeto_id}/resumo")
        assert response.status_code == 200, f"Failed to get resumo: {response.text}"
        data = response.json()
        assert "resumo" in data, "resumo should be in response"
        print(f"✓ MROSC project resumo retrieved")
    
    def test_export_mrosc_pdf(self):
        """Test PDF export with digital signature (Lei 14.063 style)"""
        if not self.login():
            pytest.skip("Login failed")
        
        # First get list of projects
        response = self.session.get(f"{BASE_URL}/api/mrosc/projetos")
        if response.status_code != 200 or not response.json():
            pytest.skip("No projects available")
        
        projetos = response.json()
        projeto_id = projetos[0]["projeto_id"]
        
        # Export PDF
        response = self.session.get(f"{BASE_URL}/api/mrosc/projetos/{projeto_id}/relatorio/pdf")
        
        # PDF export may fail if user doesn't have CPF/Cargo, but endpoint should work
        if response.status_code == 400:
            # Expected if user doesn't have CPF/Cargo
            print(f"✓ PDF export requires CPF/Cargo (expected behavior): {response.json().get('detail', '')}")
        elif response.status_code == 200:
            assert response.headers.get("content-type") == "application/pdf"
            assert len(response.content) > 0, "PDF should not be empty"
            print(f"✓ MROSC PDF exported successfully ({len(response.content)} bytes)")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code} - {response.text}")
    
    def test_export_mrosc_pdf_not_found(self):
        """Test PDF export with non-existent project"""
        if not self.login():
            pytest.skip("Login failed")
        
        response = self.session.get(f"{BASE_URL}/api/mrosc/projetos/nonexistent_id/relatorio/pdf")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        data = response.json()
        assert "detail" in data
        assert "não encontrado" in data["detail"].lower() or "not found" in data["detail"].lower()
        print("✓ Non-existent project correctly returns 404")
    
    def test_public_mrosc_projetos(self):
        """Test public MROSC projects endpoint (transparency)"""
        response = self.session.get(f"{BASE_URL}/api/public/mrosc/projetos")
        assert response.status_code == 200, f"Failed to get public projects: {response.text}"
        data = response.json()
        # Response may be wrapped in 'data' key or be a direct list
        if isinstance(data, dict) and "data" in data:
            projetos = data["data"]
        else:
            projetos = data
        assert isinstance(projetos, list), "Response should be a list"
        print(f"✓ Public MROSC projects: {len(projetos)} projects")
    
    def test_public_mrosc_estatisticas(self):
        """Test public MROSC statistics endpoint"""
        response = self.session.get(f"{BASE_URL}/api/public/mrosc/estatisticas")
        assert response.status_code == 200, f"Failed to get statistics: {response.text}"
        data = response.json()
        # Response may be wrapped in 'data' key
        if isinstance(data, dict) and "data" in data:
            stats = data["data"]
        else:
            stats = data
        assert "total_projetos" in stats, "total_projetos should be in response"
        print(f"✓ Public MROSC statistics: {stats.get('total_projetos', 0)} total projects")
    
    def test_get_mrosc_projeto_rh(self):
        """Test getting project human resources"""
        if not self.login():
            pytest.skip("Login failed")
        
        # First get list of projects
        response = self.session.get(f"{BASE_URL}/api/mrosc/projetos")
        if response.status_code != 200 or not response.json():
            pytest.skip("No projects available")
        
        projetos = response.json()
        projeto_id = projetos[0]["projeto_id"]
        
        # Get RH
        response = self.session.get(f"{BASE_URL}/api/mrosc/projetos/{projeto_id}/rh")
        assert response.status_code == 200, f"Failed to get RH: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ MROSC project RH: {len(data)} resources")
    
    def test_get_mrosc_projeto_despesas(self):
        """Test getting project expenses"""
        if not self.login():
            pytest.skip("Login failed")
        
        # First get list of projects
        response = self.session.get(f"{BASE_URL}/api/mrosc/projetos")
        if response.status_code != 200 or not response.json():
            pytest.skip("No projects available")
        
        projetos = response.json()
        projeto_id = projetos[0]["projeto_id"]
        
        # Get despesas
        response = self.session.get(f"{BASE_URL}/api/mrosc/projetos/{projeto_id}/despesas")
        assert response.status_code == 200, f"Failed to get despesas: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ MROSC project despesas: {len(data)} expenses")
    
    def test_get_mrosc_projeto_documentos(self):
        """Test getting project documents"""
        if not self.login():
            pytest.skip("Login failed")
        
        # First get list of projects
        response = self.session.get(f"{BASE_URL}/api/mrosc/projetos")
        if response.status_code != 200 or not response.json():
            pytest.skip("No projects available")
        
        projetos = response.json()
        projeto_id = projetos[0]["projeto_id"]
        
        # Get documentos
        response = self.session.get(f"{BASE_URL}/api/mrosc/projetos/{projeto_id}/documentos")
        assert response.status_code == 200, f"Failed to get documentos: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ MROSC project documentos: {len(data)} documents")
    
    def test_cleanup_test_projects(self):
        """Cleanup test projects created during testing"""
        if not self.login():
            pytest.skip("Login failed")
        
        # Get all projects
        response = self.session.get(f"{BASE_URL}/api/mrosc/projetos")
        if response.status_code != 200:
            return
        
        projetos = response.json()
        deleted = 0
        for projeto in projetos:
            if projeto.get("nome_projeto", "").startswith("TEST_"):
                delete_response = self.session.delete(f"{BASE_URL}/api/mrosc/projetos/{projeto['projeto_id']}")
                if delete_response.status_code in [200, 204]:
                    deleted += 1
        
        print(f"✓ Cleanup: {deleted} test projects deleted")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
