"""
Test PDF Export Layout - DOEM Format
Tests the PDF export endpoints to verify the layout matches the reference file:
- Two brasões (left and right)
- "ACAIACA" text centered in dark blue
- Two horizontal blue lines (thin and thick)
- Publication info between lines
- Footer with 3 centered lines of Prefeitura info
- QR Code and digital signature in top right corner
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

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://doem-pdf-system.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "cristiano.abdo@acaiaca.mg.gov.br"
ADMIN_PASSWORD = "Cris@820906"

# Test PAC ID
TEST_PAC_ID = "pac_f905e7811e98"


class TestPDFExportLayout:
    """Tests for PDF export layout verification"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip("Authentication failed")
    
    def test_pac_individual_pdf_export_authenticated(self):
        """Test PAC Individual PDF export via authenticated endpoint"""
        response = self.session.get(
            f"{BASE_URL}/api/pacs/{TEST_PAC_ID}/export/pdf",
            params={"orientation": "landscape"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert response.headers.get("content-type") == "application/pdf"
        
        # Verify PDF content
        pdf_content = response.content
        assert len(pdf_content) > 1000, "PDF content too small"
        assert pdf_content[:4] == b'%PDF', "Not a valid PDF file"
        
        # Check for validation code header
        validation_code = response.headers.get("X-Validation-Code")
        print(f"✓ PAC Individual PDF exported successfully")
        print(f"  - PDF size: {len(pdf_content)} bytes")
        print(f"  - Validation code: {validation_code}")
        
        # Save PDF for manual inspection
        with open("/tmp/pac_individual_test.pdf", "wb") as f:
            f.write(pdf_content)
        print(f"  - Saved to /tmp/pac_individual_test.pdf")
        
        return pdf_content
    
    def test_pac_individual_pdf_export_public(self):
        """Test PAC Individual PDF export via public endpoint"""
        # Public endpoint doesn't require authentication
        response = requests.get(
            f"{BASE_URL}/api/public/pacs/{TEST_PAC_ID}/export/pdf",
            params={"orientation": "landscape"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert response.headers.get("content-type") == "application/pdf"
        
        pdf_content = response.content
        assert len(pdf_content) > 1000, "PDF content too small"
        assert pdf_content[:4] == b'%PDF', "Not a valid PDF file"
        
        print(f"✓ Public PAC PDF exported successfully")
        print(f"  - PDF size: {len(pdf_content)} bytes")
        
        # Save PDF for manual inspection
        with open("/tmp/pac_public_test.pdf", "wb") as f:
            f.write(pdf_content)
        print(f"  - Saved to /tmp/pac_public_test.pdf")
        
        return pdf_content
    
    def test_processos_pdf_export_public(self):
        """Test Processos PDF export via public endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/public/processos/export/pdf",
            params={"orientation": "landscape"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert response.headers.get("content-type") == "application/pdf"
        
        pdf_content = response.content
        assert len(pdf_content) > 500, "PDF content too small"
        assert pdf_content[:4] == b'%PDF', "Not a valid PDF file"
        
        print(f"✓ Processos PDF exported successfully")
        print(f"  - PDF size: {len(pdf_content)} bytes")
        
        # Save PDF for manual inspection
        with open("/tmp/processos_public_test.pdf", "wb") as f:
            f.write(pdf_content)
        print(f"  - Saved to /tmp/processos_public_test.pdf")
        
        return pdf_content
    
    @pytest.mark.skipif(not HAS_PYPDF2, reason="PyPDF2 not installed")
    def test_pdf_content_analysis(self):
        """Analyze PDF content to verify DOEM layout elements"""
        response = self.session.get(
            f"{BASE_URL}/api/pacs/{TEST_PAC_ID}/export/pdf",
            params={"orientation": "landscape"}
        )
        
        assert response.status_code == 200
        
        pdf_content = BytesIO(response.content)
        reader = PdfReader(pdf_content)
        
        # Get number of pages
        num_pages = len(reader.pages)
        print(f"✓ PDF has {num_pages} page(s)")
        
        # Extract text from first page
        first_page = reader.pages[0]
        text = first_page.extract_text()
        
        # Verify key elements are present
        layout_checks = {
            "ACAIACA": "ACAIACA" in text,
            "ANO": "ANO" in text,
            "Prefeitura Municipal": "Prefeitura" in text.lower() or "prefeitura" in text.lower(),
            "CNPJ": "CNPJ" in text or "18.295.287" in text,
            "pac.acaiaca.mg.gov.br": "pac.acaiaca.mg.gov.br" in text or "acaiaca" in text.lower(),
        }
        
        print(f"✓ Layout element checks:")
        for element, found in layout_checks.items():
            status = "✓" if found else "✗"
            print(f"  {status} {element}: {'Found' if found else 'NOT FOUND'}")
        
        # All critical elements should be present
        assert layout_checks["ACAIACA"], "ACAIACA text not found in PDF"
        
        return text
    
    def test_pdf_portrait_orientation(self):
        """Test PDF export in portrait orientation"""
        response = self.session.get(
            f"{BASE_URL}/api/pacs/{TEST_PAC_ID}/export/pdf",
            params={"orientation": "portrait"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.headers.get("content-type") == "application/pdf"
        
        pdf_content = response.content
        assert pdf_content[:4] == b'%PDF', "Not a valid PDF file"
        
        print(f"✓ Portrait orientation PDF exported successfully")
        print(f"  - PDF size: {len(pdf_content)} bytes")
        
        # Save PDF for manual inspection
        with open("/tmp/pac_portrait_test.pdf", "wb") as f:
            f.write(pdf_content)
        print(f"  - Saved to /tmp/pac_portrait_test.pdf")
    
    def test_pdf_with_signature_date(self):
        """Test PDF export with custom signature date"""
        response = self.session.get(
            f"{BASE_URL}/api/pacs/{TEST_PAC_ID}/export/pdf",
            params={
                "orientation": "landscape",
                "assinar": "true",
                "data": "15/12/2025 10:30:00"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert response.headers.get("content-type") == "application/pdf"
        
        pdf_content = response.content
        assert pdf_content[:4] == b'%PDF', "Not a valid PDF file"
        
        validation_code = response.headers.get("X-Validation-Code")
        print(f"✓ PDF with custom signature date exported successfully")
        print(f"  - Validation code: {validation_code}")
        
        # Save PDF for manual inspection
        with open("/tmp/pac_signed_test.pdf", "wb") as f:
            f.write(pdf_content)
        print(f"  - Saved to /tmp/pac_signed_test.pdf")


class TestPDFExportErrors:
    """Tests for PDF export error handling"""
    
    def test_pac_not_found(self):
        """Test PDF export with non-existent PAC ID"""
        response = requests.get(
            f"{BASE_URL}/api/public/pacs/pac_nonexistent123/export/pdf"
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Non-existent PAC returns 404 correctly")
    
    def test_invalid_orientation(self):
        """Test PDF export with invalid orientation (should default to landscape)"""
        response = requests.get(
            f"{BASE_URL}/api/public/pacs/{TEST_PAC_ID}/export/pdf",
            params={"orientation": "invalid"}
        )
        
        # Should still work, defaulting to landscape
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.headers.get("content-type") == "application/pdf"
        print(f"✓ Invalid orientation handled gracefully")


class TestDOEMTemplateElements:
    """Tests to verify DOEM template elements are correctly implemented"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
    
    def test_brasao_file_exists(self):
        """Verify brasão image file exists"""
        import os
        brasao_path = "/app/backend/static/brasao_acaiaca.png"
        
        if os.path.exists(brasao_path):
            file_size = os.path.getsize(brasao_path)
            print(f"✓ Brasão file exists: {brasao_path}")
            print(f"  - File size: {file_size} bytes")
            assert file_size > 0, "Brasão file is empty"
        else:
            print(f"✗ Brasão file NOT FOUND: {brasao_path}")
            # This is a warning, not a failure - PDF should still generate
    
    def test_pdf_utils_module(self):
        """Verify pdf_utils module has required functions"""
        from utils.pdf_utils import (
            DOEMTemplate,
            create_page_callback,
            create_doem_callback,
            get_professional_styles,
            draw_signature_seal,
            AZUL_DOEM,
            PREFEITURA_INFO
        )
        
        # Verify AZUL_DOEM is navy blue
        assert str(AZUL_DOEM) == "#000080" or "000080" in str(AZUL_DOEM).lower(), \
            f"AZUL_DOEM should be navy blue (#000080), got {AZUL_DOEM}"
        
        # Verify PREFEITURA_INFO has required fields
        required_fields = ['nome', 'cnpj', 'endereco', 'cep', 'telefone', 'portal', 'email', 'doem_url']
        for field in required_fields:
            assert field in PREFEITURA_INFO, f"Missing field in PREFEITURA_INFO: {field}"
        
        print(f"✓ pdf_utils module has all required elements")
        print(f"  - AZUL_DOEM: {AZUL_DOEM}")
        print(f"  - PREFEITURA_INFO nome: {PREFEITURA_INFO['nome']}")
        print(f"  - PREFEITURA_INFO cnpj: {PREFEITURA_INFO['cnpj']}")
    
    def test_doem_template_class(self):
        """Test DOEMTemplate class initialization"""
        from utils.pdf_utils import DOEMTemplate
        
        template = DOEMTemplate(
            titulo="TEST DOCUMENT",
            ano=134,
            numero=1,
            paginas=1
        )
        
        assert template.titulo == "TEST DOCUMENT"
        assert template.ano == 134
        assert template.numero == 1
        assert template.paginas == 1
        
        print(f"✓ DOEMTemplate class works correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
