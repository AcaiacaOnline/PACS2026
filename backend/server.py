from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, UploadFile, File, BackgroundTasks
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
from striprtf.striprtf import rtf_to_text

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

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

# Dados adicionais do usuário para assinatura digital
class UserSignatureData(BaseModel):
    cpf: Optional[str] = None           # CPF (será mascarado na exibição)
    cargo: Optional[str] = None         # Cargo ocupado
    endereco: Optional[str] = None      # Endereço completo
    cep: Optional[str] = None           # CEP
    telefone: Optional[str] = None      # Telefone para contato

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: EmailStr
    name: str
    is_admin: bool = False
    is_active: bool = True
    picture: Optional[str] = None
    permissions: Optional[UserPermissions] = None
    signature_data: Optional[UserSignatureData] = None
    created_at: datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    is_admin: bool = False
    permissions: Optional[UserPermissions] = None
    signature_data: Optional[UserSignatureData] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: bool = True
    permissions: Optional[UserPermissions] = None
    signature_data: Optional[UserSignatureData] = None

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
    signature_data: Optional[UserSignatureData] = None
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
    ano: str = "2026"  # Ano do PAC Geral
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
    ano: str = "2026"  # Ano do PAC Geral
    secretarias_selecionadas: List[str]

class PACGeralUpdate(BaseModel):
    nome_secretaria: Optional[str] = None
    secretario: Optional[str] = None
    fiscal_contrato: Optional[str] = None  # NOVO
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    endereco: Optional[str] = None
    cep: Optional[str] = None
    ano: Optional[str] = None  # Ano do PAC Geral
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
    ano: int = 2025  # Ano do processo
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
    ano: int = None  # Será extraído do numero_processo se não fornecido
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
    ano: Optional[int] = None
    observacoes: Optional[str] = None

# ============ MODELOS DOEM (Diário Oficial Eletrônico Municipal) ============

# Segmentos/Categorias do DOEM
DOEM_SEGMENTOS = [
    "Portarias",
    "Leis",
    "Decretos",
    "Resoluções",
    "Editais",
    "Prestações de Contas",
    "Processos Administrativos",
    "Publicações do Legislativo",
    "Publicações do Terceiro Setor"
]

# Tipos de publicação por segmento
DOEM_TIPOS_PUBLICACAO = {
    "Portarias": ["Portaria", "Portaria Conjunta"],
    "Leis": ["Lei Ordinária", "Lei Complementar", "Emenda à Lei Orgânica"],
    "Decretos": ["Decreto", "Decreto Regulamentar"],
    "Resoluções": ["Resolução", "Resolução Conjunta"],
    "Editais": ["Edital de Licitação", "Edital de Convocação", "Edital de Seleção", "Aviso de Licitação"],
    "Prestações de Contas": ["Prestação de Contas", "Relatório de Gestão", "Balanço"],
    "Processos Administrativos": ["Extrato de Contrato", "Termo Aditivo", "Ata de Registro de Preços", "Homologação", "Ratificação"],
    "Publicações do Legislativo": ["Projeto de Lei", "Ata de Sessão", "Parecer", "Moção", "Requerimento"],
    "Publicações do Terceiro Setor": ["Termo de Parceria", "Convênio", "Prestação de Contas OSC", "Chamamento Público"]
}

class DOEMPublicacao(BaseModel):
    """Publicação individual dentro de uma edição do DOEM"""
    publicacao_id: str
    titulo: str
    texto: str
    secretaria: str
    segmento: str = "Decretos"  # Categoria principal
    tipo: str  # Tipo específico dentro do segmento
    ordem: int = 1

class DOEMPublicacaoCreate(BaseModel):
    titulo: str
    texto: str
    secretaria: str = "Gabinete do Prefeito"
    segmento: str = "Decretos"
    tipo: str = "Decreto"
    ordem: int = 1

class DOEMAssinante(BaseModel):
    """Dados de um assinante individual"""
    user_id: str
    nome: str
    cpf: Optional[str] = None
    cargo: Optional[str] = None
    email: Optional[str] = None
    data_assinatura: Optional[datetime] = None

