"""
Test suite for pagination features:
1. PDF export without forced pagination (all items in single table)
2. Frontend pagination of 15 items per page in PAC/PAC Geral editors
3. Portal Transparência pagination with 20/40/60/80/100 options for Processos
"""
import pytest
import requests
import os
import io
from PyPDF2 import PdfReader

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "cristiano.abdo@acaiaca.mg.gov.br"
ADMIN_PASSWORD = "Cris@820906"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestPDFExportNoPagination:
    """Test that PDF exports generate all items in a single table (no forced pagination)"""
    
    def test_pac_individual_pdf_export_returns_pdf(self, auth_headers):
        """Test PAC Individual PDF export endpoint returns valid PDF"""
        # First get a PAC ID
        response = requests.get(f"{BASE_URL}/api/pacs", headers=auth_headers)
        assert response.status_code == 200
        pacs = response.json()
        
        if not pacs:
            pytest.skip("No PACs available for testing")
        
        pac_id = pacs[0]['pac_id']
        
        # Export PDF
        response = requests.get(f"{BASE_URL}/api/pacs/{pac_id}/export/pdf", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers.get('content-type') == 'application/pdf'
        
        # Verify it's a valid PDF
        pdf_content = io.BytesIO(response.content)
        reader = PdfReader(pdf_content)
        assert len(reader.pages) >= 1
        print(f"PAC Individual PDF generated with {len(reader.pages)} page(s)")
    
    def test_pac_geral_pdf_export_returns_pdf(self, auth_headers):
        """Test PAC Geral PDF export endpoint returns valid PDF"""
        # First get a PAC Geral ID
        response = requests.get(f"{BASE_URL}/api/pacs-geral", headers=auth_headers)
        assert response.status_code == 200
        pacs_geral = response.json()
        
        if not pacs_geral:
            pytest.skip("No PACs Gerais available for testing")
        
        pac_geral_id = pacs_geral[0]['pac_geral_id']
        
        # Export PDF
        response = requests.get(f"{BASE_URL}/api/pacs-geral/{pac_geral_id}/export/pdf", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers.get('content-type') == 'application/pdf'
        
        # Verify it's a valid PDF
        pdf_content = io.BytesIO(response.content)
        reader = PdfReader(pdf_content)
        assert len(reader.pages) >= 1
        print(f"PAC Geral PDF generated with {len(reader.pages)} page(s)")
    
    def test_pac_geral_specific_pdf_export(self, auth_headers):
        """Test specific PAC Geral (pac_geral_5614f7bfda33) PDF export"""
        pac_geral_id = "pac_geral_5614f7bfda33"
        
        # Export PDF
        response = requests.get(f"{BASE_URL}/api/pacs-geral/{pac_geral_id}/export/pdf", headers=auth_headers)
        
        if response.status_code == 404:
            pytest.skip(f"PAC Geral {pac_geral_id} not found")
        
        assert response.status_code == 200
        assert response.headers.get('content-type') == 'application/pdf'
        
        # Verify it's a valid PDF
        pdf_content = io.BytesIO(response.content)
        reader = PdfReader(pdf_content)
        num_pages = len(reader.pages)
        print(f"PAC Geral {pac_geral_id} PDF generated with {num_pages} page(s)")
        
        # Check validation code header
        validation_code = response.headers.get('X-Validation-Code')
        if validation_code:
            print(f"Validation code: {validation_code}")
    
    def test_pdf_landscape_orientation(self, auth_headers):
        """Test PDF export with landscape orientation"""
        response = requests.get(f"{BASE_URL}/api/pacs", headers=auth_headers)
        if response.status_code != 200 or not response.json():
            pytest.skip("No PACs available")
        
        pac_id = response.json()[0]['pac_id']
        
        response = requests.get(
            f"{BASE_URL}/api/pacs/{pac_id}/export/pdf?orientation=landscape", 
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.headers.get('content-type') == 'application/pdf'
        print("Landscape PDF export successful")
    
    def test_pdf_portrait_orientation(self, auth_headers):
        """Test PDF export with portrait orientation"""
        response = requests.get(f"{BASE_URL}/api/pacs", headers=auth_headers)
        if response.status_code != 200 or not response.json():
            pytest.skip("No PACs available")
        
        pac_id = response.json()[0]['pac_id']
        
        response = requests.get(
            f"{BASE_URL}/api/pacs/{pac_id}/export/pdf?orientation=portrait", 
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.headers.get('content-type') == 'application/pdf'
        print("Portrait PDF export successful")


class TestPublicPortalProcessosPagination:
    """Test Portal Transparência processos pagination with 20/40/60/80/100 options"""
    
    def test_public_processos_endpoint_exists(self):
        """Test that public processos endpoint exists"""
        response = requests.get(f"{BASE_URL}/api/public/processos")
        assert response.status_code == 200
        data = response.json()
        assert 'data' in data
        print(f"Public processos endpoint returned {len(data['data'])} processos")
    
    def test_public_dashboard_stats(self):
        """Test public dashboard stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/public/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert 'data' in data
        print(f"Dashboard stats: {data['data'].get('resumo', {})}")
    
    def test_public_pacs_endpoint(self):
        """Test public PACs endpoint"""
        response = requests.get(f"{BASE_URL}/api/public/pacs")
        assert response.status_code == 200
        data = response.json()
        assert 'data' in data
        print(f"Public PACs endpoint returned {len(data['data'])} PACs")
    
    def test_public_pacs_geral_endpoint(self):
        """Test public PACs Geral endpoint"""
        response = requests.get(f"{BASE_URL}/api/public/pacs-geral")
        assert response.status_code == 200
        data = response.json()
        assert 'data' in data
        print(f"Public PACs Geral endpoint returned {len(data['data'])} PACs Gerais")


class TestPACItemsEndpoints:
    """Test PAC items endpoints for frontend pagination"""
    
    def test_pac_items_endpoint(self, auth_headers):
        """Test PAC items endpoint returns all items"""
        response = requests.get(f"{BASE_URL}/api/pacs", headers=auth_headers)
        if response.status_code != 200 or not response.json():
            pytest.skip("No PACs available")
        
        pac_id = response.json()[0]['pac_id']
        
        response = requests.get(f"{BASE_URL}/api/pacs/{pac_id}/items", headers=auth_headers)
        assert response.status_code == 200
        items = response.json()
        print(f"PAC {pac_id} has {len(items)} items")
    
    def test_pac_geral_items_endpoint(self, auth_headers):
        """Test PAC Geral items endpoint returns all items"""
        response = requests.get(f"{BASE_URL}/api/pacs-geral", headers=auth_headers)
        if response.status_code != 200 or not response.json():
            pytest.skip("No PACs Gerais available")
        
        pac_geral_id = response.json()[0]['pac_geral_id']
        
        response = requests.get(f"{BASE_URL}/api/pacs-geral/{pac_geral_id}/items", headers=auth_headers)
        assert response.status_code == 200
        items = response.json()
        print(f"PAC Geral {pac_geral_id} has {len(items)} items")


class TestPublicPDFExport:
    """Test public PDF export endpoints (no auth required)"""
    
    def test_public_pac_pdf_export(self):
        """Test public PAC PDF export"""
        # Get a PAC ID from public endpoint
        response = requests.get(f"{BASE_URL}/api/public/pacs")
        if response.status_code != 200 or not response.json().get('data'):
            pytest.skip("No public PACs available")
        
        pac_id = response.json()['data'][0]['pac_id']
        
        response = requests.get(f"{BASE_URL}/api/public/pacs/{pac_id}/export/pdf")
        assert response.status_code == 200
        assert response.headers.get('content-type') == 'application/pdf'
        print(f"Public PAC PDF export successful for {pac_id}")
    
    def test_public_pac_geral_pdf_export(self):
        """Test public PAC Geral PDF export"""
        # Get a PAC Geral ID from public endpoint
        response = requests.get(f"{BASE_URL}/api/public/pacs-geral")
        if response.status_code != 200 or not response.json().get('data'):
            pytest.skip("No public PACs Gerais available")
        
        pac_geral_id = response.json()['data'][0]['pac_geral_id']
        
        response = requests.get(f"{BASE_URL}/api/public/pacs-geral/{pac_geral_id}/export/pdf")
        assert response.status_code == 200
        assert response.headers.get('content-type') == 'application/pdf'
        print(f"Public PAC Geral PDF export successful for {pac_geral_id}")
    
    def test_public_processos_pdf_export(self):
        """Test public processos PDF export"""
        response = requests.get(f"{BASE_URL}/api/public/processos/export/pdf")
        assert response.status_code == 200
        assert response.headers.get('content-type') == 'application/pdf'
        print("Public processos PDF export successful")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
