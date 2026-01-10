"""
Modelos de PAC Geral Obras e Serviços - Planejamento Acaiaca
Lei 14.133/2021 e Portaria 448/ME
"""
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime


CLASSIFICACAO_OBRAS_SERVICOS = {
    "339040": {
        "nome": "Serviços de Tecnologia da Informação e Comunicação - PJ",
        "categoria": "SERVICOS_TIC",
        "subitens": [
            "01 - Consultoria em TI",
            "02 - Desenvolvimento de Software",
            "03 - Suporte Técnico",
            "04 - Manutenção de Sistemas",
            "05 - Licenciamento de Software",
            "06 - Hospedagem e Cloud Computing",
            "07 - Conectividade e Redes",
            "08 - Segurança da Informação"
        ]
    },
    "449051": {
        "nome": "Obras e Instalações",
        "categoria": "OBRAS",
        "subitens": [
            "01 - Construção de Edifícios Públicos",
            "02 - Reforma e Ampliação",
            "03 - Pavimentação e Urbanização",
            "04 - Saneamento Básico",
            "05 - Instalações Elétricas",
            "06 - Instalações Hidráulicas",
            "07 - Sistemas de Drenagem",
            "08 - Construção de Pontes e Viadutos",
            "09 - Obras de Contenção",
            "10 - Terraplanagem"
        ]
    },
    "339039": {
        "nome": "Outros Serviços de Terceiros - Pessoa Jurídica",
        "categoria": "SERVICOS_PJ",
        "subitens": [
            "01 - Serviços de Engenharia",
            "02 - Serviços de Arquitetura",
            "03 - Laudos e Perícias Técnicas",
            "04 - Elaboração de Projetos",
            "05 - Fiscalização de Obras",
            "06 - Gerenciamento de Obras",
            "07 - Topografia e Georreferenciamento"
        ]
    }
}


class PACGeralObras(BaseModel):
    """PAC Geral para Obras e Serviços de Engenharia"""
    model_config = ConfigDict(extra="ignore")
    pac_obras_id: str
    user_id: str
    nome_secretaria: str
    secretario: str
    fiscal_contrato: Optional[str] = None
    telefone: str
    email: EmailStr
    endereco: str
    cep: str
    ano: str = "2026"
    tipo_contratacao: str = "OBRAS"
    secretarias_selecionadas: List[str]
    created_at: datetime
    updated_at: datetime


class PACGeralObrasCreate(BaseModel):
    nome_secretaria: str
    secretario: str
    fiscal_contrato: Optional[str] = None
    telefone: str
    email: EmailStr
    endereco: str
    cep: str
    ano: str = "2026"
    tipo_contratacao: str = "OBRAS"
    secretarias_selecionadas: List[str]


class PACGeralObrasUpdate(BaseModel):
    nome_secretaria: Optional[str] = None
    secretario: Optional[str] = None
    fiscal_contrato: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    endereco: Optional[str] = None
    cep: Optional[str] = None
    ano: Optional[str] = None
    tipo_contratacao: Optional[str] = None
    secretarias_selecionadas: Optional[List[str]] = None


class PACGeralObrasItem(BaseModel):
    """Item do PAC Geral Obras"""
    model_config = ConfigDict(extra="ignore")
    item_id: str
    pac_obras_id: str
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
    codigo_classificacao: str
    subitem_classificacao: str
    prazo_execucao: Optional[int] = None
    created_at: datetime


class PACGeralObrasItemCreate(BaseModel):
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
    codigo_classificacao: str
    subitem_classificacao: str
    prazo_execucao: Optional[int] = None


class PACGeralObrasItemUpdate(BaseModel):
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
    prazo_execucao: Optional[int] = None
