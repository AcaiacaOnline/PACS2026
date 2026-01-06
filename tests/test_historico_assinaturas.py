"""
Test suite for Histórico de Assinaturas feature
Tests the signature history endpoints: /api/assinaturas/historico and /api/assinaturas/estatisticas
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHistoricoAssinaturas:
    """Tests for signature history endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "cristiano.abdo@acaiaca.mg.gov.br",
                "password": "Cris@820906"
            }
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json().get('token')
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_historico_endpoint_returns_200(self):
        """Test GET /api/assinaturas/historico returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/assinaturas/historico",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_historico_returns_paginated_response(self):
        """Test that historico endpoint returns paginated response structure"""
        response = requests.get(
            f"{BASE_URL}/api/assinaturas/historico?page=1&page_size=10",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check pagination structure
        assert 'items' in data, "Response should have 'items' field"
        assert 'total' in data, "Response should have 'total' field"
        assert 'page' in data, "Response should have 'page' field"
        assert 'page_size' in data, "Response should have 'page_size' field"
        assert 'total_pages' in data, "Response should have 'total_pages' field"
        
        # Verify types
        assert isinstance(data['items'], list), "'items' should be a list"
        assert isinstance(data['total'], int), "'total' should be an integer"
        assert isinstance(data['page'], int), "'page' should be an integer"
        assert isinstance(data['page_size'], int), "'page_size' should be an integer"
        assert isinstance(data['total_pages'], int), "'total_pages' should be an integer"
    
    def test_historico_item_structure(self):
        """Test that each signature item has the correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/assinaturas/historico?page=1&page_size=10",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data['items']) > 0:
            item = data['items'][0]
            
            # Check required fields
            assert 'signature_id' in item, "Item should have 'signature_id'"
            assert 'document_id' in item, "Item should have 'document_id'"
            assert 'document_type' in item, "Item should have 'document_type'"
            assert 'validation_code' in item, "Item should have 'validation_code'"
            assert 'created_at' in item, "Item should have 'created_at'"
            assert 'is_valid' in item, "Item should have 'is_valid'"
            assert 'total_signers' in item, "Item should have 'total_signers'"
            assert 'my_signature' in item, "Item should have 'my_signature'"
            
            # Check my_signature structure
            my_sig = item['my_signature']
            assert 'nome' in my_sig, "my_signature should have 'nome'"
            assert 'cargo' in my_sig, "my_signature should have 'cargo'"
            assert 'cpf_masked' in my_sig, "my_signature should have 'cpf_masked'"
    
    def test_historico_pagination_works(self):
        """Test that pagination parameters work correctly"""
        # Get first page with page_size=1
        response = requests.get(
            f"{BASE_URL}/api/assinaturas/historico?page=1&page_size=1",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data['page'] == 1, "Page should be 1"
        assert data['page_size'] == 1, "Page size should be 1"
        assert len(data['items']) <= 1, "Should return at most 1 item"
    
    def test_estatisticas_endpoint_returns_200(self):
        """Test GET /api/assinaturas/estatisticas returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/assinaturas/estatisticas",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_estatisticas_returns_correct_structure(self):
        """Test that estatisticas endpoint returns correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/assinaturas/estatisticas",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert 'total_assinaturas' in data, "Response should have 'total_assinaturas'"
        assert 'assinaturas_validas' in data, "Response should have 'assinaturas_validas'"
        assert 'assinaturas_invalidas' in data, "Response should have 'assinaturas_invalidas'"
        assert 'ultimos_30_dias' in data, "Response should have 'ultimos_30_dias'"
        assert 'por_tipo' in data, "Response should have 'por_tipo'"
        
        # Verify types
        assert isinstance(data['total_assinaturas'], int), "'total_assinaturas' should be an integer"
        assert isinstance(data['assinaturas_validas'], int), "'assinaturas_validas' should be an integer"
        assert isinstance(data['assinaturas_invalidas'], int), "'assinaturas_invalidas' should be an integer"
        assert isinstance(data['ultimos_30_dias'], int), "'ultimos_30_dias' should be an integer"
        assert isinstance(data['por_tipo'], list), "'por_tipo' should be a list"
    
    def test_estatisticas_por_tipo_structure(self):
        """Test that por_tipo items have correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/assinaturas/estatisticas",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data['por_tipo']) > 0:
            tipo = data['por_tipo'][0]
            assert 'tipo' in tipo, "por_tipo item should have 'tipo'"
            assert 'quantidade' in tipo, "por_tipo item should have 'quantidade'"
    
    def test_estatisticas_ultima_assinatura(self):
        """Test that ultima_assinatura is present when there are signatures"""
        response = requests.get(
            f"{BASE_URL}/api/assinaturas/estatisticas",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if data['total_assinaturas'] > 0:
            assert 'ultima_assinatura' in data, "Should have 'ultima_assinatura' when there are signatures"
            ultima = data['ultima_assinatura']
            if ultima:
                assert 'document_type' in ultima, "ultima_assinatura should have 'document_type'"
                assert 'validation_code' in ultima, "ultima_assinatura should have 'validation_code'"
                assert 'created_at' in ultima, "ultima_assinatura should have 'created_at'"
    
    def test_historico_requires_authentication(self):
        """Test that historico endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/assinaturas/historico")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
    
    def test_estatisticas_requires_authentication(self):
        """Test that estatisticas endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/assinaturas/estatisticas")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
    
    def test_data_consistency(self):
        """Test that historico and estatisticas data are consistent"""
        # Get historico
        historico_response = requests.get(
            f"{BASE_URL}/api/assinaturas/historico?page=1&page_size=100",
            headers=self.headers
        )
        assert historico_response.status_code == 200
        historico_data = historico_response.json()
        
        # Get estatisticas
        estatisticas_response = requests.get(
            f"{BASE_URL}/api/assinaturas/estatisticas",
            headers=self.headers
        )
        assert estatisticas_response.status_code == 200
        estatisticas_data = estatisticas_response.json()
        
        # Total should match
        assert historico_data['total'] == estatisticas_data['total_assinaturas'], \
            f"Total mismatch: historico={historico_data['total']}, estatisticas={estatisticas_data['total_assinaturas']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
