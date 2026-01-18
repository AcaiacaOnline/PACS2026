from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, UploadFile, File, BackgroundTasks, Form
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import re
import logging
import hashlib
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from io import BytesIO
import httpx
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from striprtf.striprtf import rtf_to_text

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# ============ IMPORTAÇÃO DE MODELOS REFATORADOS ============
# Os modelos agora são importados do pacote 'models/' para reduzir duplicação
from models import (
    # User models
    User as UserModel, UserCreate as UserCreateModel, UserUpdate as UserUpdateModel,
    UserLogin as UserLoginModel, UserListItem as UserListItemModel,
    UserPermissions as UserPermissionsModel, UserSignatureData as UserSignatureDataModel,
    # PAC models
    PAC as PACModel, PACCreate as PACCreateModel, PACUpdate as PACUpdateModel,
    PACItem as PACItemModel, PACItemCreate as PACItemCreateModel, PACItemUpdate as PACItemUpdateModel,
    PACGeral as PACGeralModel, PACGeralCreate as PACGeralCreateModel, PACGeralUpdate as PACGeralUpdateModel,
    PACGeralItem as PACGeralItemModel, PACGeralItemCreate as PACGeralItemCreateModel, PACGeralItemUpdate as PACGeralItemUpdateModel,
    # PAC Obras models
    PACGeralObras as PACGeralObrasModel, PACGeralObrasCreate as PACGeralObrasCreateModel, PACGeralObrasUpdate as PACGeralObrasUpdateModel,
    PACGeralObrasItem as PACGeralObrasItemModel, PACGeralObrasItemCreate as PACGeralObrasItemCreateModel, PACGeralObrasItemUpdate as PACGeralObrasItemUpdateModel,
    CLASSIFICACAO_OBRAS_SERVICOS,
    # Processo models
    Processo as ProcessoModel, ProcessoCreate as ProcessoCreateModel, ProcessoUpdate as ProcessoUpdateModel,
    PaginatedResponse as PaginatedResponseModel,
    # DOEM models
    DOEMPublicacao as DOEMPublicacaoModel, DOEMPublicacaoCreate as DOEMPublicacaoCreateModel,
    DOEMAssinante as DOEMAssinanteModel, DOEMAssinatura as DOEMAssinaturaModel,
    DOEMEdicao as DOEMEdicaoModel, DOEMEdicaoCreate as DOEMEdicaoCreateModel, DOEMEdicaoUpdate as DOEMEdicaoUpdateModel,
    DOEMConfig as DOEMConfigModel, DOEMConfigUpdate as DOEMConfigUpdateModel,
    DOEM_SEGMENTOS, DOEM_TIPOS_PUBLICACAO,
    # Newsletter models
    NewsletterInscrito as NewsletterInscritoModel, NewsletterInscricaoPublica as NewsletterInscricaoPublicaModel,
    NewsletterInscricaoManual as NewsletterInscricaoManualModel,
    # MROSC models
    ProjetoMROSC as ProjetoMROSCModel, ProjetoMROSCCreate as ProjetoMROSCCreateModel, ProjetoMROSCUpdate as ProjetoMROSCUpdateModel,
    RecursoHumanoMROSC as RecursoHumanoMROSCModel, RecursoHumanoMROSCCreate as RecursoHumanoMROSCCreateModel,
    DespesaMROSC as DespesaMROSCModel, DespesaMROSCCreate as DespesaMROSCCreateModel,
    DocumentoMROSC as DocumentoMROSCModel, DocumentoMROSCCreate as DocumentoMROSCCreateModel,
    NATUREZAS_DESPESA_MROSC,
)

# ============ CONFIGURAÇÕES DE EMAIL ============
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'mail.acaiaca.mg.gov.br')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '465'))
SMTP_EMAIL = os.environ.get('SMTP_EMAIL', 'naoresponda@acaiaca.mg.gov.br')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_USE_SSL = os.environ.get('SMTP_USE_SSL', 'true').lower() == 'true'

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ.get('JWT_SECRET', 'pac-acaiaca-secret-key-2026')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DAYS = 7

# ===== CONFIGURAÇÃO DO FASTAPI COM SWAGGER =====
app = FastAPI(
    title="Planejamento Acaiaca - Sistema de Gestão Municipal",
    description="""
## Sistema de Gestão Municipal - Prefeitura de Acaiaca/MG

API REST completa para gestão municipal incluindo:

### 📋 Módulos Disponíveis
- **PAC Individual** - Planos Anuais de Contratação por Secretaria
- **PAC Geral** - Visão Consolidada de todas as Secretarias
- **PAC Obras** - Obras e Serviços de Engenharia
- **Gestão Processual** - Controle de Processos Licitatórios
- **MROSC** - Prestação de Contas de OSCs (Lei 13.019/2014)
- **DOEM** - Diário Oficial Eletrônico Municipal
- **Portal de Transparência** - Acesso Público aos Dados

### 🔐 Autenticação
Utilize o endpoint `/api/auth/login` para obter um token JWT.
Inclua o token no header `Authorization: Bearer {token}` em todas as requisições autenticadas.

### 📊 WebSocket
Notificações em tempo real disponíveis em `/api/ws/notifications/{user_id}`

### 📧 Contato
- Email: planejamento@acaiaca.mg.gov.br
- CNPJ: 18.295.287/0001-90
    """,
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    openapi_tags=[
        {"name": "Autenticação", "description": "Login, registro e gerenciamento de sessão"},
        {"name": "Usuários", "description": "Gerenciamento de usuários do sistema"},
        {"name": "PAC Individual", "description": "Planos Anuais de Contratação por Secretaria"},
        {"name": "PAC Geral", "description": "PAC consolidado de todas as secretarias"},
        {"name": "PAC Obras", "description": "Obras e serviços de engenharia"},
        {"name": "Gestão Processual", "description": "Processos licitatórios"},
        {"name": "MROSC", "description": "Prestação de Contas - Lei 13.019/2014"},
        {"name": "DOEM", "description": "Diário Oficial Eletrônico Municipal"},
        {"name": "Portal da Transparência", "description": "Endpoints públicos"},
        {"name": "Dashboard Analítico", "description": "Estatísticas e métricas"},
        {"name": "Sistema de Alertas", "description": "Alertas e notificações"},
        {"name": "Relatórios Gerenciais", "description": "Geração de relatórios PDF/XLSX"},
        {"name": "Backup", "description": "Backup e restauração de dados"},
        {"name": "WebSocket Notifications", "description": "Notificações em tempo real"},
        {"name": "Assinaturas Digitais", "description": "Assinatura e validação de documentos"},
    ],
    contact={
        "name": "Prefeitura Municipal de Acaiaca",
        "url": "https://acaiaca.mg.gov.br",
        "email": "planejamento@acaiaca.mg.gov.br"
    },
    license_info={
        "name": "Uso Restrito - Prefeitura de Acaiaca/MG",
        "url": "https://acaiaca.mg.gov.br"
    }
)

# Importar e registrar WebSocket router
from utils.websocket import router as ws_router, manager as ws_manager
from utils.websocket import (
    notify_processo_created, notify_mrosc_submitted, notify_mrosc_approved,
    notify_mrosc_correction, notify_system_alert, notify_backup_completed,
    Notification, NotificationType
)

# Importar logging
from utils.logging_config import get_logger, log_info, log_error, request_logger

logger = get_logger("server")

api_router = APIRouter(prefix="/api")

# Models
# NOTA: Modelos refatorados agora são importados do pacote 'models/'
# Os aliases abaixo mantêm compatibilidade com o código existente

# ============ ALIASES PARA MODELOS REFATORADOS ============
# Estes aliases apontam para os modelos no pacote 'models/' para manter
# compatibilidade com o código existente enquanto a refatoração é concluída.

# User models - usando aliases do pacote models/
UserPermissions = UserPermissionsModel
UserSignatureData = UserSignatureDataModel
User = UserModel
UserCreate = UserCreateModel
UserUpdate = UserUpdateModel
UserLogin = UserLoginModel
UserListItem = UserListItemModel

# PAC models - usando aliases do pacote models/
PAC = PACModel
PACCreate = PACCreateModel
PACUpdate = PACUpdateModel
PACItem = PACItemModel
PACItemCreate = PACItemCreateModel
PACItemUpdate = PACItemUpdateModel

# PAC Geral models - usando aliases do pacote models/
PACGeral = PACGeralModel
PACGeralCreate = PACGeralCreateModel
PACGeralUpdate = PACGeralUpdateModel
PACGeralItem = PACGeralItemModel
PACGeralItemCreate = PACGeralItemCreateModel
PACGeralItemUpdate = PACGeralItemUpdateModel

# PAC Obras models - usando aliases do pacote models/
PACGeralObras = PACGeralObrasModel
PACGeralObrasCreate = PACGeralObrasCreateModel
PACGeralObrasUpdate = PACGeralObrasUpdateModel
PACGeralObrasItem = PACGeralObrasItemModel
PACGeralObrasItemCreate = PACGeralObrasItemCreateModel
PACGeralObrasItemUpdate = PACGeralObrasItemUpdateModel

# Processo models - usando aliases do pacote models/
Processo = ProcessoModel
ProcessoCreate = ProcessoCreateModel
ProcessoUpdate = ProcessoUpdateModel
PaginatedResponse = PaginatedResponseModel

# DOEM models - usando aliases do pacote models/
DOEMPublicacao = DOEMPublicacaoModel
DOEMPublicacaoCreate = DOEMPublicacaoCreateModel
DOEMAssinante = DOEMAssinanteModel
DOEMAssinatura = DOEMAssinaturaModel
DOEMEdicao = DOEMEdicaoModel
DOEMEdicaoCreate = DOEMEdicaoCreateModel
DOEMEdicaoUpdate = DOEMEdicaoUpdateModel
DOEMConfig = DOEMConfigModel
DOEMConfigUpdate = DOEMConfigUpdateModel

# Newsletter models - usando aliases do pacote models/
NewsletterInscrito = NewsletterInscritoModel
NewsletterInscricaoPublica = NewsletterInscricaoPublicaModel
NewsletterInscricaoManual = NewsletterInscricaoManualModel

# MROSC models - usando aliases do pacote models/
ProjetoMROSC = ProjetoMROSCModel
ProjetoMROSCCreate = ProjetoMROSCCreateModel
ProjetoMROSCUpdate = ProjetoMROSCUpdateModel
RecursoHumanoMROSC = RecursoHumanoMROSCModel
RecursoHumanoMROSCCreate = RecursoHumanoMROSCCreateModel
DespesaMROSC = DespesaMROSCModel
DespesaMROSCCreate = DespesaMROSCCreateModel
DocumentoMROSC = DocumentoMROSCModel
DocumentoMROSCCreate = DocumentoMROSCCreateModel

# ============ MODELOS ESPECÍFICOS DO SERVER (NÃO REFATORADOS) ============
# Estes modelos são usados apenas internamente e não foram movidos para o pacote models/

class SignatureRequest(BaseModel):
    """Solicitação de assinatura digital com data opcional"""
    confirmar_assinatura: bool = False  # Deve ser True para confirmar
    data_assinatura: Optional[str] = None  # Formato: DD/MM/YYYY HH:MM:SS (retroativa ou futura)
    observacoes: Optional[str] = None  # Observações opcionais

class SignaturePayload(BaseModel):
    """Payload para assinatura de documento"""
    data_assinatura: Optional[str] = None  # Data customizada de assinatura

# ============ CONSTANTES ============
# Constantes de classificação são importadas do pacote models/

# ============ FUNÇÕES DE AUTENTICAÇÃO ============
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRATION_DAYS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def mask_cpf(cpf: str) -> str:
    """Mascara o CPF para exibição (LGPD): ***456.789-**"""
    if not cpf:
        return "***.***.***-**"
    # Remove formatação
    cpf_clean = re.sub(r'[^\d]', '', cpf)
    if len(cpf_clean) != 11:
        return "***.***.***-**"
    # Exibe apenas os dígitos centrais: ***456.789-**
    return f"***{cpf_clean[3:6]}.{cpf_clean[6:9]}-**"

async def get_current_user(request: Request) -> User:
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get('user_id')
        user_data = await db.users.find_one({'user_id': user_id}, {'_id': 0, 'password_hash': 0})
        if not user_data:
            raise HTTPException(status_code=401, detail="User not found")
        if not user_data.get('is_active', True):
            raise HTTPException(status_code=403, detail="User account is disabled")
        return User(**user_data)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# ============ FUNÇÕES DE AUTENTICAÇÃO ============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRATION_DAYS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> User:
    token = request.cookies.get('session_token')
    if not token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        session_doc = await db.user_sessions.find_one({'session_token': token}, {'_id': 0})
        if session_doc:
            expires_at = session_doc['expires_at']
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < datetime.now(timezone.utc):
                raise HTTPException(status_code=401, detail="Session expired")
            user_doc = await db.users.find_one({'user_id': session_doc['user_id']}, {'_id': 0})
            if not user_doc:
                raise HTTPException(status_code=401, detail="User not found")
            return User(**user_doc)
        else:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload['user_id']
            user_doc = await db.users.find_one({'user_id': user_id}, {'_id': 0})
            if not user_doc:
                raise HTTPException(status_code=401, detail="User not found")
            return User(**user_doc)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.on_event("startup")
async def create_admin_user():
    admin_email = "cristiano.abdo@acaiaca.mg.gov.br"
    admin_exists = await db.users.find_one({'email': admin_email})
    if not admin_exists:
        admin_user = {
            'user_id': f"user_{uuid.uuid4().hex[:12]}",
            'email': admin_email,
            'name': "Cristiano Abdo de Souza",
            'password_hash': hash_password("Cris@820906"),
            'is_admin': True,
            'is_active': True,
            'picture': None,
            'created_at': datetime.now(timezone.utc)
        }
        await db.users.insert_one(admin_user)
        logging.info(f"Admin user created: {admin_email}")

@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({'email': user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    
    # Definir permissões baseadas no tipo de usuário
    tipo_usuario = getattr(user_data, 'tipo_usuario', 'SERVIDOR')
    permissions = {
        'can_view': True,
        'can_edit': tipo_usuario == 'SERVIDOR',
        'can_delete': False,
        'can_export': tipo_usuario == 'SERVIDOR',
        'can_manage_users': False,
        'is_full_admin': False,
        'mrosc_only': tipo_usuario == 'PESSOA_EXTERNA'  # Pessoa externa só acessa MROSC
    }
    
    user_doc = {
        'user_id': user_id,
        'email': user_data.email,
        'name': user_data.name,
        'password_hash': hash_password(user_data.password),
        'is_admin': False,
        'is_active': True,
        'tipo_usuario': tipo_usuario,
        'picture': None,
        'permissions': permissions,
        'created_at': datetime.now(timezone.utc)
    }
    await db.users.insert_one(user_doc)
    user_doc.pop('password_hash')
    return User(**user_doc)

@api_router.post("/auth/login")
async def login(credentials: UserLogin, response: Response):
    user_doc = await db.users.find_one({'email': credentials.email}, {'_id': 0})
    if not user_doc or not verify_password(credentials.password, user_doc['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_jwt_token(user_doc['user_id'])
    response.set_cookie(key='session_token', value=token, httponly=True, secure=True, samesite='none', max_age=JWT_EXPIRATION_DAYS*24*60*60, path='/')
    user_doc.pop('password_hash')
    return {'token': token, 'user': User(**user_doc)}

@api_router.get("/auth/me", response_model=User)
async def get_me(request: Request):
    return await get_current_user(request)

@api_router.get("/auth/oauth/session")
async def oauth_session(request: Request, response: Response):
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session ID")
    async with httpx.AsyncClient() as client:
        try:
            auth_response = await client.get('https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data', headers={'X-Session-ID': session_id})
            auth_response.raise_for_status()
            data = auth_response.json()
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"OAuth failed: {str(e)}")
    user_doc = await db.users.find_one({'email': data['email']}, {'_id': 0})
    if not user_doc:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user_doc = {'user_id': user_id, 'email': data['email'], 'name': data['name'], 'password_hash': None, 'is_admin': False, 'is_active': True, 'picture': data.get('picture'), 'created_at': datetime.now(timezone.utc)}
        await db.users.insert_one(user_doc)
    session_doc = {'user_id': user_doc['user_id'], 'session_token': data['session_token'], 'expires_at': datetime.now(timezone.utc)+timedelta(days=7), 'created_at': datetime.now(timezone.utc)}
    await db.user_sessions.insert_one(session_doc)
    response.set_cookie(key='session_token', value=data['session_token'], httponly=True, secure=True, samesite='none', max_age=7*24*60*60, path='/')
    user_doc.pop('password_hash', None)
    return User(**user_doc)


@api_router.get("/auth/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    return user

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get('session_token')
    if token:
        await db.user_sessions.delete_many({'session_token': token})
    response.delete_cookie('session_token', path='/')
    return {'message': 'Logged out'}

# ============ CLASSIFICAÇÃO ORÇAMENTÁRIA (LEI 14.133/2021) ============

@api_router.get("/classificacao/codigos")
async def get_classificacao_codigos():
    """
    Retorna todos os códigos de classificação orçamentária conforme Lei 14.133/2021
    """
    codigos = {
        "339030": {
            "nome": "Material de Consumo",
            "subitens": [
                "Material de Consumo - Combustíveis e Lubrificantes Automotivos",
                "Combustíveis e Lubrificantes de Aviação",
                "Gás Engarrafado",
                "Explosivos e Munições",
                "Alimentos para Animais",
                "Gêneros de Alimentação",
                "Animais para Pesquisa e Abate",
                "Material Farmacológico",
                "Material Odontológico",
                "Material Químico",
                "Material de Coudelaria / Zootécnico",
                "Material de Caça e Pesca",
                "Material Educativo e Esportivo",
                "Material para Festividades e Homenagens",
                "Material de Expediente",
                "Material de Processamento de Dados",
                "Material de Acondicionamento e Embalagem",
                "Material de Cama, Mesa e Banho",
                "Material de Copa e Cozinha",
                "Material de Limpeza e Higienização",
                "Uniformes, Tecidos e Aviamentos",
                "Material para Manutenção de Bens Imóveis",
                "Material para Manutenção de Bens Móveis",
                "Material Elétrico e Eletrônico",
                "Material de Proteção e Segurança",
                "Material para Áudio, Vídeo e Foto",
                "Sementes, Mudas e Insumos",
                "Material Hospitalar",
                "Material para Manutenção de Veículos",
                "Ferramentas",
                "Material de Sinalização Visual"
            ]
        },
        "339036": {
            "nome": "Outros Serviços de Terceiros (Pessoa Física)",
            "subitens": [
                "Diárias a Colaboradores Eventuais",
                "Serviços Técnicos Profissionais",
                "Estagiários",
                "Locação de Imóveis",
                "Locação de Bens Móveis",
                "Manutenção e Conservação de Equipamentos",
                "Manutenção e Conservação de Veículos",
                "Manutenção e Conservação de Imóveis",
                "Serviços de Limpeza e Conservação",
                "Serviços Médicos e Odontológicos",
                "Serviços de Apoio Administrativo/Técnico",
                "Confecção de Uniformes/Bandeiras",
                "Fretes e Transportes de Encomendas",
                "Jetons"
            ]
        },
        "339039": {
            "nome": "Outros Serviços de Terceiros (Pessoa Jurídica)",
            "subitens": [
                "Assinaturas de Periódicos",
                "Condomínios",
                "Serviços Técnicos Profissionais",
                "Manutenção de Software",
                "Locação de Imóveis",
                "Locação de Máquinas e Equipamentos",
                "Manutenção e Conservação de Imóveis",
                "Manutenção e Conservação de Máquinas",
                "Manutenção e Conservação de Veículos",
                "Exposições, Congressos e Festividades",
                "Serviços de Energia Elétrica",
                "Serviços de Água e Esgoto",
                "Serviços de Telecomunicações",
                "Serviços Gráficos",
                "Seguros em Geral",
                "Confecção de Uniformes e Bandeiras",
                "Vale-Transporte",
                "Vigilância Ostensiva",
                "Limpeza e Conservação",
                "Serviços Bancários",
                "Serviços de Cópias e Reprodução",
                "Publicidade e Propaganda"
            ]
        },
        "449052": {
            "nome": "Equipamentos e Material Permanente",
            "subitens": [
                "Aparelhos de Medição e Orientação",
                "Aparelhos e Equipamentos de Comunicação",
                "Equipamentos Médico-Hospitalares",
                "Aparelhos e Utensílios Domésticos",
                "Coleções e Materiais Bibliográficos",
                "Mobiliário em Geral",
                "Equipamentos de Processamento de Dados",
                "Máquinas e Utensílios de Escritório",
                "Máquinas, Ferramentas e Utensílios de Oficina",
                "Equipamentos Hidráulicos e Elétricos",
                "Máquinas Agrícolas e Rodoviárias",
                "Veículos de Tração Mecânica",
                "Veículos Diversos",
                "Acessórios para Automóveis"
            ]
        }
    }
    return codigos

# ============ USER MANAGEMENT ROUTES (ADMIN ONLY) ============

async def require_admin(request: Request) -> User:
    user = await get_current_user(request)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

@api_router.get("/users", response_model=List[UserListItem])
async def get_users(request: Request):
    await require_admin(request)
    users = await db.users.find({}, {'_id': 0, 'password_hash': 0}).to_list(1000)
    return [UserListItem(**u) for u in users]

@api_router.post("/users", response_model=UserListItem)
async def create_user_admin(user_data: UserCreate, request: Request):
    await require_admin(request)
    existing = await db.users.find_one({'email': user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    
    # Preparar permissões
    permissions_data = None
    if user_data.permissions:
        permissions_data = user_data.permissions.model_dump()
    elif user_data.is_admin:
        # Admin tem todas as permissões por padrão
        permissions_data = {
            'can_view': True,
            'can_edit': True,
            'can_delete': True,
            'can_export': True,
            'can_manage_users': True,
            'is_full_admin': True
        }
    else:
        # Usuário padrão só pode visualizar
        permissions_data = {
            'can_view': True,
            'can_edit': False,
            'can_delete': False,
            'can_export': False,
            'can_manage_users': False,
            'is_full_admin': False
        }
    
    user_doc = {
        'user_id': user_id,
        'email': user_data.email,
        'name': user_data.name,
        'password_hash': hash_password(user_data.password),
        'is_admin': user_data.is_admin,
        'is_active': True,
        'picture': None,
        'permissions': permissions_data,
        'signature_data': user_data.signature_data.model_dump() if user_data.signature_data else None,
        'created_at': datetime.now(timezone.utc)
    }
    await db.users.insert_one(user_doc)
    user_doc.pop('password_hash')
    return UserListItem(**user_doc)

@api_router.put("/users/{user_id}", response_model=UserListItem)
async def update_user_admin(user_id: str, user_update: UserUpdate, request: Request):
    admin = await require_admin(request)
    if user_id == admin.user_id and user_update.is_admin is False:
        raise HTTPException(status_code=400, detail="Cannot remove your own admin rights")
    user = await db.users.find_one({'user_id': user_id}, {'_id': 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {}
    for k, v in user_update.model_dump().items():
        if v is not None:
            if k == 'permissions' and isinstance(v, dict):
                update_data['permissions'] = v
            elif k == 'signature_data' and isinstance(v, dict):
                update_data['signature_data'] = v
            else:
                update_data[k] = v
    
    if 'password' in update_data:
        update_data['password_hash'] = hash_password(update_data.pop('password'))
    
    # Se is_full_admin for marcado, atualiza is_admin também
    if update_data.get('permissions', {}).get('is_full_admin'):
        update_data['is_admin'] = True
    
    await db.users.update_one({'user_id': user_id}, {'$set': update_data})
    updated_user = await db.users.find_one({'user_id': user_id}, {'_id': 0, 'password_hash': 0})
    return UserListItem(**updated_user)

@api_router.delete("/users/{user_id}")
async def delete_user_admin(user_id: str, request: Request):
    admin = await require_admin(request)
    if user_id == admin.user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    result = await db.users.delete_one({'user_id': user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    await db.user_sessions.delete_many({'user_id': user_id})
    return {'message': 'User deleted'}

# ============ PAC ROUTES (WITH PERMISSIONS) ============

# ===== CONSTANTES DE MARGENS PADRONIZADAS (Lei 14.133/2021) =====
# Margens: 5cm (esquerda/direita), 3cm (superior/inferior)
REPORT_MARGIN_LEFT = 50*mm    # 5cm
REPORT_MARGIN_RIGHT = 50*mm   # 5cm
REPORT_MARGIN_TOP = 30*mm     # 3cm
REPORT_MARGIN_BOTTOM = 30*mm  # 3cm

# ===== CONSTANTES PARA PAGINAÇÃO DE ITENS =====
ITEMS_PER_PAGE = 15  # Máximo de 15 itens por página conforme solicitado

# ===== ESTILOS DE PDF PROFISSIONAIS =====
def get_professional_styles():
    """Retorna estilos profissionais para relatórios PDF"""
    styles = getSampleStyleSheet()
    
    # Cores do tema
    cor_primaria = colors.HexColor('#1F4E78')  # Azul escuro institucional
    cor_secundaria = colors.HexColor('#2E75B6')  # Azul médio
    cor_destaque = colors.HexColor('#FFC000')  # Amarelo dourado
    cor_texto = colors.HexColor('#333333')  # Cinza escuro
    cor_subtexto = colors.HexColor('#666666')  # Cinza médio
    
    custom_styles = {
        'title': ParagraphStyle(
            'ProfTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=cor_primaria,
            alignment=TA_CENTER,
            spaceAfter=4,
            fontName='Helvetica-Bold',
            leading=22
        ),
        'subtitle': ParagraphStyle(
            'ProfSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=cor_primaria,
            alignment=TA_CENTER,
            spaceAfter=3,
            fontName='Helvetica-Bold'
        ),
        'section_header': ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading3'],
            fontSize=11,
            textColor=cor_primaria,
            alignment=TA_LEFT,
            spaceAfter=6,
            spaceBefore=12,
            fontName='Helvetica-Bold',
            borderPadding=4
        ),
        'body': ParagraphStyle(
            'ProfBody',
            parent=styles['Normal'],
            fontSize=10,
            textColor=cor_texto,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            leading=14
        ),
        'small': ParagraphStyle(
            'ProfSmall',
            parent=styles['Normal'],
            fontSize=8,
            textColor=cor_subtexto,
            alignment=TA_LEFT,
            spaceAfter=2
        ),
        'legal': ParagraphStyle(
            'Legal',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique',
            spaceAfter=8
        ),
        'footer': ParagraphStyle(
            'ProfFooter',
            parent=styles['Normal'],
            fontSize=7,
            textColor=colors.grey,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        ),
        'table_cell': ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontSize=7,
            textColor=cor_texto,
            alignment=TA_LEFT,
            leading=9
        ),
        'table_header': ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontSize=7,
            textColor=colors.white,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
    }
    
    return custom_styles, cor_primaria, cor_secundaria, cor_destaque

def create_professional_header(pac_data: dict, styles: dict, is_pac_geral: bool = False):
    """Cria cabeçalho profissional para relatórios PAC"""
    elements = []
    cor_primaria = colors.HexColor('#1F4E78')
    
    # Logo path
    logo_path = ROOT_DIR / 'brasao_acaiaca.jpg'
    
    # Título principal
    elements.append(Paragraph('PREFEITURA MUNICIPAL DE ACAIACA', styles['title']))
    elements.append(Paragraph('Estado de Minas Gerais', ParagraphStyle('Estado', fontSize=10, alignment=TA_CENTER, textColor=colors.grey, spaceAfter=8)))
    
    if is_pac_geral:
        elements.append(Paragraph('PAC GERAL - PLANO ANUAL DE CONTRATAÇÕES CONSOLIDADO', styles['subtitle']))
    else:
        elements.append(Paragraph('PAC - PLANO ANUAL DE CONTRATAÇÕES', styles['subtitle']))
    
    elements.append(Paragraph(f'<i>Exercício {pac_data.get("ano", "2026")} - Lei Federal nº 14.133/2021</i>', styles['legal']))
    elements.append(Spacer(1, 3*mm))
    
    return elements

def create_info_box(pac_data: dict, styles: dict, is_pac_geral: bool = False):
    """Cria caixa de informações do PAC"""
    info_style = styles['small']
    cor_primaria = colors.HexColor('#1F4E78')
    
    if is_pac_geral:
        info_data = [
            [
                Paragraph(f'<b>PAC Geral:</b> {pac_data.get("nome_secretaria", "")}', info_style),
                Paragraph(f'<b>Exercício:</b> {pac_data.get("ano", "")}', info_style),
            ],
            [
                Paragraph(f'<b>Secretário(a):</b> {pac_data.get("secretario", "")}', info_style),
                Paragraph(f'<b>Fiscal do Contrato:</b> {pac_data.get("fiscal_contrato", "")}', info_style),
            ],
            [
                Paragraph(f'<b>Telefone:</b> {pac_data.get("telefone", "")}', info_style),
                Paragraph(f'<b>E-mail:</b> {pac_data.get("email", "")}', info_style),
            ]
        ]
        col_widths = [14*cm, 14*cm]
    else:
        info_data = [
            [
                Paragraph(f'<b>Secretaria/Órgão:</b> {pac_data.get("secretaria", "")}', info_style),
                Paragraph(f'<b>Exercício:</b> {pac_data.get("ano", "")}', info_style),
            ],
            [
                Paragraph(f'<b>Secretário(a) Responsável:</b> {pac_data.get("secretario", "")}', info_style),
                Paragraph(f'<b>Fiscal do Contrato:</b> {pac_data.get("fiscal", "")}', info_style),
            ],
            [
                Paragraph(f'<b>Telefone:</b> {pac_data.get("telefone", "")}', info_style),
                Paragraph(f'<b>E-mail:</b> {pac_data.get("email", "")}', info_style),
            ],
            [
                Paragraph(f'<b>Endereço:</b> {pac_data.get("endereco", "")}', info_style),
                '',
            ]
        ]
        col_widths = [14*cm, 14*cm]
    
    info_table = Table(info_data, colWidths=col_widths)
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F5F5F5')),
        ('BOX', (0, 0), (-1, -1), 1.5, cor_primaria),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    return info_table

def create_items_table_paginated(items: list, styles: dict, orientation: str = 'landscape', start_index: int = 1):
    """
    Cria tabela de itens com formatação profissional.
    Retorna lista de elementos (tabelas) para uma página.
    """
    cor_primaria = colors.HexColor('#1F4E78')
    cor_destaque = colors.HexColor('#FFC000')
    
    # Cabeçalhos
    headers = [
        '#', 
        'Código\nCATMAT', 
        'Descrição do Objeto', 
        'Unidade', 
        'Qtd', 
        'Valor\nUnitário', 
        'Valor\nTotal', 
        'Prioridade',
        'Justificativa',
        'Classificação\nOrçamentária'
    ]
    
    table_data = [headers]
    
    for idx, item in enumerate(items, start=start_index):
        # Classificação Orçamentária
        classificacao_text = ''
        if item.get('codigo_classificacao'):
            classificacao_text = f"{item['codigo_classificacao']}"
            if item.get('subitem_classificacao'):
                classificacao_text += f"\n{item['subitem_classificacao']}"
        
        descricao = item.get('descricao', '')
        justificativa = item.get('justificativa', '') or 'N/I'
        
        table_data.append([
            str(idx),
            item.get('catmat', ''),
            Paragraph(f"<font size=7>{descricao}</font>", styles['table_cell']),
            item.get('unidade', ''),
            str(int(item.get('quantidade', 0))),
            f"R$ {item.get('valorUnitario', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            f"R$ {item.get('valorTotal', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            item.get('prioridade', ''),
            Paragraph(f"<font size=6>{justificativa}</font>", styles['table_cell']),
            Paragraph(f"<font size=6>{classificacao_text}</font>", styles['table_cell'])
        ])
    
    # Larguras de coluna otimizadas
    if orientation.lower() == 'portrait':
        col_widths = [0.5*cm, 1.3*cm, 3.5*cm, 0.9*cm, 0.7*cm, 1.5*cm, 1.5*cm, 1*cm, 2.5*cm, 2.5*cm]
    else:
        col_widths = [0.5*cm, 1.4*cm, 5.5*cm, 1*cm, 0.8*cm, 1.6*cm, 1.8*cm, 1.2*cm, 5*cm, 4.5*cm]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), cor_primaria),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        
        # Corpo
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # #
        ('ALIGN', (3, 1), (4, -1), 'CENTER'),  # Unidade, Qtd
        ('ALIGN', (5, 1), (6, -1), 'RIGHT'),   # Valores
        ('ALIGN', (7, 1), (7, -1), 'CENTER'),  # Prioridade
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        
        # Linhas alternadas
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#D6EAF8')]),
        
        # Bordas
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('BOX', (0, 0), (-1, -1), 1, cor_primaria),
        
        # Padding
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    return table

def create_total_row(total_value: float, styles: dict, orientation: str = 'landscape'):
    """Cria linha de total com destaque"""
    cor_destaque = colors.HexColor('#FFC000')
    
    total_formatted = f"R$ {total_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    if orientation.lower() == 'portrait':
        col_widths = [0.5*cm, 1.3*cm, 3.5*cm, 0.9*cm, 0.7*cm, 1.5*cm, 1.5*cm, 1*cm, 2.5*cm, 2.5*cm]
    else:
        col_widths = [0.5*cm, 1.4*cm, 5.5*cm, 1*cm, 0.8*cm, 1.6*cm, 1.8*cm, 1.2*cm, 5*cm, 4.5*cm]
    
    total_data = [['', '', Paragraph('<b>VALOR TOTAL ESTIMADO:</b>', styles['body']), '', '', '', total_formatted, '', '', '']]
    
    total_table = Table(total_data, colWidths=col_widths)
    total_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), cor_destaque),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (6, 0), (6, 0), 'RIGHT'),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1F4E78')),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    return total_table

def create_signature_section(pac_data: dict, styles: dict, is_pac_geral: bool = False):
    """Cria seção de assinaturas profissional"""
    elements = []
    
    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph('<b>ASSINATURAS E VALIDAÇÃO</b>', styles['section_header']))
    elements.append(Spacer(1, 4*mm))
    
    if is_pac_geral:
        responsavel = pac_data.get('secretario', '')
        fiscal = pac_data.get('fiscal_contrato', '')
    else:
        responsavel = pac_data.get('secretario', '')
        fiscal = pac_data.get('fiscal', '')
    
    sig_data = [
        ['_' * 45, '_' * 45],
        [Paragraph(f'<b>{responsavel}</b>', styles['body']), Paragraph(f'<b>{fiscal}</b>', styles['body'])],
        ['Secretário(a) Responsável', 'Fiscal do Contrato'],
        ['', ''],
        [f'Acaiaca/MG, ___/___/______', f'Acaiaca/MG, ___/___/______']
    ]
    
    sig_table = Table(sig_data, colWidths=[10*cm, 10*cm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTSIZE', (0, 2), (-1, 2), 8),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.grey),
        ('TOPPADDING', (0, 0), (-1, 0), 0),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 2),
        ('TOPPADDING', (0, 4), (-1, 4), 10),
    ]))
    
    elements.append(sig_table)
    
    return elements

def create_footer_text():
    """Cria texto de rodapé padrão"""
    return f'<font size=7><i>Documento gerado eletronicamente pelo Sistema Planejamento Acaiaca em {datetime.now().strftime("%d/%m/%Y às %H:%M")} | Desenvolvido por Cristiano Abdo de Souza - Assessor de Planejamento</i></font>'

@api_router.get("/pacs/anos")
async def get_pacs_anos(request: Request):
    """Retorna lista de anos disponíveis nos PACs individuais"""
    user = await get_current_user(request)
    
    # Buscar anos distintos dos PACs
    pipeline = [
        {'$match': {'ano': {'$exists': True, '$ne': None}}},
        {'$group': {'_id': '$ano'}},
        {'$sort': {'_id': -1}}
    ]
    
    result = await db.pacs.aggregate(pipeline).to_list(100)
    anos = [r['_id'] for r in result if r['_id']]
    
    # Converter para inteiros se necessário
    anos_int = []
    for ano in anos:
        try:
            anos_int.append(int(ano))
        except (ValueError, TypeError):
            pass
    
    # Garantir que 2025 e o ano atual estejam na lista
    ano_atual = datetime.now().year
    anos_base = list(range(2025, ano_atual + 1))
    
    for ano in anos_base:
        if ano not in anos_int:
            anos_int.append(ano)
    
    anos_int.sort(reverse=True)
    return {'anos': anos_int, 'ano_atual': ano_atual}

@api_router.get("/pacs", response_model=List[PAC])
async def get_pacs(request: Request, ano: str = None):
    user = await get_current_user(request)
    # Usuários padrão veem todos os PACs (mas só podem editar os seus)
    # Admin vê e pode editar todos
    
    query = {}
    if ano:
        query['ano'] = str(ano)
    
    pacs = await db.pacs.find(query, {'_id': 0}).to_list(1000)
    return [PAC(**p) for p in pacs]

@api_router.get("/pacs/paginado")
async def get_pacs_paginado(
    request: Request, 
    ano: str = None,
    page: int = 1,
    page_size: int = 20,
    search: str = None
):
    """Retorna PACs com paginação"""
    user = await get_current_user(request)
    
    query = {}
    if ano:
        query['ano'] = str(ano)
    
    if search:
        query['$or'] = [
            {'secretaria': {'$regex': search, '$options': 'i'}},
            {'secretario': {'$regex': search, '$options': 'i'}},
            {'fiscal': {'$regex': search, '$options': 'i'}}
        ]
    
    # Contar total
    total = await db.pacs.count_documents(query)
    
    # Buscar com paginação
    skip = (page - 1) * page_size
    pacs = await db.pacs.find(query, {'_id': 0}).sort('created_at', -1).skip(skip).limit(page_size).to_list(page_size)
    
    return {
        'items': [PAC(**p) for p in pacs],
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size
    }

@api_router.get("/pacs/stats")
async def get_pacs_stats(request: Request):
    """
    Retorna estatísticas agregadas de todos os PACs individuais,
    agrupadas por Subitem de Classificação Orçamentária.
    """
    user = await get_current_user(request)
    
    # Buscar todos os items de PAC individual
    all_items = await db.pac_items.find({}, {'_id': 0}).to_list(10000)
    
    # Agrupar por subitem_classificacao
    stats_by_subitem = {}
    total_geral = 0
    
    for item in all_items:
        subitem = item.get('subitem_classificacao', 'Não Classificado') or 'Não Classificado'
        codigo = item.get('codigo_classificacao', '') or ''
        valor = item.get('valorTotal', 0) or 0
        
        key = f"{codigo} - {subitem}" if codigo else subitem
        
        if key not in stats_by_subitem:
            stats_by_subitem[key] = {
                'subitem': subitem,
                'codigo': codigo,
                'valor_total': 0,
                'quantidade_items': 0
            }
        
        stats_by_subitem[key]['valor_total'] += valor
        stats_by_subitem[key]['quantidade_items'] += 1
        total_geral += valor
    
    stats_list = list(stats_by_subitem.values())
    stats_list.sort(key=lambda x: x['valor_total'], reverse=True)
    
    # Contar total de PACs
    total_pacs = await db.pacs.count_documents({})
    
    return {
        'stats_by_subitem': stats_list,
        'total_geral': total_geral,
        'total_items': len(all_items),
        'total_pacs': total_pacs
    }

@api_router.post("/pacs", response_model=PAC)
async def create_pac(pac_data: PACCreate, request: Request):
    user = await get_current_user(request)
    pac_id = f"pac_{uuid.uuid4().hex[:12]}"
    pac_doc = {'pac_id': pac_id, 'user_id': user.user_id, **pac_data.model_dump(), 'total_value': 0.0, 'stats': {'consumo': 0, 'consumoQtd': 0, 'permanente': 0, 'permanenteQtd': 0, 'servicos': 0, 'servicosQtd': 0, 'obras': 0, 'obrasQtd': 0}, 'created_at': datetime.now(timezone.utc), 'updated_at': datetime.now(timezone.utc)}
    await db.pacs.insert_one(pac_doc)
    return PAC(**pac_doc)

@api_router.get("/pacs/{pac_id}", response_model=PAC)
async def get_pac(pac_id: str, request: Request):
    user = await get_current_user(request)
    # CORREÇÃO 1.2: Remover filtro por user_id para permitir visualização de todos os PACs
    pac = await db.pacs.find_one({'pac_id': pac_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC not found")
    return PAC(**pac)

@api_router.put("/pacs/{pac_id}", response_model=PAC)
async def update_pac(pac_id: str, pac_update: PACUpdate, request: Request):
    user = await get_current_user(request)
    pac = await db.pacs.find_one({'pac_id': pac_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC not found")
    # Apenas admin ou dono pode editar
    if not user.is_admin and pac['user_id'] != user.user_id:
        raise HTTPException(status_code=403, detail="Permission denied")
    update_data = {k: v for k, v in pac_update.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc)
    await db.pacs.update_one({'pac_id': pac_id}, {'$set': update_data})
    updated_pac = await db.pacs.find_one({'pac_id': pac_id}, {'_id': 0})
    return PAC(**updated_pac)

@api_router.delete("/pacs/{pac_id}")
async def delete_pac(pac_id: str, request: Request):
    user = await get_current_user(request)
    pac = await db.pacs.find_one({'pac_id': pac_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC not found")
    # Apenas admin ou dono pode excluir
    if not user.is_admin and pac['user_id'] != user.user_id:
        raise HTTPException(status_code=403, detail="Permission denied")
    await db.pacs.delete_one({'pac_id': pac_id})
    await db.pac_items.delete_many({'pac_id': pac_id})
    return {'message': 'PAC deleted'}

@api_router.get("/pacs/{pac_id}/items", response_model=List[PACItem])
async def get_pac_items(pac_id: str, request: Request):
    user = await get_current_user(request)
    pac = await db.pacs.find_one({'pac_id': pac_id})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC not found")
    items = await db.pac_items.find({'pac_id': pac_id}, {'_id': 0}).to_list(1000)
    return [PACItem(**i) for i in items]

@api_router.post("/pacs/{pac_id}/items", response_model=PACItem)
async def create_pac_item(pac_id: str, item_data: PACItemCreate, request: Request):
    user = await get_current_user(request)
    pac = await db.pacs.find_one({'pac_id': pac_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC not found")
    # Apenas admin ou dono pode adicionar itens
    if not user.is_admin and pac['user_id'] != user.user_id:
        raise HTTPException(status_code=403, detail="Permission denied")
    item_id = f"item_{uuid.uuid4().hex[:12]}"
    valorTotal = item_data.quantidade * item_data.valorUnitario
    item_doc = {'item_id': item_id, 'pac_id': pac_id, **item_data.model_dump(), 'valorTotal': valorTotal, 'created_at': datetime.now(timezone.utc)}
    await db.pac_items.insert_one(item_doc)
    await recalculate_pac_totals(pac_id)
    return PACItem(**item_doc)

@api_router.put("/pacs/{pac_id}/items/{item_id}", response_model=PACItem)
async def update_pac_item(pac_id: str, item_id: str, item_update: PACItemUpdate, request: Request):
    user = await get_current_user(request)
    pac = await db.pacs.find_one({'pac_id': pac_id})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC not found")
    # Apenas admin ou dono pode editar
    if not user.is_admin and pac['user_id'] != user.user_id:
        raise HTTPException(status_code=403, detail="Permission denied")
    item = await db.pac_items.find_one({'item_id': item_id, 'pac_id': pac_id}, {'_id': 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    update_data = {k: v for k, v in item_update.model_dump().items() if v is not None}
    if 'quantidade' in update_data or 'valorUnitario' in update_data:
        qtd = update_data.get('quantidade', item['quantidade'])
        val = update_data.get('valorUnitario', item['valorUnitario'])
        update_data['valorTotal'] = qtd * val
    await db.pac_items.update_one({'item_id': item_id}, {'$set': update_data})
    await recalculate_pac_totals(pac_id)
    updated_item = await db.pac_items.find_one({'item_id': item_id}, {'_id': 0})
    return PACItem(**updated_item)

@api_router.delete("/pacs/{pac_id}/items/{item_id}")
async def delete_pac_item(pac_id: str, item_id: str, request: Request):
    user = await get_current_user(request)
    pac = await db.pacs.find_one({'pac_id': pac_id})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC not found")
    # Apenas admin ou dono pode excluir
    if not user.is_admin and pac['user_id'] != user.user_id:
        raise HTTPException(status_code=403, detail="Permission denied")
    result = await db.pac_items.delete_one({'item_id': item_id, 'pac_id': pac_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    await recalculate_pac_totals(pac_id)
    return {'message': 'Item deleted'}

async def recalculate_pac_totals(pac_id: str):
    items = await db.pac_items.find({'pac_id': pac_id}, {'_id': 0}).to_list(1000)
    stats = {'totalGeral': 0, 'consumo': 0, 'consumoQtd': 0, 'permanente': 0, 'permanenteQtd': 0, 'servicos': 0, 'servicosQtd': 0, 'obras': 0, 'obrasQtd': 0}
    for item in items:
        total = item['valorTotal']
        stats['totalGeral'] += total
        if item['tipo'] == 'Material de Consumo':
            stats['consumo'] += total
            stats['consumoQtd'] += 1
        elif item['tipo'] == 'Material Permanente':
            stats['permanente'] += total
            stats['permanenteQtd'] += 1
        elif item['tipo'] == 'Serviço':
            stats['servicos'] += total
            stats['servicosQtd'] += 1
        elif item['tipo'] == 'Obras':
            stats['obras'] += total
            stats['obrasQtd'] += 1
    await db.pacs.update_one({'pac_id': pac_id}, {'$set': {'total_value': stats['totalGeral'], 'stats': stats, 'updated_at': datetime.now(timezone.utc)}})

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(request: Request):
    user = await get_current_user(request)
    pacs = await db.pacs.find({'user_id': user.user_id}, {'_id': 0}).to_list(1000)
    stats = {'totalGeral': 0, 'consumo': {'valor': 0, 'qtd': 0}, 'permanente': {'valor': 0, 'qtd': 0}, 'servicos': {'valor': 0, 'qtd': 0}, 'obras': {'valor': 0, 'qtd': 0}, 'totalPacs': len(pacs)}
    for pac in pacs:
        stats['totalGeral'] += pac.get('total_value', 0)
        if pac.get('stats'):
            s = pac['stats']
            stats['consumo']['valor'] += s.get('consumo', 0)
            stats['consumo']['qtd'] += s.get('consumoQtd', 0)
            stats['permanente']['valor'] += s.get('permanente', 0)
            stats['permanente']['qtd'] += s.get('permanenteQtd', 0)
            stats['servicos']['valor'] += s.get('servicos', 0)
            stats['servicos']['qtd'] += s.get('servicosQtd', 0)
            stats['obras']['valor'] += s.get('obras', 0)
            stats['obras']['qtd'] += s.get('obrasQtd', 0)
    return stats

@api_router.get("/pacs/{pac_id}/export/xlsx")
async def export_xlsx(pac_id: str, request: Request):
    user = await get_current_user(request)
    pac = await db.pacs.find_one({'pac_id': pac_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC not found")
    items = await db.pac_items.find({'pac_id': pac_id}, {'_id': 0}).to_list(1000)
    
    wb = Workbook()
    ws = wb.active
    ws.title = "PAC 2026"
    
    # Estilos
    header_font = Font(name='Arial', size=14, bold=True, color='FFFFFF')
    subheader_font = Font(name='Arial', size=11, bold=True)
    normal_font = Font(name='Arial', size=10)
    bold_font = Font(name='Arial', size=10, bold=True)
    
    header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
    subheader_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    total_fill = PatternFill(start_color='FFC000', end_color='FFC000', fill_type='solid')
    
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Cabeçalho
    ws.merge_cells('A1:K1')
    ws['A1'] = 'PREFEITURA MUNICIPAL DE ACAIACA - MG'
    ws['A1'].font = Font(name='Arial', size=16, bold=True)
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 25
    
    ws.merge_cells('A2:K2')
    ws['A2'] = 'PAC ACAIACA 2026 - PLANO ANUAL DE CONTRATAÇÕES'
    ws['A2'].font = Font(name='Arial', size=14, bold=True)
    ws['A2'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[2].height = 20
    
    ws.merge_cells('A3:K3')
    ws['A3'] = 'Lei Federal nº 14.133/2021'
    ws['A3'].font = Font(name='Arial', size=10, italic=True)
    ws['A3'].alignment = Alignment(horizontal='center', vertical='center')
    
    # Informações do PAC
    current_row = 5
    ws[f'A{current_row}'] = 'DADOS DA SECRETARIA'
    ws[f'A{current_row}'].font = subheader_font
    ws.merge_cells(f'A{current_row}:K{current_row}')
    
    current_row += 1
    info_data = [
        ('Secretaria:', pac['secretaria']),
        ('Secretário(a):', pac['secretario']),
        ('Fiscal do Contrato:', pac['fiscal']),
        ('Telefone:', pac['telefone']),
        ('E-mail:', pac['email']),
        ('Endereço:', pac['endereco']),
        ('Ano:', pac['ano'])
    ]
    
    for label, value in info_data:
        ws[f'A{current_row}'] = label
        ws[f'A{current_row}'].font = bold_font
        ws[f'B{current_row}'] = value
        ws[f'B{current_row}'].font = normal_font
        ws.merge_cells(f'B{current_row}:K{current_row}')
        current_row += 1
    
    # Tabela de itens
    current_row += 1
    headers = ['#', 'Tipo', 'Código', 'Descrição', 'Unidade', 'Qtd', 'Valor Unit (R$)', 'Valor Total (R$)', 'Prioridade', 'Justificativa', 'Classificação']
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = Font(name='Arial', size=10, bold=True, color='FFFFFF')
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = border
    
    ws.row_dimensions[current_row].height = 30
    
    # Dados dos itens
    for idx, item in enumerate(items, start=1):
        current_row += 1
        # Formatar classificação orçamentária
        classificacao_text = ''
        if item.get('codigo_classificacao'):
            classificacao_text = f"{item['codigo_classificacao']}"
            if item.get('subitem_classificacao'):
                classificacao_text += f" - {item['subitem_classificacao']}"
        
        row_data = [
            idx,
            item['tipo'],
            item['catmat'],
            item['descricao'],
            item['unidade'],
            item['quantidade'],
            item['valorUnitario'],
            item['valorTotal'],
            item['prioridade'],
            item['justificativa'],
            classificacao_text
        ]
        
        for col, value in enumerate(row_data, start=1):
            cell = ws.cell(row=current_row, column=col, value=value)
            cell.font = normal_font
            cell.border = border
            cell.alignment = Alignment(horizontal='center' if col in [1,2,5,6,9] else 'left', vertical='center', wrap_text=True)
            if col in [7, 8]:
                cell.number_format = 'R$ #,##0.00'
                cell.alignment = Alignment(horizontal='right', vertical='center')
    
    # Totais
    current_row += 1
    total = sum(item['valorTotal'] for item in items)
    
    ws.merge_cells(f'A{current_row}:G{current_row}')
    ws[f'A{current_row}'] = 'TOTAL GERAL ESTIMADO:'
    ws[f'A{current_row}'].font = bold_font
    ws[f'A{current_row}'].fill = total_fill
    ws[f'A{current_row}'].alignment = Alignment(horizontal='right', vertical='center')
    ws[f'A{current_row}'].border = border
    
    ws[f'H{current_row}'] = total
    ws[f'H{current_row}'].font = Font(name='Arial', size=12, bold=True)
    ws[f'H{current_row}'].fill = total_fill
    ws[f'H{current_row}'].number_format = 'R$ #,##0.00'
    ws[f'H{current_row}'].alignment = Alignment(horizontal='right', vertical='center')
    ws[f'H{current_row}'].border = border
    
    # Ajustar largura das colunas
    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 12
    ws.column_dimensions['D'].width = 40
    ws.column_dimensions['E'].width = 10
    ws.column_dimensions['F'].width = 8
    ws.column_dimensions['G'].width = 15
    ws.column_dimensions['H'].width = 15
    ws.column_dimensions['I'].width = 12
    ws.column_dimensions['J'].width = 35
    ws.column_dimensions['K'].width = 30
    
    # Configurar impressão
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToHeight = False
    ws.page_setup.fitToWidth = 1
    ws.print_options.horizontalCentered = True
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(output, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': f'attachment; filename=PAC_{pac["secretaria"].replace(" ", "_")}_2026.xlsx'})

@api_router.get("/pacs/{pac_id}/export/pdf")
async def export_pdf(pac_id: str, request: Request, orientation: str = "landscape", assinar: bool = True, data: str = None):
    """
    Exporta PAC Individual para PDF com design profissional e paginação de 15 itens por página.
    Args:
        orientation: 'landscape' (paisagem) ou 'portrait' (retrato)
        assinar: Se True, adiciona assinatura digital
        data: Data da assinatura (formato DD/MM/YYYY HH:MM:SS) - retroativa se necessário
    """
    user = await get_current_user(request)
    pac = await db.pacs.find_one({'pac_id': pac_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC not found")
    items = await db.pac_items.find({'pac_id': pac_id}, {'_id': 0}).to_list(1000)
    
    buffer = BytesIO()
    page_size = A4 if orientation.lower() == 'portrait' else landscape(A4)
    
    # Margens ajustadas para acomodar selo de assinatura na direita
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=page_size,
        leftMargin=15*mm,
        rightMargin=25*mm,  # Espaço para selo de assinatura digital
        topMargin=15*mm, 
        bottomMargin=15*mm,
        title=f'PAC {pac["secretaria"]} {pac.get("ano", "2026")}'
    )
    
    elements = []
    custom_styles, cor_primaria, cor_secundaria, cor_destaque = get_professional_styles()
    
    # Cabeçalho profissional
    elements.extend(create_professional_header(pac, custom_styles, is_pac_geral=False))
    
    # Caixa de informações
    elements.append(create_info_box(pac, custom_styles, is_pac_geral=False))
    elements.append(Spacer(1, 6*mm))
    
    # Título da seção de itens
    elements.append(Paragraph('<b>DETALHAMENTO DOS ITENS DO PLANO ANUAL DE CONTRATAÇÕES</b>', custom_styles['section_header']))
    elements.append(Spacer(1, 3*mm))
    
    # Tabela de TODOS os itens (sem paginação forçada para economizar papel)
    if items:
        items_table = create_items_table_paginated(
            items, 
            custom_styles, 
            orientation, 
            start_index=1
        )
        elements.append(items_table)
    
    # Linha de total após todos os itens
    elements.append(Spacer(1, 4*mm))
    total = sum(item['valorTotal'] for item in items)
    elements.append(create_total_row(total, custom_styles, orientation))
    
    # Seção de assinaturas
    elements.extend(create_signature_section(pac, custom_styles, is_pac_geral=False))
    
    # Rodapé
    elements.append(Spacer(1, 6*mm))
    elements.append(Paragraph(create_footer_text(), custom_styles['footer']))
    
    doc.build(elements)
    buffer.seek(0)
    
    # Adicionar assinatura digital ao PDF
    try:
        signed_buffer, validation_code = await add_signature_to_pdf(
            buffer, user, f"PAC - {pac['secretaria']}", pac_id, None, data
        )
        return StreamingResponse(
            signed_buffer, 
            media_type='application/pdf', 
            headers={
                'Content-Disposition': f'attachment; filename=PAC_{pac["secretaria"].replace(" ", "_")}_{pac.get("ano", "2026")}.pdf',
                'X-Validation-Code': validation_code
            }
        )
    except HTTPException:
        # Re-raise HTTPException para validação de CPF/Cargo
        raise
    except Exception as e:
        logging.error(f"Erro ao adicionar assinatura ao PDF: {e}")
        buffer.seek(0)
        return StreamingResponse(buffer, media_type='application/pdf', headers={'Content-Disposition': f'attachment; filename=PAC_{pac["secretaria"].replace(" ", "_")}_{pac.get("ano", "2026")}.pdf'})

@api_router.get("/template/download")
async def download_template():
    wb = Workbook()
    ws = wb.active
    ws.title = "Template PAC"
    headers = ['Tipo', 'Código CATMAT/CATSER', 'Descrição', 'Unidade', 'Quantidade', 'Valor Unitário', 'Prioridade', 'Justificativa']
    ws.append(headers)
    ws.append(['Material de Consumo', '123456', 'Exemplo de item', 'Unidade', 10, 50.00, 'Alta', 'Justificativa exemplo'])
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(output, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': 'attachment; filename=Template_PAC.xlsx'})

@api_router.post("/pacs/{pac_id}/import")
async def import_xlsx(pac_id: str, file: UploadFile = File(...), request: Request = None):
    user = await get_current_user(request)
    pac = await db.pacs.find_one({'pac_id': pac_id, 'user_id': user.user_id})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC not found")
    contents = await file.read()
    wb = load_workbook(BytesIO(contents))
    ws = wb.active
    imported_count = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0]:
            continue
        try:
            item_id = f"item_{uuid.uuid4().hex[:12]}"
            quantidade = float(row[4]) if row[4] else 0
            valorUnitario = float(row[5]) if row[5] else 0
            item_doc = {'item_id': item_id, 'pac_id': pac_id, 'tipo': row[0] or 'Material de Consumo', 'catmat': row[1] or '', 'descricao': row[2] or '', 'unidade': row[3] or 'Unidade', 'quantidade': quantidade, 'valorUnitario': valorUnitario, 'valorTotal': quantidade * valorUnitario, 'prioridade': row[6] or 'Média', 'justificativa': row[7] or '', 'imagemUrl': None, 'created_at': datetime.now(timezone.utc)}
            await db.pac_items.insert_one(item_doc)
            imported_count += 1
        except Exception:
            continue
    await recalculate_pac_totals(pac_id)
    return {'message': f'{imported_count} itens importados com sucesso'}

# ===== ESTATÍSTICAS DO PAC GERAL (DASHBOARD) =====
@api_router.get("/pacs-geral/stats")
async def get_pacs_geral_stats(request: Request):
    """
    Retorna estatísticas agregadas de todos os PACs Gerais,
    agrupadas por Subitem de Classificação Orçamentária.
    """
    user = await get_current_user(request)
    
    # Buscar todos os items de PAC Geral
    all_items = await db.pac_geral_items.find({}, {'_id': 0}).to_list(10000)
    
    # Agrupar por subitem_classificacao
    stats_by_subitem = {}
    total_geral = 0
    
    for item in all_items:
        subitem = item.get('subitem_classificacao', 'Não Classificado') or 'Não Classificado'
        codigo = item.get('codigo_classificacao', '') or ''
        valor = item.get('valorTotal', 0) or 0
        
        # Criar chave composta: código + subitem
        key = f"{codigo} - {subitem}" if codigo else subitem
        
        if key not in stats_by_subitem:
            stats_by_subitem[key] = {
                'subitem': subitem,
                'codigo': codigo,
                'valor_total': 0,
                'quantidade_items': 0
            }
        
        stats_by_subitem[key]['valor_total'] += valor
        stats_by_subitem[key]['quantidade_items'] += 1
        total_geral += valor
    
    # Converter para lista e ordenar por valor
    stats_list = list(stats_by_subitem.values())
    stats_list.sort(key=lambda x: x['valor_total'], reverse=True)
    
    return {
        'stats_by_subitem': stats_list,
        'total_geral': total_geral,
        'total_items': len(all_items)
    }

# ===== ROTAS PAC GERAL =====

@api_router.get("/pacs-geral/anos")
async def get_pacs_geral_anos(request: Request):
    """Retorna lista de anos disponíveis nos PACs Gerais"""
    user = await get_current_user(request)
    
    # Buscar anos distintos dos PACs Gerais
    pipeline = [
        {'$match': {'ano': {'$exists': True, '$ne': None}}},
        {'$group': {'_id': '$ano'}},
        {'$sort': {'_id': -1}}
    ]
    
    result = await db.pacs_geral.aggregate(pipeline).to_list(100)
    anos = [r['_id'] for r in result if r['_id']]
    
    # Converter para inteiros se necessário
    anos_int = []
    for ano in anos:
        try:
            anos_int.append(int(ano))
        except (ValueError, TypeError):
            pass
    
    # Garantir que 2026 e o ano atual estejam na lista (PAC Geral começa em 2026)
    ano_atual = datetime.now().year
    anos_base = list(range(2026, ano_atual + 1))
    
    for ano in anos_base:
        if ano not in anos_int:
            anos_int.append(ano)
    
    anos_int.sort(reverse=True)
    return {'anos': anos_int, 'ano_atual': ano_atual}

@api_router.get("/pacs-geral", response_model=List[PACGeral])
async def get_pacs_geral(request: Request, ano: str = None):
    user = await get_current_user(request)
    # Todos os usuários podem ver todos os PACs Gerais
    
    query = {}
    if ano:
        query['ano'] = str(ano)
    
    pacs = await db.pacs_geral.find(query, {'_id': 0}).to_list(1000)
    return pacs

@api_router.get("/pacs-geral/paginado")
async def get_pacs_geral_paginado(
    request: Request,
    ano: str = None,
    page: int = 1,
    page_size: int = 20,
    search: str = None
):
    """Retorna PACs Gerais com paginação"""
    user = await get_current_user(request)
    
    query = {}
    if ano:
        query['ano'] = str(ano)
    
    if search:
        query['$or'] = [
            {'nome_secretaria': {'$regex': search, '$options': 'i'}},
            {'secretario': {'$regex': search, '$options': 'i'}},
            {'fiscal_contrato': {'$regex': search, '$options': 'i'}}
        ]
    
    # Contar total
    total = await db.pacs_geral.count_documents(query)
    
    # Buscar com paginação
    skip = (page - 1) * page_size
    pacs = await db.pacs_geral.find(query, {'_id': 0}).sort('created_at', -1).skip(skip).limit(page_size).to_list(page_size)
    
    return {
        'items': pacs,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size
    }

@api_router.post("/pacs-geral", response_model=PACGeral)
async def create_pac_geral(pac_data: PACGeralCreate, request: Request):
    user = await get_current_user(request)
    pac_geral_id = f"pac_geral_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    pac_doc = {
        'pac_geral_id': pac_geral_id,
        'user_id': user.user_id,
        **pac_data.model_dump(),
        'created_at': now,
        'updated_at': now
    }
    await db.pacs_geral.insert_one(pac_doc)
    pac_doc.pop('_id', None)
    return PACGeral(**pac_doc)

@api_router.get("/pacs-geral/{pac_geral_id}", response_model=PACGeral)
async def get_pac_geral(pac_geral_id: str, request: Request):
    user = await get_current_user(request)
    pac = await db.pacs_geral.find_one({'pac_geral_id': pac_geral_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC Geral not found")
    # Admins podem ver todos, usuários padrão só seus próprios
    if not user.is_admin and pac['user_id'] != user.user_id:
        # Permitir visualização mas não edição
        pass
    return PACGeral(**pac)

@api_router.put("/pacs-geral/{pac_geral_id}", response_model=PACGeral)
async def update_pac_geral(pac_geral_id: str, pac_data: PACGeralUpdate, request: Request):
    user = await get_current_user(request)
    pac = await db.pacs_geral.find_one({'pac_geral_id': pac_geral_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC Geral not found")
    # Todos os usuários podem editar qualquer PAC Geral
    
    update_data = {k: v for k, v in pac_data.model_dump().items() if v is not None}
    if update_data:
        update_data['updated_at'] = datetime.now(timezone.utc)
        await db.pacs_geral.update_one({'pac_geral_id': pac_geral_id}, {'$set': update_data})
    
    updated_pac = await db.pacs_geral.find_one({'pac_geral_id': pac_geral_id}, {'_id': 0})
    return PACGeral(**updated_pac)

@api_router.delete("/pacs-geral/{pac_geral_id}")
async def delete_pac_geral(pac_geral_id: str, request: Request):
    user = await get_current_user(request)
    pac = await db.pacs_geral.find_one({'pac_geral_id': pac_geral_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC Geral not found")
    # Apenas administradores podem excluir PAC Geral
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Only administrators can delete PAC Geral")
    
    await db.pacs_geral.delete_one({'pac_geral_id': pac_geral_id})
    await db.pac_geral_items.delete_many({'pac_geral_id': pac_geral_id})
    return {'message': 'PAC Geral deleted successfully'}

# ===== ROTAS ITEMS PAC GERAL =====
@api_router.get("/pacs-geral/{pac_geral_id}/items", response_model=List[PACGeralItem])
async def get_pac_geral_items(pac_geral_id: str, request: Request):
    user = await get_current_user(request)
    pac = await db.pacs_geral.find_one({'pac_geral_id': pac_geral_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC Geral not found")
    
    items = await db.pac_geral_items.find({'pac_geral_id': pac_geral_id}, {'_id': 0}).to_list(1000)
    return items

@api_router.post("/pacs-geral/{pac_geral_id}/items", response_model=PACGeralItem)
async def create_pac_geral_item(pac_geral_id: str, item_data: PACGeralItemCreate, request: Request):
    user = await get_current_user(request)
    pac = await db.pacs_geral.find_one({'pac_geral_id': pac_geral_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC Geral not found")
    
    if not user.is_admin and pac['user_id'] != user.user_id:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    item_id = f"item_{uuid.uuid4().hex[:12]}"
    
    # Calcular quantidade total
    quantidade_total = (
        item_data.qtd_ad + item_data.qtd_fa + item_data.qtd_sa + 
        item_data.qtd_se + item_data.qtd_as + item_data.qtd_ag + 
        item_data.qtd_ob + item_data.qtd_tr + item_data.qtd_cul
    )
    
    valor_total = quantidade_total * item_data.valorUnitario
    
    item_doc = {
        'item_id': item_id,
        'pac_geral_id': pac_geral_id,
        **item_data.model_dump(),
        'quantidade_total': quantidade_total,
        'valorTotal': valor_total,
        'created_at': datetime.now(timezone.utc)
    }
    
    await db.pac_geral_items.insert_one(item_doc)
    item_doc.pop('_id', None)
    return PACGeralItem(**item_doc)

@api_router.put("/pacs-geral/{pac_geral_id}/items/{item_id}", response_model=PACGeralItem)
async def update_pac_geral_item(pac_geral_id: str, item_id: str, item_data: PACGeralItemUpdate, request: Request):
    user = await get_current_user(request)
    pac = await db.pacs_geral.find_one({'pac_geral_id': pac_geral_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC Geral not found")
    
    # Todos os usuários podem editar items de qualquer PAC Geral
    
    item = await db.pac_geral_items.find_one({'item_id': item_id, 'pac_geral_id': pac_geral_id}, {'_id': 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    update_data = {k: v for k, v in item_data.model_dump().items() if v is not None}
    
    # Recalcular totais se alguma quantidade ou valor mudou
    if any(k.startswith('qtd_') for k in update_data.keys()) or 'valorUnitario' in update_data:
        updated_item = {**item, **update_data}
        quantidade_total = (
            updated_item.get('qtd_ad', 0) + updated_item.get('qtd_fa', 0) + 
            updated_item.get('qtd_sa', 0) + updated_item.get('qtd_se', 0) + 
            updated_item.get('qtd_as', 0) + updated_item.get('qtd_ag', 0) + 
            updated_item.get('qtd_ob', 0) + updated_item.get('qtd_tr', 0) + 
            updated_item.get('qtd_cul', 0)
        )
        update_data['quantidade_total'] = quantidade_total
        update_data['valorTotal'] = quantidade_total * updated_item.get('valorUnitario', 0)
    
    if update_data:
        await db.pac_geral_items.update_one(
            {'item_id': item_id, 'pac_geral_id': pac_geral_id},
            {'$set': update_data}
        )
    
    updated_item = await db.pac_geral_items.find_one({'item_id': item_id}, {'_id': 0})
    return PACGeralItem(**updated_item)

@api_router.delete("/pacs-geral/{pac_geral_id}/items/{item_id}")
async def delete_pac_geral_item(pac_geral_id: str, item_id: str, request: Request):
    user = await get_current_user(request)
    pac = await db.pacs_geral.find_one({'pac_geral_id': pac_geral_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC Geral not found")
    
    # Apenas administradores podem excluir items
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Only administrators can delete items")
    
    result = await db.pac_geral_items.delete_one({'item_id': item_id, 'pac_geral_id': pac_geral_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {'message': 'Item deleted successfully'}


# ===== EXPORTAÇÃO PAC GERAL =====
@api_router.get("/pacs-geral/{pac_geral_id}/export/xlsx")
async def export_pac_geral_xlsx(pac_geral_id: str, request: Request):
    user = await get_current_user(request)
    pac = await db.pacs_geral.find_one({'pac_geral_id': pac_geral_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC Geral not found")
    
    items = await db.pac_geral_items.find({'pac_geral_id': pac_geral_id}, {'_id': 0}).to_list(1000)
    
    wb = Workbook()
    ws = wb.active
    ws.title = "PAC Geral"
    
    # Estilos
    header_fill = PatternFill(start_color="1F4788", end_color="1F4788", fill_type="solid")
    total_fill = PatternFill(start_color="E8F4F8", end_color="E8F4F8", fill_type="solid")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    bold_font = Font(name='Arial', size=11, bold=True)
    normal_font = Font(name='Arial', size=10)
    
    current_row = 1
    
    # Cabeçalho
    ws.merge_cells(f'A{current_row}:M{current_row}')
    ws[f'A{current_row}'] = 'PREFEITURA MUNICIPAL DE ACAIACA - MG'
    ws[f'A{current_row}'].font = Font(name='Arial', size=16, bold=True)
    ws[f'A{current_row}'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[current_row].height = 25
    current_row += 1
    
    ws.merge_cells(f'A{current_row}:M{current_row}')
    ws[f'A{current_row}'] = 'PAC ACAIACA 2026 - PLANO ANUAL DE CONTRATAÇÕES COMPARTILHADO'
    ws[f'A{current_row}'].font = Font(name='Arial', size=14, bold=True)
    ws[f'A{current_row}'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[current_row].height = 20
    current_row += 1
    
    ws.merge_cells(f'A{current_row}:M{current_row}')
    ws[f'A{current_row}'] = 'Lei Federal nº 14.133/2021'
    ws[f'A{current_row}'].font = Font(name='Arial', size=10, italic=True)
    ws[f'A{current_row}'].alignment = Alignment(horizontal='center', vertical='center')
    current_row += 2
    
    # Dados da Secretaria
    ws[f'A{current_row}'] = 'Secretaria Responsável:'
    ws[f'A{current_row}'].font = bold_font
    ws[f'B{current_row}'] = pac['nome_secretaria']
    current_row += 1
    
    ws[f'A{current_row}'] = 'Secretário:'
    ws[f'A{current_row}'].font = bold_font
    ws[f'B{current_row}'] = pac['secretario']
    current_row += 1
    
    ws[f'A{current_row}'] = 'Telefone:'
    ws[f'A{current_row}'].font = bold_font
    ws[f'B{current_row}'] = pac['telefone']
    ws[f'E{current_row}'] = 'E-mail:'
    ws[f'E{current_row}'].font = bold_font
    ws[f'F{current_row}'] = pac['email']
    current_row += 1
    
    ws[f'A{current_row}'] = 'Secretarias Participantes:'
    ws[f'A{current_row}'].font = bold_font
    ws[f'B{current_row}'] = ', '.join(pac['secretarias_selecionadas'])
    current_row += 2
    
    # Tabela de itens
    headers = ['#', 'Código', 'Descrição', 'Und', 'AD', 'FA', 'SA', 'SE', 'AS', 'AG', 'OB', 'TR', 'CUL', 'Total', 'Valor Unit', 'Valor Total', 'Prior', 'Justificativa', 'Classificação']
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = Font(name='Arial', size=10, bold=True, color='FFFFFF')
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = border
    
    ws.row_dimensions[current_row].height = 30
    current_row += 1
    
    # Dados dos itens
    for idx, item in enumerate(items, start=1):
        classificacao_text = ''
        if item.get('codigo_classificacao'):
            classificacao_text = f"{item['codigo_classificacao']}"
            if item.get('subitem_classificacao'):
                classificacao_text += f" - {item['subitem_classificacao']}"
        
        row_data = [
            idx,
            item['catmat'],
            item['descricao'],
            item['unidade'],
            item.get('qtd_ad', 0),
            item.get('qtd_fa', 0),
            item.get('qtd_sa', 0),
            item.get('qtd_se', 0),
            item.get('qtd_as', 0),
            item.get('qtd_ag', 0),
            item.get('qtd_ob', 0),
            item.get('qtd_tr', 0),
            item.get('qtd_cul', 0),
            item['quantidade_total'],
            item['valorUnitario'],
            item['valorTotal'],
            item['prioridade'],
            item.get('justificativa', ''),
            classificacao_text
        ]
        
        for col, value in enumerate(row_data, start=1):
            cell = ws.cell(row=current_row, column=col, value=value)
            cell.font = normal_font
            cell.border = border
            cell.alignment = Alignment(
                horizontal='center' if col in [1,2,4,5,6,7,8,9,10,11,12,13,14,17] else 'left',
                vertical='center',
                wrap_text=True
            )
            if col in [15, 16]:
                cell.number_format = 'R$ #,##0.00'
                cell.alignment = Alignment(horizontal='right', vertical='center')
        
        current_row += 1
    
    # Totais
    total = sum(item['valorTotal'] for item in items)
    
    ws.merge_cells(f'A{current_row}:O{current_row}')
    ws[f'A{current_row}'] = 'TOTAL GERAL ESTIMADO:'
    ws[f'A{current_row}'].font = bold_font
    ws[f'A{current_row}'].fill = total_fill
    ws[f'A{current_row}'].alignment = Alignment(horizontal='right', vertical='center')
    ws[f'A{current_row}'].border = border
    
    ws[f'P{current_row}'] = total
    ws[f'P{current_row}'].font = Font(name='Arial', size=12, bold=True)
    ws[f'P{current_row}'].fill = total_fill
    ws[f'P{current_row}'].number_format = 'R$ #,##0.00'
    ws[f'P{current_row}'].alignment = Alignment(horizontal='right', vertical='center')
    ws[f'P{current_row}'].border = border
    
    # Assinaturas
    current_row += 3
    ws[f'A{current_row}'] = '_' * 40
    ws[f'A{current_row}'].alignment = Alignment(horizontal='center')
    ws[f'H{current_row}'] = '_' * 40
    ws[f'H{current_row}'].alignment = Alignment(horizontal='center')
    current_row += 1
    
    ws[f'A{current_row}'] = 'Fiscal do Contrato'
    ws[f'A{current_row}'].font = bold_font
    ws[f'A{current_row}'].alignment = Alignment(horizontal='center')
    ws[f'H{current_row}'] = 'Gestor do Contrato'
    ws[f'H{current_row}'].font = bold_font
    ws[f'H{current_row}'].alignment = Alignment(horizontal='center')
    
    # Ajustar largura das colunas
    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 40
    ws.column_dimensions['D'].width = 8
    for col in ['E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M']:
        ws.column_dimensions[col].width = 8
    ws.column_dimensions['N'].width = 10
    ws.column_dimensions['O'].width = 12
    ws.column_dimensions['P'].width = 12
    ws.column_dimensions['Q'].width = 8
    ws.column_dimensions['R'].width = 35  # Justificativa
    ws.column_dimensions['S'].width = 30  # Classificação
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=PAC_Geral_{pac['nome_secretaria']}.xlsx"}
    )

# ===== IMPORTAÇÃO DE ARQUIVO PARA PAC GERAL =====
@api_router.post("/pacs-geral/{pac_geral_id}/import")
async def import_pac_geral_items(
    pac_geral_id: str, 
    file: UploadFile = File(...), 
    request: Request = None
):
    """
    Importa itens para o PAC Geral a partir de um arquivo.
    Formatos suportados: CSV, XLSX, JSON
    
    Estrutura esperada:
    - codigo (Catmat/Catser)
    - descricao
    - unidade
    - quantidade_total (ou qtd_total)
    - valor_unitario (ou valorUnitario)
    - prioridade
    - classificacao (opcional)
    - justificativa (opcional)
    """
    user = await get_current_user(request)
    
    pac = await db.pacs_geral.find_one({'pac_geral_id': pac_geral_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC Geral not found")
    
    # Ler o arquivo
    content = await file.read()
    filename = file.filename.lower()
    
    items_to_import = []
    
    try:
        if filename.endswith('.csv'):
            # Processar CSV
            import csv
            import io
            decoded = content.decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(decoded), delimiter=';')
            for row in reader:
                items_to_import.append(row)
                
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            # Processar Excel
            from openpyxl import load_workbook
            wb = load_workbook(filename=BytesIO(content))
            ws = wb.active
            
            # Pegar cabeçalhos da primeira linha
            headers = [cell.value for cell in ws[1] if cell.value]
            
            for row in ws.iter_rows(min_row=2, values_only=True):
                if any(row):
                    item = dict(zip(headers, row))
                    items_to_import.append(item)
                    
        elif filename.endswith('.json'):
            # Processar JSON
            import json
            data = json.loads(content.decode('utf-8'))
            if isinstance(data, list):
                items_to_import = data
            elif isinstance(data, dict) and 'items' in data:
                items_to_import = data['items']
            else:
                raise HTTPException(status_code=400, detail="JSON deve conter uma lista de itens ou objeto com chave 'items'")
        else:
            raise HTTPException(status_code=400, detail="Formato de arquivo não suportado. Use CSV, XLSX ou JSON")
        
        # Processar e inserir itens
        imported_count = 0
        for item_data in items_to_import:
            # Normalizar nomes de campos
            codigo = item_data.get('codigo') or item_data.get('catmat') or item_data.get('Código') or ''
            descricao = item_data.get('descricao') or item_data.get('Descrição') or item_data.get('descricão') or ''
            unidade = item_data.get('unidade') or item_data.get('Unidade') or item_data.get('und') or 'Unidade'
            
            qtd_total = item_data.get('quantidade_total') or item_data.get('qtd_total') or item_data.get('Qtd Total') or item_data.get('quantidade') or 0
            valor_unit = item_data.get('valor_unitario') or item_data.get('valorUnitario') or item_data.get('Valor Unit') or item_data.get('valor') or 0
            
            prioridade = item_data.get('prioridade') or item_data.get('Prioridade') or item_data.get('prior') or 'Média'
            classificacao = item_data.get('classificacao') or item_data.get('Classificação') or item_data.get('codigo_classificacao') or ''
            justificativa = item_data.get('justificativa') or item_data.get('Justificativa') or ''
            
            # Converter valores numéricos
            try:
                qtd_total = float(str(qtd_total).replace(',', '.').replace('R$', '').strip()) if qtd_total else 0
                valor_unit = float(str(valor_unit).replace(',', '.').replace('R$', '').strip()) if valor_unit else 0
            except:
                qtd_total = 0
                valor_unit = 0
            
            if not descricao:
                continue
            
            item_id = f"item_{uuid.uuid4().hex[:12]}"
            item_doc = {
                'item_id': item_id,
                'pac_geral_id': pac_geral_id,
                'catmat': str(codigo)[:20],
                'descricao': str(descricao)[:500],
                'unidade': str(unidade)[:20],
                'qtd_ad': 0, 'qtd_fa': 0, 'qtd_sa': 0, 'qtd_se': 0,
                'qtd_as': 0, 'qtd_ag': 0, 'qtd_ob': 0, 'qtd_tr': 0, 'qtd_cul': 0,
                'quantidade_total': qtd_total,
                'valorUnitario': valor_unit,
                'valorTotal': qtd_total * valor_unit,
                'prioridade': str(prioridade)[:20],
                'justificativa': str(justificativa)[:500],
                'codigo_classificacao': str(classificacao)[:20] if classificacao else '',
                'subitem_classificacao': '',
                'created_at': datetime.now(timezone.utc)
            }
            
            await db.pac_geral_items.insert_one(item_doc)
            imported_count += 1
        
        return {
            'message': f'{imported_count} itens importados com sucesso',
            'total_items': imported_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {str(e)}")

@api_router.get("/pacs-geral/{pac_geral_id}/export/pdf")
async def export_pac_geral_pdf(pac_geral_id: str, request: Request, orientation: str = "landscape", assinar: bool = True, data: str = None):
    """
    Exporta o PAC Geral para PDF com design profissional e paginação de 15 itens por página.
    Args:
        orientation: 'landscape' (paisagem) ou 'portrait' (retrato)
        assinar: Se True, adiciona assinatura digital
        data: Data da assinatura (formato DD/MM/YYYY HH:MM:SS) - retroativa se necessário
    """
    user = await get_current_user(request)
    pac = await db.pacs_geral.find_one({'pac_geral_id': pac_geral_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC Geral not found")
    
    items = await db.pac_geral_items.find({'pac_geral_id': pac_geral_id}, {'_id': 0}).to_list(1000)
    
    buffer = BytesIO()
    page_size = A4 if orientation.lower() == 'portrait' else landscape(A4)
    
    # Margens ajustadas para acomodar selo de assinatura na direita
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=page_size,
        leftMargin=15*mm,
        rightMargin=25*mm,  # Espaço para selo de assinatura digital
        topMargin=15*mm, 
        bottomMargin=15*mm,
        title=f'PAC Geral {pac.get("nome_secretaria", "")} {pac.get("ano", "2026")}'
    )
    
    elements = []
    custom_styles, cor_primaria, cor_secundaria, cor_destaque = get_professional_styles()
    base_styles = getSampleStyleSheet()
    
    # Cabeçalho profissional
    elements.extend(create_professional_header(pac, custom_styles, is_pac_geral=True))
    
    # Caixa de informações
    elements.append(create_info_box(pac, custom_styles, is_pac_geral=True))
    
    # Secretarias participantes
    secretarias = pac.get('secretarias_selecionadas', [])
    if secretarias:
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph(f'<b>Secretarias Participantes:</b> {", ".join(secretarias)}', custom_styles['small']))
    
    elements.append(Spacer(1, 6*mm))
    
    # Título da seção de itens
    elements.append(Paragraph('<b>DETALHAMENTO DOS ITENS DO PLANO ANUAL DE CONTRATAÇÕES</b>', custom_styles['section_header']))
    elements.append(Spacer(1, 3*mm))
    
    # Tabela de TODOS os itens (sem paginação forçada para economizar papel)
    if items:
        # Criar tabela para todos os itens
        table_data = [['#', 'Código\nCATMAT', 'Descrição do Objeto', 'Justificativa', 'Und', 'Qtd', 'Valor\nUnitário', 'Valor\nTotal', 'Prior.', 'Classificação\nOrçamentária']]
        
        for idx, item in enumerate(items, start=1):
            classificacao_text = ''
            if item.get('codigo_classificacao'):
                classificacao_text = f"{item['codigo_classificacao']}"
                if item.get('subitem_classificacao'):
                    classificacao_text += f"\n{item['subitem_classificacao']}"
            
            justificativa = item.get('justificativa', '') or 'N/I'
            descricao = item.get('descricao', '')
            
            table_data.append([
                str(idx),
                item.get('catmat', ''),
                Paragraph(f"<font size=7>{descricao}</font>", custom_styles['table_cell']),
                Paragraph(f"<font size=6>{justificativa}</font>", custom_styles['table_cell']),
                item.get('unidade', ''),
                str(int(item.get('quantidade_total', 0))),
                f"R$ {item.get('valorUnitario', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                f"R$ {item.get('valorTotal', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                item.get('prioridade', ''),
                Paragraph(f"<font size=6>{classificacao_text}</font>", custom_styles['table_cell'])
            ])
        
        if orientation.lower() == 'portrait':
            col_widths = [0.5*cm, 1.2*cm, 3*cm, 2.5*cm, 0.8*cm, 0.8*cm, 1.4*cm, 1.5*cm, 0.8*cm, 2.2*cm]
        else:
            col_widths = [0.5*cm, 1.4*cm, 5*cm, 4.5*cm, 1*cm, 0.9*cm, 1.6*cm, 1.8*cm, 1*cm, 4.5*cm]
        
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), cor_primaria),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (4, 1), (5, -1), 'CENTER'),
            ('ALIGN', (6, 1), (7, -1), 'RIGHT'),
            ('ALIGN', (8, 1), (8, -1), 'CENTER'),
            ('VALIGN', (0, 1), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#D6EAF8')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
            ('BOX', (0, 0), (-1, -1), 1, cor_primaria),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)
    
    # Linha de total após todos os itens
    elements.append(Spacer(1, 4*mm))
    total = sum(item.get('valorTotal', 0) for item in items)
    elements.append(create_total_row(total, custom_styles, orientation))
    
    # Seção de assinaturas
    elements.extend(create_signature_section(pac, custom_styles, is_pac_geral=True))
    
    # Rodapé
    elements.append(Spacer(1, 6*mm))
    elements.append(Paragraph(create_footer_text(), custom_styles['footer']))
    
    doc.build(elements)
    buffer.seek(0)
    
    # Adicionar assinatura digital ao PDF
    try:
        signed_buffer, validation_code = await add_signature_to_pdf(
            buffer, user, f"PAC Geral - {pac.get('nome_secretaria', '')}", pac_geral_id, None, data
        )
        return StreamingResponse(
            signed_buffer, 
            media_type='application/pdf', 
            headers={
                'Content-Disposition': f'attachment; filename=PAC_Geral_{pac.get("nome_secretaria", "").replace(" ", "_")}_{pac.get("ano", "2026")}.pdf',
                'X-Validation-Code': validation_code
            }
        )
    except HTTPException:
        # Re-raise HTTPException para validação de CPF/Cargo
        raise
    except Exception as e:
        logging.error(f"Erro ao adicionar assinatura ao PDF: {e}")
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=PAC_Geral_{pac.get('nome_secretaria', '').replace(' ', '_')}_{pac.get('ano', '2026')}.pdf"}
        )


# ============ ROTAS PAC GERAL OBRAS E SERVIÇOS ============

@api_router.get("/classificacao/obras-servicos")
async def get_classificacao_obras_servicos():
    """Retorna códigos de classificação para Obras e Serviços (Lei 14.133/2021 + Portaria 448)"""
    return CLASSIFICACAO_OBRAS_SERVICOS

@api_router.get("/pacs-geral-obras", response_model=List[PACGeralObras])
async def get_pacs_geral_obras(request: Request, ano: str = None):
    """Lista todos os PAC Geral Obras do usuário"""
    user = await get_current_user(request)
    query = {'user_id': user.user_id} if not user.is_admin else {}
    if ano:
        query['ano'] = ano
    pacs = await db.pacs_geral_obras.find(query, {'_id': 0}).to_list(100)
    return [PACGeralObras(**p) for p in pacs]

@api_router.post("/pacs-geral-obras", response_model=PACGeralObras)
async def create_pac_geral_obras(pac_data: PACGeralObrasCreate, request: Request):
    """Cria um novo PAC Geral Obras"""
    user = await get_current_user(request)
    pac_obras_id = f"pacobras_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    pac_doc = {
        'pac_obras_id': pac_obras_id,
        'user_id': user.user_id,
        **pac_data.model_dump(),
        'created_at': now,
        'updated_at': now
    }
    await db.pacs_geral_obras.insert_one(pac_doc)
    return PACGeralObras(**pac_doc)

@api_router.get("/pacs-geral-obras/{pac_obras_id}", response_model=PACGeralObras)
async def get_pac_geral_obras(pac_obras_id: str, request: Request):
    """Obtém um PAC Geral Obras específico"""
    user = await get_current_user(request)
    pac = await db.pacs_geral_obras.find_one({'pac_obras_id': pac_obras_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC Geral Obras not found")
    return PACGeralObras(**pac)

@api_router.put("/pacs-geral-obras/{pac_obras_id}", response_model=PACGeralObras)
async def update_pac_geral_obras(pac_obras_id: str, pac_data: PACGeralObrasUpdate, request: Request):
    """Atualiza um PAC Geral Obras"""
    user = await get_current_user(request)
    pac = await db.pacs_geral_obras.find_one({'pac_obras_id': pac_obras_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC Geral Obras not found")
    update_data = {k: v for k, v in pac_data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc)
    await db.pacs_geral_obras.update_one({'pac_obras_id': pac_obras_id}, {'$set': update_data})
    updated = await db.pacs_geral_obras.find_one({'pac_obras_id': pac_obras_id}, {'_id': 0})
    return PACGeralObras(**updated)

@api_router.delete("/pacs-geral-obras/{pac_obras_id}")
async def delete_pac_geral_obras(pac_obras_id: str, request: Request):
    """Exclui um PAC Geral Obras e seus itens"""
    user = await get_current_user(request)
    pac = await db.pacs_geral_obras.find_one({'pac_obras_id': pac_obras_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC Geral Obras not found")
    await db.pac_geral_obras_items.delete_many({'pac_obras_id': pac_obras_id})
    await db.pacs_geral_obras.delete_one({'pac_obras_id': pac_obras_id})
    return {'message': 'PAC Geral Obras excluído com sucesso'}

# ===== ROTAS ITEMS PAC GERAL OBRAS =====
@api_router.get("/pacs-geral-obras/{pac_obras_id}/items", response_model=List[PACGeralObrasItem])
async def get_pac_geral_obras_items(pac_obras_id: str, request: Request):
    """Lista itens de um PAC Geral Obras"""
    user = await get_current_user(request)
    items = await db.pac_geral_obras_items.find({'pac_obras_id': pac_obras_id}, {'_id': 0}).to_list(1000)
    return [PACGeralObrasItem(**item) for item in items]

@api_router.post("/pacs-geral-obras/{pac_obras_id}/items", response_model=PACGeralObrasItem)
async def create_pac_geral_obras_item(pac_obras_id: str, item_data: PACGeralObrasItemCreate, request: Request):
    """Adiciona um item ao PAC Geral Obras"""
    user = await get_current_user(request)
    pac = await db.pacs_geral_obras.find_one({'pac_obras_id': pac_obras_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC Geral Obras not found")
    
    item_id = f"itemobras_{uuid.uuid4().hex[:12]}"
    item_dict = item_data.model_dump()
    
    # Calcular quantidade total
    quantidade_total = sum([
        item_dict.get('qtd_ad', 0), item_dict.get('qtd_fa', 0), item_dict.get('qtd_sa', 0),
        item_dict.get('qtd_se', 0), item_dict.get('qtd_as', 0), item_dict.get('qtd_ag', 0),
        item_dict.get('qtd_ob', 0), item_dict.get('qtd_tr', 0), item_dict.get('qtd_cul', 0)
    ])
    
    item_doc = {
        'item_id': item_id,
        'pac_obras_id': pac_obras_id,
        **item_dict,
        'quantidade_total': quantidade_total,
        'valorTotal': quantidade_total * item_dict['valorUnitario'],
        'created_at': datetime.now(timezone.utc)
    }
    await db.pac_geral_obras_items.insert_one(item_doc)
    return PACGeralObrasItem(**item_doc)

@api_router.put("/pacs-geral-obras/{pac_obras_id}/items/{item_id}", response_model=PACGeralObrasItem)
async def update_pac_geral_obras_item(pac_obras_id: str, item_id: str, item_data: PACGeralObrasItemUpdate, request: Request):
    """Atualiza um item do PAC Geral Obras"""
    user = await get_current_user(request)
    item = await db.pac_geral_obras_items.find_one({'item_id': item_id, 'pac_obras_id': pac_obras_id}, {'_id': 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    update_data = {k: v for k, v in item_data.model_dump().items() if v is not None}
    
    # Recalcular totais se necessário
    merged = {**item, **update_data}
    quantidade_total = sum([
        merged.get('qtd_ad', 0), merged.get('qtd_fa', 0), merged.get('qtd_sa', 0),
        merged.get('qtd_se', 0), merged.get('qtd_as', 0), merged.get('qtd_ag', 0),
        merged.get('qtd_ob', 0), merged.get('qtd_tr', 0), merged.get('qtd_cul', 0)
    ])
    update_data['quantidade_total'] = quantidade_total
    update_data['valorTotal'] = quantidade_total * merged.get('valorUnitario', 0)
    
    await db.pac_geral_obras_items.update_one({'item_id': item_id}, {'$set': update_data})
    updated = await db.pac_geral_obras_items.find_one({'item_id': item_id}, {'_id': 0})
    return PACGeralObrasItem(**updated)

@api_router.delete("/pacs-geral-obras/{pac_obras_id}/items/{item_id}")
async def delete_pac_geral_obras_item(pac_obras_id: str, item_id: str, request: Request):
    """Exclui um item do PAC Geral Obras"""
    user = await get_current_user(request)
    result = await db.pac_geral_obras_items.delete_one({'item_id': item_id, 'pac_obras_id': pac_obras_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {'message': 'Item excluído com sucesso'}

# ===== EXPORTAÇÃO PDF DO PAC GERAL OBRAS =====
@api_router.get("/pacs-geral-obras/{pac_obras_id}/export/pdf")
async def export_pac_geral_obras_pdf(pac_obras_id: str, request: Request, orientation: str = "landscape", assinar: bool = True, data: str = None):
    """
    Exporta PAC Geral Obras e Serviços para PDF
    Classificação conforme Lei 14.133/2021 e Portaria 448/ME
    Args:
        assinar: Se True, adiciona assinatura digital
        data: Data da assinatura (formato DD/MM/YYYY HH:MM:SS) - retroativa se necessário
    """
    user = await get_current_user(request)
    
    pac = await db.pacs_geral_obras.find_one({'pac_obras_id': pac_obras_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC Geral Obras não encontrado")
    
    items = await db.pac_geral_obras_items.find({'pac_obras_id': pac_obras_id}, {'_id': 0}).to_list(1000)
    
    buffer = BytesIO()
    page_size = landscape(A4) if orientation.lower() == 'landscape' else A4
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        leftMargin=15*mm,
        rightMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
        title=f'PAC Obras - {pac["nome_secretaria"]} {pac.get("ano", "2026")}'
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilos
    titulo_style = ParagraphStyle('TituloPACObras', parent=styles['Heading1'], fontSize=14, textColor=colors.HexColor('#1565C0'), alignment=TA_CENTER, spaceAfter=4*mm)
    subtitulo_style = ParagraphStyle('SubtituloPACObras', parent=styles['Heading2'], fontSize=11, textColor=colors.HexColor('#1976D2'), spaceBefore=6*mm, spaceAfter=3*mm)
    
    # ===== CABEÇALHO =====
    elements.append(Paragraph('PREFEITURA MUNICIPAL DE ACAIACA - MG', titulo_style))
    elements.append(Paragraph('CNPJ: 18.295.287/0001-90', ParagraphStyle('CNPJ', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8)))
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph('<b>PLANO ANUAL DE CONTRATAÇÕES - OBRAS E SERVIÇOS DE ENGENHARIA</b>', ParagraphStyle('TitDoc', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=12, textColor=colors.HexColor('#0D47A1'))))
    elements.append(Paragraph('Lei 14.133/2021 - Nova Lei de Licitações | Portaria 448/ME', ParagraphStyle('Lei', parent=styles['Normal'], alignment=TA_CENTER, fontSize=7, textColor=colors.gray)))
    elements.append(Spacer(1, 6*mm))
    
    # ===== DADOS DA SECRETARIA =====
    elements.append(Paragraph('IDENTIFICAÇÃO', subtitulo_style))
    
    sec_data = [
        ['Secretaria:', pac.get('nome_secretaria', '-')],
        ['Secretário(a):', pac.get('secretario', '-')],
        ['Fiscal do Contrato:', pac.get('fiscal_contrato', '-') or '-'],
        ['Telefone:', pac.get('telefone', '-')],
        ['E-mail:', pac.get('email', '-')],
        ['Endereço:', pac.get('endereco', '-')],
        ['Ano:', pac.get('ano', '2026')],
        ['Tipo:', pac.get('tipo_contratacao', 'OBRAS')]
    ]
    
    sec_table = Table(sec_data, colWidths=[40*mm, 100*mm])
    sec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E3F2FD')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#90CAF9')),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(sec_table)
    
    # ===== ITENS =====
    if items:
        elements.append(Paragraph('DETALHAMENTO DOS ITENS', subtitulo_style))
        
        # Secretarias selecionadas
        secs = pac.get('secretarias_selecionadas', [])
        
        # Cabeçalho dinâmico
        header = ['#', 'CATSER', 'Descrição', 'Classif.', 'Un']
        sec_labels = {'AD': 'Admin', 'FA': 'Faz', 'SA': 'Saúde', 'SE': 'Educ', 'AS': 'Assist', 'AG': 'Agric', 'OB': 'Obras', 'TR': 'Transp', 'CUL': 'Cult'}
        for s in secs:
            header.append(sec_labels.get(s, s))
        header.extend(['Total', 'Unit.', 'TOTAL'])
        
        items_data = [header]
        
        for idx, item in enumerate(items, 1):
            row = [
                str(idx),
                item.get('catmat', '-'),
                Paragraph(item.get('descricao', '-')[:40], ParagraphStyle('DescItem', fontSize=6)),
                item.get('codigo_classificacao', '-'),
                item.get('unidade', '-')
            ]
            
            # Quantidades por secretaria
            for s in secs:
                qtd = item.get(f'qtd_{s.lower()}', 0)
                row.append(str(int(qtd)) if qtd else '-')
            
            row.extend([
                str(int(item.get('quantidade_total', 0))),
                f"R$ {item.get('valorUnitario', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                f"R$ {item.get('valorTotal', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            ])
            items_data.append(row)
        
        # Calcular larguras das colunas
        num_secs = len(secs)
        col_widths = [8*mm, 18*mm, 50*mm, 18*mm, 12*mm]  # Fixas
        col_widths.extend([12*mm] * num_secs)  # Secretarias
        col_widths.extend([15*mm, 22*mm, 28*mm])  # Total, Unit, TOTAL
        
        items_table = Table(items_data, colWidths=col_widths)
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0D47A1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (5, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#90CAF9')),
            ('PADDING', (0, 0), (-1, -1), 2),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#E3F2FD')]),
        ]))
        elements.append(items_table)
        
        # Total
        total = sum(item.get('valorTotal', 0) for item in items)
        elements.append(Spacer(1, 4*mm))
        elements.append(Paragraph(f"<b>VALOR TOTAL: R$ {total:,.2f}</b>".replace(',', 'X').replace('.', ',').replace('X', '.'), ParagraphStyle('TotalPAC', fontSize=11, alignment=TA_RIGHT, textColor=colors.HexColor('#1B5E20'))))
    
    # ===== ASSINATURA =====
    elements.append(Spacer(1, 15*mm))
    elements.append(Paragraph('_' * 50, ParagraphStyle('Linha', alignment=TA_CENTER)))
    elements.append(Paragraph(f'<b>{pac.get("secretario", "Secretário(a)")}</b>', ParagraphStyle('Assinatura', alignment=TA_CENTER, fontSize=9)))
    elements.append(Paragraph(f'{pac.get("nome_secretaria", "")}', ParagraphStyle('Cargo', alignment=TA_CENTER, fontSize=7, textColor=colors.gray)))
    
    # ===== RODAPÉ =====
    elements.append(Spacer(1, 8*mm))
    data_geracao = datetime.now(timezone.utc).strftime('%d/%m/%Y às %H:%M')
    elements.append(Paragraph(f'Documento gerado em {data_geracao} | Planejamento Acaiaca © 2026', ParagraphStyle('Rodape', alignment=TA_CENTER, fontSize=6, textColor=colors.gray)))
    
    doc.build(elements)
    buffer.seek(0)
    
    filename = f"PAC_Obras_{pac['nome_secretaria'].replace(' ', '_')}_{pac.get('ano', '2026')}.pdf"
    
    # Adicionar assinatura digital ao PDF
    try:
        signed_buffer, validation_code = await add_signature_to_pdf(
            buffer, user, f"PAC Obras - {pac['nome_secretaria']}", pac_obras_id, None, data
        )
        return StreamingResponse(
            signed_buffer,
            media_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'X-Validation-Code': validation_code
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erro ao adicionar assinatura ao PDF de PAC Obras: {e}")
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )


# ============ ROTAS DE GESTÃO PROCESSUAL ============

@api_router.get("/processos/anos")
async def get_processos_anos(request: Request):
    """Retorna lista de anos disponíveis nos processos"""
    user = await get_current_user(request)
    
    # Como muitos processos não têm o campo ano, extrair do numero_processo
    processos = await db.processos.find({}, {'numero_processo': 1, 'ano': 1}).to_list(1000)
    
    anos = set()
    for p in processos:
        if p.get('ano'):
            anos.add(int(p['ano']))
        else:
            # Extrair do numero_processo (ex: PRC - 0006/2025)
            numero = p.get('numero_processo', '')
            match = re.search(r'/(\d{4})$', numero)
            if match:
                anos.add(int(match.group(1)))
    
    # Garantir que 2025 e o ano atual estejam na lista
    ano_atual = datetime.now().year
    anos_base = list(range(2025, ano_atual + 1))
    
    for ano in anos_base:
        anos.add(ano)
    
    anos_list = sorted(list(anos), reverse=True)
    
    # Definir o ano padrão como o mais recente que tenha processos
    ano_padrao = anos_list[0] if anos_list else ano_atual
    # Se existem processos em 2025 mas não em 2026, selecionar 2025
    if 2025 in anos and processos:
        ano_padrao = 2025
    
    return {'anos': anos_list, 'ano_atual': ano_padrao}


@api_router.get("/processos", response_model=List[Processo])
async def get_processos(request: Request, ano: int = None):
    """Lista todos os processos, opcionalmente filtrados por ano"""
    user = await get_current_user(request)
    
    processos = await db.processos.find({}, {'_id': 0}).to_list(1000)
    
    # Fix null string values in datetime fields e extrair ano do numero_processo
    for p in processos:
        for field in ['data_inicio', 'data_autuacao', 'data_contrato']:
            if p.get(field) == 'null' or p.get(field) == '':
                p[field] = None
        
        # Extrair ano do numero_processo se não existir (ex: PRC - 0006/2025)
        if not p.get('ano'):
            numero = p.get('numero_processo', '')
            match = re.search(r'/(\d{4})$', numero)
            if match:
                p['ano'] = int(match.group(1))
            else:
                p['ano'] = 2025  # Ano padrão
    
    # Aplicar filtro de ano após extração
    if ano:
        processos = [p for p in processos if p.get('ano') == ano]
    
    return [Processo(**p) for p in processos]

@api_router.get("/processos/paginado")
async def get_processos_paginado(
    request: Request, 
    ano: int = None,
    page: int = 1,
    page_size: int = 20,
    search: str = None,
    status: str = None,
    modalidade: str = None
):
    """Lista processos com paginação e filtros no backend"""
    user = await get_current_user(request)
    
    # Buscar todos os processos
    processos = await db.processos.find({}, {'_id': 0}).to_list(5000)
    
    # Fix null values e extrair ano
    for p in processos:
        for field in ['data_inicio', 'data_autuacao', 'data_contrato']:
            if p.get(field) == 'null' or p.get(field) == '':
                p[field] = None
        
        if not p.get('ano'):
            numero = p.get('numero_processo', '')
            match = re.search(r'/(\d{4})$', numero)
            if match:
                p['ano'] = int(match.group(1))
            else:
                p['ano'] = 2025
    
    # Aplicar filtros
    if ano:
        processos = [p for p in processos if p.get('ano') == ano]
    
    if status:
        processos = [p for p in processos if p.get('status') == status]
    
    if modalidade:
        processos = [p for p in processos if p.get('modalidade') == modalidade]
    
    if search:
        search_lower = search.lower()
        processos = [p for p in processos if 
            search_lower in (p.get('numero_processo', '') or '').lower() or
            search_lower in (p.get('objeto', '') or '').lower() or
            search_lower in (p.get('secretaria', '') or '').lower() or
            search_lower in (p.get('responsavel', '') or '').lower()
        ]
    
    # Calcular paginação
    total = len(processos)
    total_pages = (total + page_size - 1) // page_size
    
    # Aplicar paginação
    start = (page - 1) * page_size
    end = start + page_size
    paginated_items = processos[start:end]
    
    return {
        'items': [Processo(**p).model_dump() for p in paginated_items],
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages
    }

@api_router.get("/processos/stats")
async def get_processos_stats(request: Request, data_inicio: str = None, data_fim: str = None):
    """Estatísticas avançadas dos processos para dashboard"""
    user = await get_current_user(request)
    
    # Query base
    query = {}
    
    # Filtro por período
    if data_inicio or data_fim:
        date_filter = {}
        if data_inicio:
            date_filter['$gte'] = data_inicio
        if data_fim:
            date_filter['$lte'] = data_fim
        if date_filter:
            query['data_inicio'] = date_filter
    
    processos = await db.processos.find(query, {'_id': 0}).to_list(1000)
    
    # Filtrar processos com dados válidos
    processos_validos = [p for p in processos if p.get('numero_processo') and p.get('numero_processo') != 'Processo']
    
    # 1. Estatísticas por Status
    stats_by_status = {}
    for p in processos_validos:
        status = p.get('status', 'Não Definido') or 'Não Definido'
        if status not in stats_by_status:
            stats_by_status[status] = {'status': status, 'quantidade': 0}
        stats_by_status[status]['quantidade'] += 1
    
    # 2. Estatísticas por Modalidade
    stats_by_modalidade = {}
    for p in processos_validos:
        modalidade = p.get('modalidade', 'Não Definido') or 'Não Definido'
        if modalidade not in stats_by_modalidade:
            stats_by_modalidade[modalidade] = {'modalidade': modalidade, 'quantidade': 0, 'concluidos': 0}
        stats_by_modalidade[modalidade]['quantidade'] += 1
        if p.get('status') == 'Concluído':
            stats_by_modalidade[modalidade]['concluidos'] += 1
    
    # 3. Tempo médio de finalização (em dias)
    tempos_finalizacao = []
    tempos_por_mes = {}
    tempos_por_modalidade = {}
    
    for p in processos_validos:
        if p.get('status') == 'Concluído' and p.get('data_inicio') and p.get('data_contrato'):
            try:
                data_inicio_str = p.get('data_inicio')
                data_contrato_str = p.get('data_contrato')
                
                # Parse das datas
                if isinstance(data_inicio_str, str) and data_inicio_str not in ['None', 'null', '']:
                    if 'T' in data_inicio_str:
                        data_inicio_dt = datetime.fromisoformat(data_inicio_str.replace('Z', '+00:00'))
                    else:
                        data_inicio_dt = datetime.strptime(data_inicio_str.split(' ')[0], '%Y-%m-%d')
                    
                    if isinstance(data_contrato_str, str) and data_contrato_str not in ['None', 'null', '']:
                        if 'T' in data_contrato_str:
                            data_contrato_dt = datetime.fromisoformat(data_contrato_str.replace('Z', '+00:00'))
                        else:
                            data_contrato_dt = datetime.strptime(data_contrato_str.split(' ')[0], '%Y-%m-%d')
                        
                        dias = (data_contrato_dt - data_inicio_dt).days
                        if dias >= 0 and dias < 365:  # Filtrar outliers
                            tempos_finalizacao.append(dias)
                            
                            # Por mês
                            mes_ano = data_inicio_dt.strftime('%Y-%m')
                            if mes_ano not in tempos_por_mes:
                                tempos_por_mes[mes_ano] = []
                            tempos_por_mes[mes_ano].append(dias)
                            
                            # Por modalidade
                            modalidade = p.get('modalidade', 'Não Definido')
                            if modalidade not in tempos_por_modalidade:
                                tempos_por_modalidade[modalidade] = []
                            tempos_por_modalidade[modalidade].append(dias)
            except Exception as e:
                continue
    
    tempo_medio_geral = round(sum(tempos_finalizacao) / len(tempos_finalizacao), 1) if tempos_finalizacao else 0
    
    # Tempo médio por mês
    tempo_medio_por_mes = []
    for mes, tempos in sorted(tempos_por_mes.items()):
        tempo_medio_por_mes.append({
            'mes': mes,
            'tempo_medio': round(sum(tempos) / len(tempos), 1) if tempos else 0,
            'quantidade': len(tempos)
        })
    
    # Tempo médio por modalidade
    tempo_medio_por_modalidade = []
    for modalidade, tempos in tempos_por_modalidade.items():
        tempo_medio_por_modalidade.append({
            'modalidade': modalidade,
            'tempo_medio': round(sum(tempos) / len(tempos), 1) if tempos else 0,
            'quantidade': len(tempos)
        })
    tempo_medio_por_modalidade.sort(key=lambda x: x['tempo_medio'], reverse=True)
    
    # 4. Processos por Responsável/Usuário
    processos_por_responsavel = {}
    for p in processos_validos:
        responsavel = p.get('responsavel', 'Não Atribuído') or 'Não Atribuído'
        if responsavel not in processos_por_responsavel:
            processos_por_responsavel[responsavel] = {
                'responsavel': responsavel,
                'quantidade': 0,
                'concluidos': 0,
                'em_andamento': 0
            }
        processos_por_responsavel[responsavel]['quantidade'] += 1
        if p.get('status') == 'Concluído':
            processos_por_responsavel[responsavel]['concluidos'] += 1
        else:
            processos_por_responsavel[responsavel]['em_andamento'] += 1
    
    lista_responsaveis = list(processos_por_responsavel.values())
    lista_responsaveis.sort(key=lambda x: x['quantidade'], reverse=True)
    
    # 5. Processos por Secretaria
    processos_por_secretaria = {}
    for p in processos_validos:
        secretaria = p.get('secretaria', 'Não Informada') or 'Não Informada'
        if secretaria not in processos_por_secretaria:
            processos_por_secretaria[secretaria] = {'secretaria': secretaria, 'quantidade': 0}
        processos_por_secretaria[secretaria]['quantidade'] += 1
    
    lista_secretarias = list(processos_por_secretaria.values())
    lista_secretarias.sort(key=lambda x: x['quantidade'], reverse=True)
    
    # 6. Processos por mês (timeline)
    processos_por_mes = {}
    for p in processos_validos:
        data_inicio_str = p.get('data_inicio')
        if data_inicio_str and data_inicio_str not in ['None', 'null', '']:
            try:
                if 'T' in str(data_inicio_str):
                    dt = datetime.fromisoformat(str(data_inicio_str).replace('Z', '+00:00'))
                else:
                    dt = datetime.strptime(str(data_inicio_str).split(' ')[0], '%Y-%m-%d')
                mes_ano = dt.strftime('%Y-%m')
                if mes_ano not in processos_por_mes:
                    processos_por_mes[mes_ano] = {'mes': mes_ano, 'quantidade': 0, 'concluidos': 0}
                processos_por_mes[mes_ano]['quantidade'] += 1
                if p.get('status') == 'Concluído':
                    processos_por_mes[mes_ano]['concluidos'] += 1
            except:
                pass
    
    timeline = list(processos_por_mes.values())
    timeline.sort(key=lambda x: x['mes'])
    
    # Calcular médias gerais
    total_processos = len(processos_validos)
    total_concluidos = sum(1 for p in processos_validos if p.get('status') == 'Concluído')
    total_em_andamento = total_processos - total_concluidos
    taxa_conclusao = round((total_concluidos / total_processos * 100), 1) if total_processos > 0 else 0
    
    return {
        'total_processos': total_processos,
        'total_concluidos': total_concluidos,
        'total_em_andamento': total_em_andamento,
        'taxa_conclusao': taxa_conclusao,
        'tempo_medio_dias': tempo_medio_geral,
        'stats_by_status': list(stats_by_status.values()),
        'stats_by_modalidade': list(stats_by_modalidade.values()),
        'tempo_medio_por_mes': tempo_medio_por_mes,
        'tempo_medio_por_modalidade': tempo_medio_por_modalidade,
        'processos_por_responsavel': lista_responsaveis,
        'processos_por_secretaria': lista_secretarias,
        'timeline': timeline
    }

@api_router.post("/processos", response_model=Processo)
async def create_processo(processo_data: ProcessoCreate, request: Request):
    """Cria um novo processo - qualquer usuário autenticado"""
    user = await get_current_user(request)
    processo_id = f"proc_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    
    processo_doc = {
        'processo_id': processo_id,
        'user_id': user.user_id,
        **processo_data.model_dump(),
        'created_at': now,
        'updated_at': now
    }
    
    # Extrair ano do numero_processo se não fornecido (ex: PRC - 0006/2025)
    if not processo_doc.get('ano'):
        numero = processo_doc.get('numero_processo', '')
        match = re.search(r'/(\d{4})$', numero)
        if match:
            processo_doc['ano'] = int(match.group(1))
        else:
            processo_doc['ano'] = now.year
    
    # Converter datas para o formato correto
    if processo_doc.get('data_inicio'):
        processo_doc['data_inicio'] = processo_doc['data_inicio'].isoformat() if isinstance(processo_doc['data_inicio'], datetime) else processo_doc['data_inicio']
    if processo_doc.get('data_autuacao'):
        processo_doc['data_autuacao'] = processo_doc['data_autuacao'].isoformat() if isinstance(processo_doc['data_autuacao'], datetime) else processo_doc['data_autuacao']
    if processo_doc.get('data_contrato'):
        processo_doc['data_contrato'] = processo_doc['data_contrato'].isoformat() if isinstance(processo_doc['data_contrato'], datetime) else processo_doc['data_contrato']
    
    await db.processos.insert_one(processo_doc)
    return Processo(**processo_doc)

@api_router.get("/processos/{processo_id}", response_model=Processo)
async def get_processo(processo_id: str, request: Request):
    """Obtém um processo específico"""
    user = await get_current_user(request)
    processo = await db.processos.find_one({'processo_id': processo_id}, {'_id': 0})
    if not processo:
        raise HTTPException(status_code=404, detail="Processo not found")
    return Processo(**processo)

@api_router.put("/processos/{processo_id}", response_model=Processo)
async def update_processo(processo_id: str, processo_update: ProcessoUpdate, request: Request):
    """Atualiza um processo - qualquer usuário autenticado"""
    user = await get_current_user(request)
    processo = await db.processos.find_one({'processo_id': processo_id}, {'_id': 0})
    if not processo:
        raise HTTPException(status_code=404, detail="Processo not found")
    
    update_data = {k: v for k, v in processo_update.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc)
    
    # Converter datas
    for date_field in ['data_inicio', 'data_autuacao', 'data_contrato']:
        if date_field in update_data and update_data[date_field]:
            if isinstance(update_data[date_field], datetime):
                update_data[date_field] = update_data[date_field].isoformat()
    
    await db.processos.update_one({'processo_id': processo_id}, {'$set': update_data})
    updated = await db.processos.find_one({'processo_id': processo_id}, {'_id': 0})
    return Processo(**updated)

@api_router.delete("/processos/{processo_id}")
async def delete_processo(processo_id: str, request: Request):
    """Exclui um processo - APENAS ADMINISTRADORES"""
    user = await get_current_user(request)
    
    # Verificar se é admin
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Apenas administradores podem excluir processos")
    
    processo = await db.processos.find_one({'processo_id': processo_id}, {'_id': 0})
    if not processo:
        raise HTTPException(status_code=404, detail="Processo not found")
    
    await db.processos.delete_one({'processo_id': processo_id})
    return {'message': 'Processo excluído com sucesso'}

@api_router.post("/processos/migrate-fields")
async def migrate_processos_fields(request: Request):
    """
    Migra campos antigos para nova nomenclatura:
    - modalidade -> modalidade_contratacao
    - situacao -> status (se status vazio)
    ADMIN ONLY
    """
    user = await get_current_user(request)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Apenas administradores podem executar migrações")
    
    processos = await db.processos.find({}).to_list(None)
    migrated_count = 0
    
    for proc in processos:
        update_data = {}
        
        # Migrar modalidade para modalidade_contratacao
        if proc.get('modalidade') and not proc.get('modalidade_contratacao'):
            update_data['modalidade_contratacao'] = proc['modalidade']
        
        # Se não tem status mas tem situação antiga, usar como status
        # Nota: O campo status já existe mas com valores diferentes
        # Precisamos mapear os valores antigos para os novos
        old_status = proc.get('status', '')
        status_mapping = {
            'Iniciado': 'Em Elaboração',
            'Publicado': 'Em Licitação',
            'Aguardando Jurídico': 'Em Licitação',
            'Homologado': 'Homologado',
            'Concluído': 'Concluído',
            'Cancelado': 'Cancelado'
        }
        
        if old_status in status_mapping:
            update_data['status'] = status_mapping[old_status]
        
        if update_data:
            await db.processos.update_one(
                {'processo_id': proc['processo_id']},
                {'$set': update_data}
            )
            migrated_count += 1
    
    return {
        'message': f'Migração concluída: {migrated_count} processos atualizados',
        'total_processos': len(processos),
        'migrated': migrated_count
    }

@api_router.post("/processos/import")
async def import_processos(file: UploadFile = File(...), request: Request = None):
    """Importa processos de um arquivo Excel/CSV"""
    user = await get_current_user(request)
    
    content = await file.read()
    filename = file.filename.lower()
    
    items_to_import = []
    
    try:
        if filename.endswith('.csv'):
            import csv
            import io
            decoded = content.decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(decoded), delimiter=';')
            for row in reader:
                items_to_import.append(row)
                
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            from openpyxl import load_workbook
            wb = load_workbook(filename=BytesIO(content))
            ws = wb.active
            
            headers = [cell.value for cell in ws[1] if cell.value]
            
            for row in ws.iter_rows(min_row=2, values_only=True):
                if any(row):
                    item = dict(zip(headers, row))
                    items_to_import.append(item)
        else:
            raise HTTPException(status_code=400, detail="Formato não suportado. Use CSV ou XLSX")
        
        imported_count = 0
        for item_data in items_to_import:
            # Mapear campos da planilha
            numero = str(item_data.get('Processo', item_data.get('Column1', '')))
            if not numero:
                continue
            
            processo_id = f"proc_{uuid.uuid4().hex[:12]}"
            now = datetime.now(timezone.utc)
            
            # Processar datas
            data_inicio = item_data.get('Data de Início', item_data.get('Column6'))
            data_autuacao = item_data.get('Data de Autuação', item_data.get('Column7'))
            data_contrato = item_data.get('Data do Contrato', item_data.get('Column8'))
            
            processo_doc = {
                'processo_id': processo_id,
                'user_id': user.user_id,
                'numero_processo': numero,
                'status': str(item_data.get('Status', item_data.get('Column2', 'Iniciado'))),
                'modalidade': str(item_data.get('Modalidade', item_data.get('Column3', ''))),
                'objeto': str(item_data.get('Objeto', item_data.get('Column4', '')))[:1000],
                'situacao': str(item_data.get('Situação', item_data.get('Column5', '')))[:50],
                'responsavel': str(item_data.get('Responsável', item_data.get('Column6', '')))[:100] if not isinstance(item_data.get('Responsável', item_data.get('Column6')), datetime) else '',
                'data_inicio': str(data_inicio) if data_inicio else None,
                'data_autuacao': str(data_autuacao) if data_autuacao else None,
                'data_contrato': str(data_contrato) if data_contrato else None,
                'secretaria': str(item_data.get('Secretaria', item_data.get('Column9', '')))[:200],
                'secretario': str(item_data.get('Secretário', item_data.get('Column10', '')))[:100],
                'observacoes': str(item_data.get('Observações', item_data.get('Column11', '')))[:500] if item_data.get('Observações', item_data.get('Column11')) else '',
                'created_at': now,
                'updated_at': now
            }
            
            await db.processos.insert_one(processo_doc)
            imported_count += 1
        
        return {'message': f'{imported_count} processos importados com sucesso', 'total_items': imported_count}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {str(e)}")

@api_router.get("/processos/export/pdf")
async def export_processos_pdf(request: Request, orientation: str = "landscape", assinar: bool = True, data: str = None):
    """
    Exporta todos os processos para PDF com margens padronizadas
    Args:
        assinar: Se True, adiciona assinatura digital
        data: Data da assinatura (formato DD/MM/YYYY HH:MM:SS) - retroativa se necessário
    """
    user = await get_current_user(request)
    processos = await db.processos.find({}, {'_id': 0}).to_list(1000)
    
    buffer = BytesIO()
    
    # Margens padronizadas conforme Lei 14.133/2021
    # 5cm (esquerda/direita), 3cm (superior/inferior)
    page_size = A4 if orientation.lower() == 'portrait' else landscape(A4)
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=page_size,
        leftMargin=REPORT_MARGIN_LEFT, 
        rightMargin=REPORT_MARGIN_RIGHT, 
        topMargin=REPORT_MARGIN_TOP, 
        bottomMargin=REPORT_MARGIN_BOTTOM
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Heading1'], fontSize=14,
        textColor=colors.HexColor('#1F4788'), spaceAfter=4,
        alignment=TA_CENTER, fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle', parent=styles['Heading2'], fontSize=11,
        textColor=colors.HexColor('#1F4788'), spaceAfter=6,
        alignment=TA_CENTER, fontName='Helvetica-Bold'
    )
    
    # Logotipo proporcional
    logo_path = ROOT_DIR / 'brasao_acaiaca.jpg'
    if logo_path.exists():
        try:
            from PIL import Image as PILImage
            pil_img = PILImage.open(str(logo_path))
            img_width, img_height = pil_img.size
            aspect_ratio = img_height / img_width
            max_logo_width = 2*cm
            logo_width = max_logo_width
            logo_height = logo_width * aspect_ratio
            logo = Image(str(logo_path), width=logo_width, height=logo_height)
            elements.append(logo)
        except:
            pass
    
    elements.append(Paragraph('PREFEITURA MUNICIPAL DE ACAIACA - MG', title_style))
    elements.append(Paragraph('GESTÃO PROCESSUAL - RELATÓRIO DE PROCESSOS', subtitle_style))
    elements.append(Paragraph('<i>Lei Federal nº 14.133/2021</i>', ParagraphStyle('Legal', parent=styles['Normal'], fontSize=7, alignment=TA_CENTER, textColor=colors.grey, spaceAfter=6)))
    
    # Tabela de processos - campos COMPLETOS
    if orientation.lower() == 'portrait':
        table_data = [['#', 'Processo', 'Status', 'Modalidade', 'Objeto', 'Secretaria']]
        for idx, p in enumerate(processos, start=1):
            table_data.append([
                str(idx),
                p.get('numero_processo', ''),  # COMPLETO
                p.get('status', ''),  # COMPLETO
                Paragraph(f"<font size=6>{p.get('modalidade', '')}</font>", styles['Normal']),  # COMPLETO
                Paragraph(f"<font size=6>{p.get('objeto', '')}</font>", styles['Normal']),  # COMPLETO
                Paragraph(f"<font size=6>{p.get('secretaria', '')}</font>", styles['Normal'])  # COMPLETO
            ])
        col_widths = [0.5*cm, 2*cm, 1.8*cm, 3*cm, 5.5*cm, 3.5*cm]
    else:
        table_data = [['#', 'Processo', 'Status', 'Modalidade', 'Objeto', 'Responsável', 'Secretaria', 'Observações']]
        for idx, p in enumerate(processos, start=1):
            table_data.append([
                str(idx),
                p.get('numero_processo', ''),  # COMPLETO
                p.get('status', ''),  # COMPLETO
                Paragraph(f"<font size=6>{p.get('modalidade', '')}</font>", styles['Normal']),  # COMPLETO
                Paragraph(f"<font size=6>{p.get('objeto', '')}</font>", styles['Normal']),  # COMPLETO
                p.get('responsavel', ''),  # COMPLETO
                Paragraph(f"<font size=6>{p.get('secretaria', '')}</font>", styles['Normal']),  # COMPLETO
                Paragraph(f"<font size=5>{p.get('observacoes', '')}</font>", styles['Normal'])  # COMPLETO
            ])
        col_widths = [0.5*cm, 2.2*cm, 1.6*cm, 2.5*cm, 6.5*cm, 2*cm, 4*cm, 4*cm]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('FONTSIZE', (0, 1), (-1, -1), 6),
        ('ALIGN', (0, 1), (2, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 8*mm))
    
    # Rodapé
    footer_text = f'<font size=6><i>Total de {len(processos)} processos | Gerado em {datetime.now().strftime("%d/%m/%Y às %H:%M")} | Sistema Planejamento Acaiaca</i></font>'
    elements.append(Paragraph(footer_text, ParagraphStyle('Footer', alignment=TA_CENTER, textColor=colors.grey)))
    
    doc.build(elements)
    buffer.seek(0)
    
    orientation_name = 'Paisagem' if orientation.lower() == 'landscape' else 'Retrato'
    
    # Adicionar assinatura digital ao PDF
    try:
        signed_buffer, validation_code = await add_signature_to_pdf(
            buffer, user, "Relatório de Gestão Processual", f"processos_{datetime.now().strftime('%Y%m%d%H%M%S')}", None, data
        )
        return StreamingResponse(
            signed_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Gestao_Processual_{orientation_name}.pdf",
                "X-Validation-Code": validation_code
            }
        )
    except HTTPException:
        # Re-raise HTTPException para validação de CPF/Cargo
        raise
    except Exception as e:
        logging.error(f"Erro ao adicionar assinatura ao PDF de processos: {e}")
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Gestao_Processual_{orientation_name}.pdf"}
        )

@api_router.get("/processos/export/xlsx")
async def export_processos_xlsx(request: Request):
    """Exporta todos os processos para Excel"""
    user = await get_current_user(request)
    processos = await db.processos.find({}, {'_id': 0}).to_list(1000)
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Gestão Processual"
    
    # Cabeçalho
    headers = ['#', 'Processo', 'Status', 'Modalidade', 'Objeto', 'Situação', 'Responsável', 
               'Data Início', 'Data Autuação', 'Data Contrato', 'Secretaria', 'Secretário', 'Observações']
    
    header_fill = PatternFill(start_color="1F4788", end_color="1F4788", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
    
    # Dados
    for row, p in enumerate(processos, start=2):
        ws.cell(row=row, column=1, value=row-1)
        ws.cell(row=row, column=2, value=p.get('numero_processo', ''))
        ws.cell(row=row, column=3, value=p.get('status', ''))
        ws.cell(row=row, column=4, value=p.get('modalidade', ''))
        ws.cell(row=row, column=5, value=p.get('objeto', ''))
        ws.cell(row=row, column=6, value=p.get('situacao', ''))
        ws.cell(row=row, column=7, value=p.get('responsavel', ''))
        ws.cell(row=row, column=8, value=p.get('data_inicio', ''))
        ws.cell(row=row, column=9, value=p.get('data_autuacao', ''))
        ws.cell(row=row, column=10, value=p.get('data_contrato', ''))
        ws.cell(row=row, column=11, value=p.get('secretaria', ''))
        ws.cell(row=row, column=12, value=p.get('secretario', ''))
        ws.cell(row=row, column=13, value=p.get('observacoes', ''))
    
    # Ajustar larguras
    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 25
    ws.column_dimensions['E'].width = 50
    ws.column_dimensions['F'].width = 10
    ws.column_dimensions['G'].width = 20
    ws.column_dimensions['H'].width = 15
    ws.column_dimensions['I'].width = 15
    ws.column_dimensions['J'].width = 15
    ws.column_dimensions['K'].width = 30
    ws.column_dimensions['L'].width = 25
    ws.column_dimensions['M'].width = 40
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=Gestao_Processual.xlsx"}
    )

# ============ BACKUP E RESTAURAÇÃO DO SISTEMA ============

import json

# ============ FUNÇÃO HELPER PARA SERIALIZAÇÃO JSON ============
def serialize_for_json(obj):
    """Converte objetos para tipos serializáveis em JSON"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        return serialize_for_json(obj.__dict__)
    return obj

def serialize_document(doc):
    """Serializa um documento MongoDB removendo _id e convertendo datetime"""
    if doc is None:
        return None
    serialized = {}
    for key, value in doc.items():
        if key == '_id':
            continue
        serialized[key] = serialize_for_json(value)
    return serialized

@api_router.get("/backup/export")
async def export_backup(request: Request):
    """
    Exporta todos os dados do sistema para um arquivo JSON.
    Permite restaurar os dados após fork/redeploy.
    Apenas administradores podem fazer backup.
    """
    user = await get_current_user(request)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Apenas administradores podem fazer backup")
    
    try:
        # Coletar todos os dados das coleções
        backup_data = {
            'metadata': {
                'version': '2.1',
                'exported_at': datetime.now(timezone.utc).isoformat(),
                'exported_by': user.email,
                'system': 'Planejamento Acaiaca'
            },
            'users': [],
            'pacs': [],
            'pac_items': [],
            'pacs_geral': [],
            'pac_geral_items': [],
            'pacs_geral_obras': [],
            'pac_geral_obras_items': [],
            'processos': [],
            'mrosc_projetos': [],
            'mrosc_rh': [],
            'mrosc_despesas': [],
            'mrosc_documentos': [],
            'doem_edicoes': [],
            'doem_config': [],
            'doem_newsletter': [],
            'document_signatures': [],
            'user_sessions': []
        }
        
        # Exportar todas as coleções usando a função helper
        collections_map = [
            ('users', 'users'),
            ('pacs', 'pacs'),
            ('pac_items', 'pac_items'),
            ('pacs_geral', 'pacs_geral'),
            ('pac_geral_items', 'pac_geral_items'),
            ('pacs_geral_obras', 'pacs_geral_obras'),
            ('pac_geral_obras_items', 'pac_geral_obras_items'),
            ('processos', 'processos'),
            ('mrosc_projetos', 'mrosc_projetos'),
            ('mrosc_rh', 'mrosc_rh'),
            ('mrosc_despesas', 'mrosc_despesas'),
            ('mrosc_documentos', 'mrosc_documentos'),
            ('doem_edicoes', 'doem_edicoes'),
            ('doem_config', 'doem_config'),
            ('doem_newsletter', 'doem_newsletter'),
            ('document_signatures', 'document_signatures'),
        ]
        
        for collection_name, backup_key in collections_map:
            try:
                collection = db[collection_name]
                docs = await collection.find({}).to_list(100000)
                backup_data[backup_key] = [serialize_document(doc) for doc in docs]
            except Exception as e:
                logging.warning(f"Erro ao exportar {collection_name}: {str(e)}")
                backup_data[backup_key] = []
        
        # Gerar JSON
        json_content = json.dumps(backup_data, ensure_ascii=False, indent=2, default=str)
        
        # Criar resposta como download
        buffer = BytesIO(json_content.encode('utf-8'))
        buffer.seek(0)
        
        filename = f"backup_planejamento_acaiaca_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return StreamingResponse(
            buffer,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except Exception as e:
        logging.error(f"Erro ao gerar backup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar backup: {str(e)}")


@api_router.post("/backup/restore")
async def restore_backup(request: Request, file: UploadFile = File(...)):
    """
    Restaura todos os dados do sistema a partir de um arquivo de backup JSON.
    ATENÇÃO: Esta operação substitui TODOS os dados existentes!
    Apenas administradores podem restaurar backup.
    """
    user = await get_current_user(request)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Apenas administradores podem restaurar backup")
    
    try:
        # Ler arquivo
        contents = await file.read()
        backup_data = json.loads(contents.decode('utf-8'))
        
        # Validar estrutura do backup
        required_keys = ['metadata', 'users', 'pacs', 'pac_items', 'pacs_geral', 'pac_geral_items', 'processos']
        for key in required_keys:
            if key not in backup_data:
                raise HTTPException(status_code=400, detail=f"Arquivo de backup inválido: falta a chave '{key}'")
        
        # Contadores
        stats = {
            'users': 0,
            'pacs': 0,
            'pac_items': 0,
            'pacs_geral': 0,
            'pac_geral_items': 0,
            'processos': 0
        }
        
        # Restaurar usuários (não sobrescreve o admin atual)
        current_admin_email = user.email
        for u in backup_data['users']:
            # Não sobrescrever o usuário admin atual
            if u.get('email') == current_admin_email:
                continue
            
            # Converter datas
            if 'created_at' in u and isinstance(u['created_at'], str):
                u['created_at'] = datetime.fromisoformat(u['created_at'].replace('Z', '+00:00'))
            
            # Upsert por user_id
            await db.users.update_one(
                {'user_id': u['user_id']},
                {'$set': u},
                upsert=True
            )
            stats['users'] += 1
        
        # Restaurar PACs
        for p in backup_data['pacs']:
            for field in ['created_at', 'updated_at']:
                if field in p and isinstance(p[field], str):
                    p[field] = datetime.fromisoformat(p[field].replace('Z', '+00:00'))
            
            await db.pacs.update_one(
                {'pac_id': p['pac_id']},
                {'$set': p},
                upsert=True
            )
            stats['pacs'] += 1
        
        # Restaurar PAC Items
        for item in backup_data['pac_items']:
            if 'created_at' in item and isinstance(item['created_at'], str):
                item['created_at'] = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
            
            await db.pac_items.update_one(
                {'item_id': item['item_id']},
                {'$set': item},
                upsert=True
            )
            stats['pac_items'] += 1
        
        # Restaurar PACs Geral
        for pg in backup_data['pacs_geral']:
            for field in ['created_at', 'updated_at']:
                if field in pg and isinstance(pg[field], str):
                    pg[field] = datetime.fromisoformat(pg[field].replace('Z', '+00:00'))
            
            await db.pacs_geral.update_one(
                {'pac_geral_id': pg['pac_geral_id']},
                {'$set': pg},
                upsert=True
            )
            stats['pacs_geral'] += 1
        
        # Restaurar PAC Geral Items
        for item in backup_data['pac_geral_items']:
            if 'created_at' in item and isinstance(item['created_at'], str):
                item['created_at'] = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
            
            await db.pac_geral_items.update_one(
                {'item_id': item['item_id']},
                {'$set': item},
                upsert=True
            )
            stats['pac_geral_items'] += 1
        
        # Restaurar PACs Geral Obras
        for pgo in backup_data.get('pacs_geral_obras', []):
            for field in ['created_at', 'updated_at']:
                if field in pgo and isinstance(pgo[field], str):
                    try:
                        pgo[field] = datetime.fromisoformat(pgo[field].replace('Z', '+00:00'))
                    except:
                        pass
            await db.pacs_geral_obras.update_one(
                {'pac_obras_id': pgo['pac_obras_id']},
                {'$set': pgo},
                upsert=True
            )
            stats['pacs_geral_obras'] = stats.get('pacs_geral_obras', 0) + 1
        
        # Restaurar PAC Geral Obras Items
        for item in backup_data.get('pac_geral_obras_items', []):
            if 'created_at' in item and isinstance(item['created_at'], str):
                try:
                    item['created_at'] = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                except:
                    pass
            await db.pac_geral_obras_items.update_one(
                {'item_id': item['item_id']},
                {'$set': item},
                upsert=True
            )
            stats['pac_geral_obras_items'] = stats.get('pac_geral_obras_items', 0) + 1
        
        # Restaurar Processos
        for proc in backup_data['processos']:
            for field in ['created_at', 'updated_at', 'data_inicio', 'data_autuacao', 'data_contrato']:
                if field in proc and isinstance(proc[field], str):
                    try:
                        proc[field] = datetime.fromisoformat(proc[field].replace('Z', '+00:00'))
                    except:
                        proc[field] = None
            
            await db.processos.update_one(
                {'processo_id': proc['processo_id']},
                {'$set': proc},
                upsert=True
            )
            stats['processos'] += 1
        
        # Restaurar MROSC Projetos
        for proj in backup_data.get('mrosc_projetos', []):
            for field in ['created_at', 'updated_at', 'data_inicio', 'data_fim']:
                if field in proj and isinstance(proj[field], str):
                    try:
                        proj[field] = datetime.fromisoformat(proj[field].replace('Z', '+00:00'))
                    except:
                        pass
            await db.mrosc_projetos.update_one(
                {'projeto_id': proj['projeto_id']},
                {'$set': proj},
                upsert=True
            )
            stats['mrosc_projetos'] = stats.get('mrosc_projetos', 0) + 1
        
        # Restaurar MROSC RH
        for rh in backup_data.get('mrosc_rh', []):
            if 'created_at' in rh and isinstance(rh['created_at'], str):
                try:
                    rh['created_at'] = datetime.fromisoformat(rh['created_at'].replace('Z', '+00:00'))
                except:
                    pass
            await db.mrosc_rh.update_one(
                {'rh_id': rh['rh_id']},
                {'$set': rh},
                upsert=True
            )
            stats['mrosc_rh'] = stats.get('mrosc_rh', 0) + 1
        
        # Restaurar MROSC Despesas
        for desp in backup_data.get('mrosc_despesas', []):
            if 'created_at' in desp and isinstance(desp['created_at'], str):
                try:
                    desp['created_at'] = datetime.fromisoformat(desp['created_at'].replace('Z', '+00:00'))
                except:
                    pass
            await db.mrosc_despesas.update_one(
                {'despesa_id': desp['despesa_id']},
                {'$set': desp},
                upsert=True
            )
            stats['mrosc_despesas'] = stats.get('mrosc_despesas', 0) + 1
        
        # Restaurar MROSC Documentos
        for doc in backup_data.get('mrosc_documentos', []):
            for field in ['created_at', 'data_documento', 'validated_at']:
                if field in doc and isinstance(doc[field], str):
                    try:
                        doc[field] = datetime.fromisoformat(doc[field].replace('Z', '+00:00'))
                    except:
                        pass
            await db.mrosc_documentos.update_one(
                {'documento_id': doc['documento_id']},
                {'$set': doc},
                upsert=True
            )
            stats['mrosc_documentos'] = stats.get('mrosc_documentos', 0) + 1
        
        # Restaurar DOEM Edições
        for edicao in backup_data.get('doem_edicoes', []):
            for field in ['created_at', 'updated_at', 'data_publicacao']:
                if field in edicao and isinstance(edicao[field], str):
                    try:
                        edicao[field] = datetime.fromisoformat(edicao[field].replace('Z', '+00:00'))
                    except:
                        pass
            await db.doem_edicoes.update_one(
                {'edicao_id': edicao['edicao_id']},
                {'$set': edicao},
                upsert=True
            )
            stats['doem_edicoes'] = stats.get('doem_edicoes', 0) + 1
        
        # Restaurar DOEM Config
        for config in backup_data.get('doem_config', []):
            await db.doem_config.update_one(
                {'config_id': config.get('config_id', 'doem_config_main')},
                {'$set': config},
                upsert=True
            )
            stats['doem_config'] = stats.get('doem_config', 0) + 1
        
        # Restaurar DOEM Newsletter
        for news in backup_data.get('doem_newsletter', []):
            for field in ['created_at', 'confirmed_at']:
                if field in news and isinstance(news[field], str):
                    try:
                        news[field] = datetime.fromisoformat(news[field].replace('Z', '+00:00'))
                    except:
                        pass
            await db.doem_newsletter.update_one(
                {'email': news['email']},
                {'$set': news},
                upsert=True
            )
            stats['doem_newsletter'] = stats.get('doem_newsletter', 0) + 1
        
        # Restaurar Assinaturas de Documentos
        for sig in backup_data.get('document_signatures', []):
            if 'created_at' in sig and isinstance(sig['created_at'], str):
                try:
                    sig['created_at'] = datetime.fromisoformat(sig['created_at'].replace('Z', '+00:00'))
                except:
                    pass
            await db.document_signatures.update_one(
                {'validation_code': sig['validation_code']},
                {'$set': sig},
                upsert=True
            )
            stats['document_signatures'] = stats.get('document_signatures', 0) + 1
        
        return {
            'success': True,
            'message': 'Backup restaurado com sucesso!',
            'stats': stats,
            'backup_metadata': backup_data.get('metadata', {})
        }
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Arquivo de backup inválido: não é um JSON válido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao restaurar backup: {str(e)}")


@api_router.get("/backup/info")
async def get_backup_info(request: Request):
    """
    Retorna informações sobre os dados atuais do sistema para backup.
    """
    user = await get_current_user(request)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Apenas administradores podem ver informações de backup")
    
    # Contar documentos em cada coleção
    users_count = await db.users.count_documents({})
    pacs_count = await db.pacs.count_documents({})
    pac_items_count = await db.pac_items.count_documents({})
    pacs_geral_count = await db.pacs_geral.count_documents({})
    pac_geral_items_count = await db.pac_geral_items.count_documents({})
    pacs_geral_obras_count = await db.pacs_geral_obras.count_documents({})
    pac_geral_obras_items_count = await db.pac_geral_obras_items.count_documents({})
    processos_count = await db.processos.count_documents({})
    mrosc_projetos_count = await db.mrosc_projetos.count_documents({})
    mrosc_rh_count = await db.mrosc_rh.count_documents({})
    mrosc_despesas_count = await db.mrosc_despesas.count_documents({})
    mrosc_documentos_count = await db.mrosc_documentos.count_documents({})
    doem_edicoes_count = await db.doem_edicoes.count_documents({})
    doem_newsletter_count = await db.doem_newsletter.count_documents({})
    document_signatures_count = await db.document_signatures.count_documents({})
    
    total = (users_count + pacs_count + pac_items_count + pacs_geral_count + 
             pac_geral_items_count + pacs_geral_obras_count + pac_geral_obras_items_count +
             processos_count + mrosc_projetos_count + mrosc_rh_count + mrosc_despesas_count +
             mrosc_documentos_count + doem_edicoes_count + doem_newsletter_count + document_signatures_count)
    
    return {
        'system': 'Planejamento Acaiaca',
        'version': '2.0',
        'current_data': {
            'users': users_count,
            'pacs': pacs_count,
            'pac_items': pac_items_count,
            'pacs_geral': pacs_geral_count,
            'pac_geral_items': pac_geral_items_count,
            'pacs_geral_obras': pacs_geral_obras_count,
            'pac_geral_obras_items': pac_geral_obras_items_count,
            'processos': processos_count,
            'mrosc_projetos': mrosc_projetos_count,
            'mrosc_rh': mrosc_rh_count,
            'mrosc_despesas': mrosc_despesas_count,
            'mrosc_documentos': mrosc_documentos_count,
            'doem_edicoes': doem_edicoes_count,
            'doem_newsletter': doem_newsletter_count,
            'document_signatures': document_signatures_count
        },
        'total_records': total,
        'backup_available': True,
        'restore_available': True
    }


# ============ PORTAL PÚBLICO - TRANSPARÊNCIA ============
# Endpoints públicos para acesso sem autenticação
# Conformidade com Lei de Acesso à Informação (Lei 12.527/2011)

public_router = APIRouter(prefix="/api/public")

@public_router.get("/pacs")
async def public_get_pacs(
    secretaria: str = None,
    ano: str = "2026",
    page: int = 1,
    limit: int = 50
):
    """
    Lista pública de PACs Individuais.
    Não requer autenticação - Portal de Transparência.
    """
    query = {}
    if secretaria:
        query['secretaria'] = {'$regex': secretaria, '$options': 'i'}
    if ano:
        query['ano'] = ano
    
    skip = (page - 1) * limit
    total = await db.pacs.count_documents(query)
    
    pacs = await db.pacs.find(query, {
        '_id': 0,
        'user_id': 0  # Ocultar informações internas
    }).skip(skip).limit(limit).to_list(limit)
    
    return {
        'success': True,
        'data': pacs,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': total,
            'pages': (total + limit - 1) // limit
        }
    }

@public_router.get("/pacs/{pac_id}")
async def public_get_pac(pac_id: str):
    """Detalhes públicos de um PAC específico."""
    pac = await db.pacs.find_one({'pac_id': pac_id}, {'_id': 0, 'user_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC não encontrado")
    return {'success': True, 'data': pac}

@public_router.get("/pacs/{pac_id}/items")
async def public_get_pac_items(pac_id: str):
    """Lista pública de itens de um PAC."""
    pac = await db.pacs.find_one({'pac_id': pac_id})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC não encontrado")
    
    items = await db.pac_items.find({'pac_id': pac_id}, {'_id': 0}).to_list(1000)
    return {'success': True, 'data': items, 'total': len(items)}

@public_router.get("/pacs-geral")
async def public_get_pacs_geral(page: int = 1, limit: int = 50):
    """Lista pública de PACs Gerais."""
    skip = (page - 1) * limit
    total = await db.pacs_geral.count_documents({})
    
    pacs = await db.pacs_geral.find({}, {
        '_id': 0,
        'user_id': 0
    }).skip(skip).limit(limit).to_list(limit)
    
    return {
        'success': True,
        'data': pacs,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': total,
            'pages': (total + limit - 1) // limit
        }
    }

@public_router.get("/pacs-geral/{pac_geral_id}")
async def public_get_pac_geral(pac_geral_id: str):
    """Detalhes públicos de um PAC Geral."""
    pac = await db.pacs_geral.find_one({'pac_geral_id': pac_geral_id}, {'_id': 0, 'user_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC Geral não encontrado")
    return {'success': True, 'data': pac}

@public_router.get("/pacs-geral/{pac_geral_id}/items")
async def public_get_pac_geral_items(pac_geral_id: str):
    """Lista pública de itens de um PAC Geral."""
    pac = await db.pacs_geral.find_one({'pac_geral_id': pac_geral_id})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC Geral não encontrado")
    
    items = await db.pac_geral_items.find({'pac_geral_id': pac_geral_id}, {'_id': 0}).to_list(1000)
    return {'success': True, 'data': items, 'total': len(items)}

@public_router.get("/processos")
async def public_get_processos(
    status: str = None,
    modalidade: str = None,
    secretaria: str = None,
    page: int = 1,
    limit: int = 50
):
    """
    Lista pública de processos licitatórios.
    Não requer autenticação - Portal de Transparência.
    """
    query = {}
    if status:
        query['status'] = {'$regex': status, '$options': 'i'}
    if modalidade:
        query['modalidade'] = {'$regex': modalidade, '$options': 'i'}
    if secretaria:
        query['secretaria'] = {'$regex': secretaria, '$options': 'i'}
    
    skip = (page - 1) * limit
    total = await db.processos.count_documents(query)
    
    processos = await db.processos.find(query, {
        '_id': 0,
        'user_id': 0
    }).skip(skip).limit(limit).to_list(limit)
    
    return {
        'success': True,
        'data': processos,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': total,
            'pages': (total + limit - 1) // limit
        }
    }

@public_router.get("/processos/{processo_id}")
async def public_get_processo(processo_id: str):
    """Detalhes públicos de um processo."""
    processo = await db.processos.find_one({'processo_id': processo_id}, {'_id': 0, 'user_id': 0})
    if not processo:
        raise HTTPException(status_code=404, detail="Processo não encontrado")
    return {'success': True, 'data': processo}

@public_router.get("/dashboard/stats")
async def public_dashboard_stats():
    """
    Estatísticas públicas consolidadas para o Dashboard de Transparência.
    """
    # Total de PACs
    total_pacs = await db.pacs.count_documents({})
    total_pacs_geral = await db.pacs_geral.count_documents({})
    total_processos = await db.processos.count_documents({})
    
    # Processos por status
    processos_por_status = await db.processos.aggregate([
        {'$group': {'_id': '$status', 'quantidade': {'$sum': 1}}}
    ]).to_list(100)
    
    # Total de itens e valores
    pac_items = await db.pac_items.find({}, {'_id': 0, 'valorTotal': 1}).to_list(10000)
    pac_geral_items = await db.pac_geral_items.find({}, {'_id': 0, 'valorTotal': 1}).to_list(10000)
    
    valor_total_pac = sum(item.get('valorTotal', 0) for item in pac_items)
    valor_total_pac_geral = sum(item.get('valorTotal', 0) for item in pac_geral_items)
    
    # Classificações orçamentárias mais utilizadas
    classificacoes = await db.pac_geral_items.aggregate([
        {'$group': {
            '_id': '$subitem_classificacao',
            'quantidade': {'$sum': 1},
            'valor_total': {'$sum': '$valorTotal'}
        }},
        {'$sort': {'valor_total': -1}},
        {'$limit': 10}
    ]).to_list(10)
    
    return {
        'success': True,
        'data': {
            'resumo': {
                'total_pacs_individuais': total_pacs,
                'total_pacs_gerais': total_pacs_geral,
                'total_processos': total_processos,
                'valor_total_pac': valor_total_pac,
                'valor_total_pac_geral': valor_total_pac_geral
            },
            'processos_por_status': [
                {'status': p['_id'] or 'Não informado', 'quantidade': p['quantidade']}
                for p in processos_por_status
            ],
            'classificacoes_principais': [
                {
                    'subitem': c['_id'] or 'Não classificado',
                    'quantidade': c['quantidade'],
                    'valor_total': c['valor_total']
                }
                for c in classificacoes
            ]
        },
        'meta': {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'system': 'Planejamento Acaiaca - Portal de Transparência'
        }
    }

@public_router.get("/classificacoes")
async def public_get_classificacoes():
    """Retorna os códigos de classificação orçamentária (público)."""
    codigos = {
        "339030": {
            "nome": "Material de Consumo",
            "subitens": [
                "Material de Consumo - Combustíveis e Lubrificantes Automotivos",
                "Gás Engarrafado",
                "Gêneros de Alimentação",
                "Material Farmacológico",
                "Material Odontológico",
                "Material Educativo e Esportivo",
                "Material de Expediente",
                "Material de Processamento de Dados",
                "Material de Limpeza e Higienização",
                "Uniformes, Tecidos e Aviamentos",
                "Material para Manutenção de Bens Imóveis",
                "Material Elétrico e Eletrônico",
                "Material Hospitalar"
            ]
        },
        "339036": {
            "nome": "Outros Serviços de Terceiros (Pessoa Física)",
            "subitens": [
                "Serviços Técnicos Profissionais",
                "Manutenção e Conservação de Equipamentos",
                "Manutenção e Conservação de Veículos",
                "Serviços de Limpeza e Conservação",
                "Serviços Médicos e Odontológicos"
            ]
        },
        "339039": {
            "nome": "Outros Serviços de Terceiros (Pessoa Jurídica)",
            "subitens": [
                "Serviços Técnicos Profissionais",
                "Manutenção de Software",
                "Manutenção e Conservação de Veículos",
                "Serviços de Energia Elétrica",
                "Serviços de Telecomunicações",
                "Vigilância Ostensiva",
                "Limpeza e Conservação"
            ]
        },
        "449052": {
            "nome": "Equipamentos e Material Permanente",
            "subitens": [
                "Aparelhos e Equipamentos de Comunicação",
                "Equipamentos Médico-Hospitalares",
                "Mobiliário em Geral",
                "Equipamentos de Processamento de Dados",
                "Máquinas e Utensílios de Escritório",
                "Veículos de Tração Mecânica"
            ]
        }
    }
    return {'success': True, 'data': codigos}


# ============ ENDPOINTS PÚBLICOS DE EXPORTAÇÃO ============
# Seguem as mesmas regras de geração do backend

@public_router.get("/pacs/{pac_id}/export/pdf")
async def public_export_pac_pdf(pac_id: str, orientation: str = "landscape"):
    """
    Exporta PAC Individual para PDF (público).
    Segue as mesmas regras de formatação do backend.
    """
    pac = await db.pacs.find_one({'pac_id': pac_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC não encontrado")
    items = await db.pac_items.find({'pac_id': pac_id}, {'_id': 0}).to_list(1000)
    
    buffer = BytesIO()
    
    # Margens padronizadas conforme Lei 14.133/2021
    # 5cm (esquerda/direita), 3cm (superior/inferior)
    page_size = A4 if orientation.lower() == 'portrait' else landscape(A4)
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=page_size,
        leftMargin=REPORT_MARGIN_LEFT, 
        rightMargin=REPORT_MARGIN_RIGHT, 
        topMargin=REPORT_MARGIN_TOP, 
        bottomMargin=REPORT_MARGIN_BOTTOM,
        title=f'PAC {pac.get("secretaria", "")} 2026'
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Cabeçalho
    elements.append(Paragraph('<b>PREFEITURA MUNICIPAL DE ACAIACA - MG</b>', ParagraphStyle('Center', fontSize=12, fontName='Helvetica-Bold', alignment=1)))
    elements.append(Paragraph('<b>PAC ACAIACA 2026 - PLANO ANUAL DE CONTRATAÇÕES</b>', ParagraphStyle('Center', fontSize=10, fontName='Helvetica-Bold', alignment=1)))
    elements.append(Paragraph('Lei Federal nº 14.133/2021', ParagraphStyle('Center', fontSize=8, alignment=1)))
    elements.append(Spacer(1, 4*mm))
    
    # Dados da secretaria
    header_data = [
        [f"<b>Secretaria:</b> {pac.get('secretaria', '')}", f"<b>Secretário(a):</b> {pac.get('secretario', '')}"],
        [f"<b>Fiscal do Contrato:</b> {pac.get('fiscal', '')}", f"<b>Telefone:</b> {pac.get('telefone', '')}"],
        [f"<b>E-mail:</b> {pac.get('email', '')}", f"<b>Endereço:</b> {pac.get('endereco', '')}"]
    ]
    
    for row in header_data:
        elements.append(Paragraph(f"{row[0]} | {row[1]}", ParagraphStyle('Normal', fontSize=8, spaceAfter=1)))
    
    elements.append(Spacer(1, 4*mm))
    
    # Tabela de itens
    elements.append(Paragraph('<b>DETALHAMENTO DOS ITENS</b>', ParagraphStyle('Header', fontSize=10, fontName='Helvetica-Bold', spaceAfter=3)))
    
    table_data = [['#', 'Código\nCATMAT', 'Descrição do Objeto', 'Unidade', 'Qtd', 'Valor\nUnitário', 'Valor\nTotal', 'Prioridade', 'Justificativa da Contratação', 'Classificação Orçamentária\n(Código - Subitem)']]
    
    for idx, item in enumerate(items, start=1):
        classificacao_text = ''
        if item.get('codigo_classificacao'):
            classificacao_text = f"{item['codigo_classificacao']}"
            if item.get('subitem_classificacao'):
                classificacao_text += f"\n{item['subitem_classificacao']}"
        
        descricao_completa = item.get('descricao', '')
        justificativa_completa = item.get('justificativa', '') or 'Não informada'
        
        table_data.append([
            str(idx),
            item.get('catmat', ''),
            Paragraph(f"<font size=7>{descricao_completa}</font>", styles['Normal']),
            item.get('unidade', ''),
            str(int(item.get('quantidade', 0))),
            f"R$ {item.get('valorUnitario', 0):,.2f}",
            f"R$ {item.get('valorTotal', 0):,.2f}",
            item.get('prioridade', ''),
            Paragraph(f"<font size=6>{justificativa_completa}</font>", styles['Normal']),
            Paragraph(f"<font size=6>{classificacao_text}</font>", styles['Normal'])
        ])
    
    total = sum(item.get('valorTotal', 0) for item in items)
    table_data.append(['', '', Paragraph('<b>TOTAL GERAL ESTIMADO:</b>', styles['Normal']), '', '', '', f"R$ {total:,.2f}", '', '', ''])
    
    if orientation.lower() == 'portrait':
        col_widths = [0.6*cm, 1.5*cm, 4*cm, 1*cm, 0.8*cm, 1.8*cm, 1.8*cm, 1.2*cm, 3*cm, 3*cm]
    else:
        col_widths = [0.6*cm, 1.5*cm, 5*cm, 1*cm, 1*cm, 1.8*cm, 2*cm, 1.3*cm, 5*cm, 5*cm]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('FONTSIZE', (0, 1), (-1, -2), 7),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (3, 1), (4, -1), 'CENTER'),
        ('ALIGN', (5, 1), (6, -1), 'RIGHT'),
        ('ALIGN', (7, 1), (7, -1), 'CENTER'),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F2F2F2')]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFC000')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 10*mm))
    
    # Assinaturas
    elements.append(Paragraph('<b>ASSINATURAS</b>', ParagraphStyle('Header', fontSize=9, fontName='Helvetica-Bold', spaceAfter=8)))
    sig_data = [
        ['_' * 50, '_' * 50],
        [pac.get('secretario', ''), pac.get('fiscal', '')],
        ['Secretário(a) Responsável', 'Fiscal do Contrato'],
        ['', ''],
        ['Data: ___/___/______', 'Data: ___/___/______']
    ]
    sig_table = Table(sig_data, colWidths=[10*cm, 10*cm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 2), (-1, 2), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 0),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 2),
        ('TOPPADDING', (0, 4), (-1, 4), 8),
    ]))
    elements.append(sig_table)
    
    doc.build(elements)
    buffer.seek(0)
    
    filename = f'PAC_{pac.get("secretaria", "").replace(" ", "_")}_2026.pdf'
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})


@public_router.get("/pacs-geral/{pac_geral_id}/export/pdf")
async def public_export_pac_geral_pdf(pac_geral_id: str, orientation: str = "landscape"):
    """Exporta PAC Geral para PDF (público)."""
    pac_geral = await db.pacs_geral.find_one({'pac_geral_id': pac_geral_id}, {'_id': 0})
    if not pac_geral:
        raise HTTPException(status_code=404, detail="PAC Geral não encontrado")
    items = await db.pac_geral_items.find({'pac_geral_id': pac_geral_id}, {'_id': 0}).to_list(1000)
    
    buffer = BytesIO()
    
    # Margens padronizadas conforme Lei 14.133/2021
    # 5cm (esquerda/direita), 3cm (superior/inferior)
    page_size = A4 if orientation.lower() == 'portrait' else landscape(A4)
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=page_size,
        leftMargin=REPORT_MARGIN_LEFT, 
        rightMargin=REPORT_MARGIN_RIGHT, 
        topMargin=REPORT_MARGIN_TOP, 
        bottomMargin=REPORT_MARGIN_BOTTOM
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Cabeçalho
    elements.append(Paragraph('<b>PREFEITURA MUNICIPAL DE ACAIACA - MG</b>', ParagraphStyle('Center', fontSize=12, fontName='Helvetica-Bold', alignment=1)))
    elements.append(Paragraph('<b>PAC ACAIACA 2026 - PLANO ANUAL DE CONTRATAÇÕES COMPARTILHADO</b>', ParagraphStyle('Center', fontSize=10, fontName='Helvetica-Bold', alignment=1)))
    elements.append(Paragraph('Lei Federal nº 14.133/2021', ParagraphStyle('Center', fontSize=8, alignment=1)))
    elements.append(Spacer(1, 4*mm))
    
    # Dados
    elements.append(Paragraph(f"<b>Secretaria Responsável:</b> {pac_geral.get('nome_secretaria', '')}", ParagraphStyle('Normal', fontSize=9)))
    elements.append(Paragraph(f"<b>Secretário(a):</b> {pac_geral.get('secretario', '')} | <b>Fiscal:</b> {pac_geral.get('fiscal_contrato', '')}", ParagraphStyle('Normal', fontSize=9)))
    
    secretarias = pac_geral.get('secretarias_selecionadas', [])
    if secretarias:
        elements.append(Paragraph(f"<b>Secretarias Participantes:</b> {', '.join(secretarias)}", ParagraphStyle('Normal', fontSize=8)))
    
    elements.append(Spacer(1, 4*mm))
    
    # Tabela de itens
    elements.append(Paragraph('<b>DETALHAMENTO DOS ITENS</b>', ParagraphStyle('Header', fontSize=9, fontName='Helvetica-Bold', spaceAfter=2)))
    
    table_data = [['#', 'Código\nCATMAT', 'Descrição do Objeto', 'Justificativa da Contratação', 'Und', 'Qtd\nTotal', 'Valor\nUnitário', 'Valor\nTotal', 'Prior.', 'Classificação Orçamentária\n(Código - Subitem)']]
    
    for idx, item in enumerate(items, start=1):
        classificacao_text = ''
        if item.get('codigo_classificacao'):
            classificacao_text = f"{item['codigo_classificacao']}"
            if item.get('subitem_classificacao'):
                classificacao_text += f"\n{item['subitem_classificacao']}"
        
        justificativa = item.get('justificativa', '') or 'Não informada'
        descricao = item.get('descricao', '')
        
        table_data.append([
            str(idx),
            item.get('catmat', ''),
            Paragraph(f"<font size=7>{descricao}</font>", styles['Normal']),
            Paragraph(f"<font size=6>{justificativa}</font>", styles['Normal']),
            item.get('unidade', ''),
            str(int(item.get('quantidade_total', 0))),
            f"R$ {item.get('valorUnitario', 0):,.2f}",
            f"R$ {item.get('valorTotal', 0):,.2f}",
            item.get('prioridade', ''),
            Paragraph(f"<font size=6>{classificacao_text}</font>", styles['Normal'])
        ])
    
    total = sum(item.get('valorTotal', 0) for item in items)
    total_qtd = sum(item.get('quantidade_total', 0) for item in items)
    table_data.append([
        '', '', Paragraph('<b>TOTAL GERAL:</b>', styles['Normal']), '', '',
        str(int(total_qtd)), '', f"R$ {total:,.2f}", '', ''
    ])
    
    if orientation.lower() == 'portrait':
        col_widths = [0.5*cm, 1.2*cm, 3.5*cm, 3*cm, 0.8*cm, 1*cm, 1.5*cm, 1.6*cm, 0.8*cm, 2.5*cm]
    else:
        col_widths = [0.6*cm, 1.5*cm, 5*cm, 5*cm, 1*cm, 1.2*cm, 2*cm, 2.2*cm, 1*cm, 4.5*cm]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('FONTSIZE', (0, 1), (-1, -2), 7),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F2F2F2')]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFC000')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 10*mm))
    
    # Assinaturas
    sig_data = [
        ['_' * 50, '_' * 50],
        [pac_geral.get('secretario', ''), pac_geral.get('fiscal_contrato', '')],
        ['Secretário(a) Responsável', 'Fiscal do Contrato'],
    ]
    sig_table = Table(sig_data, colWidths=[10*cm, 10*cm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
    ]))
    elements.append(sig_table)
    
    doc.build(elements)
    buffer.seek(0)
    
    filename = f'PAC_Geral_{pac_geral.get("nome_secretaria", "").replace(" ", "_")}.pdf'
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})


# ===== ROTAS PÚBLICAS PAC GERAL OBRAS =====
@public_router.get("/pacs-geral-obras")
async def public_get_pacs_geral_obras(ano: str = None, page: int = 1, limit: int = 50):
    """Lista todos os PAC Geral Obras (público - transparência)"""
    query = {}
    if ano:
        query['ano'] = ano
    pacs = await db.pacs_geral_obras.find(query, {'_id': 0}).to_list(limit)
    return {'data': pacs, 'total': len(pacs)}

@public_router.get("/pacs-geral-obras/{pac_obras_id}")
async def public_get_pac_geral_obras(pac_obras_id: str):
    """Obtém detalhes de um PAC Geral Obras (público)"""
    pac = await db.pacs_geral_obras.find_one({'pac_obras_id': pac_obras_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC Geral Obras not found")
    return {'data': pac}

@public_router.get("/pacs-geral-obras/{pac_obras_id}/items")
async def public_get_pac_geral_obras_items(pac_obras_id: str):
    """Lista itens de um PAC Geral Obras (público)"""
    items = await db.pac_geral_obras_items.find({'pac_obras_id': pac_obras_id}, {'_id': 0}).to_list(1000)
    return {'data': items}

@public_router.get("/pacs-geral-obras/{pac_obras_id}/export/pdf")
async def public_export_pac_geral_obras_pdf(pac_obras_id: str, orientation: str = "landscape"):
    """Exporta PAC Geral Obras para PDF (público)"""
    pac = await db.pacs_geral_obras.find_one({'pac_obras_id': pac_obras_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC Geral Obras not found")
    
    items = await db.pac_geral_obras_items.find({'pac_obras_id': pac_obras_id}, {'_id': 0}).to_list(1000)
    
    buffer = BytesIO()
    page_size = A4 if orientation.lower() == 'portrait' else landscape(A4)
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=page_size,
        leftMargin=REPORT_MARGIN_LEFT, 
        rightMargin=REPORT_MARGIN_RIGHT, 
        topMargin=REPORT_MARGIN_TOP, 
        bottomMargin=REPORT_MARGIN_BOTTOM
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Cabeçalho
    elements.append(Paragraph('<b>PREFEITURA MUNICIPAL DE ACAIACA - MG</b>', ParagraphStyle('Center', fontSize=12, fontName='Helvetica-Bold', alignment=1)))
    elements.append(Paragraph('<b>PAC GERAL OBRAS E SERVIÇOS</b>', ParagraphStyle('Center', fontSize=10, fontName='Helvetica-Bold', alignment=1)))
    elements.append(Paragraph('Lei Federal nº 14.133/2021', ParagraphStyle('Center', fontSize=8, alignment=1)))
    elements.append(Paragraph(f'Secretaria: {pac.get("nome_secretaria", "")}', ParagraphStyle('Center', fontSize=9, fontName='Helvetica-Bold', alignment=1)))
    elements.append(Paragraph(f'Data de Geração: {datetime.now().strftime("%d/%m/%Y às %H:%M")}', ParagraphStyle('Center', fontSize=8, alignment=1)))
    elements.append(Spacer(1, 4*mm))
    
    # Dados do PAC
    info_style = ParagraphStyle('Info', fontSize=8)
    elements.append(Paragraph(f'<b>Responsável:</b> {pac.get("secretario", "")}', info_style))
    elements.append(Paragraph(f'<b>Fiscal:</b> {pac.get("fiscal_contrato", "-")}', info_style))
    elements.append(Paragraph(f'<b>Email:</b> {pac.get("email", "")}', info_style))
    elements.append(Paragraph(f'<b>Ano:</b> {pac.get("ano", "2026")}', info_style))
    elements.append(Spacer(1, 4*mm))
    
    # Tabela de itens
    if items:
        valor_total = sum(item.get('valorTotal', 0) for item in items)
        elements.append(Paragraph(f'<b>Total de Itens: {len(items)} | Valor Total: R$ {valor_total:,.2f}</b>', ParagraphStyle('Info', fontSize=9, fontName='Helvetica-Bold')))
        elements.append(Spacer(1, 2*mm))
        
        table_data = [['#', 'Descrição', 'Classificação', 'Unidade', 'Qtd', 'Valor Unit.', 'Valor Total']]
        for idx, item in enumerate(items, start=1):
            table_data.append([
                str(idx),
                Paragraph(f"<font size=6>{item.get('descricao', '')}</font>", styles['Normal']),
                Paragraph(f"<font size=6>{item.get('codigo_classificacao', '')} - {item.get('subitem_classificacao', '')}</font>", styles['Normal']),
                item.get('unidade', ''),
                str(item.get('quantidade_total', 0)),
                f"R$ {item.get('valorUnitario', 0):,.2f}",
                f"R$ {item.get('valorTotal', 0):,.2f}"
            ])
        
        col_widths = [0.5*cm, 6*cm, 5*cm, 1.5*cm, 1*cm, 2*cm, 2.5*cm] if orientation.lower() == 'landscape' else [0.5*cm, 4*cm, 3.5*cm, 1*cm, 0.8*cm, 1.5*cm, 2*cm]
        
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (-2, 1), (-1, -1), 'RIGHT'),
        ]))
        
        elements.append(table)
    else:
        elements.append(Paragraph('Nenhum item cadastrado.', ParagraphStyle('Center', fontSize=10, alignment=1)))
    
    doc.build(elements)
    buffer.seek(0)
    
    filename = f'PAC_Obras_{pac.get("nome_secretaria", "").replace(" ", "_")}.pdf'
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})

@public_router.get("/processos/export/pdf")
async def public_export_processos_pdf(orientation: str = "landscape"):
    """Exporta todos os processos para PDF (público)."""
    processos = await db.processos.find({}, {'_id': 0}).to_list(1000)
    
    buffer = BytesIO()
    
    # Margens padronizadas conforme Lei 14.133/2021
    # 5cm (esquerda/direita), 3cm (superior/inferior)
    page_size = A4 if orientation.lower() == 'portrait' else landscape(A4)
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=page_size,
        leftMargin=REPORT_MARGIN_LEFT, 
        rightMargin=REPORT_MARGIN_RIGHT, 
        topMargin=REPORT_MARGIN_TOP, 
        bottomMargin=REPORT_MARGIN_BOTTOM
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Cabeçalho
    elements.append(Paragraph('<b>PREFEITURA MUNICIPAL DE ACAIACA - MG</b>', ParagraphStyle('Center', fontSize=12, fontName='Helvetica-Bold', alignment=1)))
    elements.append(Paragraph('<b>GESTÃO PROCESSUAL - RELATÓRIO DE PROCESSOS</b>', ParagraphStyle('Center', fontSize=10, fontName='Helvetica-Bold', alignment=1)))
    elements.append(Paragraph('Lei Federal nº 14.133/2021', ParagraphStyle('Center', fontSize=8, alignment=1)))
    elements.append(Paragraph(f'Data de Geração: {datetime.now().strftime("%d/%m/%Y às %H:%M")}', ParagraphStyle('Center', fontSize=8, alignment=1)))
    elements.append(Paragraph(f'Total de Processos: {len(processos)}', ParagraphStyle('Center', fontSize=8, fontName='Helvetica-Bold', alignment=1)))
    elements.append(Spacer(1, 4*mm))
    
    # Tabela de processos
    if orientation.lower() == 'portrait':
        table_data = [['#', 'Processo', 'Status', 'Modalidade', 'Objeto', 'Secretaria']]
        for idx, p in enumerate(processos, start=1):
            table_data.append([
                str(idx),
                p.get('numero_processo', ''),
                p.get('status', ''),
                Paragraph(f"<font size=6>{p.get('modalidade', '')}</font>", styles['Normal']),
                Paragraph(f"<font size=6>{p.get('objeto', '')}</font>", styles['Normal']),
                Paragraph(f"<font size=6>{p.get('secretaria', '')}</font>", styles['Normal'])
            ])
        col_widths = [0.5*cm, 2*cm, 1.8*cm, 3*cm, 5.5*cm, 3.5*cm]
    else:
        table_data = [['#', 'Processo', 'Status', 'Modalidade', 'Objeto', 'Responsável', 'Secretaria', 'Observações']]
        for idx, p in enumerate(processos, start=1):
            table_data.append([
                str(idx),
                p.get('numero_processo', ''),
                p.get('status', ''),
                Paragraph(f"<font size=6>{p.get('modalidade', '')}</font>", styles['Normal']),
                Paragraph(f"<font size=6>{p.get('objeto', '')}</font>", styles['Normal']),
                p.get('responsavel', ''),
                Paragraph(f"<font size=6>{p.get('secretaria', '')}</font>", styles['Normal']),
                Paragraph(f"<font size=5>{p.get('observacoes', '')}</font>", styles['Normal'])
            ])
        col_widths = [0.5*cm, 2.2*cm, 1.6*cm, 2.5*cm, 6.5*cm, 2*cm, 4*cm, 4*cm]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    
    filename = f'Processos_PAC_Acaiaca_{datetime.now().strftime("%Y%m%d")}.pdf'
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})


# ===== ROTAS PÚBLICAS MROSC =====
@public_router.get("/mrosc/projetos")
async def public_get_projetos_mrosc():
    """Lista projetos MROSC (público - transparência)"""
    # Mostrar todos os projetos para transparência
    projetos = await db.mrosc_projetos.find({}, {'_id': 0}).to_list(100)
    return {'data': projetos, 'total': len(projetos)}

@public_router.get("/mrosc/projetos/{projeto_id}")
async def public_get_projeto_mrosc(projeto_id: str):
    """Obtém detalhes de um projeto MROSC (público)"""
    projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return {'data': projeto}

@public_router.get("/mrosc/projetos/{projeto_id}/resumo")
async def public_get_resumo_mrosc(projeto_id: str):
    """Resumo financeiro de um projeto MROSC (público)"""
    projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Buscar RH e despesas
    rhs = await db.mrosc_rh.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(100)
    despesas = await db.mrosc_despesas.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(500)
    
    # Calcular totais
    total_rh = sum(rh.get('custo_total_projeto', 0) for rh in rhs)
    total_despesas = sum(d.get('valor_total', 0) for d in despesas)
    valor_total_projeto = projeto.get('valor_total', 0)
    repasse_publico = projeto.get('valor_repasse_publico', 0)
    contrapartida = projeto.get('valor_contrapartida', 0)
    
    return {
        'data': {
            'projeto': projeto,
            'total_rh': total_rh,
            'total_despesas': total_despesas,
            'total_executado': total_rh + total_despesas,
            'valor_total_projeto': valor_total_projeto,
            'repasse_publico': repasse_publico,
            'contrapartida': contrapartida,
            'saldo': valor_total_projeto - (total_rh + total_despesas),
            'quantidade_rh': len(rhs),
            'quantidade_despesas': len(despesas)
        }
    }

@public_router.get("/mrosc/estatisticas")
async def public_get_estatisticas_mrosc():
    """Estatísticas gerais do MROSC (público)"""
    projetos = await db.mrosc_projetos.find({}, {'_id': 0}).to_list(100)
    
    total_projetos = len(projetos)
    total_aprovados = len([p for p in projetos if p.get('status') == 'APROVADO'])
    total_em_analise = len([p for p in projetos if p.get('status') == 'ANALISE'])
    valor_total = sum(p.get('valor_total', 0) for p in projetos)
    valor_repasse = sum(p.get('valor_repasse_publico', 0) for p in projetos)
    
    return {
        'data': {
            'total_projetos': total_projetos,
            'total_aprovados': total_aprovados,
            'total_em_analise': total_em_analise,
            'valor_total': valor_total,
            'valor_repasse_publico': valor_repasse
        }
    }

# ============ MÓDULO DOEM - Diário Oficial Eletrônico Municipal ============

doem_router = APIRouter(prefix="/api/doem", tags=["DOEM"])

# ===== Funções de Email =====

def enviar_email_smtp(destinatario: str, assunto: str, corpo_html: str, anexo_pdf: bytes = None, nome_anexo: str = None):
    """Envia email via SMTP da prefeitura"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = assunto
        msg['From'] = f"DOEM Acaiaca <{SMTP_EMAIL}>"
        msg['To'] = destinatario
        
        # Corpo do email em HTML
        html_part = MIMEText(corpo_html, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Anexar PDF se fornecido
        if anexo_pdf and nome_anexo:
            pdf_part = MIMEBase('application', 'pdf')
            pdf_part.set_payload(anexo_pdf)
            encoders.encode_base64(pdf_part)
            pdf_part.add_header('Content-Disposition', f'attachment; filename="{nome_anexo}"')
            msg.attach(pdf_part)
        
        # Conectar e enviar
        if SMTP_USE_SSL:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
                server.login(SMTP_EMAIL, SMTP_PASSWORD)
                server.sendmail(SMTP_EMAIL, destinatario, msg.as_string())
        else:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_EMAIL, SMTP_PASSWORD)
                server.sendmail(SMTP_EMAIL, destinatario, msg.as_string())
        
        logging.info(f"Email enviado com sucesso para {destinatario}")
        return True
    except Exception as e:
        logging.error(f"Erro ao enviar email para {destinatario}: {e}")
        return False

async def enviar_notificacao_doem(edicao: dict, pdf_buffer: BytesIO):
    """Envia notificação de nova edição do DOEM para todos os inscritos"""
    config = await get_doem_config()
    
    # Buscar segmentos da edição
    segmentos_edicao = set()
    for pub in edicao.get('publicacoes', []):
        segmentos_edicao.add(pub.get('segmento', 'Decretos'))
    
    # Buscar todos os destinatários
    destinatarios = []
    
    # 1. Inscritos na newsletter (confirmados e ativos)
    inscritos = await db.doem_newsletter.find({
        'ativo': True,
        'confirmado': True
    }, {'_id': 0}).to_list(1000)
    
    for inscrito in inscritos:
        # Verificar se tem interesse nos segmentos da edição
        interesses = inscrito.get('segmentos_interesse', [])
        if not interesses or any(s in segmentos_edicao for s in interesses):
            destinatarios.append(inscrito['email'])
    
    # 2. Usuários do sistema (se configurado)
    usuarios = await db.users.find({'is_active': True}, {'_id': 0, 'email': 1}).to_list(500)

async def enviar_notificacao_assinantes(edicao: dict, assinantes: list, validation_code: str):
    """Envia notificação por email para cada assinante de um documento publicado"""
    try:
        numero_edicao = edicao.get('numero_edicao', '')
        ano = edicao.get('ano', datetime.now().year)
        data_publicacao = edicao.get('data_publicacao', datetime.now().strftime('%d/%m/%Y'))
        
        enviados = 0
        for assinante in assinantes:
            email = assinante.get('email')
            nome = assinante.get('nome', 'Assinante')
            
            if not email:
                continue
            
            assunto = f"[DOEM Acaiaca] Confirmação de Assinatura - Edição nº {numero_edicao}/{ano}"
            
            corpo_html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #003366, #006699); color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 25px; border: 1px solid #ddd; border-top: none; }}
                    .validation-box {{ background: white; border: 2px solid #003366; border-radius: 8px; padding: 15px; margin: 20px 0; text-align: center; }}
                    .validation-code {{ font-family: monospace; font-size: 18px; font-weight: bold; color: #003366; letter-spacing: 2px; }}
                    .button {{ display: inline-block; background: #003366; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; margin-top: 15px; }}
                    .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                    .success-icon {{ font-size: 48px; color: #28a745; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>✅ Assinatura Confirmada</h1>
                        <p>DOEM - Diário Oficial Eletrônico Municipal de Acaiaca</p>
                    </div>
                    
                    <div class="content">
                        <p>Prezado(a) <strong>{nome}</strong>,</p>
                        
                        <p>Sua assinatura digital foi registrada com sucesso no seguinte documento:</p>
                        
                        <div class="validation-box">
                            <p><strong>DOEM - Edição nº {numero_edicao}/{ano}</strong></p>
                            <p>Data de Publicação: {data_publicacao}</p>
                            <hr style="border: none; border-top: 1px solid #ddd; margin: 15px 0;">
                            <p style="margin: 5px 0; font-size: 12px; color: #666;">Código de Validação:</p>
                            <p class="validation-code">{validation_code}</p>
                        </div>
                        
                        <p>Para verificar a autenticidade do documento a qualquer momento, acesse:</p>
                        
                        <p style="text-align: center;">
                            <a href="https://pac.acaiaca.mg.gov.br/validar?code={validation_code}" class="button">
                                Validar Documento
                            </a>
                        </p>
                        
                        <p style="margin-top: 20px; padding: 15px; background: #e8f4f8; border-radius: 5px; font-size: 13px;">
                            <strong>📋 Informações da Assinatura:</strong><br>
                            • Assinante: {nome}<br>
                            • Cargo: {assinante.get('cargo', 'Não informado')}<br>
                            • Data/Hora: {datetime.now().strftime('%d/%m/%Y às %H:%M')}<br>
                            • CPF: {mask_cpf(assinante.get('cpf', ''))}
                        </p>
                        
                        <p style="font-size: 12px; color: #666; margin-top: 20px;">
                            Este é um email automático. Por favor, não responda a esta mensagem.
                        </p>
                    </div>
                    
                    <div class="footer">
                        <p>Prefeitura Municipal de Acaiaca - MG</p>
                        <p>Sistema de Gestão Municipal - DOEM</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            if enviar_email_smtp(email, assunto, corpo_html):
                enviados += 1
        
        logging.info(f"Notificações de assinatura enviadas: {enviados}/{len(assinantes)}")
        return enviados
    except Exception as e:
        logging.error(f"Erro ao enviar notificações de assinatura: {e}")
        return 0
    for user in usuarios:
        if user['email'] not in destinatarios:
            destinatarios.append(user['email'])
    
    if not destinatarios:
        logging.info("Nenhum destinatário para notificação do DOEM")
        return 0
    
    # Formatar data
    data_pub = edicao.get('data_publicacao')
    if isinstance(data_pub, datetime):
        data_formatada = data_pub.strftime('%d/%m/%Y')
    else:
        data_formatada = str(data_pub)[:10] if data_pub else ''
    
    # Listar publicações por segmento
    pubs_por_segmento = {}
    for pub in edicao.get('publicacoes', []):
        seg = pub.get('segmento', 'Outros')
        if seg not in pubs_por_segmento:
            pubs_por_segmento[seg] = []
        pubs_por_segmento[seg].append(pub['titulo'])
    
    lista_pubs = ""
    for seg, titulos in pubs_por_segmento.items():
        lista_pubs += f"<h4 style='color:#1F4E78;margin:10px 0 5px 0;'>{seg}</h4><ul>"
        for t in titulos:
            lista_pubs += f"<li>{t}</li>"
        lista_pubs += "</ul>"
    
    # Montar email HTML
    assunto = f"DOEM Acaiaca - Edição nº {edicao['numero_edicao']} publicada"
    corpo_html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #1F4E78, #2E7D32); padding: 20px; text-align: center; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0;">📰 DOEM Acaiaca</h1>
            <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0;">Diário Oficial Eletrônico Municipal</p>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border: 1px solid #dee2e6;">
            <h2 style="color: #1F4E78; margin-top: 0;">Nova Edição Publicada!</h2>
            
            <div style="background: white; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <p><strong>Edição:</strong> nº {edicao['numero_edicao']}/{edicao['ano']}</p>
                <p><strong>Data de Publicação:</strong> {data_formatada}</p>
                <p><strong>Total de Publicações:</strong> {len(edicao.get('publicacoes', []))}</p>
            </div>
            
            <h3 style="color: #333;">Conteúdo desta edição:</h3>
            {lista_pubs}
            
            <div style="text-align: center; margin: 20px 0;">
                <a href="https://pac.acaiaca.mg.gov.br/doem-publico" 
                   style="background: #1F4E78; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    📥 Acessar o DOEM
                </a>
            </div>
        </div>
        
        <div style="background: #1F4E78; color: white; padding: 15px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px;">
            <p style="margin: 0;">Prefeitura Municipal de Acaiaca - MG</p>
            <p style="margin: 5px 0 0 0; opacity: 0.8;">Este é um email automático. Não responda.</p>
            <p style="margin: 5px 0 0 0; opacity: 0.7;">
                <a href="https://pac.acaiaca.mg.gov.br/newsletter/cancelar" style="color: #90caf9;">Cancelar inscrição</a>
            </p>
        </div>
    </body>
    </html>
    """
    
    # Enviar para todos os destinatários
    enviados = 0
    pdf_bytes = pdf_buffer.getvalue() if pdf_buffer else None
    nome_pdf = f"DOEM_Acaiaca_Edicao_{edicao['numero_edicao']}_{edicao['ano']}.pdf"
    
    for email in destinatarios:
        try:
            if enviar_email_smtp(email, assunto, corpo_html, pdf_bytes, nome_pdf):
                enviados += 1
        except Exception as e:
            logging.error(f"Falha ao enviar para {email}: {e}")
    
    logging.info(f"Notificações enviadas: {enviados}/{len(destinatarios)}")
    return enviados

# ===== Funções Auxiliares DOEM =====

def parse_rtf_publicacao(rtf_content: bytes) -> list:
    """
    Extrai publicações de arquivo RTF.
    Formato esperado: === TÍTULO === seguido do texto
    Retorna lista de dicionários com título e texto.
    """
    try:
        # Tentar diferentes encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                text = rtf_to_text(rtf_content.decode(encoding))
                break
            except:
                continue
        else:
            text = rtf_to_text(rtf_content.decode('latin-1', errors='ignore'))
        
        # Regex para extrair publicações separadas por ===
        pattern = r'===\s*(.+?)\s*===\s*(.*?)(?====|$)'
        matches = re.findall(pattern, text, re.DOTALL)
        
        publicacoes = []
        for titulo, texto in matches:
            publicacoes.append({
                'titulo': titulo.strip(),
                'texto': texto.strip()
            })
        
        # Se não encontrou o padrão, usar o texto inteiro como uma publicação
        if not publicacoes and text.strip():
            # Tentar identificar título na primeira linha
            lines = text.strip().split('\n')
            titulo = lines[0].strip() if lines else "Publicação sem título"
            texto = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""
            publicacoes.append({
                'titulo': titulo,
                'texto': texto
            })
        
        return publicacoes
    except Exception as e:
        logging.error(f"Erro ao parsear RTF: {e}")
        return []

def gerar_assinatura_simulada(pdf_bytes: bytes, user_info: dict = None) -> DOEMAssinatura:
    """Gera uma assinatura digital simulada para o documento com código de validação"""
    hash_doc = hashlib.sha256(pdf_bytes).hexdigest()
    validation_code = generate_validation_code()
    
    # Informações do assinante
    titular = user_info.get('nome', 'Prefeitura Municipal de Acaiaca') if user_info else 'Prefeitura Municipal de Acaiaca'
    
    return DOEMAssinatura(
        assinado=True,
        data_assinatura=datetime.now(timezone.utc),
        hash_documento=hash_doc,
        tipo_certificado="ICP-Brasil (Simulado)",
        titular=titular,
        validation_code=validation_code,
        cpf=user_info.get('cpf', '') if user_info else '',
        cargo=user_info.get('cargo', '') if user_info else '',
        email=user_info.get('email', '') if user_info else ''
    )

def create_signature_page_mrosc(signers: list, validation_code: str, doc_info: dict = None) -> BytesIO:
    """
    Cria uma página de assinaturas no estilo do documento de referência (Lei 14.063).
    Formato: blocos de assinatura individuais com QR Code, código de autenticidade,
    nome, cargo, data/hora e fundamento legal.
    
    Args:
        signers: Lista de dicts com {nome, cpf, cargo, email, data_hora}
        validation_code: Código de validação do documento
        doc_info: Dict com informações do documento {tipo, id, titulo}
    
    Returns:
        BytesIO com a página PDF de assinaturas
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.utils import ImageReader
    import qrcode
    
    buffer = BytesIO()
    c = pdf_canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4
    
    # Cores
    azul_escuro = colors.HexColor("#1a365d")
    azul_medio = colors.HexColor("#2563eb")
    verde = colors.HexColor("#059669")
    cinza = colors.HexColor("#6b7280")
    cinza_claro = colors.HexColor("#e5e7eb")
    
    # Cabeçalho
    c.setFillColor(azul_escuro)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(page_width/2, page_height - 40, "ASSINATURAS ELETRÔNICAS")
    
    c.setFillColor(cinza)
    c.setFont("Helvetica", 9)
    c.drawCentredString(page_width/2, page_height - 55, "Com fundamento na Lei Nº 14.063, de 23 de Setembro de 2020")
    
    # Linha separadora
    c.setStrokeColor(cinza_claro)
    c.setLineWidth(1)
    c.line(50, page_height - 65, page_width - 50, page_height - 65)
    
    # Blocos de assinatura
    current_y = page_height - 100
    block_width = 230
    block_height = 130
    margin = 30
    blocks_per_row = 2
    start_x = (page_width - (blocks_per_row * block_width + (blocks_per_row - 1) * margin)) / 2
    
    for i, signer in enumerate(signers):
        col = i % blocks_per_row
        row = i // blocks_per_row
        
        x = start_x + col * (block_width + margin)
        y = current_y - row * (block_height + 20)
        
        if y < 150:  # Nova página se necessário
            c.showPage()
            c.setFont("Helvetica-Bold", 12)
            c.setFillColor(azul_escuro)
            c.drawCentredString(page_width/2, page_height - 40, "ASSINATURAS ELETRÔNICAS (continuação)")
            current_y = page_height - 80
            y = current_y - row * (block_height + 20)
        
        # Borda do bloco
        c.setStrokeColor(cinza_claro)
        c.setLineWidth(0.5)
        c.roundRect(x, y - block_height + 20, block_width, block_height, 5, stroke=1, fill=0)
        
        # Selo circular
        seal_x = x + 15
        seal_y = y - 25
        c.setStrokeColor(azul_medio)
        c.setLineWidth(1.5)
        c.circle(seal_x, seal_y, 18, stroke=1, fill=0)
        c.circle(seal_x, seal_y, 14, stroke=1, fill=0)
        
        c.setFillColor(azul_medio)
        c.setFont("Helvetica-Bold", 4)
        c.drawCentredString(seal_x, seal_y + 5, "Lei Federal")
        c.drawCentredString(seal_x, seal_y + 1, "14.063")
        c.setFont("Helvetica", 3.5)
        c.drawCentredString(seal_x, seal_y - 4, "ASSINATURA")
        c.drawCentredString(seal_x, seal_y - 7.5, "ELETRÔNICA")
        
        # QR Code
        try:
            qr_url = f"https://pac.acaiaca.mg.gov.br/validar?code={validation_code}"
            qr = qrcode.QRCode(version=1, box_size=2, border=1)
            qr.add_data(qr_url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="#1a365d", back_color="#ffffff")
            
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            
            qr_size = 35
            c.drawImage(ImageReader(qr_buffer), x + block_width - qr_size - 15, y - qr_size - 5, 
                       width=qr_size, height=qr_size)
        except Exception as e:
            logging.error(f"Erro ao gerar QR Code: {e}")
        
        # Nome do assinante
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 9)
        nome = signer.get('nome', 'N/A')
        if len(nome) > 30:
            nome = nome[:27] + "..."
        c.drawString(x + 45, y - 15, nome.upper())
        
        # Cargo
        c.setFillColor(cinza)
        c.setFont("Helvetica", 7)
        cargo = signer.get('cargo', '')
        if len(cargo) > 35:
            cargo = cargo[:32] + "..."
        c.drawString(x + 45, y - 28, cargo)
        
        # Data/hora da assinatura
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 7)
        data_hora = signer.get('data_hora', datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S'))
        c.drawString(x + 10, y - 55, f"em {data_hora}")
        
        # Código de autenticidade
        c.setFillColor(verde)
        c.setFont("Helvetica", 6)
        signer_code = f"{validation_code[:4]}.{uuid.uuid4().hex[:4].upper()}.{uuid.uuid4().hex[:4].upper()}"
        c.drawString(x + 10, y - 70, f"Cód. Autenticidade da Assinatura: {signer_code}")
        
        # Fundamento legal
        c.setFillColor(cinza)
        c.setFont("Helvetica-Oblique", 6)
        c.drawString(x + 10, y - 85, "Com fundamento na Lei Nº 14.063,")
        c.drawString(x + 10, y - 93, "de 23 de Setembro de 2020.")
    
    # Informações do documento no rodapé
    c.setStrokeColor(cinza_claro)
    c.line(50, 120, page_width - 50, 120)
    
    c.setFillColor(azul_escuro)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 100, "Informações do Documento")
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8)
    
    doc_tipo = doc_info.get('tipo', 'PRESTAÇÃO DE CONTAS') if doc_info else 'PRESTAÇÃO DE CONTAS'
    doc_id = doc_info.get('id', validation_code) if doc_info else validation_code
    doc_titulo = doc_info.get('titulo', 'Relatório de Prestação de Contas MROSC') if doc_info else 'Relatório de Prestação de Contas MROSC'
    
    c.drawString(50, 85, f"ID do Documento: {doc_id}")
    c.drawString(50, 73, f"Tipo: {doc_tipo}")
    c.drawString(50, 61, f"Título: {doc_titulo[:60]}{'...' if len(doc_titulo) > 60 else ''}")
    c.drawString(50, 49, f"Data de Elaboração: {datetime.now(timezone.utc).strftime('%d/%m/%Y às %H:%M:%S')}")
    
    # Código de autenticidade do documento
    c.setFillColor(verde)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(50, 33, f"Código de Autenticidade deste Documento: {validation_code}")
    
    c.setFillColor(azul_medio)
    c.setFont("Helvetica", 7)
    c.drawString(50, 20, "Verifique a autenticidade em: https://pac.acaiaca.mg.gov.br/validar")
    
    c.save()
    buffer.seek(0)
    return buffer

# ===== Sistema de Assinatura Digital Avançada =====

def mask_cpf(cpf: str) -> str:
    """Mascara o CPF para exibição pública (LGPD compliance)"""
    if not cpf:
        return "***.***.***-**"
    # Remove formatação existente
    cpf_digits = re.sub(r'\D', '', cpf)
    if len(cpf_digits) != 11:
        return "***.***.***-**"
    # Mascara: XXX.XXX.XXX-XX -> ***.XXX.XXX-**
    return f"***.{cpf_digits[3:6]}.{cpf_digits[6:9]}-**"

def generate_validation_code() -> str:
    """Gera código único para validação de documento"""
    return f"DOC-{uuid.uuid4().hex[:8].upper()}-{datetime.now().strftime('%Y%m%d')}"

async def save_document_signature(doc_id: str, doc_type: str, signers: list, hash_doc: str, validation_code: str = None) -> dict:
    """Salva a assinatura do documento no banco de dados para validação posterior"""
    if not validation_code:
        validation_code = generate_validation_code()
    signature_record = {
        'signature_id': str(uuid.uuid4()),
        'document_id': doc_id,
        'document_type': doc_type,
        'validation_code': validation_code,
        'hash_document': hash_doc,
        'signers': signers,
        'created_at': datetime.now(timezone.utc),
        'is_valid': True
    }
    await db.document_signatures.insert_one(signature_record)
    return {'validation_code': validation_code, 'signature_id': signature_record['signature_id']}

def draw_signature_seal(canvas, page_width, page_height, signers: list, validation_code: str, qr_code_url: str = None, signature_date: str = None):
    """
    Desenha o selo de assinatura digital na LATERAL DIREITA da página.
    Texto VERTICAL em VERMELHO, do cabeçalho ao rodapé, no limite da margem direita.
    
    Args:
        canvas: Canvas do reportlab
        page_width: Largura da página
        page_height: Altura da página
        signers: Lista de dicts com dados dos assinantes (nome, cpf, cargo)
        validation_code: Código para validação do documento
        qr_code_url: URL para o QR Code de validação (opcional)
        signature_date: Data da assinatura (formato DD/MM/YYYY HH:MM:SS)
    """
    from reportlab.lib.utils import ImageReader
    import qrcode
    
    # Cor VERMELHA para o texto
    cor_vermelho = colors.HexColor("#DC2626")  # Vermelho
    
    # Usar a data da assinatura fornecida ou a atual
    if signature_date:
        data_assinatura = signature_date
    else:
        data_assinatura = datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S')
    
    # Preparar dados do assinante
    if signers:
        nome = signers[0].get('nome', 'N/A').upper()
        cpf = signers[0].get('cpf', '')
        cargo = signers[0].get('cargo', '')
        cpf_masked = mask_cpf(cpf)
    else:
        nome = 'N/A'
        cpf_masked = '***.***.***-**'
        cargo = ''
    
    # Posição X - no limite da margem direita
    text_x = page_width - 6 * mm  # 6mm da borda direita
    
    # QR Code pequeno no topo da lateral direita
    qr_size = 12 * mm
    qr_x = page_width - qr_size - 3 * mm
    qr_y = page_height - qr_size - 10 * mm
    
    if qr_code_url:
        try:
            qr = qrcode.QRCode(version=1, box_size=2, border=1)
            qr.add_data(qr_code_url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="#DC2626", back_color="#ffffff")
            
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            
            canvas.drawImage(ImageReader(qr_buffer), qr_x, qr_y, width=qr_size, height=qr_size)
        except Exception as e:
            logging.error(f"Erro ao gerar QR Code: {e}")
    
    # Montar texto da assinatura em uma linha
    texto_assinatura = f"ASSINADO DIGITALMENTE por {nome}"
    if cargo:
        texto_assinatura += f" - {cargo}"
    texto_assinatura += f" | CPF: {cpf_masked} | Data: {data_assinatura} | Código: {validation_code} | Verifique em: pac.acaiaca.mg.gov.br/validar"
    
    # Salvar estado do canvas
    canvas.saveState()
    
    # Rotacionar 90 graus (texto vertical, de cima para baixo)
    # Posicionar abaixo do QR Code
    start_y = qr_y - 5 * mm
    
    # Mover para posição e rotacionar
    canvas.translate(text_x, start_y)
    canvas.rotate(-90)  # Rotação para texto vertical (cabeçalho -> rodapé)
    
    # IMPORTANTE: Definir cor e fonte APÓS as transformações
    # para garantir que sejam aplicadas corretamente ao texto
    canvas.setFillColor(cor_vermelho)
    canvas.setFont("Helvetica-Bold", 5.5)
    
    # Desenhar texto (agora na horizontal após rotação)
    canvas.drawString(0, 0, texto_assinatura)
    
    # Restaurar estado do canvas
    canvas.restoreState()

async def get_doem_config() -> dict:
    """Obtém ou cria configuração padrão do DOEM"""
    config = await db.doem_config.find_one({'config_id': 'doem_config_main'}, {'_id': 0})
    if not config:
        config = {
            'config_id': 'doem_config_main',
            'nome_municipio': 'Acaiaca',
            'uf': 'MG',
            'cnpj': '18.296.673/0001-10',
            'endereco': 'Praça Antônio Carlos, 10 - Centro',
            'telefone': '(31) 3554-1222',
            'email': 'gabinete@acaiaca.mg.gov.br',
            'created_at': datetime.now(timezone.utc)
        }
        await db.doem_config.insert_one(config)
    return config

async def add_signature_to_pdf(pdf_buffer: BytesIO, user: User, doc_type: str, doc_id: str, doc_info: dict = None, signature_date: str = None) -> tuple:
    """
    Adiciona assinatura digital a qualquer PDF gerado pelo sistema.
    Para documentos MROSC, adiciona uma página de assinaturas no estilo da Lei 14.063.
    Retorna o buffer modificado e o código de validação.
    
    Args:
        pdf_buffer: Buffer do PDF original
        user: Usuário que está assinando
        doc_type: Tipo do documento
        doc_id: ID do documento
        doc_info: Informações adicionais do documento
        signature_date: Data da assinatura (formato DD/MM/YYYY HH:MM:SS) - se não informada, usa data atual
    
    IMPORTANTE: Requer que o usuário tenha CPF e Cargo preenchidos.
    """
    from reportlab.pdfgen import canvas as pdf_canvas
    from PyPDF2 import PdfReader, PdfWriter, PdfMerger
    
    # Buscar dados de assinatura do usuário
    user_doc = await db.users.find_one({'user_id': user.user_id}, {'_id': 0})
    user_signature = user_doc.get('signature_data') or {} if user_doc else {}
    
    # Validar campos obrigatórios para assinatura
    cpf = user_signature.get('cpf', '').strip()
    cargo = user_signature.get('cargo', '').strip()
    
    if not cpf:
        raise HTTPException(
            status_code=400, 
            detail="CPF é obrigatório para assinar documentos. Por favor, atualize seu perfil com o CPF."
        )
    
    if not cargo:
        raise HTTPException(
            status_code=400, 
            detail="Cargo é obrigatório para assinar documentos. Por favor, atualize seu perfil com seu cargo."
        )
    
    # Usar a data fornecida ou a atual
    if signature_date:
        data_hora = signature_date
    else:
        data_hora = datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S')
    
    signer = {
        'nome': user.name,
        'cpf': cpf,
        'cargo': cargo,
        'email': user.email,
        'data_hora': data_hora
    }
    
    # Gerar código de validação
    validation_code = generate_validation_code()
    
    # Calcular hash do documento original
    pdf_buffer.seek(0)
    hash_doc = hashlib.sha256(pdf_buffer.read()).hexdigest()
    pdf_buffer.seek(0)
    
    # Salvar registro de assinatura
    await save_document_signature(
        doc_id=doc_id,
        doc_type=doc_type,
        signers=[signer],
        hash_doc=hash_doc,
        validation_code=validation_code
    )
    
    # Verificar se é documento MROSC para usar página de assinaturas estilo Lei 14.063
    is_mrosc = 'MROSC' in doc_type.upper()
    
    if is_mrosc:
        # Para MROSC: adicionar página de assinaturas no final
        reader = PdfReader(pdf_buffer)
        writer = PdfWriter()
        
        # Copiar todas as páginas originais com selo no rodapé
        for page in reader.pages:
            overlay_buffer = BytesIO()
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)
            
            overlay_canvas = pdf_canvas.Canvas(overlay_buffer, pagesize=(page_width, page_height))
            qr_url = f"https://pac.acaiaca.mg.gov.br/validar?code={validation_code}"
            draw_signature_seal(overlay_canvas, page_width, page_height, [signer], validation_code, qr_url, data_hora)
            overlay_canvas.save()
            overlay_buffer.seek(0)
            
            overlay_reader = PdfReader(overlay_buffer)
            if len(overlay_reader.pages) > 0:
                page.merge_page(overlay_reader.pages[0])
            
            writer.add_page(page)
        
        # Criar e adicionar página de assinaturas estilo Lei 14.063
        signature_page_buffer = create_signature_page_mrosc(
            signers=[signer],
            validation_code=validation_code,
            doc_info=doc_info or {
                'tipo': doc_type,
                'id': doc_id,
                'titulo': f'Documento {doc_type}'
            }
        )
        
        sig_reader = PdfReader(signature_page_buffer)
        for sig_page in sig_reader.pages:
            writer.add_page(sig_page)
        
        output_buffer = BytesIO()
        writer.write(output_buffer)
        output_buffer.seek(0)
        
        return output_buffer, validation_code
    else:
        # Para outros documentos: selo no rodapé em todas as páginas
        reader = PdfReader(pdf_buffer)
        writer = PdfWriter()
        
        for page in reader.pages:
            overlay_buffer = BytesIO()
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)
            
            overlay_canvas = pdf_canvas.Canvas(overlay_buffer, pagesize=(page_width, page_height))
            qr_url = f"https://pac.acaiaca.mg.gov.br/validar?code={validation_code}"
            draw_signature_seal(overlay_canvas, page_width, page_height, [signer], validation_code, qr_url, data_hora)
            overlay_canvas.save()
            overlay_buffer.seek(0)
            
            overlay_reader = PdfReader(overlay_buffer)
            if len(overlay_reader.pages) > 0:
                page.merge_page(overlay_reader.pages[0])
            
            writer.add_page(page)
        
        output_buffer = BytesIO()
        writer.write(output_buffer)
        output_buffer.seek(0)
        
        return output_buffer, validation_code

async def get_doem_config() -> dict:
    """Obtém ou cria configuração padrão do DOEM"""
    config = await db.doem_config.find_one({'config_id': 'doem_config_main'}, {'_id': 0})
    if not config:
        config = {
            'config_id': 'doem_config_main',
            'nome_municipio': 'Acaiaca',
            'uf': 'MG',
            'cnpj': '18.296.673/0001-10',
            'endereco': 'Praça Antônio Carlos, 10 - Centro',
            'telefone': '(31) 3554-1222',
            'email': 'gabinete@acaiaca.mg.gov.br',
            'prefeito': '',
            'ano_inicio': 2026,
            'ultimo_numero_edicao': 0,
            'segmentos': DOEM_SEGMENTOS,
            'tipos_publicacao': DOEM_TIPOS_PUBLICACAO,
            'created_at': datetime.now(timezone.utc)
        }
        await db.doem_config.insert_one(config)
    return config

async def get_next_edicao_number() -> int:
    """Obtém o próximo número de edição"""
    config = await get_doem_config()
    next_num = config.get('ultimo_numero_edicao', 0) + 1
    await db.doem_config.update_one(
        {'config_id': 'doem_config_main'},
        {'$set': {'ultimo_numero_edicao': next_num}}
    )
    return next_num

# ===== Endpoints Administrativos DOEM =====

@doem_router.get("/config")
async def get_config(request: Request):
    """Obtém configurações do DOEM"""
    await get_current_user(request)
    config = await get_doem_config()
    return config

@doem_router.put("/config")
async def update_config(config_update: DOEMConfigUpdate, request: Request):
    """Atualiza configurações do DOEM"""
    user = await get_current_user(request)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Apenas administradores podem alterar configurações")
    
    update_data = {k: v for k, v in config_update.model_dump().items() if v is not None}
    if update_data:
        await db.doem_config.update_one(
            {'config_id': 'doem_config_main'},
            {'$set': update_data},
            upsert=True
        )
    
    return await get_doem_config()

@doem_router.get("/edicoes")
async def list_edicoes(request: Request, ano: int = None, status: str = None):
    """Lista todas as edições do DOEM"""
    await get_current_user(request)
    
    query = {}
    if ano:
        query['ano'] = ano
    if status:
        query['status'] = status
    
    edicoes = await db.doem_edicoes.find(query, {'_id': 0}).sort('data_publicacao', -1).to_list(500)
    return edicoes

@doem_router.get("/edicoes/anos")
async def get_doem_anos(request: Request):
    """Retorna lista de anos disponíveis no DOEM"""
    await get_current_user(request)
    
    pipeline = [
        {'$group': {'_id': '$ano'}},
        {'$sort': {'_id': -1}}
    ]
    
    result = await db.doem_edicoes.aggregate(pipeline).to_list(100)
    anos = [r['_id'] for r in result if r['_id']]
    
    # Garantir que o ano atual esteja na lista
    ano_atual = datetime.now().year
    if ano_atual not in anos:
        anos.append(ano_atual)
    
    anos.sort(reverse=True)
    return {'anos': anos, 'ano_atual': ano_atual}

@doem_router.post("/edicoes")
async def create_edicao(edicao_data: DOEMEdicaoCreate, request: Request):
    """Cria uma nova edição do DOEM"""
    user = await get_current_user(request)
    
    edicao_id = f"doem_{uuid.uuid4().hex[:12]}"
    numero_edicao = await get_next_edicao_number()
    now = datetime.now(timezone.utc)
    
    # Data de publicação padrão: dia seguinte
    data_pub = edicao_data.data_publicacao or (now + timedelta(days=1))
    
    # Converter publicações
    publicacoes = []
    for i, pub in enumerate(edicao_data.publicacoes):
        publicacoes.append({
            'publicacao_id': f"pub_{uuid.uuid4().hex[:8]}",
            'titulo': pub.titulo,
            'texto': pub.texto,
            'secretaria': pub.secretaria,
            'tipo': pub.tipo,
            'ordem': pub.ordem or (i + 1)
        })
    
    edicao_doc = {
        'edicao_id': edicao_id,
        'numero_edicao': numero_edicao,
        'ano': data_pub.year,
        'data_publicacao': data_pub,
        'data_criacao': now,
        'status': 'rascunho',
        'publicacoes': publicacoes,
        'criado_por': user.user_id,
        'assinatura_digital': None,
        'created_at': now,
        'updated_at': now
    }
    
    await db.doem_edicoes.insert_one(edicao_doc)
    edicao_doc.pop('_id', None)
    return edicao_doc

@doem_router.get("/edicoes/{edicao_id}")
async def get_edicao(edicao_id: str, request: Request):
    """Obtém uma edição específica"""
    await get_current_user(request)
    
    edicao = await db.doem_edicoes.find_one({'edicao_id': edicao_id}, {'_id': 0})
    if not edicao:
        raise HTTPException(status_code=404, detail="Edição não encontrada")
    return edicao

@doem_router.put("/edicoes/{edicao_id}")
async def update_edicao(edicao_id: str, edicao_update: DOEMEdicaoUpdate, request: Request):
    """Atualiza uma edição"""
    user = await get_current_user(request)
    
    edicao = await db.doem_edicoes.find_one({'edicao_id': edicao_id}, {'_id': 0})
    if not edicao:
        raise HTTPException(status_code=404, detail="Edição não encontrada")
    
    if edicao.get('status') == 'publicado' and not user.is_admin:
        raise HTTPException(status_code=403, detail="Edições publicadas só podem ser alteradas por administradores")
    
    update_data = {}
    
    if edicao_update.data_publicacao:
        update_data['data_publicacao'] = edicao_update.data_publicacao
        update_data['ano'] = edicao_update.data_publicacao.year
    
    if edicao_update.status:
        update_data['status'] = edicao_update.status
    
    if edicao_update.publicacoes is not None:
        publicacoes = []
        for i, pub in enumerate(edicao_update.publicacoes):
            publicacoes.append({
                'publicacao_id': f"pub_{uuid.uuid4().hex[:8]}",
                'titulo': pub.titulo,
                'texto': pub.texto,
                'secretaria': pub.secretaria,
                'tipo': pub.tipo,
                'ordem': pub.ordem or (i + 1)
            })
        update_data['publicacoes'] = publicacoes
    
    if update_data:
        update_data['updated_at'] = datetime.now(timezone.utc)
        await db.doem_edicoes.update_one({'edicao_id': edicao_id}, {'$set': update_data})
    
    return await db.doem_edicoes.find_one({'edicao_id': edicao_id}, {'_id': 0})

@doem_router.delete("/edicoes/{edicao_id}")
async def delete_edicao(edicao_id: str, request: Request):
    """Exclui uma edição (apenas rascunhos)"""
    user = await get_current_user(request)
    
    edicao = await db.doem_edicoes.find_one({'edicao_id': edicao_id}, {'_id': 0})
    if not edicao:
        raise HTTPException(status_code=404, detail="Edição não encontrada")
    
    if edicao.get('status') != 'rascunho' and not user.is_admin:
        raise HTTPException(status_code=403, detail="Apenas rascunhos podem ser excluídos")
    
    await db.doem_edicoes.delete_one({'edicao_id': edicao_id})
    return {'message': 'Edição excluída com sucesso'}

# ===== Endpoints de Assinatura em Lote =====

class AssinanteRequest(BaseModel):
    user_id: str

@doem_router.get("/edicoes/{edicao_id}/assinantes")
async def get_assinantes_edicao(edicao_id: str, request: Request):
    """Lista os assinantes de uma edição"""
    await get_current_user(request)
    
    edicao = await db.doem_edicoes.find_one({'edicao_id': edicao_id}, {'_id': 0})
    if not edicao:
        raise HTTPException(status_code=404, detail="Edição não encontrada")
    
    assinatura = edicao.get('assinatura_digital') or {}
    assinantes = assinatura.get('assinantes') or []
    
    return {
        'edicao_id': edicao_id,
        'assinantes': assinantes,
        'assinatura_em_lote': assinatura.get('assinatura_em_lote', False)
    }

@doem_router.post("/edicoes/{edicao_id}/assinantes")
async def add_assinante_edicao(edicao_id: str, assinante_req: AssinanteRequest, request: Request):
    """Adiciona um assinante a uma edição (antes de publicar)"""
    user = await get_current_user(request)
    
    edicao = await db.doem_edicoes.find_one({'edicao_id': edicao_id}, {'_id': 0})
    if not edicao:
        raise HTTPException(status_code=404, detail="Edição não encontrada")
    
    if edicao.get('status') == 'publicado':
        raise HTTPException(status_code=400, detail="Não é possível adicionar assinantes a edições já publicadas")
    
    # Buscar dados do usuário assinante
    assinante_user = await db.users.find_one({'user_id': assinante_req.user_id}, {'_id': 0})
    if not assinante_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    signature_data = assinante_user.get('signature_data') or {}
    
    novo_assinante = {
        'user_id': assinante_req.user_id,
        'nome': assinante_user.get('name', ''),
        'cpf': signature_data.get('cpf', '') if signature_data else '',
        'cargo': signature_data.get('cargo', '') if signature_data else '',
        'email': assinante_user.get('email', ''),
        'data_assinatura': None  # Será preenchido quando assinar
    }
    
    # Verificar se já está na lista
    assinatura = edicao.get('assinatura_digital') or {}
    assinantes = assinatura.get('assinantes') or []
    
    if any(a.get('user_id') == assinante_req.user_id for a in assinantes):
        raise HTTPException(status_code=400, detail="Este usuário já está na lista de assinantes")
    
    assinantes.append(novo_assinante)
    
    # Se assinatura_digital não existe, criar objeto completo
    if not edicao.get('assinatura_digital'):
        await db.doem_edicoes.update_one(
            {'edicao_id': edicao_id},
            {'$set': {
                'assinatura_digital': {
                    'assinado': False,
                    'assinantes': assinantes,
                    'assinatura_em_lote': len(assinantes) > 1
                }
            }}
        )
    else:
        await db.doem_edicoes.update_one(
            {'edicao_id': edicao_id},
            {'$set': {
                'assinatura_digital.assinantes': assinantes,
                'assinatura_digital.assinatura_em_lote': len(assinantes) > 1
            }}
        )
    
    return {
        'message': f'Assinante {assinante_user.get("name")} adicionado com sucesso',
        'assinantes': assinantes
    }

@doem_router.delete("/edicoes/{edicao_id}/assinantes/{user_id}")
async def remove_assinante_edicao(edicao_id: str, user_id: str, request: Request):
    """Remove um assinante de uma edição"""
    await get_current_user(request)
    
    edicao = await db.doem_edicoes.find_one({'edicao_id': edicao_id}, {'_id': 0})
    if not edicao:
        raise HTTPException(status_code=404, detail="Edição não encontrada")
    
    if edicao.get('status') == 'publicado':
        raise HTTPException(status_code=400, detail="Não é possível remover assinantes de edições já publicadas")
    
    assinatura = edicao.get('assinatura_digital') or {}
    assinantes = assinatura.get('assinantes') or []
    
    assinantes = [a for a in assinantes if a.get('user_id') != user_id]
    
    # Se assinatura_digital não existe, criar objeto completo
    if not edicao.get('assinatura_digital'):
        await db.doem_edicoes.update_one(
            {'edicao_id': edicao_id},
            {'$set': {
                'assinatura_digital': {
                    'assinado': False,
                    'assinantes': assinantes,
                    'assinatura_em_lote': len(assinantes) > 1
                }
            }}
        )
    else:
        await db.doem_edicoes.update_one(
            {'edicao_id': edicao_id},
            {'$set': {
                'assinatura_digital.assinantes': assinantes,
                'assinatura_digital.assinatura_em_lote': len(assinantes) > 1
            }}
        )
    
    return {'message': 'Assinante removido com sucesso', 'assinantes': assinantes}

@doem_router.get("/usuarios-disponiveis")
async def get_usuarios_disponiveis(request: Request):
    """Lista usuários disponíveis para assinar documentos (que possuem dados de assinatura)"""
    await get_current_user(request)
    
    # Buscar todos os usuários ativos
    users = await db.users.find(
        {'is_active': {'$ne': False}},
        {'_id': 0, 'password_hash': 0}
    ).to_list(1000)
    
    # Filtrar e formatar para exibição
    usuarios_disponiveis = []
    for user in users:
        sig_data = user.get('signature_data', {})
        usuarios_disponiveis.append({
            'user_id': user.get('user_id'),
            'nome': user.get('name', ''),
            'email': user.get('email', ''),
            'cargo': sig_data.get('cargo', ''),
            'tem_dados_assinatura': bool(sig_data.get('cpf') or sig_data.get('cargo'))
        })
    
    return usuarios_disponiveis

@doem_router.post("/import-rtf")
async def import_rtf(file: UploadFile = File(...), request: Request = None):
    """Importa um arquivo RTF e extrai as publicações"""
    if request:
        await get_current_user(request)
    
    if not file.filename.lower().endswith('.rtf'):
        raise HTTPException(status_code=400, detail="Apenas arquivos RTF são aceitos")
    
    content = await file.read()
    publicacoes = parse_rtf_publicacao(content)
    
    if not publicacoes:
        raise HTTPException(status_code=400, detail="Não foi possível extrair publicações do arquivo RTF")
    
    return {
        'filename': file.filename,
        'publicacoes_extraidas': len(publicacoes),
        'publicacoes': publicacoes
    }

@doem_router.post("/edicoes/{edicao_id}/publicar")
async def publicar_edicao(edicao_id: str, request: Request, background_tasks: BackgroundTasks, enviar_notificacao: bool = True):
    """Publica uma edição e gera PDF assinado, opcionalmente envia notificações"""
    user = await get_current_user(request)
    
    edicao = await db.doem_edicoes.find_one({'edicao_id': edicao_id}, {'_id': 0})
    if not edicao:
        raise HTTPException(status_code=404, detail="Edição não encontrada")
    
    if not edicao.get('publicacoes'):
        raise HTTPException(status_code=400, detail="A edição não possui publicações")
    
    # Verificar se há assinantes em lote pré-configurados
    assinatura_existente = edicao.get('assinatura_digital', {})
    assinantes_lote = assinatura_existente.get('assinantes', [])
    
    # Se não há assinantes pré-configurados, usar o usuário atual
    if not assinantes_lote:
        user_doc = await db.users.find_one({'user_id': user.user_id}, {'_id': 0})
        user_signature = user_doc.get('signature_data', {}) if user_doc else {}
        
        # Validar campos obrigatórios para assinatura
        cpf = (user_signature.get('cpf', '') or '').strip()
        cargo = (user_signature.get('cargo', '') or '').strip()
        
        if not cpf:
            raise HTTPException(
                status_code=400, 
                detail="CPF é obrigatório para publicar edições. Por favor, atualize seu perfil com o CPF."
            )
        
        if not cargo:
            raise HTTPException(
                status_code=400, 
                detail="Cargo é obrigatório para publicar edições. Por favor, atualize seu perfil com seu cargo."
            )
        
        assinantes_lote = [{
            'user_id': user.user_id,
            'nome': user.name,
            'email': user.email,
            'cpf': cpf,
            'cargo': cargo,
            'data_assinatura': datetime.now(timezone.utc).isoformat()
        }]
    else:
        # Validar campos obrigatórios para todos os assinantes pré-configurados
        for i, assinante in enumerate(assinantes_lote):
            cpf = (assinante.get('cpf', '') or '').strip()
            cargo = (assinante.get('cargo', '') or '').strip()
            nome = assinante.get('nome', f'Assinante {i+1}')
            
            if not cpf:
                raise HTTPException(
                    status_code=400, 
                    detail=f"O assinante '{nome}' não possui CPF cadastrado. Por favor, atualize os dados do usuário."
                )
            
            if not cargo:
                raise HTTPException(
                    status_code=400, 
                    detail=f"O assinante '{nome}' não possui Cargo cadastrado. Por favor, atualize os dados do usuário."
                )
            
            assinante['data_assinatura'] = datetime.now(timezone.utc).isoformat()
    
    # Preparar lista de signers para validação e PDF
    signers = []
    for assinante in assinantes_lote:
        signers.append({
            'nome': assinante.get('nome', ''),
            'cpf': assinante.get('cpf', ''),
            'cargo': assinante.get('cargo', ''),
            'email': assinante.get('email', '')
        })
    
    # Gerar código de validação único para o documento
    validation_code = generate_validation_code()
    
    # Criar objeto de assinatura
    assinatura_data = {
        'assinado': True,
        'data_assinatura': datetime.now(timezone.utc),
        'tipo_certificado': 'ICP-Brasil (Simulado)',
        'titular': assinantes_lote[0].get('nome', 'Prefeitura Municipal de Acaiaca'),
        'validation_code': validation_code,
        'cpf': assinantes_lote[0].get('cpf', ''),
        'cargo': assinantes_lote[0].get('cargo', ''),
        'email': assinantes_lote[0].get('email', ''),
        'assinantes': assinantes_lote,
        'assinatura_em_lote': len(assinantes_lote) > 1
    }
    
    # Atualizar edição com a assinatura ANTES de gerar o PDF
    await db.doem_edicoes.update_one(
        {'edicao_id': edicao_id},
        {'$set': {
            'status': 'publicado',
            'assinatura_digital': assinatura_data,
            'notificacao_enviada': False,
            'updated_at': datetime.now(timezone.utc)
        }}
    )
    
    # Buscar edição atualizada para gerar PDF
    edicao_atualizada = await db.doem_edicoes.find_one({'edicao_id': edicao_id}, {'_id': 0})
    
    # Gerar PDF com a assinatura
    pdf_buffer = await gerar_pdf_doem(edicao_atualizada)
    
    # Calcular hash do PDF
    hash_doc = hashlib.sha256(pdf_buffer.getvalue()).hexdigest()
    
    # Atualizar hash na assinatura
    await db.doem_edicoes.update_one(
        {'edicao_id': edicao_id},
        {'$set': {'assinatura_digital.hash_documento': hash_doc}}
    )
    
    # Salvar registro de assinatura para validação
    await save_document_signature(
        doc_id=edicao_id,
        doc_type=f"DOEM - Edição {edicao.get('numero_edicao', '')} / {edicao.get('ano', '')}",
        signers=signers,
        hash_doc=hash_doc,
        validation_code=validation_code
    )
    
    # Enviar notificações em background
    notificacao_msg = ""
    assinantes_notificados = 0
    
    # 1. Enviar notificações para assinantes do documento
    try:
        assinantes_notificados = await enviar_notificacao_assinantes(edicao_atualizada, assinantes_lote, validation_code)
        if assinantes_notificados > 0:
            notificacao_msg = f" Notificação enviada para {assinantes_notificados} assinante(s)."
    except Exception as e:
        logging.error(f"Erro ao enviar notificações para assinantes: {e}")
    
    # 2. Enviar notificações para inscritos na newsletter (se solicitado)
    if enviar_notificacao:
        pdf_buffer.seek(0)  # Reset buffer position
        try:
            enviados = await enviar_notificacao_doem(edicao_atualizada, pdf_buffer)
            await db.doem_edicoes.update_one(
                {'edicao_id': edicao_id},
                {'$set': {'notificacao_enviada': True}}
            )
            notificacao_msg += f" Newsletter enviada para {enviados} destinatário(s)."
        except Exception as e:
            logging.error(f"Erro ao enviar notificações: {e}")
            notificacao_msg += " Falha ao enviar newsletter."
    
    # Atualizar assinatura com hash
    assinatura_data['hash_documento'] = hash_doc
    
    return {
        'message': f'Edição publicada com sucesso!{notificacao_msg}',
        'assinatura': assinatura_data,
        'assinantes': len(assinantes_lote),
        'validation_code': validation_code
    }

@doem_router.get("/edicoes/{edicao_id}/pdf")
async def download_pdf_edicao(edicao_id: str, request: Request):
    """Gera e baixa o PDF de uma edição"""
    await get_current_user(request)
    
    edicao = await db.doem_edicoes.find_one({'edicao_id': edicao_id}, {'_id': 0})
    if not edicao:
        raise HTTPException(status_code=404, detail="Edição não encontrada")
    
    pdf_buffer = await gerar_pdf_doem(edicao)
    
    filename = f"DOEM_Acaiaca_Edicao_{edicao['numero_edicao']}_{edicao['ano']}.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

async def gerar_pdf_doem(edicao: dict) -> BytesIO:
    """Gera PDF do DOEM em formato de jornal oficial com cabeçalho e rodapé customizados"""
    from reportlab.platypus import Frame, PageTemplate, BaseDocTemplate
    from reportlab.lib.utils import ImageReader
    from PIL import Image as PILImage
    
    buffer = BytesIO()
    config = await get_doem_config()
    
    # Margens reduzidas para aproveitar melhor o espaço
    left_margin = 15*mm
    right_margin = 15*mm
    top_margin = 35*mm  # Espaço para cabeçalho com imagem
    bottom_margin = 30*mm  # Espaço para rodapé com imagem
    
    # Caminhos das imagens (versões otimizadas)
    brasao_path = ROOT_DIR / 'brasao_doem_small.png'
    rodape_path = ROOT_DIR / 'rodape_doem_small.jpg'
    
    # Fallback para imagens originais se as otimizadas não existirem
    if not brasao_path.exists():
        brasao_path = ROOT_DIR / 'brasao_doem.png'
    if not rodape_path.exists():
        rodape_path = ROOT_DIR / 'rodape_doem.jpg'
    
    styles = getSampleStyleSheet()
    
    # Estilos customizados
    header_title_style = ParagraphStyle(
        'DOEMHeaderTitle',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
        leading=13
    )
    
    edition_style = ParagraphStyle(
        'DOEMEdition',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#333333'),
        spaceAfter=8,
        spaceBefore=4
    )
    
    section_style = ParagraphStyle(
        'DOEMSection',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.HexColor('#1F4E78'),
        fontName='Helvetica-Bold',
        spaceBefore=8,
        spaceAfter=4
    )
    
    subsection_style = ParagraphStyle(
        'DOEMSubsection',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
        spaceBefore=6,
        spaceAfter=3,
        textColor=colors.HexColor('#2E5A1F')
    )
    
    title_style = ParagraphStyle(
        'DOEMTitle',
        parent=styles['Heading3'],
        fontSize=9,
        fontName='Helvetica-Bold',
        spaceBefore=6,
        spaceAfter=2
    )
    
    body_style = ParagraphStyle(
        'DOEMBody',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica',
        alignment=TA_JUSTIFY,
        spaceAfter=4,
        leading=11
    )
    
    footer_style = ParagraphStyle(
        'DOEMFooter',
        parent=styles['Normal'],
        fontSize=7,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#666666')
    )
    
    # Função para desenhar cabeçalho e rodapé em cada página
    def draw_header_footer(canvas, doc):
        canvas.saveState()
        page_width, page_height = A4
        
        # === CABEÇALHO ===
        # Desenhar brasão
        if brasao_path.exists():
            try:
                pil_img = PILImage.open(str(brasao_path))
                img_width, img_height = pil_img.size
                aspect_ratio = img_height / img_width
                logo_width = 22*mm
                logo_height = logo_width * aspect_ratio
                canvas.drawImage(str(brasao_path), left_margin, page_height - 28*mm, 
                               width=logo_width, height=logo_height, preserveAspectRatio=True)
            except Exception as e:
                logging.error(f"Erro ao carregar brasão: {e}")
        
        # Texto do cabeçalho ao lado do brasão
        # Cores do brasão: azul #1F4E78 e verde #2E5A1F
        text_x = left_margin + 26*mm
        text_y = page_height - 12*mm
        
        canvas.setFont('Helvetica-Bold', 12)
        canvas.setFillColor(colors.HexColor('#1F4E78'))
        canvas.drawString(text_x, text_y, "DOEM")
        
        canvas.setFont('Helvetica-Bold', 10)
        canvas.setFillColor(colors.HexColor('#2E5A1F'))
        canvas.drawString(text_x, text_y - 12, "Diário Oficial Eletrônico Municipal")
        
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.HexColor('#1F4E78'))
        canvas.drawString(text_x, text_y - 23, "de Acaiaca - MG")
        
        # Linha divisória
        canvas.setStrokeColor(colors.HexColor('#1F4E78'))
        canvas.setLineWidth(1)
        canvas.line(left_margin, page_height - 32*mm, page_width - right_margin, page_height - 32*mm)
        
        # === SELO DE ASSINATURA DIGITAL ===
        assinatura = edicao.get('assinatura_digital')
        if assinatura and assinatura.get('assinado'):
            validation_code = assinatura.get('validation_code', generate_validation_code())
            
            # Verificar se há múltiplos assinantes (assinatura em lote)
            assinantes_lote = assinatura.get('assinantes', [])
            if assinantes_lote and len(assinantes_lote) > 0:
                # Usar lista de assinantes do lote
                signers = []
                for assinante in assinantes_lote:
                    signers.append({
                        'nome': assinante.get('nome', ''),
                        'cargo': assinante.get('cargo', ''),
                        'cpf': assinante.get('cpf', ''),
                        'email': assinante.get('email', ''),
                        'data_hora': assinante.get('data_hora', datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S'))
                    })
            else:
                # Assinante único (compatibilidade com versão anterior)
                signers = [{
                    'nome': assinatura.get('titular', 'Prefeitura Municipal de Acaiaca'),
                    'cargo': assinatura.get('cargo', 'Órgão Publicador'),
                    'cpf': assinatura.get('cpf', ''),
                    'email': assinatura.get('email', 'contato@acaiaca.mg.gov.br'),
                    'data_hora': assinatura.get('data_assinatura', datetime.now(timezone.utc)).strftime('%d/%m/%Y %H:%M:%S') if isinstance(assinatura.get('data_assinatura'), datetime) else datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S')
                }]
            
            # URL para validação
            qr_url = f"https://pac.acaiaca.mg.gov.br/validar?code={validation_code}"
            # Pegar data da assinatura do primeiro assinante
            signature_date = signers[0].get('data_hora') if signers else None
            draw_signature_seal(canvas, page_width, page_height, signers, validation_code, qr_url, signature_date)
        
        # === RODAPÉ ===
        if rodape_path.exists():
            try:
                pil_img = PILImage.open(str(rodape_path))
                img_width, img_height = pil_img.size
                aspect_ratio = img_height / img_width
                rodape_width = page_width - left_margin - right_margin
                rodape_height = rodape_width * aspect_ratio
                if rodape_height > 20*mm:
                    rodape_height = 20*mm
                    rodape_width = rodape_height / aspect_ratio
                canvas.drawImage(str(rodape_path), left_margin, 5*mm, 
                               width=rodape_width, height=rodape_height, preserveAspectRatio=True)
            except Exception as e:
                logging.error(f"Erro ao carregar rodapé: {e}")
        
        # Número da página
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawCentredString(page_width / 2, 3*mm, f"Página {doc.page}")
        
        canvas.restoreState()
    
    # Criar documento com template customizado
    doc = BaseDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin
    )
    
    # Frame para o conteúdo
    frame = Frame(
        left_margin, bottom_margin,
        A4[0] - left_margin - right_margin,
        A4[1] - top_margin - bottom_margin,
        id='main'
    )
    
    # Template com cabeçalho e rodapé
    template = PageTemplate(id='doem', frames=[frame], onPage=draw_header_footer)
    doc.addPageTemplates([template])
    
    elements = []
    
    # Formatação da data
    data_pub = edicao.get('data_publicacao')
    if isinstance(data_pub, str):
        data_pub = datetime.fromisoformat(data_pub.replace('Z', '+00:00'))
    
    meses = {
        'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
        'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
        'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
        'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
    }
    data_formatada = data_pub.strftime('%d de %B de %Y')
    for en, pt in meses.items():
        data_formatada = data_formatada.replace(en, pt)
    
    # Info da edição
    ano_doem = edicao['ano'] - config.get('ano_inicio', 2026) + 1
    elements.append(Paragraph(
        f"<b>Edição nº {edicao['numero_edicao']}</b> | Ano {ano_doem} | {data_formatada}",
        edition_style
    ))
    
    elements.append(Spacer(1, 3*mm))
    
    # Agrupar publicações por segmento
    publicacoes_por_segmento = {}
    for pub in edicao.get('publicacoes', []):
        segmento = pub.get('segmento', 'Decretos')
        if segmento not in publicacoes_por_segmento:
            publicacoes_por_segmento[segmento] = {}
        
        secretaria = pub.get('secretaria', 'Gabinete do Prefeito')
        if secretaria not in publicacoes_por_segmento[segmento]:
            publicacoes_por_segmento[segmento][secretaria] = []
        publicacoes_por_segmento[segmento][secretaria].append(pub)
    
    # Seção: PODER EXECUTIVO
    elements.append(Paragraph('<b>PODER EXECUTIVO</b>', section_style))
    
    # Publicações por segmento e secretaria
    for segmento, secretarias in publicacoes_por_segmento.items():
        # Título do segmento
        elements.append(Paragraph(f'<b>{segmento.upper()}</b>', subsection_style))
        
        for secretaria, pubs in secretarias.items():
            # Nome da secretaria
            elements.append(Paragraph(f'<i>{secretaria}</i>', ParagraphStyle(
                'Secretaria',
                parent=styles['Normal'],
                fontSize=8,
                fontName='Helvetica-Oblique',
                spaceBefore=2,
                spaceAfter=2,
                textColor=colors.HexColor('#555555')
            )))
            
            for pub in sorted(pubs, key=lambda x: x.get('ordem', 1)):
                elements.append(Paragraph(f'<b>{pub["titulo"]}</b>', title_style))
                
                # Quebrar texto em parágrafos
                texto = pub.get('texto', '').strip()
                # Dividir por quebras de linha dupla ou simples
                if '\n\n' in texto:
                    paragrafos = texto.split('\n\n')
                else:
                    paragrafos = texto.split('\n')
                
                for paragrafo in paragrafos:
                    if paragrafo.strip():
                        elements.append(Paragraph(paragrafo.strip(), body_style))
                
                elements.append(Spacer(1, 2*mm))
    
    # Informação de assinatura digital
    elements.append(Spacer(1, 5*mm))
    
    assinatura = edicao.get('assinatura_digital')
    if assinatura and assinatura.get('assinado'):
        data_ass = assinatura.get('data_assinatura', '')
        if isinstance(data_ass, datetime):
            data_ass_str = data_ass.strftime('%d/%m/%Y %H:%M')
        elif isinstance(data_ass, str):
            data_ass_str = data_ass[:16].replace('T', ' ')
        else:
            data_ass_str = str(data_ass)[:16] if data_ass else ''
        
        elements.append(Paragraph(
            f"<b>Documento assinado digitalmente</b> em {data_ass_str}",
            footer_style
        ))
        elements.append(Paragraph(
            f"Hash SHA-256: {str(assinatura.get('hash_documento', ''))[:48]}...",
            footer_style
        ))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ===== Endpoints Públicos DOEM =====

@public_router.get("/doem/edicoes")
async def public_list_doem_edicoes(ano: int = None, limit: int = 20):
    """Lista edições publicadas do DOEM (público)"""
    query = {'status': 'publicado'}
    if ano:
        query['ano'] = ano
    
    edicoes = await db.doem_edicoes.find(query, {'_id': 0}).sort('data_publicacao', -1).to_list(limit)
    return edicoes

@public_router.get("/doem/edicoes/{edicao_id}")
async def public_get_doem_edicao(edicao_id: str):
    """Obtém uma edição publicada específica (público)"""
    edicao = await db.doem_edicoes.find_one(
        {'edicao_id': edicao_id, 'status': 'publicado'},
        {'_id': 0}
    )
    if not edicao:
        raise HTTPException(status_code=404, detail="Edição não encontrada ou não publicada")
    return edicao

@public_router.get("/doem/edicoes/{edicao_id}/pdf")
async def public_download_doem_pdf(edicao_id: str):
    """Download do PDF de uma edição publicada (público)"""
    edicao = await db.doem_edicoes.find_one(
        {'edicao_id': edicao_id, 'status': 'publicado'},
        {'_id': 0}
    )
    if not edicao:
        raise HTTPException(status_code=404, detail="Edição não encontrada ou não publicada")
    
    pdf_buffer = await gerar_pdf_doem(edicao)
    
    filename = f"DOEM_Acaiaca_Edicao_{edicao['numero_edicao']}_{edicao['ano']}.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@public_router.get("/doem/anos")
async def public_get_doem_anos():
    """Lista anos disponíveis no DOEM (público)"""
    pipeline = [
        {'$match': {'status': 'publicado'}},
        {'$group': {'_id': '$ano'}},
        {'$sort': {'_id': -1}}
    ]
    
    result = await db.doem_edicoes.aggregate(pipeline).to_list(100)
    anos = [r['_id'] for r in result if r['_id']]
    
    ano_atual = datetime.now().year
    if ano_atual not in anos:
        anos.append(ano_atual)
    
    anos.sort(reverse=True)
    return {'anos': anos}

# ===== Histórico de Assinaturas por Usuário =====

@api_router.get("/assinaturas/historico")
async def get_historico_assinaturas(request: Request, page: int = 1, page_size: int = 20):
    """Lista o histórico de assinaturas do usuário logado"""
    user = await get_current_user(request)
    
    # Buscar todas as assinaturas onde o usuário é um dos assinantes
    pipeline = [
        {
            '$match': {
                'signers.email': user.email
            }
        },
        {'$sort': {'created_at': -1}},
        {'$skip': (page - 1) * page_size},
        {'$limit': page_size}
    ]
    
    assinaturas = await db.document_signatures.aggregate(pipeline).to_list(page_size)
    
    # Contar total
    total = await db.document_signatures.count_documents({'signers.email': user.email})
    
    # Formatar resposta
    resultado = []
    for sig in assinaturas:
        # Encontrar dados do usuário na lista de assinantes
        user_signer = next((s for s in sig.get('signers', []) if s.get('email') == user.email), None)
        
        resultado.append({
            'signature_id': sig.get('signature_id'),
            'document_id': sig.get('document_id'),
            'document_type': sig.get('document_type'),
            'validation_code': sig.get('validation_code'),
            'created_at': sig.get('created_at').isoformat() if sig.get('created_at') else None,
            'is_valid': sig.get('is_valid', True),
            'total_signers': len(sig.get('signers', [])),
            'my_signature': {
                'nome': user_signer.get('nome') if user_signer else user.name,
                'cargo': user_signer.get('cargo') if user_signer else '',
                'cpf_masked': mask_cpf(user_signer.get('cpf', '')) if user_signer else ''
            }
        })
    
    return {
        'items': resultado,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size
    }

@api_router.get("/assinaturas/estatisticas")
async def get_estatisticas_assinaturas(request: Request):
    """Retorna estatísticas de assinaturas do usuário"""
    user = await get_current_user(request)
    
    # Total de documentos assinados
    total_assinaturas = await db.document_signatures.count_documents({'signers.email': user.email})
    
    # Assinaturas válidas
    assinaturas_validas = await db.document_signatures.count_documents({
        'signers.email': user.email,
        'is_valid': True
    })
    
    # Assinaturas por tipo de documento
    pipeline = [
        {'$match': {'signers.email': user.email}},
        {'$group': {'_id': '$document_type', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    por_tipo = await db.document_signatures.aggregate(pipeline).to_list(20)
    
    # Assinaturas dos últimos 30 dias
    data_30_dias = datetime.now(timezone.utc) - timedelta(days=30)
    ultimos_30_dias = await db.document_signatures.count_documents({
        'signers.email': user.email,
        'created_at': {'$gte': data_30_dias}
    })
    
    # Última assinatura
    ultima = await db.document_signatures.find_one(
        {'signers.email': user.email},
        {'_id': 0},
        sort=[('created_at', -1)]
    )
    
    return {
        'total_assinaturas': total_assinaturas,
        'assinaturas_validas': assinaturas_validas,
        'assinaturas_invalidas': total_assinaturas - assinaturas_validas,
        'ultimos_30_dias': ultimos_30_dias,
        'por_tipo': [{'tipo': p['_id'], 'quantidade': p['count']} for p in por_tipo],
        'ultima_assinatura': {
            'document_type': ultima.get('document_type') if ultima else None,
            'validation_code': ultima.get('validation_code') if ultima else None,
            'created_at': ultima.get('created_at').isoformat() if ultima and ultima.get('created_at') else None
        } if ultima else None
    }

@public_router.get("/doem/busca")
async def public_buscar_doem(q: str, ano: int = None):
    """Busca publicações no DOEM (público)"""
    if not q or len(q) < 3:
        raise HTTPException(status_code=400, detail="Termo de busca deve ter pelo menos 3 caracteres")
    
    query = {
        'status': 'publicado',
        '$or': [
            {'publicacoes.titulo': {'$regex': q, '$options': 'i'}},
            {'publicacoes.texto': {'$regex': q, '$options': 'i'}}
        ]
    }
    if ano:
        query['ano'] = ano
    
    edicoes = await db.doem_edicoes.find(query, {'_id': 0}).sort('data_publicacao', -1).to_list(100)
    
    # Filtrar publicações que contêm o termo
    resultados = []
    for edicao in edicoes:
        for pub in edicao.get('publicacoes', []):
            if q.lower() in pub.get('titulo', '').lower() or q.lower() in pub.get('texto', '').lower():
                resultados.append({
                    'edicao_id': edicao['edicao_id'],
                    'numero_edicao': edicao['numero_edicao'],
                    'data_publicacao': edicao['data_publicacao'],
                    'publicacao': pub
                })
    
    return {'total': len(resultados), 'resultados': resultados[:50]}

# ============ ENDPOINTS DE SEGMENTOS ============

@doem_router.get("/segmentos")
async def get_doem_segmentos(request: Request):
    """Retorna lista de segmentos e tipos de publicação do DOEM"""
    await get_current_user(request)
    config = await get_doem_config()
    return {
        'segmentos': config.get('segmentos', DOEM_SEGMENTOS),
        'tipos_publicacao': config.get('tipos_publicacao', DOEM_TIPOS_PUBLICACAO)
    }

@public_router.get("/doem/segmentos")
async def public_get_doem_segmentos():
    """Retorna lista de segmentos do DOEM (público)"""
    config = await get_doem_config()
    return {
        'segmentos': config.get('segmentos', DOEM_SEGMENTOS),
        'tipos_publicacao': config.get('tipos_publicacao', DOEM_TIPOS_PUBLICACAO)
    }

# ============ ENDPOINTS DE NEWSLETTER ============

newsletter_router = APIRouter(prefix="/api/newsletter", tags=["Newsletter"])

@newsletter_router.get("/inscritos")
async def listar_inscritos(request: Request):
    """Lista todos os inscritos na newsletter (admin only)"""
    user = await get_current_user(request)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Apenas administradores podem ver a lista de inscritos")
    
    inscritos = await db.doem_newsletter.find({}, {'_id': 0}).to_list(1000)
    return inscritos

@newsletter_router.post("/inscritos")
async def adicionar_inscrito_manual(inscricao: NewsletterInscricaoManual, request: Request):
    """Adiciona inscrito manualmente (admin only)"""
    user = await get_current_user(request)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Apenas administradores podem adicionar inscritos")
    
    # Verificar se já existe
    existente = await db.doem_newsletter.find_one({'email': inscricao.email})
    if existente:
        raise HTTPException(status_code=400, detail="Este email já está inscrito")
    
    now = datetime.now(timezone.utc)
    inscrito_doc = {
        'inscrito_id': f"news_{uuid.uuid4().hex[:12]}",
        'email': inscricao.email,
        'nome': inscricao.nome,
        'tipo': 'manual',
        'ativo': True,
        'segmentos_interesse': inscricao.segmentos_interesse,
        'data_inscricao': now,
        'data_confirmacao': now if inscricao.confirmado else None,
        'confirmado': inscricao.confirmado,
        'token_confirmacao': None
    }
    
    await db.doem_newsletter.insert_one(inscrito_doc)
    inscrito_doc.pop('_id', None)
    return inscrito_doc

@newsletter_router.delete("/inscritos/{inscrito_id}")
async def remover_inscrito(inscrito_id: str, request: Request):
    """Remove um inscrito (admin only)"""
    user = await get_current_user(request)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Apenas administradores podem remover inscritos")
    
    result = await db.doem_newsletter.delete_one({'inscrito_id': inscrito_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Inscrito não encontrado")
    
    return {'message': 'Inscrito removido com sucesso'}

@newsletter_router.put("/inscritos/{inscrito_id}/toggle")
async def toggle_inscrito(inscrito_id: str, request: Request):
    """Ativa/desativa um inscrito (admin only)"""
    user = await get_current_user(request)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Apenas administradores podem alterar status")
    
    inscrito = await db.doem_newsletter.find_one({'inscrito_id': inscrito_id})
    if not inscrito:
        raise HTTPException(status_code=404, detail="Inscrito não encontrado")
    
    novo_status = not inscrito.get('ativo', True)
    await db.doem_newsletter.update_one(
        {'inscrito_id': inscrito_id},
        {'$set': {'ativo': novo_status}}
    )
    
    return {'message': f'Inscrito {"ativado" if novo_status else "desativado"} com sucesso', 'ativo': novo_status}

@newsletter_router.get("/estatisticas")
async def estatisticas_newsletter(request: Request):
    """Retorna estatísticas da newsletter (admin only)"""
    user = await get_current_user(request)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Apenas administradores")
    
    total = await db.doem_newsletter.count_documents({})
    ativos = await db.doem_newsletter.count_documents({'ativo': True, 'confirmado': True})
    pendentes = await db.doem_newsletter.count_documents({'confirmado': False})
    
    # Por tipo
    por_tipo = await db.doem_newsletter.aggregate([
        {'$group': {'_id': '$tipo', 'count': {'$sum': 1}}}
    ]).to_list(10)
    
    return {
        'total': total,
        'ativos': ativos,
        'pendentes': pendentes,
        'por_tipo': {t['_id']: t['count'] for t in por_tipo}
    }

# Endpoint público para inscrição
@public_router.post("/newsletter/inscrever")
async def inscricao_publica_newsletter(inscricao: NewsletterInscricaoPublica):
    """Inscrição pública na newsletter do DOEM"""
    # Verificar se já existe
    existente = await db.doem_newsletter.find_one({'email': inscricao.email})
    if existente:
        if existente.get('confirmado'):
            raise HTTPException(status_code=400, detail="Este email já está inscrito e confirmado")
        else:
            # Reenviar email de confirmação
            return {'message': 'Um email de confirmação foi enviado anteriormente. Verifique sua caixa de entrada.'}
    
    now = datetime.now(timezone.utc)
    token = uuid.uuid4().hex
    
    inscrito_doc = {
        'inscrito_id': f"news_{uuid.uuid4().hex[:12]}",
        'email': inscricao.email,
        'nome': inscricao.nome,
        'tipo': 'publico',
        'ativo': True,
        'segmentos_interesse': inscricao.segmentos_interesse,
        'data_inscricao': now,
        'data_confirmacao': None,
        'confirmado': False,
        'token_confirmacao': token
    }
    
    await db.doem_newsletter.insert_one(inscrito_doc)
    
    # Enviar email de confirmação
    try:
        corpo_html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #1F4E78, #2E7D32); padding: 20px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">📰 DOEM Acaiaca</h1>
            </div>
            <div style="background: #f8f9fa; padding: 20px; border: 1px solid #dee2e6;">
                <h2 style="color: #1F4E78;">Confirme sua inscrição</h2>
                <p>Olá {inscricao.nome},</p>
                <p>Você solicitou inscrição na newsletter do Diário Oficial Eletrônico de Acaiaca.</p>
                <p>Clique no botão abaixo para confirmar:</p>
                <div style="text-align: center; margin: 20px 0;">
                    <a href="https://pac.acaiaca.mg.gov.br/api/public/newsletter/confirmar/{token}" 
                       style="background: #2E7D32; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        ✅ Confirmar Inscrição
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
        enviar_email_smtp(inscricao.email, "Confirme sua inscrição - DOEM Acaiaca", corpo_html)
    except Exception as e:
        logging.error(f"Erro ao enviar email de confirmação: {e}")
    
    return {'message': 'Inscrição recebida! Verifique seu email para confirmar.'}

@public_router.get("/newsletter/confirmar/{token}")
async def confirmar_inscricao(token: str):
    """Confirma inscrição na newsletter"""
    inscrito = await db.doem_newsletter.find_one({'token_confirmacao': token})
    if not inscrito:
        raise HTTPException(status_code=404, detail="Token inválido ou expirado")
    
    if inscrito.get('confirmado'):
        return Response(
            content="<html><body><h1>Inscrição já confirmada!</h1><p>Você já está inscrito na newsletter do DOEM.</p></body></html>",
            media_type="text/html"
        )
    
    await db.doem_newsletter.update_one(
        {'token_confirmacao': token},
        {'$set': {
            'confirmado': True,
            'data_confirmacao': datetime.now(timezone.utc),
            'token_confirmacao': None
        }}
    )
    
    return Response(
        content="""
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1 style="color: #2E7D32;">✅ Inscrição Confirmada!</h1>
            <p>Você receberá notificações quando novas edições do DOEM forem publicadas.</p>
            <a href="https://pac.acaiaca.mg.gov.br/doem-publico" style="color: #1F4E78;">Acessar o DOEM</a>
        </body>
        </html>
        """,
        media_type="text/html"
    )

@public_router.get("/newsletter/cancelar/{email}")
async def cancelar_inscricao(email: str):
    """Cancela inscrição na newsletter"""
    result = await db.doem_newsletter.update_one(
        {'email': email},
        {'$set': {'ativo': False}}
    )
    
    return Response(
        content="""
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1 style="color: #666;">Inscrição Cancelada</h1>
            <p>Você não receberá mais notificações do DOEM.</p>
            <p><small>Para se inscrever novamente, acesse o portal do DOEM.</small></p>
        </body>
        </html>
        """,
        media_type="text/html"
    )

# Registrar router Newsletter
app.include_router(newsletter_router)

# ============ MÓDULO MROSC - PRESTAÇÃO DE CONTAS (Lei 13.019/2014) ============
mrosc_router = APIRouter(prefix="/api/mrosc", tags=["Prestação de Contas MROSC"])

def calcular_encargos_clt(salario_bruto: float, numero_meses: int) -> dict:
    """Calcula encargos trabalhistas CLT conforme MROSC"""
    provisao_ferias = salario_bruto / 12
    provisao_13_salario = salario_bruto / 12
    base_fgts = salario_bruto + provisao_ferias + provisao_13_salario
    fgts = base_fgts * 0.08
    inss_patronal = salario_bruto * 0.20
    custo_mensal = salario_bruto + provisao_ferias + provisao_13_salario + fgts + inss_patronal
    return {
        'provisao_ferias': round(provisao_ferias, 2),
        'provisao_13_salario': round(provisao_13_salario, 2),
        'fgts': round(fgts, 2),
        'inss_patronal': round(inss_patronal, 2),
        'custo_mensal_total': round(custo_mensal, 2),
        'custo_total_projeto': round(custo_mensal * numero_meses, 2)
    }

def calcular_media_orcamentos(orc1: float, orc2: float, orc3: float) -> float:
    """Calcula média dos três orçamentos"""
    valores = [v for v in [orc1, orc2, orc3] if v and v > 0]
    return round(sum(valores) / len(valores), 2) if valores else 0.0

# Endpoint para naturezas de despesa
@mrosc_router.get("/naturezas-despesa")
async def get_naturezas_despesa():
    """Retorna naturezas de despesa conforme MROSC"""
    return NATUREZAS_DESPESA_MROSC

# ===== PROJETOS MROSC =====
@mrosc_router.get("/projetos", response_model=List[ProjetoMROSC])
async def get_projetos_mrosc(request: Request):
    """Lista todos os projetos MROSC"""
    user = await get_current_user(request)
    query = {} if user.is_admin else {'user_id': user.user_id}
    projetos = await db.mrosc_projetos.find(query, {'_id': 0}).to_list(100)
    return [ProjetoMROSC(**p) for p in projetos]

@mrosc_router.post("/projetos", response_model=ProjetoMROSC)
async def create_projeto_mrosc(projeto_data: ProjetoMROSCCreate, request: Request):
    """Cria um novo projeto MROSC"""
    user = await get_current_user(request)
    projeto_id = f"mrosc_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    projeto_doc = {
        'projeto_id': projeto_id,
        'user_id': user.user_id,
        **projeto_data.model_dump(),
        'created_at': now,
        'updated_at': now
    }
    await db.mrosc_projetos.insert_one(projeto_doc)
    return ProjetoMROSC(**projeto_doc)

@mrosc_router.get("/projetos/{projeto_id}", response_model=ProjetoMROSC)
async def get_projeto_mrosc(projeto_id: str, request: Request):
    """Obtém um projeto MROSC específico"""
    user = await get_current_user(request)
    projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return ProjetoMROSC(**projeto)

@mrosc_router.put("/projetos/{projeto_id}", response_model=ProjetoMROSC)
async def update_projeto_mrosc(projeto_id: str, projeto_data: ProjetoMROSCUpdate, request: Request):
    """Atualiza um projeto MROSC"""
    user = await get_current_user(request)
    projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    update_data = {k: v for k, v in projeto_data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc)
    await db.mrosc_projetos.update_one({'projeto_id': projeto_id}, {'$set': update_data})
    updated = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
    return ProjetoMROSC(**updated)

@mrosc_router.delete("/projetos/{projeto_id}")
async def delete_projeto_mrosc(projeto_id: str, request: Request):
    """Exclui um projeto MROSC e todos os dados relacionados"""
    user = await get_current_user(request)
    projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    # Excluir dados relacionados
    await db.mrosc_rh.delete_many({'projeto_id': projeto_id})
    await db.mrosc_despesas.delete_many({'projeto_id': projeto_id})
    await db.mrosc_documentos.delete_many({'projeto_id': projeto_id})
    await db.mrosc_projetos.delete_one({'projeto_id': projeto_id})
    return {'message': 'Projeto excluído com sucesso'}

# ===== RECURSOS HUMANOS MROSC =====
@mrosc_router.get("/projetos/{projeto_id}/rh", response_model=List[RecursoHumanoMROSC])
async def get_rh_mrosc(projeto_id: str, request: Request):
    """Lista recursos humanos de um projeto"""
    user = await get_current_user(request)
    rhs = await db.mrosc_rh.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(100)
    return [RecursoHumanoMROSC(**rh) for rh in rhs]

@mrosc_router.post("/projetos/{projeto_id}/rh", response_model=RecursoHumanoMROSC)
async def create_rh_mrosc(projeto_id: str, rh_data: RecursoHumanoMROSCCreate, request: Request):
    """Adiciona um recurso humano ao projeto"""
    user = await get_current_user(request)
    projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    rh_id = f"rh_{uuid.uuid4().hex[:12]}"
    rh_dict = rh_data.model_dump()
    
    # Calcular encargos CLT automaticamente
    encargos = calcular_encargos_clt(rh_dict['salario_bruto'], rh_dict['numero_meses'])
    
    # Calcular média de orçamentos se fornecidos
    media = calcular_media_orcamentos(
        rh_dict.get('orcamento_1', 0),
        rh_dict.get('orcamento_2', 0),
        rh_dict.get('orcamento_3', 0)
    )
    
    # Incluir benefícios no custo mensal total
    custo_mensal = encargos['custo_mensal_total'] + rh_dict.get('vale_transporte', 0) + rh_dict.get('vale_alimentacao', 0)
    custo_total = custo_mensal * rh_dict['numero_meses']
    
    rh_doc = {
        'rh_id': rh_id,
        'projeto_id': projeto_id,
        **rh_dict,
        'provisao_ferias': encargos['provisao_ferias'],
        'provisao_13_salario': encargos['provisao_13_salario'],
        'fgts': encargos['fgts'],
        'inss_patronal': encargos['inss_patronal'],
        'custo_mensal_total': round(custo_mensal, 2),
        'custo_total_projeto': round(custo_total, 2),
        'media_orcamentos': media,
        'created_at': datetime.now(timezone.utc)
    }
    await db.mrosc_rh.insert_one(rh_doc)
    return RecursoHumanoMROSC(**rh_doc)

@mrosc_router.delete("/projetos/{projeto_id}/rh/{rh_id}")
async def delete_rh_mrosc(projeto_id: str, rh_id: str, request: Request):
    """Remove um recurso humano do projeto"""
    user = await get_current_user(request)
    result = await db.mrosc_rh.delete_one({'rh_id': rh_id, 'projeto_id': projeto_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recurso humano não encontrado")
    return {'message': 'Recurso humano excluído com sucesso'}

# ===== DESPESAS MROSC =====
@mrosc_router.get("/projetos/{projeto_id}/despesas", response_model=List[DespesaMROSC])
async def get_despesas_mrosc(projeto_id: str, request: Request):
    """Lista despesas de um projeto"""
    user = await get_current_user(request)
    despesas = await db.mrosc_despesas.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(1000)
    return [DespesaMROSC(**d) for d in despesas]

@mrosc_router.post("/projetos/{projeto_id}/despesas", response_model=DespesaMROSC)
async def create_despesa_mrosc(projeto_id: str, despesa_data: DespesaMROSCCreate, request: Request):
    """Adiciona uma despesa ao projeto"""
    user = await get_current_user(request)
    projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    despesa_id = f"desp_{uuid.uuid4().hex[:12]}"
    despesa_dict = despesa_data.model_dump()
    
    # Calcular média de orçamentos
    media = calcular_media_orcamentos(
        despesa_dict['orcamento_1'],
        despesa_dict['orcamento_2'],
        despesa_dict['orcamento_3']
    )
    
    valor_total = despesa_dict['quantidade'] * despesa_dict['valor_unitario']
    
    despesa_doc = {
        'despesa_id': despesa_id,
        'projeto_id': projeto_id,
        **despesa_dict,
        'media_orcamentos': media,
        'valor_total': round(valor_total, 2),
        'created_at': datetime.now(timezone.utc)
    }
    await db.mrosc_despesas.insert_one(despesa_doc)
    return DespesaMROSC(**despesa_doc)

@mrosc_router.delete("/projetos/{projeto_id}/despesas/{despesa_id}")
async def delete_despesa_mrosc(projeto_id: str, despesa_id: str, request: Request):
    """Remove uma despesa do projeto"""
    user = await get_current_user(request)
    result = await db.mrosc_despesas.delete_one({'despesa_id': despesa_id, 'projeto_id': projeto_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Despesa não encontrada")
    return {'message': 'Despesa excluída com sucesso'}

# ===== RESUMO ORÇAMENTÁRIO =====
@mrosc_router.get("/projetos/{projeto_id}/resumo")
async def get_resumo_orcamentario_mrosc(projeto_id: str, request: Request):
    """Retorna resumo orçamentário do projeto"""
    user = await get_current_user(request)
    projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Somar recursos humanos
    rhs = await db.mrosc_rh.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(100)
    total_rh = sum(rh.get('custo_total_projeto', 0) for rh in rhs)
    
    # Somar despesas
    despesas = await db.mrosc_despesas.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(1000)
    total_despesas = sum(d.get('valor_total', 0) for d in despesas)
    
    # Agrupar despesas por natureza
    despesas_por_natureza = {}
    for d in despesas:
        nat = d.get('natureza_despesa', 'OUTROS')
        if nat not in despesas_por_natureza:
            despesas_por_natureza[nat] = 0
        despesas_por_natureza[nat] += d.get('valor_total', 0)
    
    total_geral = total_rh + total_despesas
    
    return {
        'projeto': projeto,
        'resumo': {
            'total_recursos_humanos': round(total_rh, 2),
            'total_despesas': round(total_despesas, 2),
            'total_geral': round(total_geral, 2),
            'quantidade_rh': len(rhs),
            'quantidade_despesas': len(despesas)
        },
        'despesas_por_natureza': despesas_por_natureza,
        'diferenca_orcamento': round(projeto.get('valor_total', 0) - total_geral, 2)
    }

# ===== DOCUMENTOS/COMPROVANTES MROSC =====
UPLOAD_DIR = ROOT_DIR / "uploads" / "mrosc"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class DocumentoMROSCCreate(BaseModel):
    tipo_documento: str  # NOTA_FISCAL, RECIBO, CONTRATO, COMPROVANTE, OUTRO
    numero_documento: str
    data_documento: datetime
    valor: float
    despesa_id: Optional[str] = None
    observacoes: Optional[str] = None

@mrosc_router.get("/projetos/{projeto_id}/documentos")
async def get_documentos_mrosc(projeto_id: str, request: Request):
    """Lista todos os documentos de um projeto"""
    user = await get_current_user(request)
    projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    documentos = await db.mrosc_documentos.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(500)
    return documentos

@mrosc_router.post("/projetos/{projeto_id}/documentos/upload")
async def upload_documento_mrosc(
    projeto_id: str,
    request: Request,
    file: UploadFile = File(...),
    tipo_documento: str = Form("COMPROVANTE"),
    numero_documento: str = Form(""),
    data_documento: str = Form(""),
    valor: float = Form(0.0),
    despesa_id: str = Form(None),
    rh_id: str = Form(None),
    descricao: str = Form(""),
    observacoes: str = Form("")
):
    """Faz upload de um documento/comprovante (PDF, JPG, PNG) para o projeto MROSC"""
    user = await get_current_user(request)
    
    # Verifica se o projeto existe
    projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Tipos de arquivo permitidos
    extensoes_permitidas = {'.pdf', '.jpg', '.jpeg', '.png'}
    extensao = Path(file.filename).suffix.lower()
    
    if extensao not in extensoes_permitidas:
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo de arquivo não permitido. Permitidos: PDF, JPG, JPEG, PNG"
        )
    
    # Define o content-type baseado na extensão
    content_types = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png'
    }
    content_type = content_types.get(extensao, 'application/octet-stream')
    
    # Limite de 10MB
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Arquivo muito grande. Limite: 10MB")
    
    # Gera nome único para o arquivo
    documento_id = f"doc_{uuid.uuid4().hex[:12]}"
    safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', file.filename)
    arquivo_nome = f"{documento_id}_{safe_filename}"
    arquivo_path = UPLOAD_DIR / arquivo_nome
    
    # Salva o arquivo
    with open(arquivo_path, "wb") as f:
        f.write(contents)
    
    # Parseia a data do documento
    try:
        if data_documento:
            dt_documento = datetime.fromisoformat(data_documento.replace('Z', '+00:00'))
        else:
            dt_documento = datetime.now(timezone.utc)
    except:
        dt_documento = datetime.now(timezone.utc)
    
    # Cria o registro no banco
    documento_doc = {
        'documento_id': documento_id,
        'projeto_id': projeto_id,
        'despesa_id': despesa_id if despesa_id and despesa_id != "null" and despesa_id != "" else None,
        'rh_id': rh_id if rh_id and rh_id != "null" and rh_id != "" else None,
        'tipo_documento': tipo_documento,
        'numero_documento': numero_documento,
        'data_documento': dt_documento,
        'valor': valor if valor else 0.0,
        'arquivo_url': f"/api/mrosc/documentos/{documento_id}/download",
        'arquivo_nome': file.filename,
        'arquivo_tipo': content_type,
        'arquivo_tamanho': len(contents),
        'descricao': descricao,
        'validado': False,
        'validado_por': None,
        'data_validacao': None,
        'observacoes': observacoes,
        'created_at': datetime.now(timezone.utc)
    }
    
    await db.mrosc_documentos.insert_one(documento_doc)
    
    # Remove _id para retorno
    documento_doc.pop('_id', None)
    
    return documento_doc

@mrosc_router.get("/documentos/{documento_id}/download")
async def download_documento_mrosc(documento_id: str):
    """Faz download de um documento (PDF ou imagem)"""
    documento = await db.mrosc_documentos.find_one({'documento_id': documento_id}, {'_id': 0})
    if not documento:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    # Define o content-type
    content_type = documento.get('arquivo_tipo', 'application/pdf')
    
    # Procura o arquivo
    for file in UPLOAD_DIR.iterdir():
        if file.name.startswith(documento_id):
            return StreamingResponse(
                open(file, "rb"),
                media_type=content_type,
                headers={
                    "Content-Disposition": f"inline; filename=\"{documento['arquivo_nome']}\""
                }
            )
    
    raise HTTPException(status_code=404, detail="Arquivo não encontrado")

@mrosc_router.delete("/projetos/{projeto_id}/documentos/{documento_id}")
async def delete_documento_mrosc(projeto_id: str, documento_id: str, request: Request):
    """Remove um documento do projeto"""
    user = await get_current_user(request)
    
    documento = await db.mrosc_documentos.find_one({'documento_id': documento_id, 'projeto_id': projeto_id}, {'_id': 0})
    if not documento:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    # Remove o arquivo físico
    for file in UPLOAD_DIR.iterdir():
        if file.name.startswith(documento_id):
            file.unlink()
            break
    
    # Remove do banco
    await db.mrosc_documentos.delete_one({'documento_id': documento_id})
    
    return {'message': 'Documento excluído com sucesso'}

@mrosc_router.put("/projetos/{projeto_id}/documentos/{documento_id}/validar")
async def validar_documento_mrosc(projeto_id: str, documento_id: str, request: Request):
    """Marca um documento como validado"""
    user = await get_current_user(request)
    
    documento = await db.mrosc_documentos.find_one({'documento_id': documento_id, 'projeto_id': projeto_id}, {'_id': 0})
    if not documento:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    await db.mrosc_documentos.update_one(
        {'documento_id': documento_id},
        {'$set': {
            'validado': True,
            'validado_por': user.name if hasattr(user, 'name') else user.get('name', 'Admin'),
            'data_validacao': datetime.now(timezone.utc)
        }}
    )
    
    return {'message': 'Documento validado com sucesso'}

# ===== WORKFLOW DE PRESTAÇÃO DE CONTAS MROSC =====

class SubmeterPrestacaoRequest(BaseModel):
    observacoes: Optional[str] = None

class PedidoCorrecaoRequest(BaseModel):
    motivo: str

class AprovarPrestacaoRequest(BaseModel):
    observacoes: Optional[str] = None

# ===== FUNÇÃO DE NOTIFICAÇÃO MROSC =====
def enviar_notificacao_mrosc(destinatario: str, assunto: str, projeto_nome: str, mensagem: str, acao: str):
    """Envia notificação por email sobre mudança de status no MROSC"""
    try:
        corpo_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #2E7D32; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">Prestação de Contas - MROSC</h1>
                <p style="margin: 5px 0 0 0; font-size: 14px;">Prefeitura Municipal de Acaiaca</p>
            </div>
            <div style="padding: 20px; background: #f5f5f5;">
                <h2 style="color: #1F4E78;">{assunto}</h2>
                <p><strong>Projeto:</strong> {projeto_nome}</p>
                <p>{mensagem}</p>
                <div style="background: white; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <p style="margin: 0; color: #666;"><strong>Ação:</strong> {acao}</p>
                </div>
                <p style="font-size: 12px; color: #888;">
                    Acesse o sistema para mais detalhes: <a href="https://acaiaca-gov-1.preview.emergentagent.com/prestacao-contas">Planejamento Acaiaca</a>
                </p>
            </div>
            <div style="background: #1F4E78; color: white; padding: 10px; text-align: center; font-size: 12px;">
                <p style="margin: 0;">CNPJ: 18.295.287/0001-90 | Lei 13.019/2014 - MROSC</p>
            </div>
        </body>
        </html>
        """
        enviar_email_smtp(destinatario, f"[MROSC] {assunto}", corpo_html)
        return True
    except Exception as e:
        logging.error(f"Erro ao enviar notificação MROSC: {e}")
        return False

@mrosc_router.post("/projetos/{projeto_id}/submeter")
async def submeter_prestacao_contas(projeto_id: str, request: Request, data: SubmeterPrestacaoRequest = None):
    """
    Usuário externo submete a prestação de contas para análise.
    Após submissão, não pode mais editar até que admin solicite correção.
    """
    user = await get_current_user(request)
    
    projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    if projeto.get('submetido') and not projeto.get('correcao_solicitada'):
        raise HTTPException(status_code=400, detail="Projeto já foi submetido e aguarda análise")
    
    user_name = user.name if hasattr(user, 'name') else user.get('name', 'Usuário')
    
    await db.mrosc_projetos.update_one(
        {'projeto_id': projeto_id},
        {'$set': {
            'submetido': True,
            'data_submissao': datetime.now(timezone.utc),
            'submetido_por': user_name,
            'pode_editar': False,  # Bloqueia edição
            'correcao_solicitada': False,  # Reseta se estava em correção
            'status': 'SUBMETIDO',
            'updated_at': datetime.now(timezone.utc)
        }}
    )
    
    # Notificar admins sobre nova submissão
    admins = await db.users.find({'is_admin': True}, {'_id': 0, 'email': 1}).to_list(50)
    for admin in admins:
        enviar_notificacao_mrosc(
            admin['email'],
            f"Nova Prestação de Contas Submetida",
            projeto.get('nome_projeto', ''),
            f"O usuário {user_name} submeteu a prestação de contas do projeto para análise.",
            "Acesse o sistema para receber e analisar a documentação."
        )
    
    return {'message': 'Prestação de contas submetida com sucesso! Aguarde análise do gestor.'}


@mrosc_router.post("/projetos/{projeto_id}/receber")
async def receber_prestacao_contas(projeto_id: str, request: Request):
    """
    Administrador recebe/confirma recebimento da prestação de contas.
    Muda status para EM_ANALISE.
    """
    user = await get_current_user(request)
    
    # Verificar se é admin
    user_is_admin = user.is_admin if hasattr(user, 'is_admin') else user.get('is_admin', False)
    if not user_is_admin:
        raise HTTPException(status_code=403, detail="Apenas administradores podem receber prestação de contas")
    
    projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    if not projeto.get('submetido'):
        raise HTTPException(status_code=400, detail="Projeto ainda não foi submetido")
    
    user_name = user.name if hasattr(user, 'name') else user.get('name', 'Admin')
    
    await db.mrosc_projetos.update_one(
        {'projeto_id': projeto_id},
        {'$set': {
            'status': 'EM_ANALISE',
            'recebido_por': user_name,
            'data_recebimento': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }}
    )
    
    return {'message': 'Prestação de contas recebida. Iniciando análise.'}


@mrosc_router.post("/projetos/{projeto_id}/solicitar-correcao")
async def solicitar_correcao_prestacao(projeto_id: str, request: Request, data: PedidoCorrecaoRequest):
    """
    Administrador solicita correção. Habilita edição para o usuário externo.
    """
    user = await get_current_user(request)
    
    user_is_admin = user.is_admin if hasattr(user, 'is_admin') else user.get('is_admin', False)
    if not user_is_admin:
        raise HTTPException(status_code=403, detail="Apenas administradores podem solicitar correção")
    
    projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    user_name = user.name if hasattr(user, 'name') else user.get('name', 'Admin')
    
    await db.mrosc_projetos.update_one(
        {'projeto_id': projeto_id},
        {'$set': {
            'correcao_solicitada': True,
            'data_correcao_solicitada': datetime.now(timezone.utc),
            'motivo_correcao': data.motivo,
            'solicitado_por': user_name,
            'pode_editar': True,  # Habilita edição novamente
            'status': 'CORRECAO_SOLICITADA',
            'updated_at': datetime.now(timezone.utc)
        }}
    )
    
    # Notificar criador do projeto sobre correção solicitada
    criador = await db.users.find_one({'user_id': projeto.get('user_id')}, {'_id': 0, 'email': 1, 'name': 1})
    if criador:
        enviar_notificacao_mrosc(
            criador['email'],
            f"Correção Solicitada em Prestação de Contas",
            projeto.get('nome_projeto', ''),
            f"O gestor {user_name} solicitou correções no seu projeto.<br><br><strong>Motivo:</strong> {data.motivo}",
            "Acesse o sistema para fazer as correções necessárias e resubmeter."
        )
    
    return {'message': 'Correção solicitada. O usuário externo pode editar novamente.'}


@mrosc_router.post("/projetos/{projeto_id}/aprovar")
async def aprovar_prestacao_contas(projeto_id: str, request: Request, data: AprovarPrestacaoRequest = None):
    """
    Administrador aprova a prestação de contas.
    """
    user = await get_current_user(request)
    
    user_is_admin = user.is_admin if hasattr(user, 'is_admin') else user.get('is_admin', False)
    if not user_is_admin:
        raise HTTPException(status_code=403, detail="Apenas administradores podem aprovar prestação de contas")
    
    projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    if not projeto.get('submetido'):
        raise HTTPException(status_code=400, detail="Projeto precisa ser submetido antes de aprovar")
    
    user_name = user.name if hasattr(user, 'name') else user.get('name', 'Admin')
    
    await db.mrosc_projetos.update_one(
        {'projeto_id': projeto_id},
        {'$set': {
            'aprovado': True,
            'data_aprovacao': datetime.now(timezone.utc),
            'aprovado_por': user_name,
            'observacoes_aprovacao': data.observacoes if data else None,
            'pode_editar': False,
            'correcao_solicitada': False,
            'status': 'APROVADO',
            'updated_at': datetime.now(timezone.utc)
        }}
    )
    
    # Notificar criador do projeto sobre aprovação
    criador = await db.users.find_one({'user_id': projeto.get('user_id')}, {'_id': 0, 'email': 1, 'name': 1})
    if criador:
        obs_msg = f"<br><br><strong>Observações:</strong> {data.observacoes}" if data and data.observacoes else ""
        enviar_notificacao_mrosc(
            criador['email'],
            f"🎉 Prestação de Contas APROVADA!",
            projeto.get('nome_projeto', ''),
            f"Parabéns! Sua prestação de contas foi aprovada pelo gestor {user_name}.{obs_msg}",
            "A prestação de contas foi concluída com sucesso."
        )
    
    return {'message': 'Prestação de contas aprovada com sucesso!'}


@mrosc_router.get("/projetos/{projeto_id}/historico")
async def get_historico_prestacao(projeto_id: str, request: Request):
    """
    Retorna o histórico de ações do workflow do projeto
    """
    user = await get_current_user(request)
    
    projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    historico = []
    
    if projeto.get('created_at'):
        historico.append({
            'acao': 'Projeto Criado',
            'data': projeto.get('created_at'),
            'usuario': None
        })
    
    if projeto.get('data_submissao'):
        historico.append({
            'acao': 'Submetido para Análise',
            'data': projeto.get('data_submissao'),
            'usuario': projeto.get('submetido_por')
        })
    
    if projeto.get('data_recebimento'):
        historico.append({
            'acao': 'Recebido pelo Gestor',
            'data': projeto.get('data_recebimento'),
            'usuario': projeto.get('recebido_por')
        })
    
    if projeto.get('data_correcao_solicitada'):
        historico.append({
            'acao': 'Correção Solicitada',
            'data': projeto.get('data_correcao_solicitada'),
            'usuario': projeto.get('solicitado_por'),
            'motivo': projeto.get('motivo_correcao')
        })
    
    if projeto.get('data_aprovacao'):
        historico.append({
            'acao': 'Aprovado',
            'data': projeto.get('data_aprovacao'),
            'usuario': projeto.get('aprovado_por'),
            'observacoes': projeto.get('observacoes_aprovacao')
        })
    
    # Ordenar por data
    historico.sort(key=lambda x: x.get('data') or datetime.min, reverse=True)
    
    return {
        'projeto_id': projeto_id,
        'status_atual': projeto.get('status'),
        'pode_editar': projeto.get('pode_editar', True),
        'historico': historico
    }


# ===== ASSINATURA DE DOCUMENTOS MROSC =====
@mrosc_router.post("/projetos/{projeto_id}/assinar")
async def assinar_documento_mrosc(projeto_id: str, signature_request: SignatureRequest, request: Request):
    """
    Endpoint para assinar documento MROSC com confirmação.
    
    Requer confirmação explícita e permite data retroativa/futura.
    
    Args:
        projeto_id: ID do projeto
        signature_request: Dados da assinatura (confirmar_assinatura, data_assinatura, observacoes)
    
    Returns:
        PDF assinado com a data especificada
    """
    user = await get_current_user(request)
    
    # Verificar se a confirmação foi dada
    if not signature_request.confirmar_assinatura:
        # Retornar informações para confirmação
        projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
        if not projeto:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        
        # Buscar dados de assinatura do usuário
        user_doc = await db.users.find_one({'user_id': user.user_id}, {'_id': 0})
        user_signature = user_doc.get('signature_data') or {} if user_doc else {}
        
        cpf = user_signature.get('cpf', '').strip()
        cargo = user_signature.get('cargo', '').strip()
        
        if not cpf or not cargo:
            return {
                "status": "DADOS_INCOMPLETOS",
                "message": "Para assinar documentos, você precisa preencher seu CPF e Cargo no perfil.",
                "cpf_preenchido": bool(cpf),
                "cargo_preenchido": bool(cargo),
                "redirect_to": "/perfil"
            }
        
        return {
            "status": "AGUARDANDO_CONFIRMACAO",
            "message": "Você está prestes a assinar digitalmente este documento. Esta ação é irreversível.",
            "projeto": {
                "id": projeto_id,
                "nome": projeto.get('nome_projeto'),
                "organizacao": projeto.get('organizacao_parceira'),
                "valor_total": projeto.get('valor_total')
            },
            "assinante": {
                "nome": user.name,
                "cpf_mascarado": mask_cpf(cpf),
                "cargo": cargo,
                "email": user.email
            },
            "data_sugerida": datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S'),
            "instrucoes": "Envie novamente com 'confirmar_assinatura': true e opcionalmente 'data_assinatura': 'DD/MM/YYYY HH:MM:SS' para assinar."
        }
    
    # Confirmar assinatura
    projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Buscar dados de assinatura do usuário
    user_doc = await db.users.find_one({'user_id': user.user_id}, {'_id': 0})
    user_signature = user_doc.get('signature_data') or {} if user_doc else {}
    
    cpf = user_signature.get('cpf', '').strip()
    cargo = user_signature.get('cargo', '').strip()
    
    if not cpf:
        raise HTTPException(
            status_code=400, 
            detail="CPF é obrigatório para assinar documentos. Por favor, atualize seu perfil."
        )
    
    if not cargo:
        raise HTTPException(
            status_code=400, 
            detail="Cargo é obrigatório para assinar documentos. Por favor, atualize seu perfil."
        )
    
    # Validar formato da data se fornecida
    signature_date = signature_request.data_assinatura
    if signature_date:
        try:
            # Validar formato DD/MM/YYYY HH:MM:SS
            datetime.strptime(signature_date, '%d/%m/%Y %H:%M:%S')
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Formato de data inválido. Use: DD/MM/YYYY HH:MM:SS"
            )
    
    return {
        "status": "ASSINATURA_CONFIRMADA",
        "message": "Use os endpoints de PDF para gerar o documento assinado.",
        "projeto_id": projeto_id,
        "data_assinatura": signature_date or datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S'),
        "assinante": user.name,
        "endpoints": {
            "pdf_simples": f"/api/mrosc/projetos/{projeto_id}/relatorio/pdf?assinar=true&data={signature_date or ''}",
            "pdf_consolidado": f"/api/mrosc/projetos/{projeto_id}/relatorio/consolidado/pdf?assinar=true&data={signature_date or ''}"
        }
    }

# ===== RELATÓRIO PDF DE PRESTAÇÃO DE CONTAS MROSC =====
@mrosc_router.get("/projetos/{projeto_id}/relatorio/pdf")
async def export_relatorio_mrosc_pdf(projeto_id: str, request: Request, assinar: bool = False, data: str = None):
    """
    Gera relatório PDF consolidado de prestação de contas conforme MROSC (Lei 13.019/2014)
    Inclui: dados do projeto, recursos humanos, despesas e documentos anexados
    """
    user = await get_current_user(request)
    
    # Buscar dados do projeto
    projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Buscar RH, despesas e documentos
    rhs = await db.mrosc_rh.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(100)
    despesas = await db.mrosc_despesas.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(1000)
    documentos = await db.mrosc_documentos.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(500)
    
    # Calcular totais
    total_rh = sum(rh.get('custo_total_projeto', 0) for rh in rhs)
    total_despesas = sum(d.get('valor_total', 0) for d in despesas)
    total_geral = total_rh + total_despesas
    total_docs_valor = sum(d.get('valor', 0) for d in documentos)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20*mm,
        rightMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
        title=f'Prestação de Contas - {projeto["nome_projeto"]}'
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilos customizados
    titulo_style = ParagraphStyle(
        'TituloMROSC',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1F4E78'),
        alignment=TA_CENTER,
        spaceAfter=6*mm
    )
    
    subtitulo_style = ParagraphStyle(
        'SubtituloMROSC',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#2E7D32'),
        spaceBefore=8*mm,
        spaceAfter=4*mm
    )
    
    normal_style = ParagraphStyle(
        'NormalMROSC',
        parent=styles['Normal'],
        fontSize=9,
        leading=12
    )
    
    # ===== CABEÇALHO =====
    elements.append(Paragraph('PREFEITURA MUNICIPAL DE ACAIACA - MG', titulo_style))
    elements.append(Paragraph('CNPJ: 18.295.287/0001-90', ParagraphStyle('CNPJ', parent=styles['Normal'], alignment=TA_CENTER, fontSize=9)))
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph('<b>RELATÓRIO DE PRESTAÇÃO DE CONTAS</b>', ParagraphStyle('RelTitulo', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=14, textColor=colors.HexColor('#2E7D32'))))
    elements.append(Paragraph('Lei 13.019/2014 - Marco Regulatório das Organizações da Sociedade Civil (MROSC)', ParagraphStyle('Lei', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8, textColor=colors.gray)))
    elements.append(Spacer(1, 8*mm))
    
    # ===== DADOS DO PROJETO =====
    elements.append(Paragraph('1. IDENTIFICAÇÃO DO PROJETO', subtitulo_style))
    
    projeto_data = [
        ['Nome do Projeto:', projeto.get('nome_projeto', '-')],
        ['Objeto:', Paragraph(projeto.get('objeto', '-'), normal_style)],
        ['Organização Parceira (OSC):', projeto.get('organizacao_parceira', '-')],
        ['CNPJ da OSC:', projeto.get('cnpj_parceira', '-')],
        ['Responsável OSC:', projeto.get('responsavel_osc', '-')],
        ['Período:', f"{projeto.get('data_inicio').strftime('%d/%m/%Y') if projeto.get('data_inicio') else '-'} a {projeto.get('data_conclusao').strftime('%d/%m/%Y') if projeto.get('data_conclusao') else '-'}"],
        ['Prazo:', f"{projeto.get('prazo_meses', 0)} meses"],
        ['Status:', projeto.get('status', '-')]
    ]
    
    projeto_table = Table(projeto_data, colWidths=[50*mm, 120*mm])
    projeto_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F5E9')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#C8E6C9')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(projeto_table)
    
    # ===== RESUMO FINANCEIRO =====
    elements.append(Paragraph('2. RESUMO FINANCEIRO', subtitulo_style))
    
    financeiro_data = [
        ['Descrição', 'Valor (R$)'],
        ['Valor Total do Projeto', f"R$ {projeto.get('valor_total', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')],
        ['Repasse Público', f"R$ {projeto.get('valor_repasse_publico', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')],
        ['Contrapartida', f"R$ {projeto.get('valor_contrapartida', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')],
        ['Total Recursos Humanos', f"R$ {total_rh:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')],
        ['Total Despesas', f"R$ {total_despesas:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')],
        ['Total Executado', f"R$ {total_geral:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')],
        ['Saldo', f"R$ {(projeto.get('valor_total', 0) - total_geral):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')]
    ]
    
    fin_table = Table(financeiro_data, colWidths=[100*mm, 70*mm])
    fin_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BBDEFB')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E3F2FD')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(fin_table)
    
    # ===== RECURSOS HUMANOS =====
    if rhs:
        elements.append(Paragraph('3. RECURSOS HUMANOS', subtitulo_style))
        
        rh_header = ['Função', 'Regime', 'Salário', 'Encargos', 'Meses', 'Custo Total']
        rh_data = [rh_header]
        
        for rh in rhs:
            encargos = rh.get('provisao_ferias', 0) + rh.get('provisao_13_salario', 0) + rh.get('fgts', 0) + rh.get('inss_patronal', 0)
            rh_data.append([
                rh.get('nome_funcao', '-'),
                rh.get('regime_contratacao', '-'),
                f"R$ {rh.get('salario_bruto', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                f"R$ {encargos:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                str(rh.get('numero_meses', 0)),
                f"R$ {rh.get('custo_total_projeto', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            ])
        
        rh_table = Table(rh_data, colWidths=[45*mm, 20*mm, 30*mm, 30*mm, 15*mm, 30*mm])
        rh_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0D47A1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#90CAF9')),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#E3F2FD')]),
        ]))
        elements.append(rh_table)
    
    # ===== DESPESAS =====
    if despesas:
        elements.append(Paragraph('4. DESPESAS', subtitulo_style))
        
        desp_header = ['Natureza', 'Descrição', 'Qtd', 'Unit.', 'Total']
        desp_data = [desp_header]
        
        for d in despesas:
            desp_data.append([
                d.get('natureza_despesa', '-'),
                Paragraph(d.get('descricao', '-')[:50], ParagraphStyle('DescDesp', fontSize=7)),
                f"{d.get('quantidade', 0)} {d.get('unidade', '')}",
                f"R$ {d.get('valor_unitario', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                f"R$ {d.get('valor_total', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            ])
        
        desp_table = Table(desp_data, colWidths=[25*mm, 65*mm, 25*mm, 25*mm, 30*mm])
        desp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E65100')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#FFCC80')),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFF3E0')]),
        ]))
        elements.append(desp_table)
    
    # ===== DOCUMENTOS =====
    if documentos:
        elements.append(Paragraph('5. DOCUMENTOS COMPROBATÓRIOS', subtitulo_style))
        
        docs_header = ['Tipo', 'Número', 'Data', 'Valor', 'Status']
        docs_data = [docs_header]
        
        for documento in documentos:
            data_doc = documento.get('data_documento', None)
            if data_doc:
                if isinstance(data_doc, datetime):
                    data_doc = data_doc.strftime('%d/%m/%Y')
                else:
                    data_doc = str(data_doc)[:10]
            else:
                data_doc = '-'
            docs_data.append([
                documento.get('tipo_documento', '-'),
                documento.get('numero_documento', '-') or '-',
                data_doc,
                f"R$ {documento.get('valor', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                'Validado' if documento.get('validado') else 'Pendente'
            ])
        
        docs_table = Table(docs_data, colWidths=[35*mm, 40*mm, 30*mm, 35*mm, 30*mm])
        docs_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6A1B9A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CE93D8')),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F3E5F5')]),
        ]))
        elements.append(docs_table)
        
        elements.append(Spacer(1, 4*mm))
        elements.append(Paragraph(f"<b>Total de documentos:</b> {len(documentos)} | <b>Validados:</b> {len([d for d in documentos if d.get('validado')])} | <b>Valor comprovado:</b> R$ {total_docs_valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), normal_style))
    
    # ===== ASSINATURA =====
    elements.append(Spacer(1, 15*mm))
    elements.append(Paragraph('_' * 60, ParagraphStyle('Linha', alignment=TA_CENTER)))
    user_name = user.name if hasattr(user, 'name') else user.get('name', 'Responsável') if isinstance(user, dict) else 'Responsável'
    elements.append(Paragraph(f'<b>{user_name}</b>', ParagraphStyle('Assinatura', alignment=TA_CENTER, fontSize=10)))
    elements.append(Paragraph(f'Responsável pela Prestação de Contas', ParagraphStyle('Cargo', alignment=TA_CENTER, fontSize=8, textColor=colors.gray)))
    
    # ===== RODAPÉ =====
    elements.append(Spacer(1, 10*mm))
    data_geracao = datetime.now(timezone.utc).strftime('%d/%m/%Y às %H:%M')
    elements.append(Paragraph(f'Documento gerado em {data_geracao} | Planejamento Acaiaca © 2026', ParagraphStyle('Rodape', alignment=TA_CENTER, fontSize=7, textColor=colors.gray)))
    
    doc.build(elements)
    buffer.seek(0)
    
    # Adicionar assinatura digital ao PDF
    try:
        doc_info = {
            'tipo': 'PRESTAÇÃO DE CONTAS MROSC',
            'id': projeto_id,
            'titulo': f"Prestação de Contas - {projeto.get('nome_projeto', 'N/A')}"
        }
        signed_buffer, validation_code = await add_signature_to_pdf(
            buffer, 
            user, 
            'MROSC_PRESTACAO_CONTAS', 
            projeto_id,
            doc_info,
            data  # Data da assinatura (pode ser retroativa)
        )
        buffer = signed_buffer
        logging.info(f"PDF de prestação de contas MROSC assinado com código: {validation_code}")
    except HTTPException as e:
        # Se falhar por falta de dados de assinatura, retorna PDF sem assinatura
        logging.warning(f"PDF sem assinatura digital: {e.detail}")
    except Exception as e:
        logging.error(f"Erro ao adicionar assinatura ao PDF MROSC: {e}")
    
    filename = f"Prestacao_Contas_{projeto['nome_projeto'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return StreamingResponse(
        buffer,
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@mrosc_router.get("/projetos/{projeto_id}/relatorio/consolidado/pdf")
@mrosc_router.get("/projetos/{projeto_id}/relatorio/consolidado")
async def gerar_relatorio_consolidado_mrosc(projeto_id: str, request: Request, assinar: bool = False, data: str = None):
    """
    Gera relatório PDF consolidado com todos os anexos incorporados
    Inclui: dados do projeto, concedente, RH, despesas, histórico e documentos
    """
    from PyPDF2 import PdfMerger
    from PIL import Image as PILImage
    from reportlab.platypus import PageBreak
    
    user = await get_current_user(request)
    
    projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    rhs = await db.mrosc_rh.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(100)
    despesas = await db.mrosc_despesas.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(100)
    documentos = await db.mrosc_documentos.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(100)
    historico = await db.mrosc_historico.find({'projeto_id': projeto_id}, {'_id': 0}).sort('data', 1).to_list(100)
    
    total_rh = sum(rh.get('custo_total_projeto', 0) for rh in rhs)
    total_despesas = sum(d.get('valor_total', 0) for d in despesas)
    total_geral = total_rh + total_despesas
    
    # Create main PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#1F4E78'), alignment=TA_CENTER, spaceAfter=5)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#2E7D32'), spaceBefore=12, spaceAfter=6)
    
    # ===== CAPA =====
    elements.append(Spacer(1, 30*mm))
    elements.append(Paragraph("PREFEITURA MUNICIPAL DE ACAIACA", title_style))
    elements.append(Paragraph("Estado de Minas Gerais", ParagraphStyle('Estado', fontSize=10, alignment=TA_CENTER)))
    elements.append(Spacer(1, 20*mm))
    elements.append(Paragraph("PRESTAÇÃO DE CONTAS CONSOLIDADA", ParagraphStyle('TitDoc', fontSize=18, alignment=TA_CENTER, textColor=colors.HexColor('#2E7D32'))))
    elements.append(Paragraph("MROSC - Lei 13.019/2014", ParagraphStyle('Lei', fontSize=12, alignment=TA_CENTER, textColor=colors.gray)))
    elements.append(Spacer(1, 15*mm))
    elements.append(Paragraph(f"<b>{projeto.get('nome_projeto', 'N/A')}</b>", ParagraphStyle('NomeProjeto', fontSize=14, alignment=TA_CENTER)))
    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph(f"Organização: {projeto.get('organizacao_parceira', 'N/A')}", ParagraphStyle('Org', fontSize=11, alignment=TA_CENTER)))
    elements.append(Paragraph(f"CNPJ: {projeto.get('cnpj_parceira', 'N/A')}", ParagraphStyle('CNPJ', fontSize=10, alignment=TA_CENTER)))
    elements.append(Spacer(1, 30*mm))
    elements.append(Paragraph(f"VALOR TOTAL: R$ {total_geral:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), ParagraphStyle('Valor', fontSize=14, alignment=TA_CENTER, textColor=colors.HexColor('#1F4E78'))))
    elements.append(Spacer(1, 20*mm))
    elements.append(Paragraph(f"Acaiaca - MG, {datetime.now(timezone.utc).strftime('%d/%m/%Y')}", ParagraphStyle('Data', fontSize=10, alignment=TA_CENTER)))
    elements.append(PageBreak())
    
    # ===== 1. DADOS DO PROJETO =====
    elements.append(Paragraph("1. DADOS DO PROJETO", section_style))
    
    projeto_data = [
        ['Campo', 'Valor'],
        ['Nome do Projeto', projeto.get('nome_projeto', 'N/A')],
        ['Objeto', str(projeto.get('objeto', projeto.get('objeto_detalhado', 'N/A')))[:100]],
        ['Organização Parceira', projeto.get('organizacao_parceira', 'N/A')],
        ['CNPJ da Parceira', projeto.get('cnpj_parceira', 'N/A')],
        ['Responsável OSC', projeto.get('responsavel_osc', 'N/A')],
        ['Valor Repasse Público', f"R$ {projeto.get('valor_repasse_publico', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')],
        ['Valor Contrapartida', f"R$ {projeto.get('valor_contrapartida', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')],
        ['Status', projeto.get('status', 'ELABORACAO')]
    ]
    
    projeto_table = Table(projeto_data, colWidths=[120, 340])
    projeto_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(projeto_table)
    
    # ===== 2. RECURSOS HUMANOS =====
    elements.append(Paragraph("2. RECURSOS HUMANOS", section_style))
    
    if rhs:
        rh_table_data = [['#', 'Função', 'Regime', 'Salário Bruto', 'Custo Mensal', 'Meses', 'Custo Total']]
        
        for i, rh in enumerate(rhs, 1):
            rh_table_data.append([
                str(i),
                rh.get('nome_funcao', '')[:25],
                rh.get('regime_contratacao', '')[:10],
                f"R$ {rh.get('salario_bruto', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                f"R$ {rh.get('custo_mensal_total', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                str(rh.get('numero_meses', '')),
                f"R$ {rh.get('custo_total_projeto', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            ])
        
        rh_table_data.append(['', '', '', '', '', 'TOTAL:', f"R$ {total_rh:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')])
        
        rh_table = Table(rh_table_data, colWidths=[20, 90, 50, 70, 70, 35, 80])
        rh_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E3F2FD')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(rh_table)
    else:
        elements.append(Paragraph("Nenhum recurso humano cadastrado.", ParagraphStyle('Empty', fontSize=10, textColor=colors.gray)))
    
    # ===== 3. DESPESAS =====
    elements.append(Paragraph("3. DESPESAS", section_style))
    
    if despesas:
        desp_table_data = [['#', 'Item', 'Natureza', 'Qtd', 'V.Unit', 'V.Total']]
        
        for i, d in enumerate(despesas, 1):
            desp_table_data.append([
                str(i),
                d.get('item_despesa', '')[:30],
                d.get('natureza_despesa', '')[:8],
                str(d.get('quantidade', 0)),
                f"R$ {d.get('valor_unitario', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                f"R$ {d.get('valor_total', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            ])
        
        desp_table_data.append(['', '', '', '', 'TOTAL:', f"R$ {total_despesas:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')])
        
        desp_table = Table(desp_table_data, colWidths=[20, 150, 50, 40, 70, 80])
        desp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8F5E9')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(desp_table)
    else:
        elements.append(Paragraph("Nenhuma despesa cadastrada.", ParagraphStyle('Empty', fontSize=10, textColor=colors.gray)))
    
    # ===== 4. RESUMO FINANCEIRO =====
    elements.append(Paragraph("4. RESUMO FINANCEIRO", section_style))
    
    resumo_data = [
        ['Categoria', 'Valor'],
        ['Total Recursos Humanos', f"R$ {total_rh:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')],
        ['Total Despesas', f"R$ {total_despesas:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')],
        ['TOTAL GERAL', f"R$ {total_geral:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')],
    ]
    
    resumo_table = Table(resumo_data, colWidths=[200, 150])
    resumo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6F00')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFF3E0')),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(resumo_table)
    
    # ===== 5. DOCUMENTOS ANEXADOS =====
    elements.append(Paragraph("5. DOCUMENTOS ANEXADOS", section_style))
    
    if documentos:
        doc_table_data = [['#', 'Tipo', 'Número', 'Valor', 'Validado']]
        
        for i, documento in enumerate(documentos, 1):
            doc_table_data.append([
                str(i),
                documento.get('tipo_documento', '')[:20],
                documento.get('numero_documento', '')[:20],
                f"R$ {documento.get('valor', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if documento.get('valor') else '-',
                '✓' if documento.get('validado') else '✗'
            ])
        
        doc_list_table = Table(doc_table_data, colWidths=[25, 100, 100, 70, 45])
        doc_list_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7B1FA2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(doc_list_table)
        elements.append(Spacer(1, 5))
        elements.append(Paragraph("<i>Os documentos originais estão anexados nas páginas seguintes.</i>", ParagraphStyle('Nota', fontSize=8, textColor=colors.gray)))
    else:
        elements.append(Paragraph("Nenhum documento anexado.", ParagraphStyle('Empty', fontSize=10, textColor=colors.gray)))
    
    # ===== FOOTER =====
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("_" * 60, ParagraphStyle('Linha', alignment=TA_CENTER)))
    elements.append(Paragraph("Documento gerado automaticamente pelo Sistema Planejamento Acaiaca", ParagraphStyle('Footer', fontSize=8, alignment=TA_CENTER, textColor=colors.gray)))
    elements.append(Paragraph(f"Data: {datetime.now(timezone.utc).strftime('%d/%m/%Y às %H:%M:%S')}", ParagraphStyle('Footer2', fontSize=8, alignment=TA_CENTER, textColor=colors.gray)))
    
    # Build main PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Merge with attachments
    merger = PdfMerger()
    merger.append(buffer)
    
    upload_dir = Path('/app/backend/uploads/mrosc')
    
    for documento in documentos:
        doc_id = documento.get('documento_id')
        arquivo_nome = documento.get('arquivo_nome', '')
        ext = arquivo_nome.split('.')[-1].lower() if '.' in arquivo_nome else ''
        
        filepath = upload_dir / projeto_id / f"{doc_id}.{ext}"
        
        if filepath.exists():
            try:
                if ext == 'pdf':
                    merger.append(str(filepath))
                elif ext in ['jpg', 'jpeg', 'png']:
                    # Convert image to PDF
                    img = PILImage.open(filepath)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    
                    max_width = 1800
                    if img.width > max_width:
                        ratio = max_width / img.width
                        new_size = (int(img.width * ratio), int(img.height * ratio))
                        img = img.resize(new_size, PILImage.Resampling.LANCZOS)
                    
                    img_pdf = BytesIO()
                    img.save(img_pdf, format='PDF', resolution=100.0)
                    img_pdf.seek(0)
                    merger.append(img_pdf)
            except Exception as e:
                logging.error(f"Erro ao processar anexo {doc_id}: {e}")
                continue
    
    final_buffer = BytesIO()
    merger.write(final_buffer)
    merger.close()
    final_buffer.seek(0)
    
    # Adicionar assinatura digital ao PDF consolidado
    try:
        doc_info = {
            'tipo': 'RELATÓRIO CONSOLIDADO MROSC',
            'id': projeto_id,
            'titulo': f"Relatório Consolidado - {projeto.get('nome_projeto', 'N/A')}"
        }
        signed_buffer, validation_code = await add_signature_to_pdf(
            final_buffer, 
            user, 
            'MROSC_CONSOLIDADO', 
            projeto_id,
            doc_info,
            data  # Data da assinatura (pode ser retroativa)
        )
        final_buffer = signed_buffer
        logging.info(f"PDF consolidado MROSC assinado com código: {validation_code}")
    except HTTPException as e:
        # Se falhar por falta de dados de assinatura, retorna PDF sem assinatura
        logging.warning(f"PDF consolidado sem assinatura digital: {e.detail}")
    except Exception as e:
        logging.error(f"Erro ao adicionar assinatura ao PDF consolidado MROSC: {e}")
    
    filename = f"MROSC_Consolidado_{projeto.get('nome_projeto', 'projeto')[:15].replace(' ', '_')}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"
    return StreamingResponse(
        final_buffer,
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


# Registrar router MROSC
app.include_router(mrosc_router)

# ===== DASHBOARD ANALÍTICO E SISTEMA DE ALERTAS =====
analytics_router = APIRouter(prefix="/api/analytics", tags=["Dashboard Analítico"])

@analytics_router.get("/dashboard")
async def get_dashboard_analytics(request: Request):
    """
    Dashboard analítico consolidado com métricas de todos os módulos
    """
    user = await get_current_user(request)
    
    # Estatísticas de PACs
    pacs = await db.pacs.find({}, {'_id': 0}).to_list(1000)
    pac_items = await db.pac_items.find({}, {'_id': 0}).to_list(10000)
    
    # Estatísticas de PACs Geral
    pacs_geral = await db.pacs_geral.find({}, {'_id': 0}).to_list(100)
    pac_geral_items = await db.pac_geral_items.find({}, {'_id': 0}).to_list(10000)
    
    # Estatísticas de PACs Obras
    pacs_obras = await db.pacs_geral_obras.find({}, {'_id': 0}).to_list(100)
    pac_obras_items = await db.pac_geral_obras_items.find({}, {'_id': 0}).to_list(10000)
    
    # Estatísticas de Processos
    processos = await db.processos.find({}, {'_id': 0}).to_list(1000)
    
    # Estatísticas de MROSC
    projetos_mrosc = await db.mrosc_projetos.find({}, {'_id': 0}).to_list(100)
    rh_mrosc = await db.mrosc_rh.find({}, {'_id': 0}).to_list(500)
    despesas_mrosc = await db.mrosc_despesas.find({}, {'_id': 0}).to_list(5000)
    docs_mrosc = await db.mrosc_documentos.find({}, {'_id': 0}).to_list(1000)
    
    # Cálculos
    total_pac = sum(item.get('valorTotal', 0) for item in pac_items)
    total_pac_geral = sum(item.get('valorTotal', 0) for item in pac_geral_items)
    total_pac_obras = sum(item.get('valorTotal', 0) for item in pac_obras_items)
    total_mrosc = sum(p.get('valor_total', 0) for p in projetos_mrosc)
    total_rh_mrosc = sum(rh.get('custo_total_projeto', 0) for rh in rh_mrosc)
    total_despesas_mrosc = sum(d.get('valor_total', 0) for d in despesas_mrosc)
    
    # Processos por status
    processos_por_status = {}
    for p in processos:
        status = p.get('status', 'Não Definido')
        processos_por_status[status] = processos_por_status.get(status, 0) + 1
    
    # Execução orçamentária MROSC
    execucao_mrosc = []
    for proj in projetos_mrosc:
        proj_id = proj.get('projeto_id')
        rh_proj = sum(r.get('custo_total_projeto', 0) for r in rh_mrosc if r.get('projeto_id') == proj_id)
        desp_proj = sum(d.get('valor_total', 0) for d in despesas_mrosc if d.get('projeto_id') == proj_id)
        docs_proj = len([d for d in docs_mrosc if d.get('projeto_id') == proj_id])
        total_exec = rh_proj + desp_proj
        percentual = (total_exec / proj.get('valor_total', 1)) * 100 if proj.get('valor_total') else 0
        execucao_mrosc.append({
            'projeto_id': proj_id,
            'nome': proj.get('nome_projeto', ''),
            'valor_total': proj.get('valor_total', 0),
            'executado': total_exec,
            'rh': rh_proj,
            'despesas': desp_proj,
            'documentos': docs_proj,
            'percentual': round(percentual, 1),
            'saldo': proj.get('valor_total', 0) - total_exec
        })
    
    # Top 5 itens por valor (PAC Geral)
    top_items = sorted(pac_geral_items, key=lambda x: x.get('valorTotal', 0), reverse=True)[:5]
    
    # Distribuição por secretaria
    distribuicao_secretarias = {}
    for item in pac_geral_items:
        for sec in ['AD', 'FA', 'SA', 'SE', 'AS', 'AG', 'OB', 'TR', 'CUL']:
            qtd = item.get(f'qtd_{sec.lower()}', 0)
            if qtd > 0:
                valor = qtd * item.get('valorUnitario', 0)
                if sec not in distribuicao_secretarias:
                    distribuicao_secretarias[sec] = {'quantidade': 0, 'valor': 0}
                distribuicao_secretarias[sec]['quantidade'] += qtd
                distribuicao_secretarias[sec]['valor'] += valor
    
    sec_labels = {
        'AD': 'Administração', 'FA': 'Fazenda', 'SA': 'Saúde', 'SE': 'Educação',
        'AS': 'Assist. Social', 'AG': 'Agricultura', 'OB': 'Obras', 'TR': 'Transporte', 'CUL': 'Cultura'
    }
    
    distribuicao_chart = [
        {'secretaria': sec_labels.get(k, k), 'codigo': k, 'valor': v['valor'], 'quantidade': v['quantidade']}
        for k, v in distribuicao_secretarias.items()
    ]
    distribuicao_chart.sort(key=lambda x: x['valor'], reverse=True)
    
    return {
        'resumo': {
            'total_geral': total_pac + total_pac_geral + total_pac_obras,
            'total_pac_individual': total_pac,
            'total_pac_geral': total_pac_geral,
            'total_pac_obras': total_pac_obras,
            'total_mrosc': total_mrosc,
            'total_executado_mrosc': total_rh_mrosc + total_despesas_mrosc
        },
        'contadores': {
            'pacs': len(pacs),
            'pacs_geral': len(pacs_geral),
            'pacs_obras': len(pacs_obras),
            'itens_pac': len(pac_items),
            'itens_pac_geral': len(pac_geral_items),
            'itens_pac_obras': len(pac_obras_items),
            'processos': len(processos),
            'projetos_mrosc': len(projetos_mrosc),
            'funcionarios_mrosc': len(rh_mrosc),
            'despesas_mrosc': len(despesas_mrosc),
            'documentos_mrosc': len(docs_mrosc)
        },
        'processos_por_status': [
            {'status': k, 'quantidade': v} for k, v in processos_por_status.items()
        ],
        'execucao_mrosc': execucao_mrosc,
        'top_itens': [
            {'descricao': i.get('descricao', '')[:50], 'valor': i.get('valorTotal', 0), 'catmat': i.get('catmat', '')}
            for i in top_items
        ],
        'distribuicao_secretarias': distribuicao_chart
    }


@analytics_router.get("/realtime")
async def get_realtime_metrics(request: Request):
    """
    Métricas em tempo real para monitoramento do sistema
    Inclui: uso por secretaria, horários de pico, tendências de gastos
    """
    user = await get_current_user(request)
    
    from datetime import timedelta
    from collections import defaultdict
    
    hoje = datetime.now(timezone.utc)
    inicio_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    
    # ===== USO POR SECRETARIA =====
    pacs = await db.pacs.find({}, {'_id': 0}).to_list(1000)
    processos = await db.processos.find({}, {'_id': 0}).to_list(1000)
    
    uso_secretaria = defaultdict(lambda: {'pacs': 0, 'processos': 0, 'valor_total': 0, 'ultimo_acesso': None})
    
    for pac in pacs:
        sec = pac.get('secretaria', 'Não Definida')
        uso_secretaria[sec]['pacs'] += 1
        created = pac.get('created_at') or pac.get('updated_at')
        if created and (not uso_secretaria[sec]['ultimo_acesso'] or created > uso_secretaria[sec]['ultimo_acesso']):
            uso_secretaria[sec]['ultimo_acesso'] = created
    
    for proc in processos:
        sec = proc.get('secretaria', 'Não Definida')
        uso_secretaria[sec]['processos'] += 1
    
    # Calcular valores por secretaria
    pac_items = await db.pac_items.find({}, {'_id': 0}).to_list(10000)
    pac_lookup = {p['pac_id']: p.get('secretaria', 'Não Definida') for p in pacs}
    
    for item in pac_items:
        sec = pac_lookup.get(item.get('pac_id'), 'Não Definida')
        uso_secretaria[sec]['valor_total'] += item.get('valorTotal', 0)
    
    uso_secretaria_list = []
    for sec, data in uso_secretaria.items():
        ultimo = data['ultimo_acesso']
        if isinstance(ultimo, datetime):
            ultimo = ultimo.isoformat()
        uso_secretaria_list.append({
            'secretaria': sec,
            'pacs': data['pacs'],
            'processos': data['processos'],
            'valor_total': data['valor_total'],
            'ultimo_acesso': ultimo
        })
    uso_secretaria_list.sort(key=lambda x: x['valor_total'], reverse=True)
    
    # ===== ATIVIDADE POR HORÁRIO (últimos 7 dias) =====
    atividade_horario = [0] * 24
    
    # Buscar documentos criados nos últimos 7 dias
    sete_dias_atras = hoje - timedelta(days=7)
    
    async def count_by_hour(collection, date_field='created_at'):
        docs = await collection.find({
            date_field: {'$gte': sete_dias_atras}
        }, {'_id': 0, date_field: 1}).to_list(10000)
        
        for doc in docs:
            dt = doc.get(date_field)
            if isinstance(dt, datetime):
                atividade_horario[dt.hour] += 1
    
    await count_by_hour(db.pacs)
    await count_by_hour(db.processos)
    await count_by_hour(db.mrosc_projetos)
    await count_by_hour(db.pac_items)
    
    atividade_horario_data = [
        {'hora': f'{h:02d}:00', 'atividade': atividade_horario[h]}
        for h in range(24)
    ]
    
    # ===== TENDÊNCIA DE GASTOS (últimos 6 meses) =====
    tendencia_gastos = []
    
    for i in range(6, 0, -1):
        mes = hoje - timedelta(days=i*30)
        mes_inicio = mes.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        mes_fim = (mes_inicio + timedelta(days=32)).replace(day=1)
        
        # PAC items criados nesse mês
        items_mes = await db.pac_items.find({
            'created_at': {'$gte': mes_inicio, '$lt': mes_fim}
        }, {'valorTotal': 1, '_id': 0}).to_list(10000)
        
        valor_mes = sum(i.get('valorTotal', 0) for i in items_mes)
        
        tendencia_gastos.append({
            'mes': mes_inicio.strftime('%b/%Y'),
            'valor': valor_mes,
            'quantidade': len(items_mes)
        })
    
    # ===== MÉTRICAS DE DESEMPENHO =====
    total_usuarios = await db.users.count_documents({})
    usuarios_ativos = await db.users.count_documents({'is_active': True})
    
    # Documentos criados hoje
    inicio_hoje = hoje.replace(hour=0, minute=0, second=0, microsecond=0)
    docs_hoje = {
        'pacs': await db.pacs.count_documents({'created_at': {'$gte': inicio_hoje}}),
        'processos': await db.processos.count_documents({'created_at': {'$gte': inicio_hoje}}),
        'pac_items': await db.pac_items.count_documents({'created_at': {'$gte': inicio_hoje}}),
        'mrosc': await db.mrosc_projetos.count_documents({'created_at': {'$gte': inicio_hoje}})
    }
    
    # Documentos criados esta semana
    docs_semana = {
        'pacs': await db.pacs.count_documents({'created_at': {'$gte': inicio_semana}}),
        'processos': await db.processos.count_documents({'created_at': {'$gte': inicio_semana}}),
        'pac_items': await db.pac_items.count_documents({'created_at': {'$gte': inicio_semana}}),
        'mrosc': await db.mrosc_projetos.count_documents({'created_at': {'$gte': inicio_semana}})
    }
    
    # ===== STATUS DOS MÓDULOS =====
    status_modulos = {
        'PAC Individual': {
            'total': len(pacs),
            'itens': len(pac_items),
            'status': 'online'
        },
        'PAC Geral': {
            'total': await db.pacs_geral.count_documents({}),
            'itens': await db.pac_geral_items.count_documents({}),
            'status': 'online'
        },
        'PAC Obras': {
            'total': await db.pacs_geral_obras.count_documents({}),
            'itens': await db.pac_obras_items.count_documents({}),
            'status': 'online'
        },
        'Processos': {
            'total': len(processos),
            'status': 'online'
        },
        'MROSC': {
            'total': await db.mrosc_projetos.count_documents({}),
            'documentos': await db.mrosc_documentos.count_documents({}),
            'status': 'online'
        },
        'DOEM': {
            'total': await db.doem_edicoes.count_documents({}),
            'status': 'online'
        }
    }
    
    # ===== TOP USUÁRIOS ATIVOS (por documentos criados) =====
    top_usuarios = []
    users = await db.users.find({'is_active': True}, {'_id': 0, 'user_id': 1, 'name': 1, 'email': 1}).to_list(100)
    
    for usr in users:
        uid = usr.get('user_id')
        count = await db.pacs.count_documents({'user_id': uid})
        count += await db.processos.count_documents({'user_id': uid})
        count += await db.mrosc_projetos.count_documents({'user_id': uid})
        if count > 0:
            top_usuarios.append({
                'user_id': uid,
                'name': usr.get('name', 'N/A'),
                'email': usr.get('email', ''),
                'documentos': count
            })
    
    top_usuarios.sort(key=lambda x: x['documentos'], reverse=True)
    top_usuarios = top_usuarios[:10]
    
    return {
        'timestamp': hoje.isoformat(),
        'uso_por_secretaria': uso_secretaria_list,
        'atividade_por_horario': atividade_horario_data,
        'tendencia_gastos': tendencia_gastos,
        'metricas_desempenho': {
            'usuarios_totais': total_usuarios,
            'usuarios_ativos': usuarios_ativos,
            'documentos_hoje': docs_hoje,
            'documentos_semana': docs_semana
        },
        'status_modulos': status_modulos,
        'top_usuarios': top_usuarios,
        'horario_pico': max(atividade_horario_data, key=lambda x: x['atividade']) if any(a['atividade'] for a in atividade_horario_data) else {'hora': '09:00', 'atividade': 0}
    }


# ===== SISTEMA DE ALERTAS =====
alertas_router = APIRouter(prefix="/api/alertas", tags=["Sistema de Alertas"])

class AlertaCreate(BaseModel):
    tipo: str  # PRAZO, DOCUMENTO, CONTRATO, PRESTACAO_CONTAS, SISTEMA
    titulo: str
    mensagem: str
    prioridade: str = "MEDIA"  # BAIXA, MEDIA, ALTA, CRITICA
    modulo: str  # PAC, MROSC, PROCESSO, DOEM
    referencia_id: Optional[str] = None
    data_vencimento: Optional[datetime] = None

@alertas_router.get("/")
async def get_alertas(request: Request):
    """
    Lista todos os alertas ativos do sistema, incluindo alertas automáticos
    """
    user = await get_current_user(request)
    
    alertas = []
    hoje = datetime.now(timezone.utc)
    
    # ===== ALERTAS DE MROSC =====
    projetos_mrosc = await db.mrosc_projetos.find({}, {'_id': 0}).to_list(100)
    docs_mrosc = await db.mrosc_documentos.find({}, {'_id': 0}).to_list(1000)
    
    for proj in projetos_mrosc:
        # Alerta de prazo do projeto
        data_conclusao = proj.get('data_conclusao')
        if data_conclusao:
            if isinstance(data_conclusao, str):
                try:
                    data_conclusao = datetime.fromisoformat(data_conclusao.replace('Z', '+00:00'))
                except:
                    continue
            
            # Garantir que a data tem timezone
            if data_conclusao.tzinfo is None:
                data_conclusao = data_conclusao.replace(tzinfo=timezone.utc)
            
            dias_restantes = (data_conclusao - hoje).days
            
            if dias_restantes < 0:
                alertas.append({
                    'tipo': 'PRAZO',
                    'titulo': 'Projeto MROSC Vencido',
                    'mensagem': f'O projeto "{proj.get("nome_projeto")}" está vencido há {abs(dias_restantes)} dias.',
                    'prioridade': 'CRITICA',
                    'modulo': 'MROSC',
                    'referencia_id': proj.get('projeto_id'),
                    'data_vencimento': data_conclusao.isoformat() if isinstance(data_conclusao, datetime) else data_conclusao,
                    'dias_restantes': dias_restantes
                })
            elif dias_restantes <= 30:
                alertas.append({
                    'tipo': 'PRAZO',
                    'titulo': 'Prazo de Projeto MROSC',
                    'mensagem': f'O projeto "{proj.get("nome_projeto")}" vence em {dias_restantes} dias.',
                    'prioridade': 'ALTA' if dias_restantes <= 7 else 'MEDIA',
                    'modulo': 'MROSC',
                    'referencia_id': proj.get('projeto_id'),
                    'data_vencimento': data_conclusao.isoformat() if isinstance(data_conclusao, datetime) else data_conclusao,
                    'dias_restantes': dias_restantes
                })
        
        # Alerta de documentos pendentes de validação
        docs_pendentes = [d for d in docs_mrosc if d.get('projeto_id') == proj.get('projeto_id') and not d.get('validado')]
        if len(docs_pendentes) > 0:
            alertas.append({
                'tipo': 'DOCUMENTO',
                'titulo': 'Documentos Pendentes de Validação',
                'mensagem': f'{len(docs_pendentes)} documento(s) do projeto "{proj.get("nome_projeto")}" aguardam validação.',
                'prioridade': 'MEDIA',
                'modulo': 'MROSC',
                'referencia_id': proj.get('projeto_id'),
                'quantidade': len(docs_pendentes)
            })
    
    # ===== ALERTAS DE PROCESSOS =====
    processos = await db.processos.find({}, {'_id': 0}).to_list(1000)
    
    for proc in processos:
        # Alerta de processos sem número
        if not proc.get('numero_processo'):
            alertas.append({
                'tipo': 'SISTEMA',
                'titulo': 'Processo sem Número',
                'mensagem': f'O processo "{proc.get("objeto", "")[:50]}" não possui número de processo.',
                'prioridade': 'BAIXA',
                'modulo': 'PROCESSO',
                'referencia_id': proc.get('processo_id')
            })
        
        # Alerta de prazo de processo
        data_abertura = proc.get('data_abertura')
        if data_abertura and proc.get('status') not in ['Concluído', 'Cancelado', 'Homologado']:
            if isinstance(data_abertura, str):
                try:
                    data_abertura = datetime.fromisoformat(data_abertura.replace('Z', '+00:00'))
                except:
                    continue
            
            # Garantir que a data tem timezone
            if data_abertura.tzinfo is None:
                data_abertura = data_abertura.replace(tzinfo=timezone.utc)
            
            dias_aberto = (hoje - data_abertura).days
            if dias_aberto > 90:
                alertas.append({
                    'tipo': 'PRAZO',
                    'titulo': 'Processo Aberto há Muito Tempo',
                    'mensagem': f'O processo "{proc.get("objeto", "")[:40]}" está aberto há {dias_aberto} dias.',
                    'prioridade': 'MEDIA' if dias_aberto < 180 else 'ALTA',
                    'modulo': 'PROCESSO',
                    'referencia_id': proc.get('processo_id'),
                    'dias_aberto': dias_aberto
                })
    
    # ===== ALERTAS DE DOEM =====
    edicoes = await db.doem_edicoes.find({'status': {'$ne': 'PUBLICADA'}}, {'_id': 0}).to_list(50)
    
    for edicao in edicoes:
        if edicao.get('status') == 'RASCUNHO':
            alertas.append({
                'tipo': 'DOCUMENTO',
                'titulo': 'Edição do DOEM em Rascunho',
                'mensagem': f'A edição {edicao.get("numero_edicao", "")} do DOEM está em rascunho.',
                'prioridade': 'BAIXA',
                'modulo': 'DOEM',
                'referencia_id': edicao.get('edicao_id')
            })
    
    # Ordenar por prioridade
    prioridade_ordem = {'CRITICA': 0, 'ALTA': 1, 'MEDIA': 2, 'BAIXA': 3}
    alertas.sort(key=lambda x: prioridade_ordem.get(x.get('prioridade', 'MEDIA'), 2))
    
    return {
        'total': len(alertas),
        'criticos': len([a for a in alertas if a.get('prioridade') == 'CRITICA']),
        'altos': len([a for a in alertas if a.get('prioridade') == 'ALTA']),
        'medios': len([a for a in alertas if a.get('prioridade') == 'MEDIA']),
        'baixos': len([a for a in alertas if a.get('prioridade') == 'BAIXA']),
        'alertas': alertas
    }


@alertas_router.get("/resumo")
async def get_alertas_resumo(request: Request):
    """Resumo rápido de alertas para exibição no header"""
    user = await get_current_user(request)
    alertas = await get_alertas(request)
    
    return {
        'total': alertas['total'],
        'criticos': alertas['criticos'],
        'altos': alertas['altos'],
        'tem_alertas_urgentes': alertas['criticos'] > 0 or alertas['altos'] > 0
    }


# ===== RELATÓRIOS GERENCIAIS CONSOLIDADOS =====
relatorios_router = APIRouter(prefix="/api/relatorios", tags=["Relatórios Gerenciais"])

@relatorios_router.get("/consolidado/pdf")
async def export_relatorio_consolidado_pdf(request: Request):
    """
    Gera relatório PDF consolidado de todos os módulos do sistema
    """
    user = await get_current_user(request)
    
    # Verificar se é admin
    user_is_admin = user.is_admin if hasattr(user, 'is_admin') else user.get('is_admin', False)
    if not user_is_admin:
        raise HTTPException(status_code=403, detail="Apenas administradores podem gerar relatórios consolidados")
    
    # Buscar dados de todos os módulos
    pacs = await db.pacs.find({}, {'_id': 0}).to_list(100)
    pac_items = await db.pac_items.find({}, {'_id': 0}).to_list(10000)
    pacs_geral = await db.pacs_geral.find({}, {'_id': 0}).to_list(50)
    pac_geral_items = await db.pac_geral_items.find({}, {'_id': 0}).to_list(10000)
    pacs_obras = await db.pacs_geral_obras.find({}, {'_id': 0}).to_list(50)
    pac_obras_items = await db.pac_geral_obras_items.find({}, {'_id': 0}).to_list(10000)
    processos = await db.processos.find({}, {'_id': 0}).to_list(1000)
    projetos_mrosc = await db.mrosc_projetos.find({}, {'_id': 0}).to_list(100)
    
    # Cálculos
    total_pac = sum(i.get('valorTotal', 0) for i in pac_items)
    total_pac_geral = sum(i.get('valorTotal', 0) for i in pac_geral_items)
    total_obras = sum(i.get('valorTotal', 0) for i in pac_obras_items)
    total_mrosc = sum(p.get('valor_total', 0) for p in projetos_mrosc)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    
    elements = []
    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle('Titulo', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#1F4E78'), alignment=TA_CENTER, spaceAfter=6*mm)
    subtitulo_style = ParagraphStyle('Subtitulo', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#2E7D32'), spaceBefore=6*mm, spaceAfter=3*mm)
    
    # Cabeçalho
    elements.append(Paragraph('PREFEITURA MUNICIPAL DE ACAIACA - MG', titulo_style))
    elements.append(Paragraph('CNPJ: 18.295.287/0001-90', ParagraphStyle('CNPJ', alignment=TA_CENTER, fontSize=9)))
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph('<b>RELATÓRIO GERENCIAL CONSOLIDADO</b>', ParagraphStyle('TitDoc', alignment=TA_CENTER, fontSize=14, textColor=colors.HexColor('#1F4E78'))))
    elements.append(Paragraph(f'Gerado em: {datetime.now().strftime("%d/%m/%Y às %H:%M")}', ParagraphStyle('Data', alignment=TA_CENTER, fontSize=8, textColor=colors.gray)))
    elements.append(Spacer(1, 8*mm))
    
    # Resumo Executivo
    elements.append(Paragraph('1. RESUMO EXECUTIVO', subtitulo_style))
    resumo_data = [
        ['Indicador', 'Quantidade', 'Valor Total'],
        ['PACs Individuais', str(len(pacs)), f"R$ {total_pac:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')],
        ['PACs Gerais', str(len(pacs_geral)), f"R$ {total_pac_geral:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')],
        ['PACs Obras', str(len(pacs_obras)), f"R$ {total_obras:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')],
        ['Processos', str(len(processos)), '-'],
        ['Projetos MROSC', str(len(projetos_mrosc)), f"R$ {total_mrosc:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')],
        ['TOTAL GERAL', '-', f"R$ {(total_pac + total_pac_geral + total_obras + total_mrosc):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')]
    ]
    
    resumo_table = Table(resumo_data, colWidths=[80*mm, 40*mm, 50*mm])
    resumo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BBDEFB')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E3F2FD')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(resumo_table)
    
    # Processos por Status
    elements.append(Paragraph('2. PROCESSOS POR STATUS', subtitulo_style))
    status_count = {}
    for p in processos:
        s = p.get('status', 'Não Definido')
        status_count[s] = status_count.get(s, 0) + 1
    
    status_data = [['Status', 'Quantidade']]
    for s, c in sorted(status_count.items(), key=lambda x: x[1], reverse=True):
        status_data.append([s, str(c)])
    
    status_table = Table(status_data, colWidths=[100*mm, 40*mm])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#C8E6C9')),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(status_table)
    
    # Rodapé
    elements.append(Spacer(1, 15*mm))
    user_name = user.name if hasattr(user, 'name') else user.get('name', 'Admin')
    elements.append(Paragraph('_' * 50, ParagraphStyle('Linha', alignment=TA_CENTER)))
    elements.append(Paragraph(f'<b>{user_name}</b>', ParagraphStyle('Assinatura', alignment=TA_CENTER, fontSize=10)))
    elements.append(Paragraph('Responsável pelo Relatório', ParagraphStyle('Cargo', alignment=TA_CENTER, fontSize=8, textColor=colors.gray)))
    
    doc.build(elements)
    buffer.seek(0)
    
    filename = f"Relatorio_Consolidado_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return StreamingResponse(buffer, media_type='application/pdf', headers={'Content-Disposition': f'attachment; filename="{filename}"'})


# Registrar routers
app.include_router(analytics_router)
app.include_router(alertas_router)
app.include_router(relatorios_router)

# ===== Router de Validação de Documentos (Público) =====
validation_router = APIRouter(prefix="/api/validar", tags=["Validação de Documentos"])

class DocumentValidationRequest(BaseModel):
    validation_code: str

class DocumentValidationResponse(BaseModel):
    is_valid: bool
    message: str
    document_info: Optional[dict] = None

@validation_router.get("/")
async def validation_info():
    """Retorna informações sobre a validação de documentos"""
    return {
        "titulo": "Validação de Documentos Assinados Digitalmente",
        "descricao": "Use este serviço para verificar a autenticidade de documentos emitidos pela Prefeitura Municipal de Acaiaca.",
        "instrucoes": [
            "Digite o código de validação presente no selo de assinatura do documento",
            "O código possui o formato: DOC-XXXXXXXX-YYYYMMDD",
            "Você também pode escanear o QR Code presente no documento"
        ]
    }

@validation_router.get("/{validation_code}")
async def validate_document_get(validation_code: str):
    """Valida um documento pelo código (via QR Code ou link direto)"""
    return await validate_document_internal(validation_code)

@validation_router.post("/verificar")
async def validate_document_post(request: DocumentValidationRequest):
    """Valida um documento pelo código (via formulário)"""
    return await validate_document_internal(request.validation_code)

async def validate_document_internal(validation_code: str) -> DocumentValidationResponse:
    """Função interna para validação de documentos"""
    try:
        # Buscar assinatura no banco
        signature = await db.document_signatures.find_one(
            {'validation_code': validation_code.strip().upper()},
            {'_id': 0}
        )
        
        if not signature:
            return DocumentValidationResponse(
                is_valid=False,
                message="Código de validação não encontrado. Verifique se o código foi digitado corretamente.",
                document_info=None
            )
        
        if not signature.get('is_valid', True):
            return DocumentValidationResponse(
                is_valid=False,
                message="Este documento foi revogado ou invalidado.",
                document_info=None
            )
        
        # Preparar informações do documento
        signers_info = []
        for signer in signature.get('signers', []):
            signers_info.append({
                'nome': signer.get('nome', 'N/A'),
                'cargo': signer.get('cargo', ''),
                'cpf_masked': mask_cpf(signer.get('cpf', '')),
                'email': signer.get('email', '')[:3] + '***@***' if signer.get('email') else ''
            })
        
        return DocumentValidationResponse(
            is_valid=True,
            message="Documento válido! A assinatura digital foi verificada com sucesso.",
            document_info={
                'tipo_documento': signature.get('document_type', 'Documento'),
                'data_assinatura': signature.get('created_at').isoformat() if signature.get('created_at') else None,
                'assinantes': signers_info,
                'hash_parcial': signature.get('hash_document', '')[:16] + '...'
            }
        )
    except Exception as e:
        logging.error(f"Erro ao validar documento: {e}")
        return DocumentValidationResponse(
            is_valid=False,
            message="Erro ao processar a validação. Tente novamente.",
            document_info=None
        )

app.include_router(validation_router)

# Registrar router DOEM
app.include_router(doem_router)

# Registrar router WebSocket
app.include_router(ws_router, prefix="/api")

app.include_router(api_router)
app.include_router(public_router)  # Rotas públicas para transparência

# CORS Middleware
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','), allow_methods=["*"], allow_headers=["*"])

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Middleware de logging de requisições
from starlette.middleware.base import BaseHTTPMiddleware
import time

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        
        # Extrair user_id do token se presente
        user_id = None
        auth_header = request.headers.get('authorization', '')
        if auth_header.startswith('Bearer '):
            try:
                token = auth_header.split(' ')[1]
                payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
                user_id = payload.get('user_id')
            except:
                pass
        
        response = await call_next(request)
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Logar apenas se não for health check ou assets estáticos
        path = request.url.path
        if not path.startswith('/api/docs') and not path.startswith('/api/openapi') and not path.startswith('/api/redoc'):
            request_logger.log_request(
                method=request.method,
                path=path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                user_id=user_id
            )
        
        return response

app.add_middleware(LoggingMiddleware)

log_info("🚀 Planejamento Acaiaca API iniciada com sucesso!")

@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização do servidor"""
    log_info("Conectando ao MongoDB...")
    log_info(f"Banco de dados: {os.environ.get('DB_NAME', 'pac_acaiaca')}")
    log_info("Sistema pronto para receber requisições")

@app.on_event("shutdown")
async def shutdown_db_client():
    """Evento executado no encerramento do servidor"""
    log_info("Encerrando conexões...")
    client.close()
    log_info("Sistema encerrado com sucesso")
