"""
Pytest configuration and fixtures for Planejamento Acaiaca tests
"""
import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from httpx import AsyncClient, ASGITransport
import os
from datetime import datetime, timezone
import sys

# Add backend to path
sys.path.insert(0, '/app/backend')


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db():
    """Database fixture - uses test database"""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'pac_acaiaca') + '_test'
    
    client = AsyncIOMotorClient(mongo_url)
    database = client[db_name]
    
    yield database
    
    # Cleanup - drop test collections after tests
    # await database.drop_collection('test_users')
    client.close()


@pytest.fixture(scope="session")
async def app():
    """FastAPI application fixture"""
    from server import app as fastapi_app
    yield fastapi_app


@pytest.fixture(scope="session")
async def client(app):
    """Async HTTP client fixture"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def admin_token(client):
    """Get admin authentication token"""
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "cristiano.abdo@acaiaca.mg.gov.br",
            "password": "Cris@820906"
        }
    )
    if response.status_code == 200:
        return response.json().get("token")
    return None


@pytest.fixture
def auth_headers(admin_token):
    """Authorization headers with admin token"""
    if admin_token:
        return {"Authorization": f"Bearer {admin_token}"}
    return {}


# Test data fixtures
@pytest.fixture
def sample_pac_data():
    """Sample PAC data for tests"""
    return {
        "secretaria": "Secretaria de Teste",
        "secretario": "Secretário Teste",
        "fiscal": "Fiscal Teste",
        "telefone": "(31) 99999-9999",
        "email": "teste@acaiaca.mg.gov.br",
        "endereco": "Rua Teste, 123",
        "ano": "2026"
    }


@pytest.fixture
def sample_pac_item_data():
    """Sample PAC item data for tests"""
    return {
        "tipo": "Material",
        "catmat": "123456",
        "descricao": "Material de teste",
        "unidade": "UN",
        "quantidade": 10,
        "valorUnitario": 50.00,
        "prioridade": "Alta",
        "justificativa": "Necessário para testes"
    }


@pytest.fixture
def sample_processo_data():
    """Sample processo data for tests"""
    return {
        "numero_processo": "PRC-0001/2025",
        "modalidade_contratacao": "Pregão Eletrônico",
        "status": "Em Elaboração",
        "objeto": "Aquisição de material de teste",
        "responsavel": "Responsável Teste",
        "secretaria": "Secretaria de Teste",
        "secretario": "Secretário Teste",
        "ano": 2025
    }


@pytest.fixture
def sample_mrosc_projeto_data():
    """Sample MROSC project data for tests"""
    return {
        "nome_projeto": "Projeto de Teste MROSC",
        "objeto": "Objeto do projeto de teste",
        "organizacao_parceira": "OSC Teste",
        "cnpj_parceira": "12.345.678/0001-90",
        "responsavel_osc": "Responsável OSC",
        "data_inicio": datetime.now(timezone.utc).isoformat(),
        "data_conclusao": datetime(2026, 12, 31, tzinfo=timezone.utc).isoformat(),
        "prazo_meses": 12,
        "valor_total": 100000.00,
        "valor_repasse_publico": 80000.00,
        "valor_contrapartida": 20000.00,
        "status": "ELABORACAO"
    }
