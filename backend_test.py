#!/usr/bin/env python3
"""
Backend API Testing for Sistema PAC Acaiaca 2026
Tests all endpoints with the admin user credentials
"""

import requests
import sys
import json
from datetime import datetime

class PACBackendTester:
    def __init__(self, base_url="https://govprocure-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.pac_id = None
        self.item_id = None
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

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

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

    def test_auth_login(self):
        """Test admin login"""
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
            self.token = response['token']
            self.user_id = response['user']['user_id']
            return True
        return False

    def test_auth_me(self):
        """Test get current user"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        success, response = self.run_test(
            "Dashboard Stats",
            "GET",
            "dashboard/stats",
            200
        )
        return success

    def test_create_pac(self):
        """Test PAC creation"""
        pac_data = {
            "secretaria": "Secretaria de Teste Automatizado",
            "secretario": "João da Silva",
            "fiscal": "Maria Santos",
            "telefone": "(31) 99999-9999",
            "email": "teste@acaiaca.mg.gov.br",
            "endereco": "Rua Teste, 123 - Centro - Acaiaca/MG",
            "ano": "2026"
        }
        
        success, response = self.run_test(
            "Create PAC",
            "POST",
            "pacs",
            200,
            data=pac_data
        )
        
        if success and 'pac_id' in response:
            self.pac_id = response['pac_id']
            return True
        return False

    def test_get_pacs(self):
        """Test get all PACs"""
        success, response = self.run_test(
            "Get All PACs",
            "GET",
            "pacs",
            200
        )
        return success

    def test_get_pac_by_id(self):
        """Test get specific PAC"""
        if not self.pac_id:
            self.log_test("Get PAC by ID", False, "No PAC ID available")
            return False
            
        success, response = self.run_test(
            "Get PAC by ID",
            "GET",
            f"pacs/{self.pac_id}",
            200
        )
        return success

    def test_update_pac(self):
        """Test PAC update"""
        if not self.pac_id:
            self.log_test("Update PAC", False, "No PAC ID available")
            return False
            
        update_data = {
            "secretaria": "Secretaria de Teste Atualizada",
            "telefone": "(31) 88888-8888"
        }
        
        success, response = self.run_test(
            "Update PAC",
            "PUT",
            f"pacs/{self.pac_id}",
            200,
            data=update_data
        )
        return success

    def test_create_pac_item(self):
        """Test PAC item creation"""
        if not self.pac_id:
            self.log_test("Create PAC Item", False, "No PAC ID available")
            return False
            
        item_data = {
            "tipo": "Material de Consumo",
            "catmat": "123456",
            "descricao": "Papel A4 75g/m² - Resma com 500 folhas",
            "unidade": "Resma",
            "quantidade": 100,
            "valorUnitario": 25.50,
            "prioridade": "Alta",
            "justificativa": "Material necessário para atividades administrativas da secretaria"
        }
        
        success, response = self.run_test(
            "Create PAC Item",
            "POST",
            f"pacs/{self.pac_id}/items",
            200,
            data=item_data
        )
        
        if success and 'item_id' in response:
            self.item_id = response['item_id']
            return True
        return False

    def test_get_pac_items(self):
        """Test get PAC items"""
        if not self.pac_id:
            self.log_test("Get PAC Items", False, "No PAC ID available")
            return False
            
        success, response = self.run_test(
            "Get PAC Items",
            "GET",
            f"pacs/{self.pac_id}/items",
            200
        )
        return success

    def test_update_pac_item(self):
        """Test PAC item update"""
        if not self.pac_id or not self.item_id:
            self.log_test("Update PAC Item", False, "No PAC ID or Item ID available")
            return False
            
        update_data = {
            "quantidade": 150,
            "valorUnitario": 24.00,
            "prioridade": "Média"
        }
        
        success, response = self.run_test(
            "Update PAC Item",
            "PUT",
            f"pacs/{self.pac_id}/items/{self.item_id}",
            200,
            data=update_data
        )
        return success

    def test_download_template(self):
        """Test template download"""
        success, response = self.run_test(
            "Download Template",
            "GET",
            "template/download",
            200
        )
        return success

    def test_export_xlsx(self):
        """Test XLSX export"""
        if not self.pac_id:
            self.log_test("Export XLSX", False, "No PAC ID available")
            return False
            
        success, response = self.run_test(
            "Export XLSX",
            "GET",
            f"pacs/{self.pac_id}/export/xlsx",
            200
        )
        return success

    def test_export_pdf(self):
        """Test PDF export"""
        if not self.pac_id:
            self.log_test("Export PDF", False, "No PAC ID available")
            return False
            
        success, response = self.run_test(
            "Export PDF",
            "GET",
            f"pacs/{self.pac_id}/export/pdf",
            200
        )
        return success

    def test_delete_pac_item(self):
        """Test PAC item deletion"""
        if not self.pac_id or not self.item_id:
            self.log_test("Delete PAC Item", False, "No PAC ID or Item ID available")
            return False
            
        success, response = self.run_test(
            "Delete PAC Item",
            "DELETE",
            f"pacs/{self.pac_id}/items/{self.item_id}",
            200
        )
        return success

    def test_delete_pac(self):
        """Test PAC deletion"""
        if not self.pac_id:
            self.log_test("Delete PAC", False, "No PAC ID available")
            return False
            
        success, response = self.run_test(
            "Delete PAC",
            "DELETE",
            f"pacs/{self.pac_id}",
            200
        )
        return success

    def test_logout(self):
        """Test logout"""
        success, response = self.run_test(
            "Logout",
            "POST",
            "auth/logout",
            200
        )
        return success

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Sistema PAC Acaiaca 2026 Backend Tests")
        print("=" * 60)
        
        # Authentication Tests
        print("\n📋 AUTHENTICATION TESTS")
        if not self.test_auth_login():
            print("❌ Login failed - stopping tests")
            return False
            
        self.test_auth_me()
        
        # Dashboard Tests
        print("\n📊 DASHBOARD TESTS")
        self.test_dashboard_stats()
        
        # PAC CRUD Tests
        print("\n📁 PAC CRUD TESTS")
        self.test_create_pac()
        self.test_get_pacs()
        self.test_get_pac_by_id()
        self.test_update_pac()
        
        # PAC Items Tests
        print("\n📝 PAC ITEMS TESTS")
        self.test_create_pac_item()
        self.test_get_pac_items()
        self.test_update_pac_item()
        
        # Export/Import Tests
        print("\n📤 EXPORT/IMPORT TESTS")
        self.test_download_template()
        self.test_export_xlsx()
        self.test_export_pdf()
        
        # Cleanup Tests
        print("\n🗑️ CLEANUP TESTS")
        self.test_delete_pac_item()
        self.test_delete_pac()
        
        # Logout Test
        print("\n🚪 LOGOUT TEST")
        self.test_logout()
        
        return True

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"  • {test['test']}: {test['error']}")
        
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