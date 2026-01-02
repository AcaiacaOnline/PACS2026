"""
Test suite for Processos Year Filter Bug Fix
Tests:
1. GET /api/processos/anos - should return available years with ano_atual=2025
2. GET /api/processos?ano=2025 - should return 70 processos
3. Year extraction from numero_processo (e.g., PRC - 0006/2025 -> ano=2025)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestProcessosYearFilter:
    """Tests for processos year filter functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login with admin credentials
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "cristiano.abdo@acaiaca.mg.gov.br",
            "password": "Cris@820906"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.authenticated = True
        else:
            self.authenticated = False
            pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_get_processos_anos_endpoint(self):
        """Test GET /api/processos/anos returns available years"""
        response = self.session.get(f"{BASE_URL}/api/processos/anos")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "anos" in data, "Response should contain 'anos' field"
        assert "ano_atual" in data, "Response should contain 'ano_atual' field"
        
        # Verify anos is a list
        assert isinstance(data["anos"], list), "anos should be a list"
        
        # Verify 2025 is in the list (since processos are from 2025)
        assert 2025 in data["anos"], "2025 should be in the available years"
        
        # Verify ano_atual is 2025 (since processos exist in 2025)
        assert data["ano_atual"] == 2025, f"ano_atual should be 2025, got {data['ano_atual']}"
        
        print(f"✓ GET /api/processos/anos - anos: {data['anos']}, ano_atual: {data['ano_atual']}")
    
    def test_get_processos_filtered_by_2025(self):
        """Test GET /api/processos?ano=2025 returns processos from 2025"""
        response = self.session.get(f"{BASE_URL}/api/processos?ano=2025")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Should return approximately 70 processos
        count = len(data)
        print(f"✓ GET /api/processos?ano=2025 - returned {count} processos")
        
        # Verify count is around 70 (allowing some tolerance)
        assert count >= 60, f"Expected at least 60 processos, got {count}"
        assert count <= 80, f"Expected at most 80 processos, got {count}"
        
        # Verify all returned processos have ano=2025
        for processo in data:
            assert processo.get("ano") == 2025, f"Processo {processo.get('numero_processo')} should have ano=2025, got {processo.get('ano')}"
    
    def test_processos_have_ano_field(self):
        """Test that processos have the 'ano' field populated"""
        response = self.session.get(f"{BASE_URL}/api/processos?ano=2025")
        
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0, "Should have at least one processo"
        
        # Check first few processos have ano field
        for processo in data[:5]:
            assert "ano" in processo, f"Processo should have 'ano' field"
            assert processo["ano"] is not None, f"Processo ano should not be None"
            assert processo["ano"] == 2025, f"Processo ano should be 2025"
            
            # Verify numero_processo format matches ano
            numero = processo.get("numero_processo", "")
            if "/2025" in numero:
                print(f"✓ Processo {numero} has ano={processo['ano']} (extracted correctly)")
    
    def test_processos_without_ano_filter(self):
        """Test GET /api/processos without filter returns all processos"""
        response = self.session.get(f"{BASE_URL}/api/processos")
        
        assert response.status_code == 200
        
        data = response.json()
        total_count = len(data)
        print(f"✓ GET /api/processos (no filter) - returned {total_count} processos")
        
        # Should return all processos
        assert total_count >= 60, f"Expected at least 60 processos total, got {total_count}"
    
    def test_processos_filter_by_nonexistent_year(self):
        """Test GET /api/processos?ano=2030 returns empty list"""
        response = self.session.get(f"{BASE_URL}/api/processos?ano=2030")
        
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) == 0, f"Expected 0 processos for year 2030, got {len(data)}"
        
        print("✓ GET /api/processos?ano=2030 - returned 0 processos (correct)")


class TestDOEMPDFGeneration:
    """Tests for DOEM PDF generation with custom header/footer"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login with admin credentials
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "cristiano.abdo@acaiaca.mg.gov.br",
            "password": "Cris@820906"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.authenticated = True
        else:
            self.authenticated = False
            pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_doem_edicoes_list(self):
        """Test GET /api/doem/edicoes returns list of editions"""
        response = self.session.get(f"{BASE_URL}/api/doem/edicoes")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        print(f"✓ GET /api/doem/edicoes - returned {len(data)} edições")
        
        # Return the first edition ID for PDF test
        if len(data) > 0:
            return data[0].get("edicao_id")
        return None
    
    def test_doem_pdf_generation(self):
        """Test DOEM PDF generation with custom header/footer"""
        # First get list of editions
        response = self.session.get(f"{BASE_URL}/api/doem/edicoes")
        assert response.status_code == 200
        
        edicoes = response.json()
        if len(edicoes) == 0:
            pytest.skip("No DOEM editions available for PDF test")
        
        # Get the first edition ID (doem_57dc5741c733)
        edicao_id = edicoes[0].get("edicao_id")
        print(f"Testing PDF generation for edition: {edicao_id}")
        
        # Generate PDF
        pdf_response = self.session.get(f"{BASE_URL}/api/doem/edicoes/{edicao_id}/pdf")
        
        assert pdf_response.status_code == 200, f"Expected 200, got {pdf_response.status_code}"
        
        # Verify content type is PDF
        content_type = pdf_response.headers.get("content-type", "")
        assert "application/pdf" in content_type, f"Expected PDF content type, got {content_type}"
        
        # Verify PDF has content
        pdf_content = pdf_response.content
        assert len(pdf_content) > 1000, f"PDF should have substantial content, got {len(pdf_content)} bytes"
        
        # Verify PDF header (PDF files start with %PDF)
        assert pdf_content[:4] == b'%PDF', "Content should be a valid PDF file"
        
        print(f"✓ DOEM PDF generated successfully - {len(pdf_content)} bytes")
    
    def test_doem_images_exist(self):
        """Test that DOEM header/footer images exist on server"""
        import os
        
        # These paths are relative to the backend directory
        brasao_path = "/app/backend/brasao_doem_small.png"
        rodape_path = "/app/backend/rodape_doem_small.jpg"
        
        assert os.path.exists(brasao_path), f"Brasão image not found at {brasao_path}"
        assert os.path.exists(rodape_path), f"Rodapé image not found at {rodape_path}"
        
        # Verify file sizes are reasonable
        brasao_size = os.path.getsize(brasao_path)
        rodape_size = os.path.getsize(rodape_path)
        
        assert brasao_size > 1000, f"Brasão image too small: {brasao_size} bytes"
        assert rodape_size > 1000, f"Rodapé image too small: {rodape_size} bytes"
        
        print(f"✓ Brasão image exists: {brasao_size} bytes")
        print(f"✓ Rodapé image exists: {rodape_size} bytes")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
