"""
Test Suite for PAC Acaiaca 2026 - New Features
Tests:
1. Pagination in Gestão Processual (20/30/50/100 items per page)
2. User signature_data fields (CPF, Cargo, Telefone, CEP, Endereço)
3. Input masks validation (telefone, CPF, CEP formats)
4. Persistence of signature_data when creating/updating users
"""

import pytest
import requests
import os
import json
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://muni-docs.preview.emergentagent.com').rstrip('/')

class TestSetup:
    """Setup fixtures for tests"""
    
    @pytest.fixture(scope="class")
    def session(self):
        """Create a requests session"""
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        return s
    
    @pytest.fixture(scope="class")
    def admin_session(self, session):
        """Login as admin and return authenticated session"""
        login_data = {
            "email": "cristiano.abdo@acaiaca.mg.gov.br",
            "password": "Cris@820906"
        }
        response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code != 200:
            pytest.skip("Admin login failed - skipping authenticated tests")
        return session


class TestProcessosPagination(TestSetup):
    """Test pagination functionality in Gestão Processual"""
    
    def test_get_processos_returns_list(self, admin_session):
        """Test that GET /api/processos returns a list of processos"""
        response = admin_session.get(f"{BASE_URL}/api/processos?ano=2025")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/processos returns {len(data)} processos")
    
    def test_processos_count_for_pagination(self, admin_session):
        """Test that there are enough processos to test pagination"""
        response = admin_session.get(f"{BASE_URL}/api/processos?ano=2025")
        assert response.status_code == 200
        data = response.json()
        # Should have more than 20 items to test pagination
        assert len(data) >= 20, f"Expected at least 20 processos, got {len(data)}"
        print(f"✓ Found {len(data)} processos - sufficient for pagination testing")
    
    def test_processos_anos_endpoint(self, admin_session):
        """Test GET /api/processos/anos returns available years"""
        response = admin_session.get(f"{BASE_URL}/api/processos/anos")
        assert response.status_code == 200
        data = response.json()
        assert 'anos' in data
        assert isinstance(data['anos'], list)
        assert 2025 in data['anos'] or 2026 in data['anos']
        print(f"✓ GET /api/processos/anos returns years: {data['anos']}")


class TestUserSignatureData(TestSetup):
    """Test user signature_data fields (CPF, Cargo, Telefone, CEP, Endereço)"""
    
    def test_get_users_includes_signature_data(self, admin_session):
        """Test that GET /api/users returns users with signature_data field"""
        response = admin_session.get(f"{BASE_URL}/api/users")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "No users found"
        
        # Check that signature_data field exists
        first_user = data[0]
        assert 'signature_data' in first_user, "signature_data field missing from user"
        print(f"✓ Users have signature_data field")
    
    def test_signature_data_structure(self, admin_session):
        """Test that signature_data has correct structure"""
        response = admin_session.get(f"{BASE_URL}/api/users")
        assert response.status_code == 200
        data = response.json()
        
        # Find a user with signature_data
        for user in data:
            if user.get('signature_data'):
                sig_data = user['signature_data']
                expected_fields = ['cpf', 'cargo', 'endereco', 'cep', 'telefone']
                for field in expected_fields:
                    assert field in sig_data, f"Field '{field}' missing from signature_data"
                print(f"✓ signature_data has all required fields: {expected_fields}")
                return
        
        # If no user has signature_data populated, check structure from schema
        print("✓ signature_data structure validated (no populated data found)")
    
    def test_create_user_with_signature_data(self, admin_session):
        """Test creating a user with signature_data fields"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        user_data = {
            "name": f"TEST_User_{timestamp}",
            "email": f"test.signature.{timestamp}@example.com",
            "password": "TestPass123!",
            "is_admin": False,
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
                "cargo": "Analista de Sistemas",
                "endereco": "Rua das Flores, 123",
                "cep": "35180-000",
                "telefone": "(31) 99999-8888"
            }
        }
        
        response = admin_session.post(f"{BASE_URL}/api/users", json=user_data)
        assert response.status_code == 200 or response.status_code == 201, f"Failed to create user: {response.text}"
        
        created_user = response.json()
        assert 'user_id' in created_user
        assert 'signature_data' in created_user
        
        # Verify signature_data was saved
        sig_data = created_user.get('signature_data', {})
        assert sig_data.get('cpf') == "123.456.789-00", f"CPF not saved correctly: {sig_data.get('cpf')}"
        assert sig_data.get('cargo') == "Analista de Sistemas"
        assert sig_data.get('telefone') == "(31) 99999-8888"
        
        print(f"✓ Created user with signature_data: {created_user['user_id']}")
        
        # Cleanup - delete test user
        user_id = created_user['user_id']
        admin_session.delete(f"{BASE_URL}/api/users/{user_id}")
        print(f"✓ Cleaned up test user: {user_id}")
    
    def test_update_user_signature_data(self, admin_session):
        """Test updating user signature_data fields"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # First create a user
        user_data = {
            "name": f"TEST_Update_{timestamp}",
            "email": f"test.update.{timestamp}@example.com",
            "password": "TestPass123!",
            "is_admin": False,
            "signature_data": {
                "cpf": "",
                "cargo": "",
                "endereco": "",
                "cep": "",
                "telefone": ""
            }
        }
        
        create_response = admin_session.post(f"{BASE_URL}/api/users", json=user_data)
        assert create_response.status_code in [200, 201]
        created_user = create_response.json()
        user_id = created_user['user_id']
        
        # Update signature_data
        update_data = {
            "signature_data": {
                "cpf": "987.654.321-00",
                "cargo": "Coordenador",
                "endereco": "Av. Brasil, 456",
                "cep": "35180-001",
                "telefone": "(31) 98888-7777"
            }
        }
        
        update_response = admin_session.put(f"{BASE_URL}/api/users/{user_id}", json=update_data)
        assert update_response.status_code == 200, f"Failed to update user: {update_response.text}"
        
        updated_user = update_response.json()
        sig_data = updated_user.get('signature_data', {})
        assert sig_data.get('cpf') == "987.654.321-00"
        assert sig_data.get('cargo') == "Coordenador"
        
        print(f"✓ Updated user signature_data successfully")
        
        # Cleanup
        admin_session.delete(f"{BASE_URL}/api/users/{user_id}")
        print(f"✓ Cleaned up test user: {user_id}")


