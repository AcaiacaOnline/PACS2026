from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, UploadFile, File
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ.get('JWT_SECRET', 'pac-acaiaca-secret-key-2026')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DAYS = 7

app = FastAPI(title="PAC Acaiaca 2026 - Plano Anual de Contratações")
api_router = APIRouter(prefix="/api")

# Models
# Modelo de permissões do usuário
class UserPermissions(BaseModel):
    can_view: bool = True          # Visualizar PACs
    can_edit: bool = False         # Editar PACs
    can_delete: bool = False       # Excluir PACs
    can_export: bool = False       # Gerar relatórios PDF/XLSX
    can_manage_users: bool = False # Cadastrar/gerenciar usuários
    is_full_admin: bool = False    # Todos os privilégios de administrador

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: EmailStr
    name: str
    is_admin: bool = False
    is_active: bool = True
    picture: Optional[str] = None
    permissions: Optional[UserPermissions] = None
    created_at: datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    is_admin: bool = False
    permissions: Optional[UserPermissions] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: bool = True
    permissions: Optional[UserPermissions] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserListItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: EmailStr
    name: str
    is_admin: bool
    is_active: bool = True
    permissions: Optional[UserPermissions] = None
    created_at: datetime

class PAC(BaseModel):
    model_config = ConfigDict(extra="ignore")
    pac_id: str
    user_id: str
    secretaria: str
    secretario: str
    fiscal: str
    telefone: str
    email: str
    endereco: str
    ano: str = "2026"
    codigo_classificacao: Optional[str] = None  # NOVO: Código de classificação orçamentária
    subitem_classificacao: Optional[str] = None  # NOVO: Subitem da classificação
    total_value: float = 0.0
    stats: Optional[Dict] = None
    created_at: datetime
    updated_at: datetime

class PACCreate(BaseModel):
    secretaria: str
    secretario: str
    fiscal: str
    telefone: str
    email: str
    endereco: str
    ano: str = "2026"
    codigo_classificacao: Optional[str] = None  # NOVO
    subitem_classificacao: Optional[str] = None  # NOVO

class PACUpdate(BaseModel):
    secretaria: Optional[str] = None
    secretario: Optional[str] = None
    fiscal: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    endereco: Optional[str] = None
    ano: Optional[str] = None
    codigo_classificacao: Optional[str] = None  # NOVO
    subitem_classificacao: Optional[str] = None  # NOVO

class PACItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    item_id: str
    pac_id: str
    tipo: str
    catmat: str
    descricao: str
    unidade: str
    quantidade: float
    valorUnitario: float
    valorTotal: float
    prioridade: str
    justificativa: str
    codigo_classificacao: Optional[str] = None
    subitem_classificacao: Optional[str] = None
    created_at: datetime

class PACItemCreate(BaseModel):
    tipo: str
    catmat: str
    descricao: str
    unidade: str
    quantidade: float
    valorUnitario: float
    prioridade: str
    justificativa: str
    codigo_classificacao: Optional[str] = None
    subitem_classificacao: Optional[str] = None

class PACItemUpdate(BaseModel):
    tipo: Optional[str] = None
    catmat: Optional[str] = None
    descricao: Optional[str] = None
    unidade: Optional[str] = None
    quantidade: Optional[float] = None
    valorUnitario: Optional[float] = None
    prioridade: Optional[str] = None
    justificativa: Optional[str] = None
    codigo_classificacao: Optional[str] = None
    subitem_classificacao: Optional[str] = None

# ===== MODELOS PAC GERAL =====
class PACGeral(BaseModel):
    model_config = ConfigDict(extra="ignore")
    pac_geral_id: str
    user_id: str
    nome_secretaria: str
    secretario: str
    fiscal_contrato: Optional[str] = None  # NOVO - Nome do Fiscal do Contrato
    telefone: str
    email: EmailStr
    endereco: str
    cep: str
    secretarias_selecionadas: List[str]  # AD, FA, SA, SE, AS, AG, OB, TR, CUL
    created_at: datetime
    updated_at: datetime

