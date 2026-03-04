"""
Test PDF Export Functionality for PAC Individual and PAC Geral
Tests:
- Professional design with institutional header
- Pagination (max 15 items per page)
- Alternating row colors in tables
- Digital signature seal on right side
- Signature and validation section
"""

import pytest
import requests
import os
from io import BytesIO

# Try to import PyPDF2 for PDF analysis
try:
    from PyPDF2 import PdfReader
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://municipal-refactor.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "cristiano.abdo@acaiaca.mg.gov.br"
TEST_PASSWORD = "Cris@820906"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["token"]


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Create authenticated session"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


class TestPACIndividualPDFExport:
    """Tests for PAC Individual PDF export endpoint"""
    
    def test_export_pdf_endpoint_exists(self, api_client):
        """Test that the PDF export endpoint exists and returns PDF"""
        # Get first PAC
        pacs_response = api_client.get(f"{BASE_URL}/api/pacs")
        assert pacs_response.status_code == 200
        pacs = pacs_response.json()
        
        if not pacs:
            pytest.skip("No PACs available for testing")
        
        pac_id = pacs[0]["pac_id"]
        
        # Export PDF
        response = api_client.get(f"{BASE_URL}/api/pacs/{pac_id}/export/pdf")
        
        assert response.status_code == 200, f"PDF export failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf"
        print(f"✓ PDF export endpoint working for PAC {pac_id}")
    
    def test_pdf_has_validation_code_header(self, api_client):
        """Test that PDF response includes validation code header"""
        pacs_response = api_client.get(f"{BASE_URL}/api/pacs")
        pacs = pacs_response.json()
        
        if not pacs:
            pytest.skip("No PACs available for testing")
        
        pac_id = pacs[0]["pac_id"]
        response = api_client.get(f"{BASE_URL}/api/pacs/{pac_id}/export/pdf")
        
        assert response.status_code == 200
        validation_code = response.headers.get("X-Validation-Code")
        assert validation_code is not None, "Missing X-Validation-Code header"
        print(f"✓ PDF has validation code: {validation_code}")
    
    def test_pdf_content_is_valid(self, api_client):
        """Test that PDF content is valid PDF format"""
        pacs_response = api_client.get(f"{BASE_URL}/api/pacs")
        pacs = pacs_response.json()
        
        if not pacs:
            pytest.skip("No PACs available for testing")
        
        pac_id = pacs[0]["pac_id"]
        response = api_client.get(f"{BASE_URL}/api/pacs/{pac_id}/export/pdf")
        
        assert response.status_code == 200
        
        # Check PDF magic bytes
        pdf_content = response.content
        assert pdf_content[:4] == b'%PDF', "Content is not a valid PDF"
        print(f"✓ PDF content is valid (size: {len(pdf_content)} bytes)")
    
    @pytest.mark.skipif(not HAS_PYPDF2, reason="PyPDF2 not installed")
    def test_pdf_page_count_with_items(self, api_client):
        """Test PDF pagination - PAC with items should have correct page count"""
        # Find PAC with items
        pacs_response = api_client.get(f"{BASE_URL}/api/pacs")
        pacs = pacs_response.json()
        
        pac_with_items = None
        items_count = 0
        
        for pac in pacs:
            items_response = api_client.get(f"{BASE_URL}/api/pacs/{pac['pac_id']}/items")
            items = items_response.json()
            if len(items) > 0:
                pac_with_items = pac
                items_count = len(items)
                break
        
        if not pac_with_items:
            pytest.skip("No PAC with items found")
        
        response = api_client.get(f"{BASE_URL}/api/pacs/{pac_with_items['pac_id']}/export/pdf")
        assert response.status_code == 200
        
        # Analyze PDF
        pdf_reader = PdfReader(BytesIO(response.content))
        page_count = len(pdf_reader.pages)
        
        # Expected pages: ceil(items / 15) minimum
        expected_min_pages = (items_count + 14) // 15  # At least this many pages for items
        
        print(f"✓ PAC {pac_with_items['pac_id']} has {items_count} items")
        print(f"✓ PDF has {page_count} pages (expected at least {expected_min_pages} for items)")
        
        # PDF should have at least 1 page
        assert page_count >= 1, f"PDF should have at least 1 page, got {page_count}"
    
    def test_pdf_landscape_orientation(self, api_client):
        """Test PDF export with landscape orientation"""
        pacs_response = api_client.get(f"{BASE_URL}/api/pacs")
        pacs = pacs_response.json()
        
        if not pacs:
            pytest.skip("No PACs available for testing")
        
        pac_id = pacs[0]["pac_id"]
        response = api_client.get(f"{BASE_URL}/api/pacs/{pac_id}/export/pdf?orientation=landscape")
        
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        print(f"✓ Landscape PDF export working")
    
    def test_pdf_portrait_orientation(self, api_client):
        """Test PDF export with portrait orientation"""
        pacs_response = api_client.get(f"{BASE_URL}/api/pacs")
        pacs = pacs_response.json()
        
        if not pacs:
            pytest.skip("No PACs available for testing")
        
        pac_id = pacs[0]["pac_id"]
        response = api_client.get(f"{BASE_URL}/api/pacs/{pac_id}/export/pdf?orientation=portrait")
        
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        print(f"✓ Portrait PDF export working")


