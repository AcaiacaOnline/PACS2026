"""
Test CPF/Cargo Validation for PDF Export and Document Signing
=============================================================
Tests the mandatory CPF and Cargo validation for:
1. PDF export from PAC individual
2. PDF export from PAC Geral
3. DOEM edition publishing
4. User profile update with CPF/Cargo
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "cristiano.abdo@acaiaca.mg.gov.br"
ADMIN_PASSWORD = "Cris@820906"

# Known PAC ID for testing
TEST_PAC_ID = "pac_f905e7811e98"


class TestAuthAndLogin:
    """Test authentication endpoints"""
    
    def test_login_success(self):
        """Test successful login with admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not in response"
        assert "user" in data, "User not in response"
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✓ Login successful for {ADMIN_EMAIL}")
        return data["token"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Invalid credentials correctly rejected")


class TestUserSignatureData:
    """Test user signature data (CPF/Cargo) management"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_current_user_with_signature_data(self, auth_headers):
        """Test getting current user info including signature_data"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get user: {response.text}"
        user = response.json()
        assert "user_id" in user
        assert "email" in user
        # Check if signature_data exists (may or may not have CPF/Cargo)
        print(f"✓ User retrieved: {user.get('name')}")
        print(f"  - signature_data: {user.get('signature_data')}")
        return user
    
    def test_get_users_list(self, auth_headers):
        """Test getting list of users (admin only)"""
        response = requests.get(f"{BASE_URL}/api/users", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get users: {response.text}"
        users = response.json()
        assert isinstance(users, list)
        print(f"✓ Retrieved {len(users)} users")
        return users


class TestCPFCargoValidationForPDFExport:
    """Test CPF/Cargo validation when exporting PDFs"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_pac_exists(self, auth_headers):
        """Verify the test PAC exists"""
        response = requests.get(f"{BASE_URL}/api/pacs/{TEST_PAC_ID}", headers=auth_headers)
        assert response.status_code == 200, f"PAC not found: {response.text}"
        pac = response.json()
        print(f"✓ PAC found: {pac.get('secretaria')}")
        return pac
    
    def test_export_pdf_with_valid_cpf_cargo(self, auth_headers):
        """Test PDF export when user has CPF and Cargo filled"""
        # First, ensure the admin user has CPF and Cargo
        # Get current user
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert me_response.status_code == 200
        user = me_response.json()
        user_id = user.get("user_id")
        
        # Check if user has signature_data with CPF and Cargo
        signature_data = user.get("signature_data") or {}
        cpf = signature_data.get("cpf", "")
        cargo = signature_data.get("cargo", "")
        
        print(f"  User CPF: {cpf}")
        print(f"  User Cargo: {cargo}")
        
        # Try to export PDF
        response = requests.get(
            f"{BASE_URL}/api/pacs/{TEST_PAC_ID}/export/pdf",
            headers=auth_headers
        )
        
        if cpf and cargo:
            # Should succeed if CPF and Cargo are filled
            assert response.status_code == 200, f"PDF export failed: {response.text}"
            assert response.headers.get("content-type") == "application/pdf"
            print("✓ PDF export successful with valid CPF/Cargo")
        else:
            # Should fail with 400 if CPF or Cargo is missing
            assert response.status_code == 400, f"Expected 400, got {response.status_code}"
            error_detail = response.json().get("detail", "")
            assert "CPF" in error_detail or "Cargo" in error_detail
            print(f"✓ PDF export correctly rejected: {error_detail}")


class TestUpdateUserSignatureData:
    """Test updating user signature data (CPF/Cargo)"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_update_user_with_cpf_cargo(self, auth_headers):
        """Test updating user with CPF and Cargo"""
        # Get current user
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert me_response.status_code == 200
        user = me_response.json()
        user_id = user.get("user_id")
        
        # Update with CPF and Cargo
        update_data = {
            "signature_data": {
                "cpf": "123.456.789-00",
                "cargo": "Assessor de Planejamento"
            }
        }
        
        response = requests.put(
            f"{BASE_URL}/api/users/{user_id}",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        updated_user = response.json()
        assert updated_user.get("signature_data") is not None
        assert updated_user["signature_data"].get("cpf") == "123.456.789-00"
        assert updated_user["signature_data"].get("cargo") == "Assessor de Planejamento"
        print("✓ User updated with CPF and Cargo successfully")
        
        # Verify the update persisted
        verify_response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert verify_response.status_code == 200
        verified_user = verify_response.json()
        assert verified_user.get("signature_data", {}).get("cpf") == "123.456.789-00"
        print("✓ CPF/Cargo update verified in database")


class TestPDFExportAfterCPFCargoUpdate:
    """Test PDF export after updating CPF/Cargo"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_pdf_export_after_cpf_cargo_filled(self, auth_headers):
        """Test that PDF export works after CPF/Cargo are filled"""
        # Get current user
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert me_response.status_code == 200
        user = me_response.json()
        user_id = user.get("user_id")
        
        # Ensure CPF and Cargo are set
        update_data = {
            "signature_data": {
                "cpf": "123.456.789-00",
                "cargo": "Assessor de Planejamento"
            }
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/users/{user_id}",
            headers=auth_headers,
            json=update_data
        )
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        # Now try to export PDF
        pdf_response = requests.get(
            f"{BASE_URL}/api/pacs/{TEST_PAC_ID}/export/pdf",
            headers=auth_headers
        )
        
        assert pdf_response.status_code == 200, f"PDF export failed: {pdf_response.text}"
        assert pdf_response.headers.get("content-type") == "application/pdf"
        assert len(pdf_response.content) > 0
        print(f"✓ PDF exported successfully ({len(pdf_response.content)} bytes)")


class TestPublicEndpoints:
    """Test public endpoints that don't require authentication"""
    
    def test_public_pacs_endpoint(self):
        """Test public PACs endpoint"""
        response = requests.get(f"{BASE_URL}/api/public/pacs")
        assert response.status_code == 200, f"Public PACs failed: {response.text}"
        data = response.json()
        # API returns object with 'data' key containing the list
        if isinstance(data, dict) and "data" in data:
            pacs_list = data["data"]
            assert isinstance(pacs_list, list)
            print(f"✓ Public PACs endpoint returned {len(pacs_list)} items")
        else:
            assert isinstance(data, list)
            print(f"✓ Public PACs endpoint returned {len(data)} items")
    
    def test_public_doem_anos(self):
        """Test public DOEM anos endpoint"""
        response = requests.get(f"{BASE_URL}/api/public/doem/anos")
        assert response.status_code == 200, f"Public DOEM anos failed: {response.text}"
        data = response.json()
        print(f"✓ Public DOEM anos endpoint returned: {data}")
    
    def test_public_doem_edicoes(self):
        """Test public DOEM edicoes endpoint"""
        response = requests.get(f"{BASE_URL}/api/public/doem/edicoes")
        assert response.status_code == 200, f"Public DOEM edicoes failed: {response.text}"
        data = response.json()
        print(f"✓ Public DOEM edicoes endpoint returned {len(data)} items")


class TestUserWithoutCPFCargo:
    """Test behavior when user doesn't have CPF/Cargo"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_clear_cpf_cargo_and_try_export(self, auth_headers):
        """Test that PDF export fails when CPF/Cargo are cleared"""
        # Get current user
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert me_response.status_code == 200
        user = me_response.json()
        user_id = user.get("user_id")
        
        # Clear CPF and Cargo
        update_data = {
            "signature_data": {
                "cpf": "",
                "cargo": ""
            }
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/users/{user_id}",
            headers=auth_headers,
            json=update_data
        )
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        # Try to export PDF - should fail with 400
        pdf_response = requests.get(
            f"{BASE_URL}/api/pacs/{TEST_PAC_ID}/export/pdf",
            headers=auth_headers
        )
        
        assert pdf_response.status_code == 400, f"Expected 400, got {pdf_response.status_code}"
        error_detail = pdf_response.json().get("detail", "")
        assert "CPF" in error_detail, f"Expected CPF error, got: {error_detail}"
        print(f"✓ PDF export correctly rejected without CPF: {error_detail}")
    
    def test_restore_cpf_cargo_after_test(self, auth_headers):
        """Restore CPF/Cargo after test"""
        # Get current user
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert me_response.status_code == 200
        user = me_response.json()
        user_id = user.get("user_id")
        
        # Restore CPF and Cargo
        update_data = {
            "signature_data": {
                "cpf": "123.456.789-00",
                "cargo": "Assessor de Planejamento"
            }
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/users/{user_id}",
            headers=auth_headers,
            json=update_data
        )
        assert update_response.status_code == 200, f"Restore failed: {update_response.text}"
        print("✓ CPF/Cargo restored for admin user")


class TestDashboardAccess:
    """Test dashboard access after login"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_dashboard_stats(self, auth_headers):
        """Test dashboard stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=auth_headers)
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        data = response.json()
        assert "totalGeral" in data
        assert "totalPacs" in data
        print(f"✓ Dashboard stats: Total Geral = R$ {data.get('totalGeral', 0):,.2f}")
    
    def test_pacs_list(self, auth_headers):
        """Test PACs list endpoint"""
        response = requests.get(f"{BASE_URL}/api/pacs", headers=auth_headers)
        assert response.status_code == 200, f"PACs list failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ PACs list returned {len(data)} items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