class PACGeralCreate(BaseModel):
    nome_secretaria: str
    secretario: str
    fiscal_contrato: Optional[str] = None  # NOVO
    telefone: str
    email: EmailStr
    endereco: str
    cep: str
    secretarias_selecionadas: List[str]

class PACGeralUpdate(BaseModel):
    nome_secretaria: Optional[str] = None
    secretario: Optional[str] = None
    fiscal_contrato: Optional[str] = None  # NOVO
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    endereco: Optional[str] = None
    cep: Optional[str] = None
    secretarias_selecionadas: Optional[List[str]] = None

class PACGeralItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    item_id: str
    pac_geral_id: str
    catmat: str
    descricao: str
    unidade: str
    # Quantidades por secretaria
    qtd_ad: float = 0  # Administração
    qtd_fa: float = 0  # Fazenda
    qtd_sa: float = 0  # Saúde
    qtd_se: float = 0  # Educação
    qtd_as: float = 0  # Assistência Social
    qtd_ag: float = 0  # Agricultura
    qtd_ob: float = 0  # Obras
    qtd_tr: float = 0  # Transporte
    qtd_cul: float = 0  # Cultura
    quantidade_total: float
    valorUnitario: float
    valorTotal: float
    prioridade: str
    justificativa: str
    codigo_classificacao: Optional[str] = None
    subitem_classificacao: Optional[str] = None
    created_at: datetime

class PACGeralItemCreate(BaseModel):
    catmat: str
    descricao: str
    unidade: str
    qtd_ad: float = 0
    qtd_fa: float = 0
    qtd_sa: float = 0
    qtd_se: float = 0
    qtd_as: float = 0
    qtd_ag: float = 0
    qtd_ob: float = 0
    qtd_tr: float = 0
    qtd_cul: float = 0
    valorUnitario: float
    prioridade: str
    justificativa: str
    codigo_classificacao: Optional[str] = None
    subitem_classificacao: Optional[str] = None

class PACGeralItemUpdate(BaseModel):
    catmat: Optional[str] = None
    descricao: Optional[str] = None
    unidade: Optional[str] = None
    qtd_ad: Optional[float] = None
    qtd_fa: Optional[float] = None
    qtd_sa: Optional[float] = None
    qtd_se: Optional[float] = None
    qtd_as: Optional[float] = None
    qtd_ag: Optional[float] = None
    qtd_ob: Optional[float] = None
    qtd_tr: Optional[float] = None
    qtd_cul: Optional[float] = None
    valorUnitario: Optional[float] = None
    prioridade: Optional[str] = None
    justificativa: Optional[str] = None
    codigo_classificacao: Optional[str] = None
    subitem_classificacao: Optional[str] = None

# ============ MODELOS DE GESTÃO PROCESSUAL ============
class Processo(BaseModel):
    model_config = ConfigDict(extra="ignore")
    processo_id: str
    user_id: str
    numero_processo: str  # Ex: PRC - 0006/2025
    status: str  # Concluído, Iniciado, Publicado, Aguardando Jurídico, Homologado
    modalidade: str  # Dispensa por Limite, Chamamento Público, Inexigibilidade, Pregão, etc.
    objeto: str  # Descrição do processo
    situacao: Optional[str] = None  # OK ou outro indicador
    responsavel: str
    data_inicio: Optional[datetime] = None
    data_autuacao: Optional[datetime] = None
    data_contrato: Optional[datetime] = None
    secretaria: str
    secretario: str
    observacoes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ProcessoCreate(BaseModel):
    numero_processo: str
    status: str
    modalidade: str
    objeto: str
    situacao: Optional[str] = None
    responsavel: str
    data_inicio: Optional[datetime] = None
    data_autuacao: Optional[datetime] = None
    data_contrato: Optional[datetime] = None
    secretaria: str
    secretario: str
    observacoes: Optional[str] = None