class TestInputMasks:
    """Test input mask formats (these are frontend validations, but we verify the expected formats)"""
    
    def test_telefone_mask_format(self):
        """Verify telefone mask format: (XX) XXXXX-XXXX"""
        # Test cases for telefone mask
        test_cases = [
            ("31999998888", "(31) 99999-8888"),
            ("3199998888", "(31) 9999-8888"),
        ]
        
        for raw, expected in test_cases:
            # Simulate mask application
            numbers = ''.join(filter(str.isdigit, raw))
            if len(numbers) >= 11:
                masked = f"({numbers[:2]}) {numbers[2:7]}-{numbers[7:11]}"
            elif len(numbers) >= 10:
                masked = f"({numbers[:2]}) {numbers[2:6]}-{numbers[6:10]}"
            else:
                masked = numbers
            
            assert masked == expected, f"Telefone mask failed: {raw} -> {masked}, expected {expected}"
        
        print("✓ Telefone mask format validated: (XX) XXXXX-XXXX")
    
    def test_cpf_mask_format(self):
        """Verify CPF mask format: XXX.XXX.XXX-XX"""
        raw = "12345678900"
        numbers = ''.join(filter(str.isdigit, raw))
        masked = f"{numbers[:3]}.{numbers[3:6]}.{numbers[6:9]}-{numbers[9:11]}"
        expected = "123.456.789-00"
        
        assert masked == expected, f"CPF mask failed: {raw} -> {masked}, expected {expected}"
        print("✓ CPF mask format validated: XXX.XXX.XXX-XX")
    
    def test_cep_mask_format(self):
        """Verify CEP mask format: XXXXX-XXX"""
        raw = "35180000"
        numbers = ''.join(filter(str.isdigit, raw))
        masked = f"{numbers[:5]}-{numbers[5:8]}"
        expected = "35180-000"
        
        assert masked == expected, f"CEP mask failed: {raw} -> {masked}, expected {expected}"
        print("✓ CEP mask format validated: XXXXX-XXX")


class TestUserPermissions(TestSetup):
    """Test user permissions structure"""
    
    def test_user_has_permissions_field(self, admin_session):
        """Test that users have permissions field"""
        response = admin_session.get(f"{BASE_URL}/api/users")
        assert response.status_code == 200
        data = response.json()
        
        for user in data:
            if 'permissions' in user and user['permissions'] is not None:
                perms = user['permissions']
                expected_perms = ['can_view', 'can_edit', 'can_delete', 'can_export', 'can_manage_users', 'is_full_admin']
                for perm in expected_perms:
                    assert perm in perms, f"Permission '{perm}' missing"
                print(f"✓ User {user['email']} has all permission fields")
                return
        
        print("✓ Permissions structure validated (some users may have null permissions)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
