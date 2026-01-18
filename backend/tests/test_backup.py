"""
Test Backup and Restore Routes
"""
import pytest
import json
from io import BytesIO


class TestBackup:
    """Tests for backup and restore routes"""
    
    def test_backup_info(self, client, auth_headers):
        """Test getting backup info"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/backup/info", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "current_data" in data
        assert "total_records" in data
        assert data["backup_available"] == True
    
    def test_backup_export(self, client, auth_headers):
        """Test exporting backup data"""
        if not auth_headers:
            pytest.skip("No auth token available")
        
        response = client.get("/api/backup/export", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/json"
        
        # Verify it's valid JSON
        data = response.json()
        assert "metadata" in data
        assert "users" in data
        assert "pacs" in data
        assert data["metadata"]["system"] == "Planejamento Acaiaca"
    
    def test_backup_info_unauthenticated(self, client):
        """Test backup info without authentication"""
        response = client.get("/api/backup/info")
        assert response.status_code == 401


class TestClassificacao:
    """Tests for classification routes"""
    
    def test_get_classificacao_codigos(self, client, auth_headers):
        """Test getting classification codes"""
        response = client.get("/api/classificacao/codigos")
        # This endpoint might be public or require auth
        if response.status_code == 401:
            response = client.get("/api/classificacao/codigos", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "339030" in data
        assert "339039" in data
        assert "449052" in data
        
        # Verify structure
        assert "nome" in data["339030"]
        assert "subitens" in data["339030"]