class ProcessoUpdate(BaseModel):
    numero_processo: Optional[str] = None
    status: Optional[str] = None
    modalidade: Optional[str] = None
    objeto: Optional[str] = None
    situacao: Optional[str] = None
    responsavel: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_autuacao: Optional[datetime] = None
    data_contrato: Optional[datetime] = None
    secretaria: Optional[str] = None
    secretario: Optional[str] = None
    observacoes: Optional[str] = None

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
    user_doc = {
        'user_id': user_id,
        'email': user_data.email,
        'name': user_data.name,
        'password_hash': hash_password(user_data.password),
        'is_admin': False,
        'is_active': True,
        'picture': None,
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

@api_router.get("/pacs", response_model=List[PAC])
async def get_pacs(request: Request):
    user = await get_current_user(request)
    # Usuários padrão veem todos os PACs (mas só podem editar os seus)
    # Admin vê e pode editar todos
    pacs = await db.pacs.find({}, {'_id': 0}).to_list(1000)
    return [PAC(**p) for p in pacs]

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
async def export_pdf(pac_id: str, request: Request, orientation: str = "landscape"):
    """
    Exporta PAC Individual para PDF com margens otimizadas para assinatura digital.
    Args:
        orientation: 'landscape' (paisagem) ou 'portrait' (retrato)
    """
    user = await get_current_user(request)
    pac = await db.pacs.find_one({'pac_id': pac_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC not found")
    items = await db.pac_items.find({'pac_id': pac_id}, {'_id': 0}).to_list(1000)
    
    buffer = BytesIO()
    
    # Configuração de margens otimizadas para assinatura digital
    # Margem direita ampliada para permitir assinatura digital em lote
    if orientation.lower() == 'portrait':
        page_size = A4
        left_margin = 10*mm
        right_margin = 30*mm  # AMPLIADA PARA ASSINATURA DIGITAL
        top_margin = 10*mm
        bottom_margin = 10*mm
    else:
        page_size = landscape(A4)
        left_margin = 8*mm
        right_margin = 25*mm  # AMPLIADA PARA ASSINATURA DIGITAL
        top_margin = 8*mm
        bottom_margin = 8*mm
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=page_size,
        leftMargin=left_margin, 
        rightMargin=right_margin, 
        topMargin=top_margin, 
        bottomMargin=bottom_margin,
        title=f'PAC {pac["secretaria"]} 2026'
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1F4E78'),
        alignment=TA_CENTER,
        spaceAfter=4,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#1F4E78'),
        alignment=TA_CENTER,
        spaceAfter=4,
        fontName='Helvetica-Bold'
    )
    
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=2
    )
    
    # Cabeçalho com logotipo
    logo_path = ROOT_DIR / 'brasao_acaiaca.jpg'
    header_elements = []
    if logo_path.exists():
        try:
            logo = Image(str(logo_path), width=1.8*cm, height=1.8*cm)
            header_elements.append(logo)
        except:
            pass
    
    elements.append(Paragraph('PREFEITURA MUNICIPAL DE ACAIACA - MG', title_style))
    elements.append(Paragraph('PAC ACAIACA 2026 - PLANO ANUAL DE CONTRATAÇÕES', subtitle_style))
    elements.append(Paragraph('<i>Lei Federal nº 14.133/2021</i>', ParagraphStyle('Legal', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey, spaceAfter=6)))
    
    # Informações da Secretaria em formato compacto horizontal
    info_data = [
        [
            Paragraph(f'<b>Secretaria:</b> {pac["secretaria"]}', info_style),
            Paragraph(f'<b>Secretário(a):</b> {pac["secretario"]}', info_style),
            Paragraph(f'<b>Fiscal:</b> {pac["fiscal"]}', info_style),
        ],
        [
            Paragraph(f'<b>Telefone:</b> {pac["telefone"]}', info_style),
            Paragraph(f'<b>E-mail:</b> {pac["email"]}', info_style),
            Paragraph(f'<b>Ano:</b> {pac["ano"]}', info_style),
        ],
        [
            Paragraph(f'<b>Endereço:</b> {pac["endereco"]}', info_style),
            '', ''
        ]
    ]
    
    info_table = Table(info_data, colWidths=[9.3*cm, 9.3*cm, 9.3*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#E7E6E6')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1F4E78')),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('SPAN', (0, 2), (2, 2)),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 5*mm))
    
    # Tabela de itens - formato paisagem com todas as informações COMPLETAS
    # IMPORTANTE: Sem truncamento de textos - campos exibidos integralmente
    elements.append(Paragraph('<b>DETALHAMENTO DOS ITENS</b>', ParagraphStyle('Header', fontSize=10, fontName='Helvetica-Bold', spaceAfter=3)))
    
    # Cabeçalhos completos conforme especificação
    table_data = [['#', 'Código\nCATMAT', 'Descrição do Objeto', 'Unidade', 'Qtd', 'Valor\nUnitário', 'Valor\nTotal', 'Prioridade', 'Justificativa da Contratação', 'Classificação Orçamentária\n(Código - Subitem)']]
    
    for idx, item in enumerate(items, start=1):
        # Classificação Orçamentária COMPLETA
        classificacao_text = ''
        if item.get('codigo_classificacao'):
            classificacao_text = f"{item['codigo_classificacao']}"
            if item.get('subitem_classificacao'):
                # Subitem COMPLETO sem truncamento
                classificacao_text += f"\n{item['subitem_classificacao']}"
        
        # Descrição COMPLETA - sem truncamento
        descricao_completa = item.get('descricao', '')
        
        # Justificativa COMPLETA - sem truncamento
        justificativa_completa = item.get('justificativa', '') or 'Não informada'
        
        table_data.append([
            str(idx),
            item.get('catmat', ''),  # Código COMPLETO
            Paragraph(f"<font size=7>{descricao_completa}</font>", styles['Normal']),  # Descrição COMPLETA
            item['unidade'],  # Unidade
            str(int(item['quantidade'])),  # Quantidade
            f"R$ {item['valorUnitario']:,.2f}",  # Valor Unitário
            f"R$ {item['valorTotal']:,.2f}",  # Valor Total
            item['prioridade'],  # Prioridade COMPLETA
            Paragraph(f"<font size=6>{justificativa_completa}</font>", styles['Normal']),  # Justificativa COMPLETA
            Paragraph(f"<font size=6>{classificacao_text}</font>", styles['Normal'])  # Classificação COMPLETA
        ])
    
    # Linha de total
    total = sum(item['valorTotal'] for item in items)
    table_data.append(['', '', '', '', Paragraph('<b>TOTAL GERAL ESTIMADO:</b>', styles['Normal']), '', '', '', f"R$ {total:,.2f}", '', ''])
    
    # Larguras para A4 Paisagem (277mm - margens = ~257mm disponível)
    col_widths = [0.6*cm, 1.8*cm, 1.2*cm, 5*cm, 4*cm, 1*cm, 1*cm, 1.8*cm, 1.8*cm, 1.2*cm, 5*cm]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        
        # Corpo
        ('FONTSIZE', (0, 1), (-1, -2), 7),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (5, 1), (9, -1), 'CENTER'),
        ('ALIGN', (7, 1), (8, -1), 'RIGHT'),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        
        # Linhas alternadas
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F2F2F2')]),
        
        # Total
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFC000')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 9),
        
        # Bordas
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        
        # Padding
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 8*mm))
    
    # Assinaturas na mesma página se couber
    sig_data = [
        ['_' * 45, '_' * 45],
        [pac['secretario'], pac['fiscal']],
        ['Secretário(a) Responsável', 'Fiscal do Contrato']
    ]
    
    sig_table = Table(sig_data, colWidths=[12*cm, 12*cm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 2), (-1, 2), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 0),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 2),
    ]))
    
    elements.append(sig_table)
    elements.append(Spacer(1, 5*mm))
    
    # Rodapé
    footer_text = f'<font size=7><i>Documento gerado eletronicamente pelo Sistema PAC Acaiaca 2026 em {datetime.now().strftime("%d/%m/%Y às %H:%M")} | Desenvolvido por Cristiano Abdo de Souza - Assessor de Planejamento, Compras e Logística</i></font>'
    elements.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER, textColor=colors.grey)))
    
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(buffer, media_type='application/pdf', headers={'Content-Disposition': f'attachment; filename=PAC_{pac["secretaria"].replace(" ", "_")}_2026.pdf'})

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
@api_router.get("/pacs-geral", response_model=List[PACGeral])
async def get_pacs_geral(request: Request):
    user = await get_current_user(request)
    # Todos os usuários podem ver todos os PACs Gerais
    pacs = await db.pacs_geral.find({}, {'_id': 0}).to_list(1000)
    return pacs

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
async def export_pac_geral_pdf(pac_geral_id: str, request: Request, orientation: str = "landscape"):
    """
    Exporta o PAC Geral para PDF.
    Args:
        orientation: 'landscape' (paisagem) ou 'portrait' (retrato)
    """
    user = await get_current_user(request)
    pac = await db.pacs_geral.find_one({'pac_geral_id': pac_geral_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC Geral not found")
    
    items = await db.pac_geral_items.find({'pac_geral_id': pac_geral_id}, {'_id': 0}).to_list(1000)
    
    buffer = BytesIO()
    
    # Determinar orientação
    if orientation.lower() == 'portrait':
        page_size = A4
        page_width = 210*mm
        margin = 12*mm
    else:  # landscape (padrão)
        page_size = landscape(A4)
        page_width = 297*mm
        margin = 10*mm
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=page_size,
        rightMargin=margin, 
        leftMargin=margin, 
        topMargin=margin, 
        bottomMargin=margin
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilos customizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14 if orientation == 'landscape' else 12,
        textColor=colors.HexColor('#1F4788'),
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=11 if orientation == 'landscape' else 10,
        textColor=colors.HexColor('#1F4788'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=8 if orientation == 'landscape' else 7,
        spaceAfter=2
    )
    
    # Cabeçalho com logotipo - proporcional
    logo_path = ROOT_DIR / 'brasao_acaiaca.jpg'
    if logo_path.exists():
        try:
            from PIL import Image as PILImage
            pil_img = PILImage.open(str(logo_path))
            img_width, img_height = pil_img.size
            aspect_ratio = img_height / img_width
            
            # Definir largura máxima e calcular altura proporcional
            max_logo_width = 2*cm
            logo_width = max_logo_width
            logo_height = logo_width * aspect_ratio
            
            logo = Image(str(logo_path), width=logo_width, height=logo_height)
            elements.append(logo)
        except Exception as e:
            # Fallback sem proporção
            logo = Image(str(logo_path), width=2*cm, height=2*cm)
            elements.append(logo)
    
    elements.append(Paragraph('PREFEITURA MUNICIPAL DE ACAIACA - MG', title_style))
    elements.append(Paragraph('PAC ACAIACA 2026 - PLANO ANUAL DE CONTRATAÇÕES COMPARTILHADO', subtitle_style))
    elements.append(Paragraph('<i>Lei Federal nº 14.133/2021</i>', ParagraphStyle('Legal', parent=styles['Normal'], fontSize=7, alignment=TA_CENTER, textColor=colors.grey, spaceAfter=4)))
    
    # Dados da Secretaria incluindo Fiscal do Contrato
    fiscal_contrato = pac.get('fiscal_contrato', 'Não informado')
    
    if orientation.lower() == 'portrait':
        # Formato Retrato - dados em linhas
        info_data = [
            [Paragraph(f'<b>Secretaria Responsável:</b> {pac["nome_secretaria"]}', info_style)],
            [Paragraph(f'<b>Secretário(a):</b> {pac["secretario"]}', info_style)],
            [Paragraph(f'<b>Fiscal do Contrato:</b> {fiscal_contrato}', info_style)],
            [Paragraph(f'<b>Telefone:</b> {pac["telefone"]} | <b>E-mail:</b> {pac["email"]}', info_style)],
            [Paragraph(f'<b>Endereço:</b> {pac["endereco"]} | <b>CEP:</b> {pac.get("cep", "")}', info_style)],
            [Paragraph(f'<b>Secretarias Participantes:</b> {", ".join(pac["secretarias_selecionadas"])}', info_style)],
        ]
        info_table = Table(info_data, colWidths=[18*cm])
    else:
        # Formato Paisagem - dados em colunas
        info_data = [
            [
                Paragraph(f'<b>Secretaria:</b> {pac["nome_secretaria"]}', info_style),
                Paragraph(f'<b>Secretário:</b> {pac["secretario"]}', info_style),
                Paragraph(f'<b>Fiscal do Contrato:</b> {fiscal_contrato}', info_style),
            ],
            [
                Paragraph(f'<b>Telefone:</b> {pac["telefone"]}', info_style),
                Paragraph(f'<b>E-mail:</b> {pac["email"]}', info_style),
                Paragraph(f'<b>Secretarias:</b> {", ".join(pac["secretarias_selecionadas"])}', info_style),
            ],
            [
                Paragraph(f'<b>Endereço:</b> {pac["endereco"]}', info_style),
                Paragraph(f'<b>CEP:</b> {pac.get("cep", "")}', info_style),
                ''
            ]
        ]
        info_table = Table(info_data, colWidths=[9.2*cm, 9.2*cm, 9.2*cm])
    
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#E7E6E6')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1F4788')),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 5*mm))
    
    # Tabela de itens - SEM granularidade por secretaria (consolidado)
    elements.append(Paragraph('<b>DETALHAMENTO DOS ITENS</b>', ParagraphStyle('Header', fontSize=9, fontName='Helvetica-Bold', spaceAfter=2)))
    
    # Cabeçalho com coluna de Justificativa
    table_data = [['#', 'Código', 'Descrição', 'Justificativa', 'Und', 'Qtd Total', 'Valor Unit.', 'Valor Total', 'Prior', 'Classificação']]
    
    for idx, item in enumerate(items, start=1):
        classificacao_text = ''
        if item.get('codigo_classificacao'):
            classificacao_text = f"{item['codigo_classificacao']}"
            if item.get('subitem_classificacao'):
                classificacao_text += f" - {item['subitem_classificacao']}"
        
        # Justificativa em coluna separada
        justificativa = item.get('justificativa', '') or ''
        
        table_data.append([
            str(idx),
            item.get('catmat', '')[:12],
            Paragraph(f"<font size=7>{item['descricao'][:70]}</font>", styles['Normal']),
            Paragraph(f"<font size=6>{justificativa[:80]}</font>", styles['Normal']),
            item['unidade'][:5],
            str(int(item.get('quantidade_total', 0))),
            f"R$ {item['valorUnitario']:,.2f}",
            f"R$ {item['valorTotal']:,.2f}",
            item.get('prioridade', '')[:3],
            Paragraph(f"<font size=6>{classificacao_text}</font>", styles['Normal'])
        ])
    
    # Linha de total
    total = sum(item['valorTotal'] for item in items)
    total_qtd = sum(item.get('quantidade_total', 0) for item in items)
    table_data.append([
        '', '', Paragraph('<b>TOTAL GERAL:</b>', styles['Normal']), '', '',
        str(int(total_qtd)), '', f"R$ {total:,.2f}", '', ''
    ])
    
    # Larguras das colunas ajustadas para relatório com Justificativa
    if orientation.lower() == 'portrait':
        col_widths = [0.6*cm, 1.3*cm, 4*cm, 3.5*cm, 0.9*cm, 1.2*cm, 1.8*cm, 1.8*cm, 0.8*cm, 2.8*cm]
    else:
        col_widths = [0.7*cm, 1.5*cm, 5.5*cm, 5*cm, 1.2*cm, 1.5*cm, 2.2*cm, 2.4*cm, 1*cm, 4.5*cm]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('TOPPADDING', (0, 0), (-1, 0), 5),
        
        # Corpo
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (3, 1), (6, -1), 'CENTER'),
        ('ALIGN', (5, 1), (6, -1), 'RIGHT'),
        ('ALIGN', (7, 1), (7, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Linhas alternadas
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F5F5F5')]),
        
        # Total
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFC000')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 9),
        
        # Bordas
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        
        # Padding
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 8*mm))
    
    # Assinaturas - Responsável e Fiscal
    secretario_nome = pac.get('secretario', 'Responsável da Secretaria')
    fiscal_nome = pac.get('fiscal_contrato', 'Fiscal do Contrato')
    
    signature_data = [
        ['_' * 50, '_' * 50],
        [secretario_nome, fiscal_nome],
        ['Responsável pela Secretaria', 'Fiscal do Contrato']
    ]
    
    sig_table = Table(signature_data, colWidths=[12*cm, 12*cm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 9),
        ('FONTSIZE', (0, 2), (-1, 2), 8),
        ('TOPPADDING', (0, 1), (-1, 1), 6),
    ]))
    
    elements.append(sig_table)
    elements.append(Spacer(1, 5*mm))
    
    # Rodapé
    footer_text = f'<font size=6><i>Documento gerado pelo Sistema PAC Acaiaca 2026 em {datetime.now().strftime("%d/%m/%Y às %H:%M")} | Desenvolvido por Cristiano Abdo de Souza</i></font>'
    elements.append(Paragraph(footer_text, ParagraphStyle('Footer', alignment=TA_CENTER, textColor=colors.grey)))
    
    doc.build(elements)
    buffer.seek(0)
    
    orientation_name = 'Paisagem' if orientation.lower() == 'landscape' else 'Retrato'
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=PAC_Geral_{pac['nome_secretaria']}_{orientation_name}.pdf"}
    )


