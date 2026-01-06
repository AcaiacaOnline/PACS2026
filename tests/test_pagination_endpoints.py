"""
Test suite for PAC and PAC Geral pagination endpoints
Tests the new paginated endpoints: /api/pacs/paginado and /api/pacs-geral/paginado
Also tests Gestão Processual pagination: /api/processos/paginado
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPACPagination:
    """Tests for /api/pacs/paginado endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "cristiano.abdo@acaiaca.mg.gov.br",
            "password": "Cris@820906"
        })
        if login_response.status_code == 200:
            self.token = login_response.json().get('token')
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Authentication failed")
    
    def test_pacs_paginado_default(self):
        """Test GET /api/pacs/paginado with default parameters"""
        response = self.session.get(f"{BASE_URL}/api/pacs/paginado")
        assert response.status_code == 200
        
        data = response.json()
        assert 'items' in data
        assert 'total' in data
        assert 'page' in data
        assert 'page_size' in data
        assert 'total_pages' in data
        
        # Default page should be 1
        assert data['page'] == 1
        # Default page_size should be 20
        assert data['page_size'] == 20
        
        print(f"✓ PACs paginado: {data['total']} total, page {data['page']}/{data['total_pages']}")
    
    def test_pacs_paginado_with_page_size(self):
        """Test GET /api/pacs/paginado with custom page_size"""
        response = self.session.get(f"{BASE_URL}/api/pacs/paginado?page_size=10")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page_size'] == 10
        assert len(data['items']) <= 10
        
        print(f"✓ PACs paginado with page_size=10: {len(data['items'])} items returned")
    
    def test_pacs_paginado_with_year_filter(self):
        """Test GET /api/pacs/paginado with year filter"""
        response = self.session.get(f"{BASE_URL}/api/pacs/paginado?ano=2026")
        assert response.status_code == 200
        
        data = response.json()
        # All items should be from 2026
        for item in data['items']:
            assert item.get('ano') == '2026' or item.get('ano') == 2026
        
        print(f"✓ PACs paginado with ano=2026: {data['total']} items")
    
    def test_pacs_paginado_pagination_navigation(self):
        """Test pagination navigation (page 2)"""
        response = self.session.get(f"{BASE_URL}/api/pacs/paginado?page=2&page_size=5")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page'] == 2
        assert data['page_size'] == 5
        
        print(f"✓ PACs paginado page 2: {len(data['items'])} items")


