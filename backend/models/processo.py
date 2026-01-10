"""
Processo (Process Management) Models - Pydantic schemas
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime

class Processo(BaseModel):
    """Process model"""
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
    """Process creation model"""
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
    """Process update model"""
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

class PaginatedResponse(BaseModel):
    """Generic paginated response model"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
