"""
Modelos DOEM (Diário Oficial Eletrônico Municipal)
"""
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List, Dict
from datetime import datetime

# Segmentos/Categorias do DOEM
DOEM_SEGMENTOS = [
    "Portarias",
    "Leis",
    "Decretos",
    "Resoluções",
    "Editais",
    "Prestações de Contas",
    "Processos Administrativos",
    "Publicações do Legislativo",
    "Publicações do Terceiro Setor"
]

# Tipos de publicação por segmento
DOEM_TIPOS_PUBLICACAO = {
    "Portarias": ["Portaria", "Portaria Conjunta"],
    "Leis": ["Lei Ordinária", "Lei Complementar", "Emenda à Lei Orgânica"],
    "Decretos": ["Decreto", "Decreto Regulamentar"],
    "Resoluções": ["Resolução", "Resolução Conjunta"],
    "Editais": ["Edital de Licitação", "Edital de Convocação", "Edital de Seleção", "Aviso de Licitação"],
    "Prestações de Contas": ["Prestação de Contas", "Relatório de Gestão", "Balanço"],
    "Processos Administrativos": ["Extrato de Contrato", "Termo Aditivo", "Ata de Registro de Preços", "Homologação", "Ratificação"],
    "Publicações do Legislativo": ["Projeto de Lei", "Ata de Sessão", "Parecer", "Moção", "Requerimento"],
    "Publicações do Terceiro Setor": ["Termo de Parceria", "Convênio", "Prestação de Contas OSC", "Chamamento Público"]
}

class DOEMPublicacao(BaseModel):
    publicacao_id: str
    titulo: str
    texto: str
    secretaria: str
    segmento: str = "Decretos"
    tipo: str
    ordem: int = 1

class DOEMPublicacaoCreate(BaseModel):
    titulo: str
    texto: str
    secretaria: str = "Gabinete do Prefeito"
    segmento: str = "Decretos"
    tipo: str = "Decreto"
    ordem: int = 1

class DOEMAssinante(BaseModel):
    user_id: str
    nome: str
    cpf: Optional[str] = None
    cargo: Optional[str] = None
    email: Optional[str] = None
    data_assinatura: Optional[datetime] = None

class DOEMAssinatura(BaseModel):
    assinado: bool = False
    data_assinatura: Optional[datetime] = None
    hash_documento: Optional[str] = None
    tipo_certificado: str = "ICP-Brasil (Simulado)"
    titular: str = "Prefeitura Municipal de Acaiaca"
    validation_code: Optional[str] = None
    cpf: Optional[str] = None
    cargo: Optional[str] = None
    email: Optional[str] = None
    assinantes: Optional[List[DOEMAssinante]] = None
    assinatura_em_lote: bool = False

class DOEMEdicao(BaseModel):
    model_config = ConfigDict(extra="ignore")
    edicao_id: str
    numero_edicao: int
    ano: int
    data_publicacao: datetime
    data_criacao: datetime
    status: str = "rascunho"
    publicacoes: List[DOEMPublicacao] = []
    criado_por: str
    assinatura_digital: Optional[DOEMAssinatura] = None
    notificacao_enviada: bool = False
    created_at: datetime
    updated_at: datetime

class DOEMEdicaoCreate(BaseModel):
    data_publicacao: Optional[datetime] = None
    publicacoes: List[DOEMPublicacaoCreate] = []

class DOEMEdicaoUpdate(BaseModel):
    data_publicacao: Optional[datetime] = None
    status: Optional[str] = None
    publicacoes: Optional[List[DOEMPublicacaoCreate]] = None

class DOEMConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    config_id: str = "doem_config_main"
    nome_municipio: str = "Acaiaca"
    uf: str = "MG"
    prefeito: str = ""
    ano_inicio: int = 2026
    ultimo_numero_edicao: int = 0
    segmentos: List[str] = DOEM_SEGMENTOS
    tipos_publicacao: Dict[str, List[str]] = DOEM_TIPOS_PUBLICACAO

class DOEMConfigUpdate(BaseModel):
    nome_municipio: Optional[str] = None
    uf: Optional[str] = None
    prefeito: Optional[str] = None
    segmentos: Optional[List[str]] = None
    tipos_publicacao: Optional[Dict[str, List[str]]] = None
