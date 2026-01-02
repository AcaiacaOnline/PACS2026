"""
Test suite for DOEM Newsletter and Segmentos features
Tests the following endpoints:
- GET /api/doem/segmentos - returns 9 segments
- POST /api/newsletter/inscritos - add manual subscriber (admin)
- GET /api/newsletter/inscritos - list subscribers (admin)
- GET /api/newsletter/estatisticas - newsletter statistics (admin)
- PUT /api/newsletter/inscritos/{id}/toggle - toggle subscriber status
- DELETE /api/newsletter/inscritos/{id} - remove subscriber
- POST /api/public/newsletter/inscrever - public subscription
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Expected 9 segments
EXPECTED_SEGMENTOS = [
    "Portarias",
    "Leis",
    "Decretos",
    "Resoluções",
    "Editais",
    "Prestações de Contas",
    "Processos Administrativos",
    "Publicações do Legislativo",
    "Publicações do Terceiro Setor"
]


class TestDOEMSegmentos:
    """Tests for DOEM Segmentos endpoint"""
    
    def test_get_segmentos_returns_9_segments(self, auth_token):
        """GET /api/doem/segmentos should return exactly 9 segments"""
        response = requests.get(
            f"{BASE_URL}/api/doem/segmentos",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'segmentos' in data, "Response should contain 'segmentos' key"
        
        segmentos = data['segmentos']
        assert len(segmentos) == 9, f"Expected 9 segments, got {len(segmentos)}"
        
        # Verify all expected segments are present
        for seg in EXPECTED_SEGMENTOS:
            assert seg in segmentos, f"Missing segment: {seg}"
    
    def test_get_segmentos_returns_tipos_publicacao(self, auth_token):
        """GET /api/doem/segmentos should return tipos_publicacao mapping"""
        response = requests.get(
            f"{BASE_URL}/api/doem/segmentos",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'tipos_publicacao' in data, "Response should contain 'tipos_publicacao' key"
        tipos = data['tipos_publicacao']
        
        # Verify each segment has types
        for seg in EXPECTED_SEGMENTOS:
            assert seg in tipos, f"tipos_publicacao missing segment: {seg}"
            assert len(tipos[seg]) > 0, f"Segment {seg} should have at least one type"
    
    def test_public_segmentos_endpoint(self):
        """GET /api/public/doem/segmentos should work without auth"""
        response = requests.get(f"{BASE_URL}/api/public/doem/segmentos")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert 'segmentos' in data
        assert len(data['segmentos']) == 9


class TestNewsletterAdmin:
    """Tests for Newsletter admin endpoints (require admin auth)"""
    
    def test_list_inscritos(self, auth_token):
        """GET /api/newsletter/inscritos should list all subscribers"""
        response = requests.get(
            f"{BASE_URL}/api/newsletter/inscritos",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
    
    def test_get_estatisticas(self, auth_token):
        """GET /api/newsletter/estatisticas should return statistics"""
        response = requests.get(
            f"{BASE_URL}/api/newsletter/estatisticas",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'total' in data, "Response should contain 'total'"
        assert 'ativos' in data, "Response should contain 'ativos'"
        assert 'pendentes' in data, "Response should contain 'pendentes'"
        assert 'por_tipo' in data, "Response should contain 'por_tipo'"
        
        # Verify types are integers
        assert isinstance(data['total'], int)
        assert isinstance(data['ativos'], int)
        assert isinstance(data['pendentes'], int)
    
    def test_add_inscrito_manual(self, auth_token):
        """POST /api/newsletter/inscritos should add a manual subscriber"""
        unique_email = f"TEST_manual_{uuid.uuid4().hex[:8]}@acaiaca.mg.gov.br"
        
        payload = {
            "email": unique_email,
            "nome": "TEST Manual Subscriber",
            "segmentos_interesse": ["Portarias", "Decretos"],
            "confirmado": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/newsletter/inscritos",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=payload
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data['email'] == unique_email
        assert data['nome'] == "TEST Manual Subscriber"
        assert data['tipo'] == 'manual'
        assert data['ativo'] == True
        assert data['confirmado'] == True
        assert 'inscrito_id' in data
        
        # Store for cleanup
        return data['inscrito_id']
    
    def test_toggle_inscrito(self, auth_token):
        """PUT /api/newsletter/inscritos/{id}/toggle should toggle status"""
        # First create a subscriber
        unique_email = f"TEST_toggle_{uuid.uuid4().hex[:8]}@acaiaca.mg.gov.br"
        
        create_response = requests.post(
            f"{BASE_URL}/api/newsletter/inscritos",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "email": unique_email,
                "nome": "TEST Toggle Subscriber",
                "segmentos_interesse": [],
                "confirmado": True
            }
        )
        
        assert create_response.status_code == 200
        inscrito_id = create_response.json()['inscrito_id']
        
        # Toggle to inactive
        toggle_response = requests.put(
            f"{BASE_URL}/api/newsletter/inscritos/{inscrito_id}/toggle",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert toggle_response.status_code == 200, f"Expected 200, got {toggle_response.status_code}"
        toggle_data = toggle_response.json()
        assert 'ativo' in toggle_data
        assert toggle_data['ativo'] == False  # Should be toggled to inactive
        
        # Toggle back to active
        toggle_response2 = requests.put(
            f"{BASE_URL}/api/newsletter/inscritos/{inscrito_id}/toggle",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert toggle_response2.status_code == 200
        assert toggle_response2.json()['ativo'] == True
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/newsletter/inscritos/{inscrito_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
    
    def test_delete_inscrito(self, auth_token):
        """DELETE /api/newsletter/inscritos/{id} should remove subscriber"""
        # First create a subscriber
        unique_email = f"TEST_delete_{uuid.uuid4().hex[:8]}@acaiaca.mg.gov.br"
        
        create_response = requests.post(
            f"{BASE_URL}/api/newsletter/inscritos",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "email": unique_email,
                "nome": "TEST Delete Subscriber",
                "segmentos_interesse": [],
                "confirmado": True
            }
        )
        
        assert create_response.status_code == 200
        inscrito_id = create_response.json()['inscrito_id']
        
        # Delete the subscriber
        delete_response = requests.delete(
            f"{BASE_URL}/api/newsletter/inscritos/{inscrito_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}"
        assert 'message' in delete_response.json()
        
        # Verify it's deleted - should not appear in list
        list_response = requests.get(
            f"{BASE_URL}/api/newsletter/inscritos",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        inscritos = list_response.json()
        inscrito_ids = [i['inscrito_id'] for i in inscritos]
        assert inscrito_id not in inscrito_ids, "Deleted subscriber should not appear in list"
    
    def test_delete_nonexistent_inscrito(self, auth_token):
        """DELETE /api/newsletter/inscritos/{id} should return 404 for nonexistent"""
        response = requests.delete(
            f"{BASE_URL}/api/newsletter/inscritos/nonexistent_id_12345",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404


class TestNewsletterPublic:
    """Tests for public newsletter subscription endpoint"""
    
    def test_public_subscription(self):
        """POST /api/public/newsletter/inscrever should create pending subscription"""
        unique_email = f"TEST_public_{uuid.uuid4().hex[:8]}@example.com"
        
        payload = {
            "email": unique_email,
            "nome": "TEST Public Subscriber",
            "segmentos_interesse": ["Leis", "Editais"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/public/newsletter/inscrever",
            json=payload
        )
        
        # Should succeed (200) or return message about confirmation email
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
    
    def test_public_subscription_duplicate(self):
        """POST /api/public/newsletter/inscrever should handle duplicates"""
        unique_email = f"TEST_dup_{uuid.uuid4().hex[:8]}@example.com"
        
        payload = {
            "email": unique_email,
            "nome": "TEST Duplicate Subscriber",
            "segmentos_interesse": []
        }
        
        # First subscription
        response1 = requests.post(
            f"{BASE_URL}/api/public/newsletter/inscrever",
            json=payload
        )
        assert response1.status_code in [200, 201]
        
        # Second subscription with same email
        response2 = requests.post(
            f"{BASE_URL}/api/public/newsletter/inscrever",
            json=payload
        )
        
        # Should return 400 or message about existing subscription
        assert response2.status_code in [200, 400], f"Expected 200 or 400, got {response2.status_code}"


class TestNewsletterUnauthorized:
    """Tests for unauthorized access to admin endpoints"""
    
    def test_list_inscritos_unauthorized(self):
        """GET /api/newsletter/inscritos should require auth"""
        response = requests.get(f"{BASE_URL}/api/newsletter/inscritos")
        assert response.status_code == 401
    
    def test_add_inscrito_unauthorized(self):
        """POST /api/newsletter/inscritos should require auth"""
        response = requests.post(
            f"{BASE_URL}/api/newsletter/inscritos",
            json={"email": "test@test.com", "nome": "Test", "segmentos_interesse": [], "confirmado": True}
        )
        assert response.status_code == 401
    
    def test_estatisticas_unauthorized(self):
        """GET /api/newsletter/estatisticas should require auth"""
        response = requests.get(f"{BASE_URL}/api/newsletter/estatisticas")
        assert response.status_code == 401


# Fixtures
@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": "cristiano.abdo@acaiaca.mg.gov.br",
            "password": "Cris@820906"
        }
    )
    
    if login_response.status_code != 200:
        pytest.skip(f"Authentication failed: {login_response.status_code} - {login_response.text}")
    
    return login_response.json().get("token")


@pytest.fixture(autouse=True, scope="module")
def cleanup_test_data(auth_token):
    """Cleanup TEST_ prefixed data after all tests"""
    yield
    
    # Cleanup: Delete all test-created newsletter subscribers
    try:
        list_response = requests.get(
            f"{BASE_URL}/api/newsletter/inscritos",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        if list_response.status_code == 200:
            inscritos = list_response.json()
            for inscrito in inscritos:
                if inscrito.get('nome', '').startswith('TEST') or inscrito.get('email', '').startswith('TEST'):
                    requests.delete(
                        f"{BASE_URL}/api/newsletter/inscritos/{inscrito['inscrito_id']}",
                        headers={"Authorization": f"Bearer {auth_token}"}
                    )
    except Exception as e:
        print(f"Cleanup error: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
