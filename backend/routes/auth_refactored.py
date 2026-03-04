"""
Auth Module - Funções e rotas de autenticação
Planejamento Acaiaca - Sistema de Gestão Municipal
"""
from fastapi import APIRouter, HTTPException, Request, Response
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import uuid
import os
import httpx
import logging

# Configuração
JWT_SECRET = os.environ.get('JWT_SECRET', 'pac-acaiaca-secret-key-2026')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DAYS = 7

# Router
router = APIRouter(prefix="/auth", tags=["Autenticação"])

# Database reference (será injetada)
db = None

def setup_auth_routes(database):
    """Configura o módulo com a referência do banco de dados"""
    global db
    db = database


# ===== MODELOS =====
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    tipo_usuario: Optional[str] = "SERVIDOR"

class User(BaseModel):
    user_id: str
    email: str
    name: str
    is_admin: bool = False
    is_active: bool = True
    tipo_usuario: Optional[str] = "SERVIDOR"
    picture: Optional[str] = None
    permissions: Optional[dict] = None
    signature_data: Optional[dict] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== FUNÇÕES AUXILIARES =====
def hash_password(password: str) -> str:
    """Hash de senha usando bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verifica senha contra hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_jwt_token(user_id: str) -> str:
    """Cria token JWT para usuário"""
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRATION_DAYS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(request: Request) -> User:
    """Obtém usuário atual a partir do token JWT"""
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


# ===== ROTAS =====
@router.post("/register", response_model=User)
async def register(user_data: UserCreate):
    """Registra novo usuário"""
    existing = await db.users.find_one({'email': user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    tipo_usuario = user_data.tipo_usuario or 'SERVIDOR'
    
    permissions = {
        'can_view': True,
        'can_edit': tipo_usuario == 'SERVIDOR',
        'can_delete': False,
        'can_export': tipo_usuario == 'SERVIDOR',
        'can_manage_users': False,
        'is_full_admin': False,
        'mrosc_only': tipo_usuario == 'PESSOA_EXTERNA'
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


@router.post("/login")
async def login(credentials: UserLogin, response: Response):
    """Autentica usuário"""
    user_doc = await db.users.find_one({'email': credentials.email}, {'_id': 0})
    if not user_doc or not verify_password(credentials.password, user_doc['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token(user_doc['user_id'])
    response.set_cookie(
        key='session_token', 
        value=token, 
        httponly=True, 
        secure=True, 
        samesite='none', 
        max_age=JWT_EXPIRATION_DAYS*24*60*60, 
        path='/'
    )
    user_doc.pop('password_hash')
    return {'token': token, 'user': User(**user_doc)}


@router.get("/me", response_model=User)
async def get_me(request: Request):
    """Retorna dados do usuário autenticado"""
    return await get_current_user(request)


@router.get("/oauth/session")
async def oauth_session(request: Request, response: Response):
    """Autenticação via OAuth (Google)"""
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session ID")
    
    async with httpx.AsyncClient() as client:
        try:
            auth_response = await client.get(
                'https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data', 
                headers={'X-Session-ID': session_id}
            )
            auth_response.raise_for_status()
            data = auth_response.json()
        except Exception as e:
            logging.error(f"OAuth error: {str(e)}")
            raise HTTPException(status_code=401, detail=f"OAuth failed: {str(e)}")
    
    user_doc = await db.users.find_one({'email': data['email']}, {'_id': 0})
    if not user_doc:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user_doc = {
            'user_id': user_id, 
            'email': data['email'], 
            'name': data['name'], 
            'password_hash': None, 
            'is_admin': False, 
            'is_active': True, 
            'picture': data.get('picture'), 
            'created_at': datetime.now(timezone.utc)
        }
        await db.users.insert_one(user_doc)
        user_doc.pop('_id', None)
    
    token_data = {
        "user_id": user_doc['user_id'],
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    jwt_token = jwt.encode(token_data, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    session_doc = {
        'user_id': user_doc['user_id'], 
        'session_token': data['session_token'], 
        'expires_at': datetime.now(timezone.utc) + timedelta(days=7), 
        'created_at': datetime.now(timezone.utc)
    }
    await db.user_sessions.insert_one(session_doc)
    response.set_cookie(
        key='session_token', 
        value=data['session_token'], 
        httponly=True, 
        secure=True, 
        samesite='none', 
        max_age=7*24*60*60, 
        path='/'
    )
    
    user_doc.pop('password_hash', None)
    user_doc.pop('_id', None)
    
    if 'created_at' in user_doc and isinstance(user_doc['created_at'], datetime):
        user_doc['created_at'] = user_doc['created_at'].isoformat()
    
    return {**user_doc, "token": jwt_token}


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Encerra sessão do usuário"""
    token = request.cookies.get('session_token')
    if token:
        await db.user_sessions.delete_many({'session_token': token})
    response.delete_cookie('session_token', path='/')
    return {'message': 'Logged out'}