class DOEMAssinatura(BaseModel):
    """Metadados de assinatura digital (simulada) - Suporta múltiplos assinantes"""
    assinado: bool = False
    data_assinatura: Optional[datetime] = None
    hash_documento: Optional[str] = None
    tipo_certificado: str = "ICP-Brasil (Simulado)"
    titular: str = "Prefeitura Municipal de Acaiaca"
    validation_code: Optional[str] = None
    cpf: Optional[str] = None
    cargo: Optional[str] = None
    email: Optional[str] = None
    # Suporte para múltiplos assinantes
    assinantes: Optional[List[DOEMAssinante]] = None
    assinatura_em_lote: bool = False

class DOEMEdicao(BaseModel):
    """Edição do Diário Oficial"""
    model_config = ConfigDict(extra="ignore")
    edicao_id: str
    numero_edicao: int
    ano: int
    data_publicacao: datetime
    data_criacao: datetime
    status: str = "rascunho"  # rascunho, agendado, publicado
    publicacoes: List[DOEMPublicacao] = []
    criado_por: str
    assinatura_digital: Optional[DOEMAssinatura] = None
    notificacao_enviada: bool = False
    created_at: datetime
    updated_at: datetime

class DOEMEdicaoCreate(BaseModel):
    data_publicacao: Optional[datetime] = None
    publicacoes: List[DOEMPublicacaoCreate] = []

class DOEMEdicaoUpdate(BaseModel):
    data_publicacao: Optional[datetime] = None
    status: Optional[str] = None
    publicacoes: Optional[List[DOEMPublicacaoCreate]] = None

class DOEMConfig(BaseModel):
    """Configurações do DOEM"""
    model_config = ConfigDict(extra="ignore")
    config_id: str = "doem_config_main"
    nome_municipio: str = "Acaiaca"
    uf: str = "MG"
    prefeito: str = ""
    ano_inicio: int = 2026
    ultimo_numero_edicao: int = 0
    segmentos: List[str] = DOEM_SEGMENTOS
    tipos_publicacao: Dict[str, List[str]] = DOEM_TIPOS_PUBLICACAO

class DOEMConfigUpdate(BaseModel):
    nome_municipio: Optional[str] = None
    uf: Optional[str] = None
    prefeito: Optional[str] = None
    segmentos: Optional[List[str]] = None
    tipos_publicacao: Optional[Dict[str, List[str]]] = None

# ============ MODELOS NEWSLETTER/NOTIFICAÇÕES ============

class NewsletterInscrito(BaseModel):
    """Inscrito na newsletter do DOEM"""
    model_config = ConfigDict(extra="ignore")
    inscrito_id: str
    email: EmailStr
    nome: str
    tipo: str = "publico"  # publico, usuario, manual
    ativo: bool = True
    segmentos_interesse: List[str] = []  # Segmentos de interesse (vazio = todos)
    data_inscricao: datetime
    data_confirmacao: Optional[datetime] = None
    confirmado: bool = False
    token_confirmacao: Optional[str] = None

class NewsletterInscricaoPublica(BaseModel):
    """Dados para inscrição pública na newsletter"""
    email: EmailStr
    nome: str
    segmentos_interesse: List[str] = []

