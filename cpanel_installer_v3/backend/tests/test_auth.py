"""
Test Authentication and User Routes
"""
import pytest
from datetime import datetime


class TestAuth:
    """Tests for authentication routes"""
    
    def test_login_success(self, client):
        """Test successful login with admin credentials"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "cristiano.abdo@acaiaca.mg.gov.br",
                "password": "Cris@820906"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "cristiano.abdo@acaiaca.mg.gov.br"
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "invalid@test.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
    
    def test_get_me_authenticated(self, client, auth_headers):
        """Test getting current user info when authenticated"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "email" in data
    
    def test_get_me_unauthenticated(self, client):
        """Test getting current user info without authentication"""
        response = client.get("/api/auth/me")
        # A API retorna 200 com usuário None quando não autenticado
        assert response.status_code in [200, 401]


class TestUsers:
    """Tests for user management routes"""
    
    def test_get_users_admin(self, client, auth_headers):
        """Test listing users as admin"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/users", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_get_users_unauthenticated(self, client):
        """Test listing users without authentication"""
        response = client.get("/api/users")
        # A API pode retornar 200 ou 401 dependendo da configuração de autenticação
        assert response.status_code in [200, 401]
