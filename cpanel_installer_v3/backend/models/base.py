"""
Modelos Pydantic compartilhados
"""
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# ============ MODELOS DE USUÁRIO ============

class UserPermissions(BaseModel):
    can_view: bool = True
    can_edit: bool = False
    can_delete: bool = False
    can_export: bool = False
    can_manage_users: bool = False
    is_full_admin: bool = False

class UserSignatureData(BaseModel):
    cpf: Optional[str] = None
    cargo: Optional[str] = None
    endereco: Optional[str] = None
    cep: Optional[str] = None
    telefone: Optional[str] = None

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

# ============ MODELOS PAC ============

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
    codigo_classificacao: Optional[str] = None
    subitem_classificacao: Optional[str] = None
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
    codigo_classificacao: Optional[str] = None
    subitem_classificacao: Optional[str] = None

class PACUpdate(BaseModel):
    secretaria: Optional[str] = None
    secretario: Optional[str] = None
    fiscal: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    endereco: Optional[str] = None
    ano: Optional[str] = None
    codigo_classificacao: Optional[str] = None
    subitem_classificacao: Optional[str] = None

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

# ============ MODELOS PAC GERAL ============

class PACGeral(BaseModel):
    model_config = ConfigDict(extra="ignore")
    pac_geral_id: str
    user_id: str
    nome_secretaria: str
    secretario: str
    fiscal_contrato: Optional[str] = None
    telefone: str
    email: EmailStr
    endereco: str
    cep: str
    ano: str = "2026"
    secretarias_selecionadas: List[str]
    created_at: datetime
    updated_at: datetime

class PACGeralCreate(BaseModel):
    nome_secretaria: str
    secretario: str
    fiscal_contrato: Optional[str] = None
    telefone: str
    email: EmailStr
    endereco: str
    cep: str
    ano: str = "2026"
    secretarias_selecionadas: List[str]

class PACGeralUpdate(BaseModel):
    nome_secretaria: Optional[str] = None
    secretario: Optional[str] = None
    fiscal_contrato: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    endereco: Optional[str] = None
    cep: Optional[str] = None
    ano: Optional[str] = None
    secretarias_selecionadas: Optional[List[str]] = None

class PACGeralItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    item_id: str
    pac_geral_id: str
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
    quantidade_total: float
    valorUnitario: float
    valorTotal: float
    prioridade: str
    justificativa: Optional[str] = None
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

# ============ MODELOS DE PROCESSO ============

class Processo(BaseModel):
    model_config = ConfigDict(extra="ignore")
    processo_id: str
    user_id: str
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
    ano: int = 2025
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
    ano: int = None
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

# ============ MODELO DE RESPOSTA PAGINADA ============

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