class NewsletterInscricaoManual(BaseModel):
    """Dados para inscrição manual (admin)"""
    email: EmailStr
    nome: str
    segmentos_interesse: List[str] = []
    confirmado: bool = True

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
    table_data.append(['', '', Paragraph('<b>TOTAL GERAL ESTIMADO:</b>', styles['Normal']), '', '', '', f"R$ {total:,.2f}", '', '', ''])
    
    # Larguras otimizadas para campos COMPLETOS em A4 Paisagem
    # Total disponível em paisagem: ~252mm (297 - 8 - 25 - margens internas)
    if orientation.lower() == 'portrait':
        col_widths = [0.6*cm, 1.5*cm, 4*cm, 1*cm, 0.8*cm, 1.8*cm, 1.8*cm, 1.2*cm, 3*cm, 3*cm]
    else:
        col_widths = [0.6*cm, 1.5*cm, 5*cm, 1*cm, 1*cm, 1.8*cm, 2*cm, 1.3*cm, 5*cm, 5*cm]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('WORDWRAP', (0, 0), (-1, 0), True),
        
        # Corpo - fonte 7pt para legibilidade
        ('FONTSIZE', (0, 1), (-1, -2), 7),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # #
        ('ALIGN', (3, 1), (4, -1), 'CENTER'),  # Unidade, Qtd
        ('ALIGN', (5, 1), (6, -1), 'RIGHT'),   # Valores
        ('ALIGN', (7, 1), (7, -1), 'CENTER'),  # Prioridade
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('WORDWRAP', (2, 1), (2, -1), True),   # Descrição
        ('WORDWRAP', (8, 1), (8, -1), True),   # Justificativa
        ('WORDWRAP', (9, 1), (9, -1), True),   # Classificação
        
        # Linhas alternadas para legibilidade
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F2F2F2')]),
        
        # Linha de Total - destaque
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFC000')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 9),
        
        # Bordas
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        
        # Padding adequado
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 10*mm))
    
    # Área de Assinaturas - otimizada para assinatura digital
    # As assinaturas são posicionadas à esquerda, deixando espaço na margem direita
    elements.append(Paragraph('<b>ASSINATURAS</b>', ParagraphStyle('Header', fontSize=9, fontName='Helvetica-Bold', spaceAfter=8)))
    
    sig_data = [
        ['_' * 50, '_' * 50],
        [pac['secretario'], pac['fiscal']],
        ['Secretário(a) Responsável', 'Fiscal do Contrato'],
        ['', ''],
        ['Data: ___/___/______', 'Data: ___/___/______']
    ]
    
    # Largura reduzida para deixar espaço para assinatura digital na margem direita
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
    
    # Tabela de itens - CAMPOS COMPLETOS sem truncamento
    # Conforme especificação: todos os campos devem ser exibidos integralmente
    elements.append(Paragraph('<b>DETALHAMENTO DOS ITENS</b>', ParagraphStyle('Header', fontSize=9, fontName='Helvetica-Bold', spaceAfter=2)))
    
    # Cabeçalhos COMPLETOS conforme especificação técnica
    table_data = [['#', 'Código\nCATMAT', 'Descrição do Objeto', 'Justificativa da Contratação', 'Und', 'Qtd\nTotal', 'Valor\nUnitário', 'Valor\nTotal', 'Prior.', 'Classificação Orçamentária\n(Código - Subitem)']]
    
    for idx, item in enumerate(items, start=1):
        # Classificação Orçamentária COMPLETA - destaque para Subitem
        classificacao_text = ''
        if item.get('codigo_classificacao'):
            classificacao_text = f"{item['codigo_classificacao']}"
            if item.get('subitem_classificacao'):
                # SUBITEM COMPLETO - identificador do PAC para licitação
                classificacao_text += f"\n{item['subitem_classificacao']}"
        
        # Justificativa COMPLETA - sem truncamento
        justificativa = item.get('justificativa', '') or 'Não informada'
        
        # Descrição COMPLETA - sem truncamento
        descricao = item.get('descricao', '')
        
        table_data.append([
            str(idx),
            item.get('catmat', ''),  # Código COMPLETO
            Paragraph(f"<font size=7>{descricao}</font>", styles['Normal']),  # Descrição COMPLETA
            Paragraph(f"<font size=6>{justificativa}</font>", styles['Normal']),  # Justificativa COMPLETA
            item['unidade'],
            str(int(item.get('quantidade_total', 0))),
            f"R$ {item['valorUnitario']:,.2f}",
            f"R$ {item['valorTotal']:,.2f}",
            item.get('prioridade', ''),  # Prioridade COMPLETA
            Paragraph(f"<font size=6>{classificacao_text}</font>", styles['Normal'])  # Classificação COMPLETA
        ])
    
    # Linha de total
    total = sum(item['valorTotal'] for item in items)
    total_qtd = sum(item.get('quantidade_total', 0) for item in items)
    table_data.append([
        '', '', Paragraph('<b>TOTAL GERAL:</b>', styles['Normal']), '', '',
        str(int(total_qtd)), '', f"R$ {total:,.2f}", '', ''
    ])
    
    # Larguras otimizadas para campos COMPLETOS
    # Paisagem: ~244mm disponíveis (297 - 8 - 25 - margens internas)
    # Retrato: ~150mm disponíveis (210 - 10 - 30 - margens internas)
    if orientation.lower() == 'portrait':
        col_widths = [0.5*cm, 1.2*cm, 3.5*cm, 3*cm, 0.8*cm, 1*cm, 1.5*cm, 1.6*cm, 0.8*cm, 2.5*cm]
    else:
        col_widths = [0.6*cm, 1.5*cm, 5*cm, 5*cm, 1*cm, 1.2*cm, 2*cm, 2.2*cm, 1*cm, 4.5*cm]
    
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
    """Exporta todos os processos para PDF com margens padronizadas"""
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
            'system': 'PAC Acaiaca 2026 - Portal de Transparência'
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
                <a href="https://muni-docs.preview.emergentagent.com/doem-publico" 
                   style="background: #1F4E78; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    📥 Acessar o DOEM
                </a>
            </div>
        </div>
        
        <div style="background: #1F4E78; color: white; padding: 15px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px;">
            <p style="margin: 0;">Prefeitura Municipal de Acaiaca - MG</p>
            <p style="margin: 5px 0 0 0; opacity: 0.8;">Este é um email automático. Não responda.</p>
            <p style="margin: 5px 0 0 0; opacity: 0.7;">
                <a href="https://muni-docs.preview.emergentagent.com/newsletter/cancelar" style="color: #90caf9;">Cancelar inscrição</a>
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

