"""
Authentication routes
"""
from fastapi import APIRouter, HTTPException, Request, Response
from datetime import datetime, timezone, timedelta
from typing import List
import uuid
import bcrypt
import jwt
import os

router = APIRouter(prefix="/auth", tags=["Authentication"])

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

def get_routes(db, User, UserCreate, UserUpdate, UserLogin, UserListItem, UserPermissions, get_current_user):
    """Factory function to create routes with dependencies"""
    
    @router.post("/register", response_model=User)
    async def register(user_data: UserCreate):
        existing = await db.users.find_one({'email': user_data.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        user_doc = {
            'user_id': f"user_{uuid.uuid4().hex[:12]}",
            'email': user_data.email,
            'password_hash': hash_password(user_data.password),
            'name': user_data.name,
            'is_admin': user_data.is_admin,
            'is_active': True,
            'permissions': user_data.permissions.model_dump() if user_data.permissions else UserPermissions().model_dump(),
            'signature_data': user_data.signature_data.model_dump() if user_data.signature_data else None,
            'created_at': datetime.now(timezone.utc)
        }
        await db.users.insert_one(user_doc)
        del user_doc['password_hash']
        del user_doc['_id']
        return User(**user_doc)

    @router.post("/login")
    async def login(credentials: UserLogin, response: Response):
        user = await db.users.find_one({'email': credentials.email}, {'_id': 0})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        if not verify_password(credentials.password, user.get('password_hash', '')):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        if not user.get('is_active', True):
            raise HTTPException(status_code=401, detail="User account is disabled")
        
        token = create_jwt_token(user['user_id'])
        return {"token": token, "user": User(**{k: v for k, v in user.items() if k != 'password_hash'})}

    @router.get("/me", response_model=User)
    async def get_me(request: Request):
        return await get_current_user(request)

    @router.put("/me", response_model=User)
    async def update_me(request: Request, user_data: UserUpdate):
        current_user = await get_current_user(request)
        update_data = user_data.model_dump(exclude_unset=True, exclude_none=True)
        
        if 'password' in update_data:
            update_data['password_hash'] = hash_password(update_data.pop('password'))
        
        if 'permissions' in update_data and update_data['permissions']:
            update_data['permissions'] = update_data['permissions']
        
        if 'signature_data' in update_data and update_data['signature_data']:
            update_data['signature_data'] = update_data['signature_data']
        
        if update_data:
            await db.users.update_one(
                {'user_id': current_user.user_id},
                {'$set': update_data}
            )
        
        updated_user = await db.users.find_one({'user_id': current_user.user_id}, {'_id': 0, 'password_hash': 0})
        return User(**updated_user)

    @router.post("/logout")
    async def logout(request: Request, response: Response):
        token = request.cookies.get('session_token')
        if not token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if token:
            await db.user_sessions.delete_one({'session_token': token})
        
        response.delete_cookie('session_token')
        return {"message": "Logged out successfully"}

    return router
