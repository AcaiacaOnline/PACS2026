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
    numero_processo: str  # Ex: PRC - 0006/2025 (OBRIGATÓRIO)
    modalidade_contratacao: Optional[str] = None  # Pregão Eletrônico, Dispensa, Inexigibilidade, etc.
    numero_modalidade: Optional[str] = None  # Número da modalidade (Ex: PE 001/2026)
    status: Optional[str] = None  # Em Elaboração, Aprovado, Em Licitação, Homologado, Contratado, Concluído
    objeto: str  # Descrição do processo
    responsavel: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_autuacao: Optional[datetime] = None
    data_contrato: Optional[datetime] = None
    secretaria: Optional[str] = None
    secretario: Optional[str] = None
    ano: int = 2025  # Ano do processo
    observacoes: Optional[str] = None
    fornecedor: Optional[str] = None
    valor_estimado: Optional[float] = None
    valor_contratado: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    # Campos legados para compatibilidade (serão removidos em versão futura)
    modalidade: Optional[str] = None  # DEPRECATED: usar modalidade_contratacao
    situacao: Optional[str] = None  # DEPRECATED: usar status

class ProcessoCreate(BaseModel):
    """Process creation model"""
    numero_processo: str  # OBRIGATÓRIO *
    modalidade_contratacao: str
    status: str = "Em Elaboração"
    objeto: str
    responsavel: Optional[str] = None
    numero_modalidade: Optional[str] = None  # Campo para número da modalidade
    data_inicio: Optional[datetime] = None
    data_autuacao: Optional[datetime] = None
    data_contrato: Optional[datetime] = None
    secretaria: Optional[str] = None
    secretario: Optional[str] = None
    ano: Optional[int] = None  # Será extraído do numero_processo se não fornecido
    observacoes: Optional[str] = None
    fornecedor: Optional[str] = None
    valor_estimado: Optional[float] = None
    valor_contratado: Optional[float] = None

class ProcessoUpdate(BaseModel):
    """Process update model"""
    numero_processo: Optional[str] = None
    modalidade_contratacao: Optional[str] = None
    status: Optional[str] = None
    objeto: Optional[str] = None
    responsavel: Optional[str] = None
    numero_modalidade: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_autuacao: Optional[datetime] = None
    data_contrato: Optional[datetime] = None
    secretaria: Optional[str] = None
    secretario: Optional[str] = None
    ano: Optional[int] = None
    observacoes: Optional[str] = None
    fornecedor: Optional[str] = None
    valor_estimado: Optional[float] = None
    valor_contratado: Optional[float] = None

class PaginatedResponse(BaseModel):
    """Generic paginated response model"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