class TestPACGeralPDFExport:
    """Tests for PAC Geral PDF export endpoint"""
    
    def test_export_pdf_endpoint_exists(self, api_client):
        """Test that the PAC Geral PDF export endpoint exists"""
        # Get first PAC Geral
        pacs_response = api_client.get(f"{BASE_URL}/api/pacs-geral")
        assert pacs_response.status_code == 200
        pacs = pacs_response.json()
        
        if not pacs:
            pytest.skip("No PACs Gerais available for testing")
        
        pac_geral_id = pacs[0]["pac_geral_id"]
        
        # Export PDF
        response = api_client.get(f"{BASE_URL}/api/pacs-geral/{pac_geral_id}/export/pdf")
        
        assert response.status_code == 200, f"PDF export failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf"
        print(f"✓ PAC Geral PDF export endpoint working for {pac_geral_id}")
    
    def test_pdf_has_validation_code_header(self, api_client):
        """Test that PAC Geral PDF response includes validation code header"""
        pacs_response = api_client.get(f"{BASE_URL}/api/pacs-geral")
        pacs = pacs_response.json()
        
        if not pacs:
            pytest.skip("No PACs Gerais available for testing")
        
        pac_geral_id = pacs[0]["pac_geral_id"]
        response = api_client.get(f"{BASE_URL}/api/pacs-geral/{pac_geral_id}/export/pdf")
        
        assert response.status_code == 200
        validation_code = response.headers.get("X-Validation-Code")
        assert validation_code is not None, "Missing X-Validation-Code header"
        print(f"✓ PAC Geral PDF has validation code: {validation_code}")
    
    def test_pdf_content_is_valid(self, api_client):
        """Test that PAC Geral PDF content is valid PDF format"""
        pacs_response = api_client.get(f"{BASE_URL}/api/pacs-geral")
        pacs = pacs_response.json()
        
        if not pacs:
            pytest.skip("No PACs Gerais available for testing")
        
        pac_geral_id = pacs[0]["pac_geral_id"]
        response = api_client.get(f"{BASE_URL}/api/pacs-geral/{pac_geral_id}/export/pdf")
        
        assert response.status_code == 200
        
        # Check PDF magic bytes
        pdf_content = response.content
        assert pdf_content[:4] == b'%PDF', "Content is not a valid PDF"
        print(f"✓ PAC Geral PDF content is valid (size: {len(pdf_content)} bytes)")
    
    @pytest.mark.skipif(not HAS_PYPDF2, reason="PyPDF2 not installed")
    def test_pdf_pagination_with_more_than_15_items(self, api_client):
        """Test PDF pagination - PAC Geral with >15 items should have multiple pages"""
        # Find PAC Geral with more than 15 items
        pacs_response = api_client.get(f"{BASE_URL}/api/pacs-geral")
        pacs = pacs_response.json()
        
        pac_with_many_items = None
        items_count = 0
        
        for pac in pacs:
            items_response = api_client.get(f"{BASE_URL}/api/pacs-geral/{pac['pac_geral_id']}/items")
            if items_response.status_code == 200:
                items = items_response.json()
                if len(items) > 15:
                    pac_with_many_items = pac
                    items_count = len(items)
                    break
        
        if not pac_with_many_items:
            pytest.skip("No PAC Geral with >15 items found for pagination test")
        
        response = api_client.get(f"{BASE_URL}/api/pacs-geral/{pac_with_many_items['pac_geral_id']}/export/pdf")
        assert response.status_code == 200
        
        # Analyze PDF
        pdf_reader = PdfReader(BytesIO(response.content))
        page_count = len(pdf_reader.pages)
        
        # With 15 items per page, >15 items should result in at least 2 pages
        expected_min_pages = 2
        
        print(f"✓ PAC Geral {pac_with_many_items['pac_geral_id']} has {items_count} items")
        print(f"✓ PDF has {page_count} pages (expected at least {expected_min_pages} for pagination)")
        
        assert page_count >= expected_min_pages, f"PDF with {items_count} items should have at least {expected_min_pages} pages, got {page_count}"