def draw_signature_seal(canvas, page_width, page_height, signers: list, validation_code: str, qr_code_url: str = None):
    """
    Desenha o selo de assinatura digital na lateral direita da página.
    
    Args:
        canvas: Canvas do reportlab
        page_width: Largura da página
        page_height: Altura da página
        signers: Lista de dicts com dados dos assinantes (nome, cpf, cargo, data)
        validation_code: Código para validação do documento
        qr_code_url: URL para o QR Code de validação (opcional)
    """
    from reportlab.lib.utils import ImageReader
    import qrcode
    
    seal_width = 50 * mm
    seal_x = page_width - seal_width - 5 * mm
    seal_y = page_height - 40 * mm
    
    # Desenhar borda do selo
    canvas.setStrokeColor(colors.HexColor("#003366"))
    canvas.setLineWidth(1.5)
    
    # Calcular altura baseada no número de assinantes
    base_height = 60 * mm
    signer_height = 22 * mm * len(signers)
    qr_height = 35 * mm if qr_code_url else 0
    seal_height = base_height + signer_height + qr_height
    
    # Ajustar posição Y para não ultrapassar a página
    if seal_y - seal_height < 20 * mm:
        seal_y = seal_height + 20 * mm
    
    # Desenhar retângulo do selo
    canvas.roundRect(seal_x, seal_y - seal_height, seal_width, seal_height, 3 * mm, stroke=1, fill=0)
    
    # Desenhar header do selo
    header_height = 18 * mm
    canvas.setFillColor(colors.HexColor("#003366"))
    canvas.rect(seal_x, seal_y - header_height, seal_width, header_height, stroke=0, fill=1)
    
    # Texto "DOCUMENTO ASSINADO DIGITALMENTE"
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 6)
    canvas.drawCentredString(seal_x + seal_width/2, seal_y - 6 * mm, "DOCUMENTO")
    canvas.drawCentredString(seal_x + seal_width/2, seal_y - 10 * mm, "ASSINADO")
    canvas.drawCentredString(seal_x + seal_width/2, seal_y - 14 * mm, "DIGITALMENTE")
    
    # Data e hora da assinatura
    canvas.setFillColor(colors.HexColor("#003366"))
    canvas.setFont("Helvetica", 5)
    current_date = datetime.now().strftime("%d/%m/%Y %H:%M")
    canvas.drawCentredString(seal_x + seal_width/2, seal_y - header_height - 4 * mm, f"Data: {current_date}")
    
    # Desenhar informações de cada assinante
    current_y = seal_y - header_height - 10 * mm
    
    for i, signer in enumerate(signers):
        # Nome do assinante (itálico)
        canvas.setFont("Helvetica-BoldOblique", 6)
        canvas.setFillColor(colors.HexColor("#003366"))
        nome = signer.get('nome', 'N/A')[:25]
        canvas.drawCentredString(seal_x + seal_width/2, current_y, nome)
        current_y -= 4 * mm
        
        # Cargo
        canvas.setFont("Helvetica", 5)
        cargo = signer.get('cargo', '')[:30]
        if cargo:
            canvas.drawCentredString(seal_x + seal_width/2, current_y, cargo)
            current_y -= 3 * mm
        
        # CPF mascarado
        cpf_masked = mask_cpf(signer.get('cpf', ''))
        canvas.drawCentredString(seal_x + seal_width/2, current_y, f"CPF: {cpf_masked}")
        current_y -= 3 * mm
        
        # Email (se disponível)
        email = signer.get('email', '')
        if email:
            canvas.setFont("Helvetica", 4)
            email_display = email[:30] + "..." if len(email) > 30 else email
            canvas.drawCentredString(seal_x + seal_width/2, current_y, email_display)
            current_y -= 3 * mm
        
        # Linha separadora entre assinantes
        if i < len(signers) - 1:
            canvas.setStrokeColor(colors.HexColor("#cccccc"))
            canvas.setLineWidth(0.5)
            canvas.line(seal_x + 5 * mm, current_y, seal_x + seal_width - 5 * mm, current_y)
            current_y -= 4 * mm
    
    # QR Code para validação (se fornecido URL)
    if qr_code_url:
        current_y -= 3 * mm
        
        # Gerar QR Code
        qr = qrcode.QRCode(version=1, box_size=2, border=1)
        qr.add_data(qr_code_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="#003366", back_color="white")
        
        # Salvar QR temporariamente
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # Desenhar QR Code
        qr_size = 20 * mm
        qr_x = seal_x + (seal_width - qr_size) / 2
        canvas.drawImage(ImageReader(qr_buffer), qr_x, current_y - qr_size, width=qr_size, height=qr_size)
        current_y -= qr_size + 3 * mm
        
        # Texto de validação
        canvas.setFont("Helvetica", 4)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.drawCentredString(seal_x + seal_width/2, current_y, "Escaneie para validar")
        current_y -= 3 * mm
    
    # Código de validação
    canvas.setFont("Helvetica-Bold", 5)
    canvas.setFillColor(colors.HexColor("#003366"))
    canvas.drawCentredString(seal_x + seal_width/2, current_y, f"Cód: {validation_code}")
    
    # Linha final com URL de validação
    current_y -= 4 * mm
    canvas.setFont("Helvetica", 4)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawCentredString(seal_x + seal_width/2, current_y, "acaiaca.mg.gov.br/validar")