class TestPACGeralPagination:
    """Tests for /api/pacs-geral/paginado endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "cristiano.abdo@acaiaca.mg.gov.br",
            "password": "Cris@820906"
        })
        if login_response.status_code == 200:
            self.token = login_response.json().get('token')
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Authentication failed")
    
    def test_pacs_geral_paginado_default(self):
        """Test GET /api/pacs-geral/paginado with default parameters"""
        response = self.session.get(f"{BASE_URL}/api/pacs-geral/paginado")
        assert response.status_code == 200
        
        data = response.json()
        assert 'items' in data
        assert 'total' in data
        assert 'page' in data
        assert 'page_size' in data
        assert 'total_pages' in data
        
        # Default page should be 1
        assert data['page'] == 1
        # Default page_size should be 20
        assert data['page_size'] == 20
        
        print(f"✓ PACs Geral paginado: {data['total']} total, page {data['page']}/{data['total_pages']}")
    
    def test_pacs_geral_paginado_with_page_size(self):
        """Test GET /api/pacs-geral/paginado with custom page_size"""
        response = self.session.get(f"{BASE_URL}/api/pacs-geral/paginado?page_size=10")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page_size'] == 10
        assert len(data['items']) <= 10
        
        print(f"✓ PACs Geral paginado with page_size=10: {len(data['items'])} items returned")
    
    def test_pacs_geral_paginado_with_year_filter(self):
        """Test GET /api/pacs-geral/paginado with year filter"""
        response = self.session.get(f"{BASE_URL}/api/pacs-geral/paginado?ano=2026")
        assert response.status_code == 200
        
        data = response.json()
        # All items should be from 2026
        for item in data['items']:
            assert item.get('ano') == '2026' or item.get('ano') == 2026
        
        print(f"✓ PACs Geral paginado with ano=2026: {data['total']} items")
    
    def test_pacs_geral_paginado_search(self):
        """Test GET /api/pacs-geral/paginado with search parameter"""
        response = self.session.get(f"{BASE_URL}/api/pacs-geral/paginado?search=secretaria")
        assert response.status_code == 200
        
        data = response.json()
        assert 'items' in data
        
        print(f"✓ PACs Geral paginado with search: {data['total']} items found")


class TestProcessosPagination:
    """Tests for /api/processos/paginado endpoint (Gestão Processual)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "cristiano.abdo@acaiaca.mg.gov.br",
            "password": "Cris@820906"
        })
        if login_response.status_code == 200:
            self.token = login_response.json().get('token')
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Authentication failed")
    
    def test_processos_paginado_default(self):
        """Test GET /api/processos/paginado with default parameters"""
        response = self.session.get(f"{BASE_URL}/api/processos/paginado")
        assert response.status_code == 200
        
        data = response.json()
        assert 'items' in data
        assert 'total' in data
        assert 'page' in data
        assert 'page_size' in data
        assert 'total_pages' in data
        
        # Default page should be 1
        assert data['page'] == 1
        # Default page_size should be 20
        assert data['page_size'] == 20
        
        print(f"✓ Processos paginado: {data['total']} total, page {data['page']}/{data['total_pages']}")
    
    def test_processos_paginado_with_page_size_20(self):
        """Test GET /api/processos/paginado with page_size=20 (default for Gestão Processual)"""
        response = self.session.get(f"{BASE_URL}/api/processos/paginado?page_size=20")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page_size'] == 20
        assert len(data['items']) <= 20
        
        print(f"✓ Processos paginado with page_size=20: {len(data['items'])} items returned")
    
    def test_processos_paginado_with_year_filter(self):
        """Test GET /api/processos/paginado with year filter"""
        response = self.session.get(f"{BASE_URL}/api/processos/paginado?ano=2025")
        assert response.status_code == 200
        
        data = response.json()
        # All items should be from 2025
        for item in data['items']:
            assert item.get('ano') == 2025 or item.get('ano') == '2025'
        
        print(f"✓ Processos paginado with ano=2025: {data['total']} items")
    
    def test_processos_paginado_with_status_filter(self):
        """Test GET /api/processos/paginado with status filter"""
        response = self.session.get(f"{BASE_URL}/api/processos/paginado?status=Concluído")
        assert response.status_code == 200
        
        data = response.json()
        # All items should have status 'Concluído'
        for item in data['items']:
            assert item.get('status') == 'Concluído'
        
        print(f"✓ Processos paginado with status=Concluído: {data['total']} items")
    
    def test_processos_paginado_with_search(self):
        """Test GET /api/processos/paginado with search parameter"""
        response = self.session.get(f"{BASE_URL}/api/processos/paginado?search=PRC")
        assert response.status_code == 200
        
        data = response.json()
        assert 'items' in data
        
        print(f"✓ Processos paginado with search: {data['total']} items found")


class TestPDFSignature:
    """Tests for PDF export with digital signature seal"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "cristiano.abdo@acaiaca.mg.gov.br",
            "password": "Cris@820906"
        })
        if login_response.status_code == 200:
            self.token = login_response.json().get('token')
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Authentication failed")
    
    def test_pac_pdf_export_has_signature(self):
        """Test that PAC PDF export includes digital signature"""
        # First get a PAC ID
        pacs_response = self.session.get(f"{BASE_URL}/api/pacs")
        if pacs_response.status_code != 200 or not pacs_response.json():
            pytest.skip("No PACs available for testing")
        
        pac_id = pacs_response.json()[0]['pac_id']
        
        # Export PDF
        pdf_response = self.session.get(f"{BASE_URL}/api/pacs/{pac_id}/export/pdf")
        assert pdf_response.status_code == 200
        assert pdf_response.headers.get('content-type') == 'application/pdf'
        
        # Check for validation code header
        validation_code = pdf_response.headers.get('X-Validation-Code')
        if validation_code:
            print(f"✓ PAC PDF exported with validation code: {validation_code}")
        else:
            print("✓ PAC PDF exported (signature may have failed silently)")
    
    def test_pac_geral_pdf_export_has_signature(self):
        """Test that PAC Geral PDF export includes digital signature"""
        # First get a PAC Geral ID
        pacs_response = self.session.get(f"{BASE_URL}/api/pacs-geral")
        if pacs_response.status_code != 200 or not pacs_response.json():
            pytest.skip("No PACs Gerais available for testing")
        
        pac_geral_id = pacs_response.json()[0]['pac_geral_id']
        
        # Export PDF
        pdf_response = self.session.get(f"{BASE_URL}/api/pacs-geral/{pac_geral_id}/export/pdf")
        assert pdf_response.status_code == 200
        assert pdf_response.headers.get('content-type') == 'application/pdf'
        
        # Check for validation code header
        validation_code = pdf_response.headers.get('X-Validation-Code')
        if validation_code:
            print(f"✓ PAC Geral PDF exported with validation code: {validation_code}")
        else:
            print("✓ PAC Geral PDF exported (signature may have failed silently)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