# ============ ROTAS DE GESTÃO PROCESSUAL ============

@api_router.get("/processos", response_model=List[Processo])
async def get_processos(request: Request):
    """Lista todos os processos"""
    user = await get_current_user(request)
    processos = await db.processos.find({}, {'_id': 0}).to_list(1000)
    
    # Fix null string values in datetime fields
    for p in processos:
        for field in ['data_inicio', 'data_autuacao', 'data_contrato']:
            if p.get(field) == 'null' or p.get(field) == '':
                p[field] = None
    
    return [Processo(**p) for p in processos]

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
async def export_processos_pdf(request: Request, orientation: str = "landscape"):
    """Exporta todos os processos para PDF"""
    user = await get_current_user(request)
    processos = await db.processos.find({}, {'_id': 0}).to_list(1000)
    
    buffer = BytesIO()
    
    if orientation.lower() == 'portrait':
        page_size = A4
        margin = 12*mm
    else:
        page_size = landscape(A4)
        margin = 10*mm
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=page_size,
        rightMargin=margin, 
        leftMargin=margin, 
        topMargin=margin, 
        bottomMargin=margin
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
    
    # Tabela de processos
    if orientation.lower() == 'portrait':
        table_data = [['#', 'Processo', 'Status', 'Modalidade', 'Objeto', 'Secretaria']]
        for idx, p in enumerate(processos, start=1):
            table_data.append([
                str(idx),
                p.get('numero_processo', '')[:20],
                p.get('status', '')[:15],
                Paragraph(f"<font size=6>{p.get('modalidade', '')[:25]}</font>", styles['Normal']),
                Paragraph(f"<font size=6>{p.get('objeto', '')[:60]}</font>", styles['Normal']),
                Paragraph(f"<font size=6>{p.get('secretaria', '')[:30]}</font>", styles['Normal'])
            ])
        col_widths = [0.6*cm, 2.5*cm, 2*cm, 3*cm, 6*cm, 4*cm]
    else:
        table_data = [['#', 'Processo', 'Status', 'Modalidade', 'Objeto', 'Responsável', 'Secretaria', 'Observações']]
        for idx, p in enumerate(processos, start=1):
            table_data.append([
                str(idx),
                p.get('numero_processo', '')[:22],
                p.get('status', '')[:12],
                Paragraph(f"<font size=6>{p.get('modalidade', '')[:20]}</font>", styles['Normal']),
                Paragraph(f"<font size=6>{p.get('objeto', '')[:80]}</font>", styles['Normal']),
                p.get('responsavel', '')[:15],
                Paragraph(f"<font size=6>{p.get('secretaria', '')[:25]}</font>", styles['Normal']),
                Paragraph(f"<font size=5>{p.get('observacoes', '')[:50]}</font>", styles['Normal'])
            ])
        col_widths = [0.6*cm, 2.5*cm, 1.8*cm, 2.5*cm, 7*cm, 2*cm, 4*cm, 4*cm]
    
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
    footer_text = f'<font size=6><i>Total de {len(processos)} processos | Gerado em {datetime.now().strftime("%d/%m/%Y às %H:%M")} | Sistema PAC Acaiaca 2026</i></font>'
    elements.append(Paragraph(footer_text, ParagraphStyle('Footer', alignment=TA_CENTER, textColor=colors.grey)))
    
    doc.build(elements)
    buffer.seek(0)
    
    orientation_name = 'Paisagem' if orientation.lower() == 'landscape' else 'Retrato'
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
                'version': '1.0',
                'exported_at': datetime.now(timezone.utc).isoformat(),
                'exported_by': user.email,
                'system': 'PAC Acaiaca 2026'
            },
            'users': [],
            'pacs': [],
            'pac_items': [],
            'pacs_geral': [],
            'pac_geral_items': [],
            'processos': []
        }
        
        # Exportar usuários (sem password_hash por segurança - serão recriados)
        users = await db.users.find({}, {'_id': 0}).to_list(10000)
        for u in users:
            # Manter password_hash para restauração completa
            if 'created_at' in u and isinstance(u['created_at'], datetime):
                u['created_at'] = u['created_at'].isoformat()
            backup_data['users'].append(u)
        
        # Exportar PACs
        pacs = await db.pacs.find({}, {'_id': 0}).to_list(10000)
        for p in pacs:
            if 'created_at' in p and isinstance(p['created_at'], datetime):
                p['created_at'] = p['created_at'].isoformat()
            if 'updated_at' in p and isinstance(p['updated_at'], datetime):
                p['updated_at'] = p['updated_at'].isoformat()
            backup_data['pacs'].append(p)
        
        # Exportar PAC Items
        pac_items = await db.pac_items.find({}, {'_id': 0}).to_list(100000)
        for item in pac_items:
            if 'created_at' in item and isinstance(item['created_at'], datetime):
                item['created_at'] = item['created_at'].isoformat()
            backup_data['pac_items'].append(item)
        
        # Exportar PACs Geral
        pacs_geral = await db.pacs_geral.find({}, {'_id': 0}).to_list(10000)
        for pg in pacs_geral:
            if 'created_at' in pg and isinstance(pg['created_at'], datetime):
                pg['created_at'] = pg['created_at'].isoformat()
            if 'updated_at' in pg and isinstance(pg['updated_at'], datetime):
                pg['updated_at'] = pg['updated_at'].isoformat()
            backup_data['pacs_geral'].append(pg)
        
        # Exportar PAC Geral Items
        pac_geral_items = await db.pac_geral_items.find({}, {'_id': 0}).to_list(100000)
        for item in pac_geral_items:
            if 'created_at' in item and isinstance(item['created_at'], datetime):
                item['created_at'] = item['created_at'].isoformat()
            backup_data['pac_geral_items'].append(item)
        
        # Exportar Processos
        processos = await db.processos.find({}, {'_id': 0}).to_list(100000)
        for proc in processos:
            for field in ['created_at', 'updated_at', 'data_inicio', 'data_autuacao', 'data_contrato']:
                if field in proc and isinstance(proc[field], datetime):
                    proc[field] = proc[field].isoformat()
            backup_data['processos'].append(proc)
        
        # Gerar JSON
        json_content = json.dumps(backup_data, ensure_ascii=False, indent=2)
        
        # Criar resposta como download
        buffer = BytesIO(json_content.encode('utf-8'))
        buffer.seek(0)
        
        filename = f"backup_pac_acaiaca_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return StreamingResponse(
            buffer,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except Exception as e:
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
    processos_count = await db.processos.count_documents({})
    
    return {
        'system': 'PAC Acaiaca 2026',
        'current_data': {
            'users': users_count,
            'pacs': pacs_count,
            'pac_items': pac_items_count,
            'pacs_geral': pacs_geral_count,
            'pac_geral_items': pac_geral_items_count,
            'processos': processos_count
        },
        'total_records': users_count + pacs_count + pac_items_count + pacs_geral_count + pac_geral_items_count + processos_count,
        'backup_available': True,
        'restore_available': True
    }


app.include_router(api_router)
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','), allow_methods=["*"], allow_headers=["*"])
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
