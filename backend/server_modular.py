"""
Planejamento Acaiaca - Sistema de Gestão Municipal
Servidor Principal (Refatorado)

Este arquivo serve como ponto de entrada da aplicação,
importando e registrando os routers de cada módulo.
"""
from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import os
import logging

# Carregar variáveis de ambiente
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('planejamento_acaiaca')

# ===== CONFIGURAÇÃO DO BANCO DE DADOS =====
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'planejamento_acaiaca')

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# ===== CONFIGURAÇÃO DO FASTAPI =====
app = FastAPI(
    title="Planejamento Acaiaca - API",
    description="""
    ## Sistema de Gestão Municipal - Prefeitura de Acaiaca/MG
    
    API completa para gerenciamento de:
    - **PAC** - Plano Anual de Contratações
    - **PAC Geral** - Consolidação de PACs
    - **PAC Obras** - Obras e Serviços de Engenharia
    - **Gestão Processual** - Processos Licitatórios
    - **MROSC** - Prestação de Contas (Lei 13.019/2014)
    - **Portal de Transparência** - Dados Públicos
    
    ### Autenticação
    Utilize o endpoint `/api/auth/login` para obter um token JWT.
    Inclua o token no header: `Authorization: Bearer <token>`
    """,
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# ===== MIDDLEWARE =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de performance (opcional)
try:
    from middleware.performance import PerformanceMiddleware
    app.add_middleware(PerformanceMiddleware)
    logger.info("Performance middleware loaded")
except ImportError:
    logger.warning("Performance middleware not available")

# ===== ROUTERS =====
api_router = APIRouter(prefix="/api")
public_router = APIRouter(prefix="/api/public", tags=["Portal Público"])

# ===== IMPORTAR E CONFIGURAR MÓDULOS =====

# Shared functions
from shared import set_database
set_database(db)

# Auth routes
from routes.auth_refactored import router as auth_router, setup_auth_routes
setup_auth_routes(db)
api_router.include_router(auth_router)

# ===== INCLUIR ROUTERS NO APP =====
app.include_router(api_router)
app.include_router(public_router)

# ===== HEALTH CHECK =====
@app.get("/api/health")
async def health_check():
    """Verificação de saúde da API"""
    try:
        # Verificar conexão com MongoDB
        await db.command('ping')
        return {
            "status": "healthy",
            "database": "connected",
            "version": "3.0.0"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )

# ===== STARTUP =====
@app.on_event("startup")
async def startup():
    """Executa na inicialização da aplicação"""
    logger.info("Starting Planejamento Acaiaca API...")
    
    # Criar índices no MongoDB
    try:
        await db.users.create_index("email", unique=True)
        await db.users.create_index("user_id", unique=True)
        await db.pacs.create_index("pac_id", unique=True)
        await db.processos.create_index("processo_id", unique=True)
        await db.processos.create_index("ano")
        logger.info("Database indexes created")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
    
    # Criar usuário admin padrão
    admin_email = "cristiano.abdo@acaiaca.mg.gov.br"
    admin_exists = await db.users.find_one({'email': admin_email})
    if not admin_exists:
        import bcrypt
        import uuid
        from datetime import datetime, timezone
        
        admin_user = {
            'user_id': f"user_{uuid.uuid4().hex[:12]}",
            'email': admin_email,
            'name': "Cristiano Abdo de Souza",
            'password_hash': bcrypt.hashpw("Cris@820906".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'is_admin': True,
            'is_active': True,
            'picture': None,
            'created_at': datetime.now(timezone.utc)
        }
        await db.users.insert_one(admin_user)
        logger.info(f"Admin user created: {admin_email}")

@app.on_event("shutdown")
async def shutdown():
    """Executa no encerramento da aplicação"""
    logger.info("Shutting down Planejamento Acaiaca API...")
    client.close()


# ===== IMPORTAR ROTAS DO SERVER.PY ORIGINAL =====
# Temporariamente, importamos as rotas do server.py original
# até que todos os módulos sejam refatorados

# Por enquanto, usar o server.py original
# Esta linha será removida quando a refatoração estiver completa