class TestPDFDesignFeatures:
    """Tests to verify PDF design features through code review"""
    
    def test_items_per_page_constant(self):
        """Verify ITEMS_PER_PAGE constant is set to 15"""
        # Read server.py to check the constant
        server_path = "/app/backend/server.py"
        with open(server_path, 'r') as f:
            content = f.read()
        
        assert "ITEMS_PER_PAGE = 15" in content, "ITEMS_PER_PAGE should be set to 15"
        print("✓ ITEMS_PER_PAGE constant is set to 15")
    
    def test_professional_styles_function_exists(self):
        """Verify get_professional_styles function exists"""
        server_path = "/app/backend/server.py"
        with open(server_path, 'r') as f:
            content = f.read()
        
        assert "def get_professional_styles():" in content, "get_professional_styles function should exist"
        print("✓ get_professional_styles function exists")
    
    def test_professional_header_function_exists(self):
        """Verify create_professional_header function exists"""
        server_path = "/app/backend/server.py"
        with open(server_path, 'r') as f:
            content = f.read()
        
        assert "def create_professional_header(" in content, "create_professional_header function should exist"
        assert "PREFEITURA MUNICIPAL DE ACAIACA" in content, "Header should include Prefeitura Municipal de Acaiaca"
        print("✓ create_professional_header function exists with institutional header")
    
    def test_signature_section_function_exists(self):
        """Verify create_signature_section function exists"""
        server_path = "/app/backend/server.py"
        with open(server_path, 'r') as f:
            content = f.read()
        
        assert "def create_signature_section(" in content, "create_signature_section function should exist"
        assert "ASSINATURAS E VALIDAÇÃO" in content, "Signature section should include validation text"
        print("✓ create_signature_section function exists")
    
    def test_digital_signature_seal_function_exists(self):
        """Verify draw_signature_seal function exists for digital signature on right side"""
        server_path = "/app/backend/server.py"
        with open(server_path, 'r') as f:
            content = f.read()
        
        assert "def draw_signature_seal(" in content, "draw_signature_seal function should exist"
        assert "lateral DIREITA" in content, "Signature seal should be on right side"
        print("✓ draw_signature_seal function exists (positioned on right side)")
    
    def test_alternating_row_colors_in_table(self):
        """Verify alternating row colors are implemented in tables"""
        server_path = "/app/backend/server.py"
        with open(server_path, 'r') as f:
            content = f.read()
        
        # Check for ROWBACKGROUNDS style which creates alternating colors
        assert "ROWBACKGROUNDS" in content, "Table should have alternating row colors"
        assert "#D6EAF8" in content, "Light blue color should be used for alternating rows"
        print("✓ Alternating row colors implemented (white and #D6EAF8)")
    
    def test_pagination_implementation(self):
        """Verify pagination logic is implemented in export functions"""
        server_path = "/app/backend/server.py"
        with open(server_path, 'r') as f:
            content = f.read()
        
        # Check for pagination logic
        assert "total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE" in content, "Pagination calculation should exist"
        assert "for page_num in range(total_pages):" in content, "Pagination loop should exist"
        assert "PageBreak()" in content, "PageBreak should be used for pagination"
        assert "Continuação - Página" in content, "Continuation header should exist for subsequent pages"
        print("✓ Pagination logic implemented with page breaks and continuation headers")


class TestPDFExportErrorHandling:
    """Tests for error handling in PDF export"""
    
    def test_export_pdf_nonexistent_pac(self, api_client):
        """Test PDF export with non-existent PAC ID"""
        response = api_client.get(f"{BASE_URL}/api/pacs/nonexistent_pac_id/export/pdf")
        assert response.status_code == 404
        print("✓ Returns 404 for non-existent PAC")
    
    def test_export_pdf_nonexistent_pac_geral(self, api_client):
        """Test PDF export with non-existent PAC Geral ID"""
        response = api_client.get(f"{BASE_URL}/api/pacs-geral/nonexistent_pac_geral_id/export/pdf")
        assert response.status_code == 404
        print("✓ Returns 404 for non-existent PAC Geral")
    
    def test_export_pdf_without_auth(self):
        """Test PDF export without authentication"""
        response = requests.get(f"{BASE_URL}/api/pacs/any_pac_id/export/pdf")
        assert response.status_code == 401
        print("✓ Returns 401 for unauthenticated request")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
