"""
User Management Routes - Refactored Module
Handles CRUD operations for users (admin only)
"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from typing import List
import uuid

router = APIRouter(prefix="/api/users", tags=["User Management"])

def setup_users_routes(db, User, UserCreate, UserUpdate, UserListItem, UserPermissions, get_current_user, hash_password):
    """Setup user management routes with dependencies"""
    
    async def require_admin(request: Request) -> User:
        user = await get_current_user(request)
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        return user

    @router.get("", response_model=List[UserListItem])
    async def get_users(request: Request):
        await require_admin(request)
        users = await db.users.find({}, {'_id': 0, 'password_hash': 0}).to_list(1000)
        return [UserListItem(**u) for u in users]

    @router.post("", response_model=UserListItem)
    async def create_user_admin(user_data: UserCreate, request: Request):
        await require_admin(request)
        existing = await db.users.find_one({'email': user_data.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        
        # Prepare permissions
        permissions_data = None
        if user_data.permissions:
            permissions_data = user_data.permissions.model_dump()
        elif user_data.is_admin:
            permissions_data = {
                'can_view': True,
                'can_edit': True,
                'can_delete': True,
                'can_export': True,
                'can_manage_users': True,
                'is_full_admin': True
            }
        else:
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

    @router.put("/{user_id}", response_model=UserListItem)
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
        
        if update_data.get('permissions', {}).get('is_full_admin'):
            update_data['is_admin'] = True
        
        await db.users.update_one({'user_id': user_id}, {'$set': update_data})
        updated_user = await db.users.find_one({'user_id': user_id}, {'_id': 0, 'password_hash': 0})
        return UserListItem(**updated_user)

    @router.delete("/{user_id}")
    async def delete_user_admin(user_id: str, request: Request):
        admin = await require_admin(request)
        if user_id == admin.user_id:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        result = await db.users.delete_one({'user_id': user_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        await db.user_sessions.delete_many({'user_id': user_id})
        return {'message': 'User deleted'}

    return router