async def get_doem_config() -> dict:
    """Obtém ou cria configuração padrão do DOEM"""
    config = await db.doem_config.find_one({'config_id': 'doem_config_main'}, {'_id': 0})
    if not config:
        config = {
            'config_id': 'doem_config_main',
            'nome_municipio': 'Acaiaca',
            'uf': 'MG',
            'prefeito': '',
            'ano_inicio': 2026,
            'ultimo_numero_edicao': 0,
            'segmentos': DOEM_SEGMENTOS,
            'tipos_publicacao': DOEM_TIPOS_PUBLICACAO
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
    
    assinatura = edicao.get('assinatura_digital', {})
    assinantes = assinatura.get('assinantes', [])
    
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
    
    signature_data = assinante_user.get('signature_data', {})
    
    novo_assinante = {
        'user_id': assinante_req.user_id,
        'nome': assinante_user.get('name', ''),
        'cpf': signature_data.get('cpf', ''),
        'cargo': signature_data.get('cargo', ''),
        'email': assinante_user.get('email', ''),
        'data_assinatura': None  # Será preenchido quando assinar
    }
    
    # Verificar se já está na lista
    assinatura = edicao.get('assinatura_digital', {})
    assinantes = assinatura.get('assinantes', [])
    
    if any(a.get('user_id') == assinante_req.user_id for a in assinantes):
        raise HTTPException(status_code=400, detail="Este usuário já está na lista de assinantes")
    
    assinantes.append(novo_assinante)
    
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
    
    assinatura = edicao.get('assinatura_digital', {})
    assinantes = assinatura.get('assinantes', [])
    
    assinantes = [a for a in assinantes if a.get('user_id') != user_id]
    
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
    
    # Buscar dados de assinatura do usuário
    user_doc = await db.users.find_one({'user_id': user.user_id}, {'_id': 0})
    user_signature = user_doc.get('signature_data', {}) if user_doc else {}
    user_info = {
        'nome': user.name,
        'email': user.email,
        'cpf': user_signature.get('cpf', ''),
        'cargo': user_signature.get('cargo', '')
    }
    
    # Gerar PDF e assinatura
    pdf_buffer = await gerar_pdf_doem(edicao)
    assinatura = gerar_assinatura_simulada(pdf_buffer.getvalue(), user_info)
    
    # Salvar registro de assinatura para validação
    signers = [{
        'nome': user_info['nome'],
        'cpf': user_info['cpf'],
        'cargo': user_info['cargo'],
        'email': user_info['email']
    }]
    await save_document_signature(
        doc_id=edicao_id,
        doc_type=f"DOEM - Edição {edicao.get('numero_edicao', '')} / {edicao.get('ano', '')}",
        signers=signers,
        hash_doc=assinatura.hash_documento,
        validation_code=assinatura.validation_code
    )
    
    # Atualizar status
    await db.doem_edicoes.update_one(
        {'edicao_id': edicao_id},
        {'$set': {
            'status': 'publicado',
            'assinatura_digital': assinatura.model_dump(),
            'notificacao_enviada': False,
            'updated_at': datetime.now(timezone.utc)
        }}
    )
    
    # Enviar notificações em background
    notificacao_msg = ""
    if enviar_notificacao:
        edicao_atualizada = await db.doem_edicoes.find_one({'edicao_id': edicao_id}, {'_id': 0})
        pdf_buffer.seek(0)  # Reset buffer position
        try:
            enviados = await enviar_notificacao_doem(edicao_atualizada, pdf_buffer)
            await db.doem_edicoes.update_one(
                {'edicao_id': edicao_id},
                {'$set': {'notificacao_enviada': True}}
            )
            notificacao_msg = f" Notificações enviadas para {enviados} destinatário(s)."
        except Exception as e:
            logging.error(f"Erro ao enviar notificações: {e}")
            notificacao_msg = " Falha ao enviar notificações."
    
    return {
        'message': f'Edição publicada com sucesso!{notificacao_msg}',
        'assinatura': assinatura.model_dump()
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
            signers = [{
                'nome': assinatura.get('titular', 'Prefeitura Municipal de Acaiaca'),
                'cargo': assinatura.get('cargo', 'Órgão Publicador'),
                'cpf': assinatura.get('cpf', ''),
                'email': assinatura.get('email', 'contato@acaiaca.mg.gov.br')
            }]
            # URL para validação
            qr_url = f"https://muni-docs.preview.emergentagent.com/validar?code={validation_code}"
            draw_signature_seal(canvas, page_width, page_height, signers, validation_code, qr_url)
        
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
                    <a href="https://muni-docs.preview.emergentagent.com/api/public/newsletter/confirmar/{token}" 
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
            <a href="https://muni-docs.preview.emergentagent.com/doem-publico" style="color: #1F4E78;">Acessar o DOEM</a>
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

app.include_router(api_router)
app.include_router(public_router)  # Rotas públicas para transparência
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','), allow_methods=["*"], allow_headers=["*"])
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
