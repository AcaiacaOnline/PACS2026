"""
Modelos Newsletter/Notificações
"""
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List
from datetime import datetime

class NewsletterInscrito(BaseModel):
    model_config = ConfigDict(extra="ignore")
    inscrito_id: str
    email: EmailStr
    nome: str
    tipo: str = "publico"
    ativo: bool = True
    segmentos_interesse: List[str] = []
    data_inscricao: datetime
    data_confirmacao: Optional[datetime] = None
    confirmado: bool = False
    token_confirmacao: Optional[str] = None

class NewsletterInscricaoPublica(BaseModel):
    email: EmailStr
    nome: str
    segmentos_interesse: List[str] = []

class NewsletterInscricaoManual(BaseModel):
    email: EmailStr
    nome: str
    segmentos_interesse: List[str] = []
    confirmado: bool = True
