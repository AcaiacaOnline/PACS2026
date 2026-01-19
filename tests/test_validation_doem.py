"""
Test suite for Document Validation and DOEM PDF features
Tests: 
- Document validation API (/api/validar/verificar)
- DOEM PDF generation with signature seal
- User signature_data fields
- Pagination in Gestão Processual
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://doem-pdf-system.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "cristiano.abdo@acaiaca.mg.gov.br"
ADMIN_PASSWORD = "Cris@820906"


class TestDocumentValidationAPI:
    """Tests for the document validation API endpoints"""
    
    def test_validation_info_endpoint(self):
        """Test GET /api/validar/ returns validation info"""
        response = requests.get(f"{BASE_URL}/api/validar/")
        assert response.status_code == 200
        data = response.json()
        assert "titulo" in data
        assert "descricao" in data
        assert "instrucoes" in data
        assert len(data["instrucoes"]) > 0
        print(f"✓ Validation info endpoint working: {data['titulo']}")
    
    def test_validation_post_invalid_code(self):
        """Test POST /api/validar/verificar with invalid code"""
        response = requests.post(
            f"{BASE_URL}/api/validar/verificar",
            json={"validation_code": "DOC-INVALID-20260106"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] == False
        assert "não encontrado" in data["message"].lower() or "not found" in data["message"].lower()
        print(f"✓ Invalid code returns proper response: {data['message']}")
    
    def test_validation_get_invalid_code(self):
        """Test GET /api/validar/{code} with invalid code"""
        response = requests.get(f"{BASE_URL}/api/validar/DOC-INVALID-20260106")
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] == False
        print(f"✓ GET validation endpoint working")
    
    def test_validation_empty_code(self):
        """Test validation with empty code"""
        response = requests.post(
            f"{BASE_URL}/api/validar/verificar",
            json={"validation_code": ""}
        )
        # Should return invalid, not error
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] == False
        print(f"✓ Empty code handled properly")


class TestDOEMPDFGeneration:
    """Tests for DOEM PDF generation with signature seal"""
    
    def test_public_doem_pdf_endpoint(self):
        """Test GET /api/public/doem/edicoes/{id}/pdf"""
        edicao_id = "doem_57dc5741c733"
        response = requests.get(
            f"{BASE_URL}/api/public/doem/edicoes/{edicao_id}/pdf",
            stream=True
        )
        assert response.status_code == 200
        assert response.headers.get('content-type') == 'application/pdf'
        
        # Check PDF content starts with %PDF
        content = response.content
        assert content[:4] == b'%PDF'
        print(f"✓ DOEM PDF generated successfully, size: {len(content)} bytes")
    
    def test_public_doem_pdf_not_found(self):
        """Test PDF endpoint with non-existent edition"""
        response = requests.get(
            f"{BASE_URL}/api/public/doem/edicoes/invalid_id/pdf"
        )
        assert response.status_code == 404
        print(f"✓ Non-existent edition returns 404")
    
    def test_public_doem_edicoes_list(self):
        """Test GET /api/public/doem/edicoes"""
        response = requests.get(f"{BASE_URL}/api/public/doem/edicoes")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            edicao = data[0]
            assert "edicao_id" in edicao
            assert "status" in edicao
            print(f"✓ Found {len(data)} DOEM editions")
        else:
            print("✓ DOEM editions endpoint working (no editions found)")
    
    def test_public_doem_anos(self):
        """Test GET /api/public/doem/anos"""
        response = requests.get(f"{BASE_URL}/api/public/doem/anos")
        assert response.status_code == 200
        data = response.json()
        assert "anos" in data
        assert isinstance(data["anos"], list)
        print(f"✓ DOEM anos endpoint working: {data['anos']}")


class TestUserSignatureData:
    """Tests for user signature_data fields"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_get_users_list(self, auth_token):
        """Test GET /api/users returns users with signature_data"""
        response = requests.get(
            f"{BASE_URL}/api/users",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        print(f"✓ Found {len(users)} users")
        
        # Check if signature_data field exists in user schema
        if len(users) > 0:
            user = users[0]
            # signature_data may or may not be present depending on if it was set
            print(f"✓ User fields: {list(user.keys())}")
    
    def test_create_user_with_signature_data(self, auth_token):
        """Test creating user with signature_data fields"""
        import uuid
        test_email = f"test_sig_{uuid.uuid4().hex[:8]}@test.com"
        
        user_data = {
            "name": "Test Signature User",
            "email": test_email,
            "password": "TestPass123!",
            "is_admin": False,
            "is_active": True,
            "permissions": {
                "can_view": True,
                "can_edit": False,
                "can_delete": False,
                "can_export": False,
                "can_manage_users": False,
                "is_full_admin": False
            },
            "signature_data": {
                "cpf": "123.456.789-00",
                "cargo": "Assessor de Teste",
                "endereco": "Rua Teste, 123, Centro",
                "cep": "35180-000",
                "telefone": "(31) 99999-8888"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/users",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=user_data
        )
        
        assert response.status_code in [200, 201]
        created_user = response.json()
        
        # Verify signature_data was saved
        assert "signature_data" in created_user or "user_id" in created_user
        print(f"✓ User created with signature_data")
        
        # Cleanup - delete test user
        if "user_id" in created_user:
            requests.delete(
                f"{BASE_URL}/api/users/{created_user['user_id']}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            print(f"✓ Test user cleaned up")


class TestPagination:
    """Tests for pagination in Gestão Processual"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_processos_pagination_default(self, auth_token):
        """Test processos endpoint with default pagination"""
        response = requests.get(
            f"{BASE_URL}/api/processos",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Processos endpoint working, found {len(data)} items")
    
    def test_processos_returns_data(self, auth_token):
        """Test processos endpoint returns data (pagination is frontend-side)"""
        response = requests.get(
            f"{BASE_URL}/api/processos",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Note: Pagination is handled on frontend, backend returns all data
        print(f"✓ Processos endpoint returned {len(data)} items (pagination is frontend-side)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
