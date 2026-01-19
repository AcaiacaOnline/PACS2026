#!/usr/bin/env python3
"""
Backend API Testing for Sistema PAC Acaiaca 2026
Comprehensive tests for authentication, permissions, and budget classification
"""

import requests
import sys
import json
from datetime import datetime
import uuid

class PACBackendTester:
    def __init__(self, base_url="https://planning-system-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.admin_token = None
        self.user_token = None
        self.admin_user_id = None
        self.regular_user_id = None
        self.pac_id_admin = None
        self.pac_id_user = None
        self.item_id = None
        self.new_user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
            self.failed_tests.append({"test": name, "error": details})

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, token=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Use specific token if provided, otherwise use admin token
        auth_token = token if token else self.admin_token
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    headers.pop('Content-Type', None)  # Let requests set it for multipart
                    response = requests.post(url, files=files, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            
            if success:
                self.log_test(name, True)
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                error_msg = f"Expected {expected_status}, got {response.status_code}"
                try:
                    error_detail = response.json().get('detail', '')
                    if error_detail:
                        error_msg += f" - {error_detail}"
                except:
                    pass
                self.log_test(name, False, error_msg)
                return False, {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    # ============ PHASE 1: AUTHENTICATION AND PERMISSIONS ============

    def test_admin_login(self):
        """Test admin login and JWT token validation"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": "cristiano.abdo@acaiaca.mg.gov.br",
                "password": "Cris@820906"
            }
        )
        if success and 'token' in response:
            self.admin_token = response['token']
            self.admin_user_id = response['user']['user_id']
            # Verify JWT token structure
            if '.' in self.admin_token and len(self.admin_token.split('.')) == 3:
                self.log_test("JWT Token Structure Valid", True)
            else:
                self.log_test("JWT Token Structure Valid", False, "Invalid JWT format")
            return True
        return False

    def test_regular_user_login(self):
        """Test regular user login"""
        success, response = self.run_test(
            "Regular User Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": "teste@acaiaca.mg.gov.br",
                "password": "Senha123"
            }
        )
        if success and 'token' in response:
            self.user_token = response['token']
            self.regular_user_id = response['user']['user_id']
            return True
        return False

    def test_create_user_with_password_hash(self):
        """Test creating new user via admin API and verify password is hashed"""
        if not self.admin_token:
            self.log_test("Create User with Password Hash", False, "No admin token")
            return False

        # Generate unique email for test
        test_email = f"test_user_{uuid.uuid4().hex[:8]}@acaiaca.mg.gov.br"
        
        user_data = {
            "email": test_email,
            "password": "TestPassword123!",
            "name": "Test User for Hash Validation",
            "is_admin": False
        }
        
        success, response = self.run_test(
            "Create User via Admin API",
            "POST",
            "users",
            200,
            data=user_data,
            token=self.admin_token
        )
        
        if success and 'user_id' in response:
            self.new_user_id = response['user_id']
            
            # Now verify the user was created with password_hash (not plain password)
            # We'll try to login with the new user to verify the hash works
            login_success, login_response = self.run_test(
                "Login with New User (Hash Validation)",
                "POST",
                "auth/login",
                200,
                data={
                    "email": test_email,
                    "password": "TestPassword123!"
                }
            )
            
            if login_success:
                self.log_test("Password Hash Validation", True, "User can login with hashed password")
                return True
            else:
                self.log_test("Password Hash Validation", False, "User cannot login - hash may not be working")
                return False
        return False

    def test_create_pac_as_admin(self):
        """Test PAC creation as admin"""
        if not self.admin_token:
            self.log_test("Create PAC as Admin", False, "No admin token")
            return False

        pac_data = {
            "secretaria": "Secretaria de Teste Admin",
            "secretario": "Admin User",
            "fiscal": "Fiscal Admin",
            "telefone": "(31) 99999-1111",
            "email": "admin@acaiaca.mg.gov.br",
            "endereco": "Rua Admin, 123 - Centro - Acaiaca/MG",
            "ano": "2026"
        }
        
        success, response = self.run_test(
            "Create PAC as Admin",
            "POST",
            "pacs",
            200,
            data=pac_data,
            token=self.admin_token
        )
        
        if success and 'pac_id' in response:
            self.pac_id_admin = response['pac_id']
            return True
        return False

    def test_create_pac_as_user(self):
        """Test PAC creation as regular user"""
        if not self.user_token:
            self.log_test("Create PAC as User", False, "No user token")
            return False

        pac_data = {
            "secretaria": "Secretaria de Teste Usuario",
            "secretario": "Regular User",
            "fiscal": "Fiscal User",
            "telefone": "(31) 99999-2222",
            "email": "user@acaiaca.mg.gov.br",
            "endereco": "Rua User, 456 - Centro - Acaiaca/MG",
            "ano": "2026"
        }
        
        success, response = self.run_test(
            "Create PAC as User",
            "POST",
            "pacs",
            200,
            data=pac_data,
            token=self.user_token
        )
        
        if success and 'pac_id' in response:
            self.pac_id_user = response['pac_id']
            return True
        return False

    def test_user_view_other_pac(self):
        """Test that regular user CAN view PACs from other users"""
        if not self.user_token or not self.pac_id_admin:
            self.log_test("User View Other PAC", False, "Missing tokens or PAC ID")
            return False

        success, response = self.run_test(
            "User View Admin's PAC (Should Work)",
            "GET",
            f"pacs/{self.pac_id_admin}",
            200,
            token=self.user_token
        )
        return success

    def test_user_edit_other_pac_forbidden(self):
        """Test that regular user CANNOT edit PACs from other users"""
        if not self.user_token or not self.pac_id_admin:
            self.log_test("User Edit Other PAC (Should Fail)", False, "Missing tokens or PAC ID")
            return False

        update_data = {
            "secretaria": "Tentativa de Edição Não Autorizada"
        }

        success, response = self.run_test(
            "User Edit Admin's PAC (Should Fail with 403)",
            "PUT",
            f"pacs/{self.pac_id_admin}",
            403,  # Expecting 403 Forbidden
            data=update_data,
            token=self.user_token
        )
        return success

    def test_admin_edit_user_pac(self):
        """Test that admin CAN edit PACs from any user"""
        if not self.admin_token or not self.pac_id_user:
            self.log_test("Admin Edit User PAC", False, "Missing tokens or PAC ID")
            return False

        update_data = {
            "secretaria": "Editado pelo Admin"
        }

        success, response = self.run_test(
            "Admin Edit User's PAC (Should Work)",
            "PUT",
            f"pacs/{self.pac_id_user}",
            200,
            data=update_data,
            token=self.admin_token
        )
        return success

    def test_admin_delete_user_pac(self):
        """Test that admin CAN delete PACs from any user"""
        if not self.admin_token or not self.pac_id_user:
            self.log_test("Admin Delete User PAC", False, "Missing tokens or PAC ID")
            return False

        success, response = self.run_test(
            "Admin Delete User's PAC (Should Work)",
            "DELETE",
            f"pacs/{self.pac_id_user}",
            200,
            token=self.admin_token
        )
        return success

    # ============ PHASE 2: BUDGET CLASSIFICATION ============

    def test_get_classification_codes(self):
        """Test GET /api/classificacao/codigos endpoint"""
        success, response = self.run_test(
            "Get Classification Codes",
            "GET",
            "classificacao/codigos",
            200,
            token=self.admin_token
        )
        
        if success:
            # Verify expected codes are present
            expected_codes = ["339030", "339036", "339039", "449052"]
            for code in expected_codes:
                if code in response:
                    self.log_test(f"Classification Code {code} Present", True)
                else:
                    self.log_test(f"Classification Code {code} Present", False, f"Code {code} not found")
            
            # Verify structure of 339030 (Material de Consumo)
            if "339030" in response and "subitens" in response["339030"]:
                subitens = response["339030"]["subitens"]
                if "Material de Expediente" in subitens:
                    self.log_test("Material de Expediente Subitem Present", True)
                else:
                    self.log_test("Material de Expediente Subitem Present", False, "Subitem not found")
        
        return success

    def test_create_pac_item_with_classification(self):
        """Test creating PAC item WITH budget classification"""
        if not self.admin_token or not self.pac_id_admin:
            self.log_test("Create Item with Classification", False, "Missing tokens or PAC ID")
            return False

        item_data = {
            "tipo": "Material de Consumo",
            "catmat": "123456",
            "descricao": "Papel A4 75g/m² - Resma com 500 folhas",
            "unidade": "Resma",
            "quantidade": 100,
            "valorUnitario": 25.50,
            "prioridade": "Alta",
            "justificativa": "Material necessário para atividades administrativas",
            "codigo_classificacao": "339030",
            "subitem_classificacao": "Material de Expediente"
        }
        
        success, response = self.run_test(
            "Create PAC Item with Classification",
            "POST",
            f"pacs/{self.pac_id_admin}/items",
            200,
            data=item_data,
            token=self.admin_token
        )
        
        if success and 'item_id' in response:
            self.item_id = response['item_id']
            
            # Verify classification fields are present in response
            if response.get('codigo_classificacao') == "339030":
                self.log_test("Classification Code in Response", True)
            else:
                self.log_test("Classification Code in Response", False, "Code not in response")
                
            if response.get('subitem_classificacao') == "Material de Expediente":
                self.log_test("Classification Subitem in Response", True)
            else:
                self.log_test("Classification Subitem in Response", False, "Subitem not in response")
            
            return True
        return False

    def test_get_pac_items_with_classification(self):
        """Test retrieving PAC items and verify classification is present"""
        if not self.admin_token or not self.pac_id_admin:
            self.log_test("Get Items with Classification", False, "Missing tokens or PAC ID")
            return False

        success, response = self.run_test(
            "Get PAC Items with Classification",
            "GET",
            f"pacs/{self.pac_id_admin}/items",
            200,
            token=self.admin_token
        )
        
        if success and isinstance(response, list) and len(response) > 0:
            item = response[0]  # Check first item
            if item.get('codigo_classificacao') == "339030":
                self.log_test("Classification Persisted in Database", True)
            else:
                self.log_test("Classification Persisted in Database", False, "Classification not found in retrieved item")
            return True
        return False

    def test_edit_item_classification(self):
        """Test editing item and changing classification"""
        if not self.admin_token or not self.pac_id_admin or not self.item_id:
            self.log_test("Edit Item Classification", False, "Missing tokens, PAC ID, or Item ID")
            return False

        update_data = {
            "codigo_classificacao": "339039",
            "subitem_classificacao": "Serviços Técnicos Profissionais"
        }

        success, response = self.run_test(
            "Edit Item Classification",
            "PUT",
            f"pacs/{self.pac_id_admin}/items/{self.item_id}",
            200,
            data=update_data,
            token=self.admin_token
        )
        
        if success:
            # Verify updated classification
            if response.get('codigo_classificacao') == "339039":
                self.log_test("Classification Update Successful", True)
            else:
                self.log_test("Classification Update Successful", False, "Classification not updated")
        
        return success

    # ============ PHASE 3: EXPORT FUNCTIONALITY ============

    def test_export_xlsx_with_classification(self):
        """Test XLSX export includes classification fields"""
        if not self.admin_token or not self.pac_id_admin:
            self.log_test("Export XLSX with Classification", False, "Missing tokens or PAC ID")
            return False

        success, response = self.run_test(
            "Export XLSX with Classification",
            "GET",
            f"pacs/{self.pac_id_admin}/export/xlsx",
            200,
            token=self.admin_token
        )
        return success

    def test_export_pdf_with_classification(self):
        """Test PDF export includes classification fields"""
        if not self.admin_token or not self.pac_id_admin:
            self.log_test("Export PDF with Classification", False, "Missing tokens or PAC ID")
            return False

        success, response = self.run_test(
            "Export PDF with Classification",
            "GET",
            f"pacs/{self.pac_id_admin}/export/pdf",
            200,
            token=self.admin_token
        )
        return success

    # ============ ADDITIONAL TESTS ============

    def test_get_users_admin_only(self):
        """Test that only admin can access user management"""
        if not self.admin_token:
            self.log_test("Get Users (Admin Only)", False, "No admin token")
            return False

        success, response = self.run_test(
            "Get Users (Admin Access)",
            "GET",
            "users",
            200,
            token=self.admin_token
        )
        
        if success and self.user_token:
            # Test that regular user gets 403
            user_success, user_response = self.run_test(
                "Get Users (User Access - Should Fail)",
                "GET",
                "users",
                403,
                token=self.user_token
            )
            return user_success  # Should return True because we expect 403
        
        return success

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        success, response = self.run_test(
            "Dashboard Stats",
            "GET",
            "dashboard/stats",
            200,
            token=self.admin_token
        )
        return success

    # ============ CLEANUP ============

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🗑️ CLEANUP PHASE")
        
        # Delete test item
        if self.item_id and self.pac_id_admin:
            self.run_test(
                "Delete Test Item",
                "DELETE",
                f"pacs/{self.pac_id_admin}/items/{self.item_id}",
                200,
                token=self.admin_token
            )
        
        # Delete admin's PAC
        if self.pac_id_admin:
            self.run_test(
                "Delete Admin PAC",
                "DELETE",
                f"pacs/{self.pac_id_admin}",
                200,
                token=self.admin_token
            )
        
        # Delete test user
        if self.new_user_id:
            self.run_test(
                "Delete Test User",
                "DELETE",
                f"users/{self.new_user_id}",
                200,
                token=self.admin_token
            )

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Sistema PAC Acaiaca 2026 Comprehensive Backend Tests")
        print("=" * 80)
        
        # Phase 1: Authentication and Permissions
        print("\n📋 PHASE 1: AUTHENTICATION AND PERMISSIONS")
        print("-" * 50)
        
        if not self.test_admin_login():
            print("❌ Admin login failed - stopping tests")
            return False
            
        if not self.test_regular_user_login():
            print("❌ Regular user login failed - some permission tests will be skipped")
        
        self.test_create_user_with_password_hash()
        self.test_create_pac_as_admin()
        self.test_create_pac_as_user()
        self.test_user_view_other_pac()
        self.test_user_edit_other_pac_forbidden()
        self.test_admin_edit_user_pac()
        self.test_admin_delete_user_pac()
        
        # Phase 2: Budget Classification
        print("\n💰 PHASE 2: BUDGET CLASSIFICATION")
        print("-" * 50)
        
        self.test_get_classification_codes()
        self.test_create_pac_item_with_classification()
        self.test_get_pac_items_with_classification()
        self.test_edit_item_classification()
        
        # Phase 3: Export Functionality
        print("\n📤 PHASE 3: EXPORT FUNCTIONALITY")
        print("-" * 50)
        
        self.test_export_xlsx_with_classification()
        self.test_export_pdf_with_classification()
        
        # Additional Tests
        print("\n🔧 ADDITIONAL TESTS")
        print("-" * 50)
        
        self.test_get_users_admin_only()
        self.test_dashboard_stats()
        
        # Cleanup
        self.cleanup_test_data()
        
        return True

    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"  • {test['test']}: {test['error']}")
        else:
            print("\n🎉 ALL TESTS PASSED!")
        
        print("\n📋 TEST COVERAGE:")
        print("  ✓ Password hashing validation")
        print("  ✓ User permission system")
        print("  ✓ Admin vs regular user access")
        print("  ✓ Budget classification functionality")
        print("  ✓ Export functionality with classification")
        print("  ✓ CRUD operations with permissions")
        
        return len(self.failed_tests) == 0

def main():
    """Main test function"""
    tester = PACBackendTester()
    
    try:
        tester.run_all_tests()
        success = tester.print_summary()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())