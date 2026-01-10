"""
Modelos de Prestação de Contas MROSC - Planejamento Acaiaca
Lei 13.019/2014 - Marco Regulatório das Organizações da Sociedade Civil
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


NATUREZAS_DESPESA_MROSC = {
    "319011": "Vencimentos e Vantagens Fixas",
    "319013": "Obrigações Patronais",
    "339030": "Material de Consumo",
    "339035": "Serviços de Consultoria",
    "339036": "Serviços Terceiros - PF",
    "339039": "Serviços Terceiros - PJ",
    "339046": "Auxílio-Alimentação",
    "339049": "Auxílio-Transporte",
    "449052": "Equipamentos Permanentes"
}


class ProjetoMROSC(BaseModel):
    """Projeto de parceria conforme MROSC (Lei 13.019/2014)"""
    model_config = ConfigDict(extra="ignore")
    projeto_id: str
    user_id: str
    nome_projeto: str
    objeto: str
    organizacao_parceira: str
    cnpj_parceira: str
    responsavel_osc: str
    data_inicio: datetime
    data_conclusao: datetime
    prazo_meses: int
    valor_total: float
    valor_repasse_publico: float
    valor_contrapartida: float
    status: str
    created_at: datetime
    updated_at: datetime


class ProjetoMROSCCreate(BaseModel):
    nome_projeto: str
    objeto: str
    organizacao_parceira: str
    cnpj_parceira: str
    responsavel_osc: str
    data_inicio: datetime
    data_conclusao: datetime
    prazo_meses: int
    valor_total: float
    valor_repasse_publico: float
    valor_contrapartida: float
    status: str = "ELABORACAO"


class ProjetoMROSCUpdate(BaseModel):
    nome_projeto: Optional[str] = None
    objeto: Optional[str] = None
    organizacao_parceira: Optional[str] = None
    cnpj_parceira: Optional[str] = None
    responsavel_osc: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_conclusao: Optional[datetime] = None
    prazo_meses: Optional[int] = None
    valor_total: Optional[float] = None
    valor_repasse_publico: Optional[float] = None
    valor_contrapartida: Optional[float] = None
    status: Optional[str] = None


class RecursoHumanoMROSC(BaseModel):
    """Recurso Humano do projeto MROSC"""
    model_config = ConfigDict(extra="ignore")
    rh_id: str
    projeto_id: str
    nome_funcao: str
    regime_contratacao: str
    carga_horaria_semanal: int
    salario_bruto: float
    provisao_ferias: float
    provisao_13_salario: float
    fgts: float
    inss_patronal: float
    vale_transporte: float
    vale_alimentacao: float
    custo_mensal_total: float
    numero_meses: int
    custo_total_projeto: float
    orcamento_1: Optional[float] = None
    orcamento_2: Optional[float] = None
    orcamento_3: Optional[float] = None
    media_orcamentos: Optional[float] = None
    observacoes: Optional[str] = None
    created_at: datetime


class RecursoHumanoMROSCCreate(BaseModel):
    nome_funcao: str
    regime_contratacao: str
    carga_horaria_semanal: int
    salario_bruto: float
    vale_transporte: float = 0
    vale_alimentacao: float = 0
    numero_meses: int
    orcamento_1: Optional[float] = None
    orcamento_2: Optional[float] = None
    orcamento_3: Optional[float] = None
    observacoes: Optional[str] = None


class DespesaMROSC(BaseModel):
    """Item de despesa do projeto MROSC"""
    model_config = ConfigDict(extra="ignore")
    despesa_id: str
    projeto_id: str
    natureza_despesa: str
    item_despesa: str
    descricao: str
    unidade: str
    quantidade: float
    orcamento_1: float
    orcamento_2: float
    orcamento_3: float
    media_orcamentos: float
    valor_unitario: float
    valor_total: float
    referencia_preco_municipal: Optional[float] = None
    observacoes: Optional[str] = None
    justificativa: Optional[str] = None
    created_at: datetime


class DespesaMROSCCreate(BaseModel):
    natureza_despesa: str
    item_despesa: str
    descricao: str
    unidade: str
    quantidade: float
    orcamento_1: float
    orcamento_2: float
    orcamento_3: float
    valor_unitario: float
    referencia_preco_municipal: Optional[float] = None
    observacoes: Optional[str] = None
    justificativa: Optional[str] = None


class DocumentoMROSC(BaseModel):
    """Documento anexo à prestação de contas"""
    model_config = ConfigDict(extra="ignore")
    documento_id: str
    projeto_id: str
    despesa_id: Optional[str] = None
    tipo_documento: str
    numero_documento: str
    data_documento: datetime
    valor: float
    arquivo_url: str
    arquivo_nome: str
    arquivo_tamanho: int
    validado: bool = False
    validado_por: Optional[str] = None
    data_validacao: Optional[datetime] = None
    observacoes_validacao: Optional[str] = None
    created_at: datetime


class DocumentoMROSCCreate(BaseModel):
    tipo_documento: str
    numero_documento: str
    data_documento: datetime
    valor: float
    despesa_id: Optional[str] = None
    observacoes: Optional[str] = None
