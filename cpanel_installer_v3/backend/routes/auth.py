"""
Authentication Routes - Refactored Module
Handles user registration, login, logout, and session management
"""
from fastapi import APIRouter, HTTPException, Request, Response
from datetime import datetime, timezone, timedelta
from typing import List
import uuid
import bcrypt
import jwt
import os
import httpx
import logging

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Constants
JWT_SECRET = os.environ.get('JWT_SECRET', 'pac-acaiaca-secret-key-2026')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DAYS = 7

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

def setup_auth_routes(db, User, UserCreate, UserUpdate, UserLogin, UserListItem, UserPermissions):
    """Setup authentication routes with database dependency"""
    
    async def get_current_user(request: Request) -> User:
        """Extract and validate user from request token"""
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
    
    @router.post("/register", response_model=User)
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

    @router.post("/login")
    async def login(credentials: UserLogin, response: Response):
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
        return await get_current_user(request)

    @router.get("/oauth/session")
    async def oauth_session(request: Request, response: Response):
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
        return User(**user_doc)

    @router.post("/logout")
    async def logout(request: Request, response: Response):
        token = request.cookies.get('session_token')
        if token:
            await db.user_sessions.delete_many({'session_token': token})
        response.delete_cookie('session_token', path='/')
        return {'message': 'Logged out'}

    return router, get_current_user
