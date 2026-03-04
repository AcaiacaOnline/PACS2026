"""
Modelos de PAC Geral - Planejamento Acaiaca
"""
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime


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
