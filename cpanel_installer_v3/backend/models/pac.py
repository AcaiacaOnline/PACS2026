"""
PAC (Plano Anual de Contratações) Models - Pydantic schemas
"""
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, Dict, List
from datetime import datetime

class PAC(BaseModel):
    """PAC (Individual) model"""
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
    """PAC creation model"""
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
    """PAC update model"""
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
    """PAC item model"""
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
    """PAC item creation model"""
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
    """PAC item update model"""
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

# PAC Geral Models
class PACGeral(BaseModel):
    """PAC Geral (Consolidated) model"""
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
    """PAC Geral creation model"""
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
    """PAC Geral update model"""
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
    """PAC Geral item model"""
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
    """PAC Geral item creation model"""
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
    """PAC Geral item update model"""
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
