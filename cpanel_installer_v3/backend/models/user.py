"""
User and Authentication Models - Pydantic schemas
"""
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, Literal
from datetime import datetime

# Tipos de usuário
TIPO_USUARIO = Literal["SERVIDOR", "PESSOA_EXTERNA"]

class UserPermissions(BaseModel):
    """User permissions model"""
    can_view: bool = True
    can_edit: bool = False
    can_delete: bool = False
    can_export: bool = False
    can_manage_users: bool = False
    is_full_admin: bool = False
    # Restrição específica para MROSC
    mrosc_only: bool = False  # Se True, usuário só pode acessar MROSC

class UserSignatureData(BaseModel):
    """User signature data for digital documents"""
    cpf: Optional[str] = None
    cargo: Optional[str] = None
    endereco: Optional[str] = None
    cep: Optional[str] = None
    telefone: Optional[str] = None

class User(BaseModel):
    """User model"""
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: EmailStr
    name: str
    is_admin: bool = False
    is_active: bool = True
    tipo_usuario: str = "SERVIDOR"  # SERVIDOR ou PESSOA_EXTERNA
    picture: Optional[str] = None
    permissions: Optional[UserPermissions] = None
    signature_data: Optional[UserSignatureData] = None
    created_at: datetime

class UserCreate(BaseModel):
    """User creation model"""
    email: EmailStr
    password: str
    name: str
    is_admin: bool = False
    tipo_usuario: str = "SERVIDOR"  # SERVIDOR ou PESSOA_EXTERNA
    permissions: Optional[UserPermissions] = None
    signature_data: Optional[UserSignatureData] = None

class UserUpdate(BaseModel):
    """User update model"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: bool = True
    tipo_usuario: Optional[str] = None
    permissions: Optional[UserPermissions] = None
    signature_data: Optional[UserSignatureData] = None

class UserLogin(BaseModel):
    """User login credentials"""
    email: EmailStr
    password: str

class UserListItem(BaseModel):
    """User list item model"""
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: EmailStr
    name: str
    is_admin: bool
    is_active: bool = True
    tipo_usuario: str = "SERVIDOR"
    permissions: Optional[UserPermissions] = None
    signature_data: Optional[UserSignatureData] = None
    created_at: datetime

