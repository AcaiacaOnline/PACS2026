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
from reportlab.lib.pagesizes import A4
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

app = FastAPI(title="PAC Acaiaca 2026")
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: EmailStr
    name: str
    is_admin: bool = False
    is_active: bool = True
    picture: Optional[str] = None
    created_at: datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    is_admin: bool = False

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: bool = True

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
    imagemUrl: Optional[str] = None
    codigo_classificacao: Optional[str] = None  # NOVO: Código de classificação orçamentária
    subitem_classificacao: Optional[str] = None  # NOVO: Subitem da classificação
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
    imagemUrl: Optional[str] = None
    codigo_classificacao: Optional[str] = None  # NOVO
    subitem_classificacao: Optional[str] = None  # NOVO

class PACItemUpdate(BaseModel):
    tipo: Optional[str] = None
    catmat: Optional[str] = None
    descricao: Optional[str] = None
    unidade: Optional[str] = None
    quantidade: Optional[float] = None
    valorUnitario: Optional[float] = None
    prioridade: Optional[str] = None
    justificativa: Optional[str] = None
    imagemUrl: Optional[str] = None
    codigo_classificacao: Optional[str] = None  # NOVO
    subitem_classificacao: Optional[str] = None  # NOVO

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
    user_doc = {
        'user_id': user_id,
        'email': user_data.email,
        'name': user_data.name,
        'password_hash': hash_password(user_data.password),
        'is_admin': user_data.is_admin,
        'is_active': True,
        'picture': None,
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
    update_data = {k: v for k, v in user_update.model_dump().items() if v is not None}
    if 'password' in update_data:
        update_data['password_hash'] = hash_password(update_data.pop('password'))
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
    ws['A2'] = 'PLANO ANUAL DE CONTRATAÇÕES - EXERCÍCIO 2026'
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
async def export_pdf(pac_id: str, request: Request):
    user = await get_current_user(request)
    pac = await db.pacs.find_one({'pac_id': pac_id}, {'_id': 0})
    if not pac:
        raise HTTPException(status_code=404, detail="PAC not found")
    items = await db.pac_items.find({'pac_id': pac_id}, {'_id': 0}).to_list(1000)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        leftMargin=15*mm, 
        rightMargin=15*mm, 
        topMargin=15*mm, 
        bottomMargin=15*mm,
        title=f'PAC {pac["secretaria"]} 2026'
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#1F4E78'),
        alignment=TA_CENTER,
        spaceAfter=6,
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
    
    info_label_style = ParagraphStyle(
        'InfoLabel',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Bold',
        spaceAfter=2
    )
    
    info_value_style = ParagraphStyle(
        'InfoValue',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=2
    )
    
    # Cabeçalho
    elements.append(Paragraph('PREFEITURA MUNICIPAL DE ACAIACA - MG', title_style))
    elements.append(Paragraph('PLANO ANUAL DE CONTRATAÇÕES - EXERCÍCIO 2026', subtitle_style))
    elements.append(Paragraph('<i>Lei Federal nº 14.133/2021</i>', ParagraphStyle('Legal', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey, spaceAfter=10)))
    elements.append(Spacer(1, 8*mm))
    
    # Informações da Secretaria em box
    info_data = [
        [Paragraph('<b>DADOS DA UNIDADE REQUISITANTE</b>', info_label_style)],
        [Paragraph(f'<b>Secretaria:</b> {pac["secretaria"]}', info_value_style)],
        [Paragraph(f'<b>Secretário(a):</b> {pac["secretario"]}', info_value_style)],
        [Paragraph(f'<b>Fiscal do Contrato:</b> {pac["fiscal"]}', info_value_style)],
        [Paragraph(f'<b>Telefone:</b> {pac["telefone"]} | <b>E-mail:</b> {pac["email"]}', info_value_style)],
        [Paragraph(f'<b>Endereço:</b> {pac["endereco"]}', info_value_style)],
        [Paragraph(f'<b>Ano de Referência:</b> {pac["ano"]}', info_value_style)]
    ]
    
    info_table = Table(info_data, colWidths=[18*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#E7E6E6')),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 8*mm))
    
    # Tabela de itens
    elements.append(Paragraph('<b>DETALHAMENTO DOS ITENS</b>', info_label_style))
    elements.append(Spacer(1, 3*mm))
    
    table_data = [['#', 'Tipo', 'Cód', 'Descrição/Justificativa', 'Und', 'Qtd', 'Valor Unit', 'Total', 'Prior', 'Classif']]
    
    for idx, item in enumerate(items, start=1):
        desc_just = f"<b>{item['descricao'][:80]}</b><br/><font size=7><i>{item['justificativa'][:100] if item['justificativa'] else ''}</i></font>"
        
        # Formatar classificação orçamentária
        classificacao_text = ''
        if item.get('codigo_classificacao'):
            classificacao_text = f"{item['codigo_classificacao']}"
            if item.get('subitem_classificacao'):
                # Pegar apenas as primeiras palavras do subitem para economizar espaço
                subitem_short = ' '.join(item['subitem_classificacao'].split()[:3])
                classificacao_text += f"\n{subitem_short}..."
        
        table_data.append([
            str(idx),
            Paragraph(item['tipo'][:18], styles['Normal']),
            item['catmat'][:8],
            Paragraph(desc_just, styles['Normal']),
            item['unidade'][:5],
            str(int(item['quantidade'])),
            f"R$ {item['valorUnitario']:.2f}",
            f"R$ {item['valorTotal']:.2f}",
            item['prioridade'][0]
        ])
    
    # Linha de total
    total = sum(item['valorTotal'] for item in items)
    table_data.append(['', '', '', Paragraph('<b>TOTAL GERAL ESTIMADO:</b>', styles['Normal']), '', '', '', f"R$ {total:,.2f}", ''])
    
    # Larguras das colunas ajustadas para A4 retrato
    col_widths = [0.8*cm, 2.5*cm, 1.2*cm, 7*cm, 1*cm, 1*cm, 1.8*cm, 1.8*cm, 0.9*cm]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        
        # Corpo
        ('FONTSIZE', (0, 1), (-1, -2), 7),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (4, 1), (5, -1), 'CENTER'),
        ('ALIGN', (6, 1), (7, -1), 'RIGHT'),
        ('ALIGN', (8, 1), (8, -1), 'CENTER'),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        
        # Linhas alternadas
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F2F2F2')]),
        
        # Total
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFC000')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 9),
        ('ALIGN', (0, -1), (7, -1), 'RIGHT'),
        
        # Bordas
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
        
        # Padding
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 10*mm))
    
    # Assinaturas
    elements.append(PageBreak())
    elements.append(Spacer(1, 40*mm))
    
    sig_data = [
        ['', ''],
        ['_' * 50, '_' * 50],
        [pac['secretario'], pac['fiscal']],
        ['Secretário(a) Responsável', 'Fiscal do Contrato']
    ]
    
    sig_table = Table(sig_data, colWidths=[9*cm, 9*cm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 3), (-1, 3), 8),
        ('TOPPADDING', (0, 1), (-1, 1), 0),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 2),
    ]))
    
    elements.append(sig_table)
    elements.append(Spacer(1, 20*mm))
    
    # Rodapé
    footer_text = f'<font size=7><i>Documento gerado eletronicamente pelo Sistema PAC Acaiaca 2026 em {datetime.now().strftime("%d/%m/%Y às %H:%M")}<br/>Desenvolvido por Cristiano Abdo de Souza - Assessor de Planejamento, Compras e Logística</i></font>'
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

app.include_router(api_router)
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','), allow_methods=["*"], allow_headers=["*"])
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
