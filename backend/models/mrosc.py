"""
Modelos de Prestação de Contas MROSC - Planejamento Acaiaca
Lei 13.019/2014 - Marco Regulatório das Organizações da Sociedade Civil
Recomendação MPC-MG nº 01/2025 - Transparência e Rastreabilidade
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


# ============ NATUREZAS DE DESPESA CONFORME PLANILHA ORÇAMENTÁRIA SUCC/BH ============
NATUREZAS_DESPESA_MROSC = {
    "319011": "Vencimentos e Vantagens Fixas - Pessoal Civil",
    "319013": "Obrigações Patronais",
    "319092": "Despesas de Exercícios Anteriores - Pessoal",
    "319094": "Indenizações e Restituições Trabalhistas",
    "339014": "Diárias",
    "339030": "Material de Consumo",
    "339031": "Premiações Culturais, Artísticas, Científicas",
    "339032": "Material de Distribuição Gratuita",
    "339033": "Passagens e Despesas com Locomoção",
    "339035": "Serviços de Consultoria",
    "339036": "Serviços Terceiros - Pessoa Física",
    "339039": "Serviços Terceiros - Pessoa Jurídica",
    "339046": "Auxílio-Alimentação",
    "339049": "Auxílio-Transporte",
    "339092": "Despesas de Exercícios Anteriores",
    "449051": "Obras e Instalações",
    "449052": "Equipamentos e Material Permanente"
}

# Subitens de despesa detalhados por natureza
ITENS_DESPESA_MROSC = {
    "319011": [
        {"codigo": "01", "descricao": "Vencimentos e Salários"},
        {"codigo": "02", "descricao": "Gratificações e Vantagens"},
        {"codigo": "03", "descricao": "1/3 de Férias Constitucionais"},
        {"codigo": "04", "descricao": "Horas-Extras"},
        {"codigo": "05", "descricao": "Décimo Terceiro Salário"},
        {"codigo": "06", "descricao": "Adicional de Insalubridade"},
        {"codigo": "07", "descricao": "Adicional de Periculosidade"},
        {"codigo": "08", "descricao": "Adicional Noturno"},
        {"codigo": "09", "descricao": "Férias Vencidas"},
        {"codigo": "99", "descricao": "Outras Vantagens Fixas"}
    ],
    "319013": [
        {"codigo": "01", "descricao": "INSS Patronal"},
        {"codigo": "02", "descricao": "FGTS"},
        {"codigo": "03", "descricao": "PIS/PASEP"},
        {"codigo": "04", "descricao": "Contribuição Previdenciária"},
        {"codigo": "99", "descricao": "Outros Encargos Patronais"}
    ],
    "339030": [
        {"codigo": "01", "descricao": "Combustíveis e Lubrificantes"},
        {"codigo": "02", "descricao": "Gás e Outros Materiais Engarrafados"},
        {"codigo": "03", "descricao": "Gêneros Alimentícios"},
        {"codigo": "04", "descricao": "Material Farmacológico"},
        {"codigo": "05", "descricao": "Material Odontológico"},
        {"codigo": "06", "descricao": "Material Químico"},
        {"codigo": "07", "descricao": "Material de Consumo"},
        {"codigo": "08", "descricao": "Material de Expediente"},
        {"codigo": "09", "descricao": "Material de Processamento de Dados"},
        {"codigo": "10", "descricao": "Material Educativo e Esportivo"},
        {"codigo": "11", "descricao": "Material de Limpeza e Higiene"},
        {"codigo": "12", "descricao": "Material de Proteção e Segurança"},
        {"codigo": "13", "descricao": "Material de Copa e Cozinha"},
        {"codigo": "99", "descricao": "Outros Materiais de Consumo"}
    ],
    "339036": [
        {"codigo": "01", "descricao": "Apoio Administrativo, Técnico e Operacional"},
        {"codigo": "02", "descricao": "Serviços de Manutenção e Conservação"},
        {"codigo": "03", "descricao": "Serviços Técnicos Profissionais"},
        {"codigo": "04", "descricao": "Instrutores e Monitores"},
        {"codigo": "05", "descricao": "Estagiários"},
        {"codigo": "99", "descricao": "Outros Serviços de Terceiros PF"}
    ],
    "339039": [
        {"codigo": "01", "descricao": "Locação de Imóveis"},
        {"codigo": "02", "descricao": "Locação de Equipamentos"},
        {"codigo": "03", "descricao": "Locação de Veículos"},
        {"codigo": "04", "descricao": "Manutenção e Conservação de Bens Imóveis"},
        {"codigo": "05", "descricao": "Manutenção e Conservação de Equipamentos"},
        {"codigo": "06", "descricao": "Manutenção e Conservação de Veículos"},
        {"codigo": "07", "descricao": "Serviços de Comunicação"},
        {"codigo": "08", "descricao": "Serviços de Água e Esgoto"},
        {"codigo": "09", "descricao": "Serviços de Energia Elétrica"},
        {"codigo": "10", "descricao": "Serviços Gráficos e de Publicações"},
        {"codigo": "11", "descricao": "Serviços de Processamento de Dados"},
        {"codigo": "12", "descricao": "Serviços de Limpeza e Conservação"},
        {"codigo": "13", "descricao": "Serviços de Vigilância e Segurança"},
        {"codigo": "14", "descricao": "Serviços de Copa e Cozinha"},
        {"codigo": "15", "descricao": "Serviços Bancários"},
        {"codigo": "16", "descricao": "Serviços de Auditoria"},
        {"codigo": "17", "descricao": "Serviços de Contabilidade"},
        {"codigo": "18", "descricao": "Serviços de Assessoria Jurídica"},
        {"codigo": "99", "descricao": "Outros Serviços de Terceiros PJ"}
    ],
    "449052": [
        {"codigo": "01", "descricao": "Aparelhos de Medição e Orientação"},
        {"codigo": "02", "descricao": "Aparelhos e Equipamentos de Comunicação"},
        {"codigo": "03", "descricao": "Aparelhos e Equipamentos para Esportes"},
        {"codigo": "04", "descricao": "Aparelhos e Utensílios Domésticos"},
        {"codigo": "05", "descricao": "Coleções e Materiais Bibliográficos"},
        {"codigo": "06", "descricao": "Equipamentos para Áudio, Vídeo e Foto"},
        {"codigo": "07", "descricao": "Equipamentos de Informática"},
        {"codigo": "08", "descricao": "Equipamentos de Processamento de Dados"},
        {"codigo": "09", "descricao": "Máquinas e Equipamentos Industriais"},
        {"codigo": "10", "descricao": "Mobiliário em Geral"},
        {"codigo": "11", "descricao": "Veículos"},
        {"codigo": "99", "descricao": "Outros Equipamentos e Material Permanente"}
    ]
}

# Status do workflow de prestação de contas
STATUS_PRESTACAO = {
    "ELABORACAO": "Em Elaboração",
    "SUBMETIDO": "Submetido para Análise",
    "RECEBIDO": "Recebido pelo Gestor",
    "EM_ANALISE": "Em Análise pelo Gestor",
    "CORRECAO_SOLICITADA": "Correção Solicitada",
    "APROVADO": "Aprovado",
    "EXECUCAO": "Em Execução",
    "PRESTACAO_CONTAS": "Prestação de Contas",
    "CONCLUIDO": "Concluído",
    "REJEITADO": "Rejeitado"
}

# Tipos de documentos para upload
TIPOS_DOCUMENTO_MROSC = [
    "Nota Fiscal",
    "Cupom Fiscal",
    "Recibo",
    "Contrato",
    "Folha de Pagamento",
    "Guia INSS",
    "Guia FGTS",
    "Comprovante de Transferência",
    "Extrato Bancário",
    "Relatório de Execução",
    "Termo de Aceite",
    "Plano de Trabalho",
    "Termo de Fomento",
    "Termo de Colaboração",
    "Acordo de Cooperação",
    "Certidão Negativa",
    "Foto/Imagem",
    "Outro"
]


# ============ MODELOS PYDANTIC ============

class DadosConcedente(BaseModel):
    """Dados do concedente conforme Recomendação MPC 01/2025"""
    tipo_concedente: str  # "Parlamentar", "Comissão", "Bancada", "Executivo", "Outro"
    nome_concedente: str
    numero_emenda: Optional[str] = None
    numero_termo: Optional[str] = None  # Termo de Fomento, Colaboração, etc
    tipo_termo: Optional[str] = None  # "Fomento", "Colaboração", "Acordo"
    numero_processo_administrativo: Optional[str] = None
    data_publicacao_dou: Optional[datetime] = None
    link_publicacao: Optional[str] = None


class ContaBancaria(BaseModel):
    """Conta bancária específica do projeto (Recomendação MPC)"""
    banco: str
    agencia: str
    conta: str
    tipo_conta: str  # "Corrente", "Poupança"
    titular: str
    cnpj_titular: str


class PlanoTrabalho(BaseModel):
    """Plano de Trabalho conforme LC 210/2024 e Recomendação MPC"""
    objeto_detalhado: str
    justificativa: str
    publico_alvo: str
    quantidade_beneficiarios: int
    metas: List[dict]  # [{"descricao": "", "indicador": "", "prazo": ""}]
    cronograma_execucao: List[dict]  # [{"etapa": "", "inicio": "", "fim": ""}]
    metodologia: str
    resultados_esperados: str


class ProjetoMROSC(BaseModel):
    """Projeto de parceria conforme MROSC (Lei 13.019/2014) e Recomendação MPC 01/2025"""
    model_config = ConfigDict(extra="ignore")
    projeto_id: str
    user_id: str
    
    # Dados básicos do projeto
    nome_projeto: str
    objeto: str
    
    # Dados da OSC
    nome_osc: str  # Renomeado de organizacao_parceira
    cnpj_osc: str  # Renomeado de cnpj_parceira
    responsavel_osc: str
    email_osc: Optional[str] = None
    telefone_osc: Optional[str] = None
    endereco_osc: Optional[str] = None
    
    # Dados do concedente (Recomendação MPC)
    tipo_concedente: Optional[str] = None
    nome_concedente: Optional[str] = None
    numero_emenda: Optional[str] = None
    numero_termo: Optional[str] = None
    tipo_termo: Optional[str] = None
    numero_processo: Optional[str] = None
    
    # Conta bancária específica (Recomendação MPC)
    banco: Optional[str] = None
    agencia: Optional[str] = None
    conta_bancaria: Optional[str] = None
    tipo_conta: Optional[str] = None
    
    # Gestor responsável (Recomendação MPC)
    gestor_responsavel: Optional[str] = None
    cpf_gestor: Optional[str] = None
    cargo_gestor: Optional[str] = None
    
    # Datas e prazos
    data_inicio: datetime
    data_fim: datetime  # Renomeado de data_conclusao
    prazo_meses: int
    
    # Valores financeiros
    valor_total: float
    valor_repasse_publico: float
    valor_contrapartida: float
    
    # Plano de Trabalho resumido
    objeto_detalhado: Optional[str] = None
    justificativa: Optional[str] = None
    publico_alvo: Optional[str] = None
    quantidade_beneficiarios: Optional[int] = None
    metodologia: Optional[str] = None
    resultados_esperados: Optional[str] = None
    
    # Status e workflow
    status: str = "ELABORACAO"
    submetido: bool = False
    data_submissao: Optional[datetime] = None
    submetido_por: Optional[str] = None
    
    recebido: bool = False
    data_recebimento: Optional[datetime] = None
    recebido_por: Optional[str] = None
    
    pode_editar: bool = True
    aprovado: bool = False
    data_aprovacao: Optional[datetime] = None
    aprovado_por: Optional[str] = None
    observacoes_aprovacao: Optional[str] = None
    
    # Histórico de correções
    correcao_solicitada: bool = False
    data_correcao_solicitada: Optional[datetime] = None
    motivo_correcao: Optional[str] = None
    solicitado_por: Optional[str] = None
    
    # Histórico de ações
    historico_status: Optional[List[dict]] = None
    
    # Conformidade MPC
    aprovado_sus: Optional[bool] = None  # Para projetos de saúde
    data_aprovacao_sus: Optional[datetime] = None
    
    # Campos de controle
    created_at: datetime
    updated_at: datetime


class ProjetoMROSCCreate(BaseModel):
    """Criação de projeto MROSC"""
    nome_projeto: str
    objeto: str
    nome_osc: str
    cnpj_osc: str
    responsavel_osc: str
    email_osc: Optional[str] = None
    telefone_osc: Optional[str] = None
    endereco_osc: Optional[str] = None
    data_inicio: datetime
    data_fim: datetime
    prazo_meses: int
    valor_total: float
    valor_repasse_publico: float
    valor_contrapartida: float
    status: str = "ELABORACAO"
    # Campos adicionais opcionais
    tipo_concedente: Optional[str] = None
    nome_concedente: Optional[str] = None
    numero_emenda: Optional[str] = None
    numero_termo: Optional[str] = None
    tipo_termo: Optional[str] = None
    numero_processo: Optional[str] = None
    banco: Optional[str] = None
    agencia: Optional[str] = None
    conta_bancaria: Optional[str] = None
    tipo_conta: Optional[str] = None
    gestor_responsavel: Optional[str] = None
    cpf_gestor: Optional[str] = None
    cargo_gestor: Optional[str] = None
    objeto_detalhado: Optional[str] = None
    justificativa: Optional[str] = None
    publico_alvo: Optional[str] = None
    quantidade_beneficiarios: Optional[int] = None
    metodologia: Optional[str] = None
    resultados_esperados: Optional[str] = None


class ProjetoMROSCUpdate(BaseModel):
    """Atualização de projeto MROSC"""
    nome_projeto: Optional[str] = None
    objeto: Optional[str] = None
    nome_osc: Optional[str] = None
    cnpj_osc: Optional[str] = None
    responsavel_osc: Optional[str] = None
    email_osc: Optional[str] = None
    telefone_osc: Optional[str] = None
    endereco_osc: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    prazo_meses: Optional[int] = None
    valor_total: Optional[float] = None
    valor_repasse_publico: Optional[float] = None
    valor_contrapartida: Optional[float] = None
    status: Optional[str] = None
    tipo_concedente: Optional[str] = None
    nome_concedente: Optional[str] = None
    numero_emenda: Optional[str] = None
    numero_termo: Optional[str] = None
    tipo_termo: Optional[str] = None
    numero_processo: Optional[str] = None
    banco: Optional[str] = None
    agencia: Optional[str] = None
    conta_bancaria: Optional[str] = None
    tipo_conta: Optional[str] = None
    gestor_responsavel: Optional[str] = None
    cpf_gestor: Optional[str] = None
    cargo_gestor: Optional[str] = None
    objeto_detalhado: Optional[str] = None
    justificativa: Optional[str] = None
    publico_alvo: Optional[str] = None
    quantidade_beneficiarios: Optional[int] = None
    metodologia: Optional[str] = None
    resultados_esperados: Optional[str] = None


class RecursoHumanoMROSC(BaseModel):
    """Recurso Humano do projeto MROSC conforme planilha SUCC/BH"""
    model_config = ConfigDict(extra="ignore")
    rh_id: str
    projeto_id: str
    
    # Identificação do cargo
    nome_funcao: str
    codigo_cbo: Optional[str] = None  # Classificação Brasileira de Ocupações
    
    # Forma de contratação
    regime_contratacao: str  # CLT, Autônomo, Cooperado, etc
    tipo_vinculo: Optional[str] = None  # Efetivo, Temporário, etc
    
    # Jornada
    carga_horaria_semanal: int
    carga_horaria_mensal: Optional[int] = None
    
    # Remuneração base
    salario_bruto: float
    
    # Encargos CLT (calculados automaticamente)
    provisao_ferias: float  # 1/12 + 1/3
    provisao_13_salario: float  # 1/12
    fgts: float  # 8% sobre (salário + férias + 13º)
    fgts_rescisao: Optional[float] = None  # 40% ou 50% sobre FGTS
    inss_patronal: float  # 20% sobre salário
    outros_encargos: Optional[float] = None
    
    # Benefícios
    vale_transporte: float = 0
    vale_alimentacao: float = 0
    plano_saude: Optional[float] = None
    outros_beneficios: Optional[float] = None
    
    # Totais calculados
    custo_mensal_encargos: float
    custo_mensal_beneficios: float
    custo_mensal_total: float
    numero_meses: int
    custo_total_projeto: float
    
    # Orçamentos de referência
    orcamento_1: Optional[float] = None
    orcamento_2: Optional[float] = None
    orcamento_3: Optional[float] = None
    media_orcamentos: Optional[float] = None
    valor_referencia_municipal: Optional[float] = None
    
    # Observações
    observacoes: Optional[str] = None
    justificativa_valor: Optional[str] = None
    
    created_at: datetime


class RecursoHumanoMROSCCreate(BaseModel):
    """Criação de RH MROSC"""
    nome_funcao: str
    codigo_cbo: Optional[str] = None
    regime_contratacao: str
    tipo_vinculo: Optional[str] = None
    carga_horaria_semanal: int
    carga_horaria_mensal: Optional[int] = None
    salario_bruto: float
    vale_transporte: float = 0
    vale_alimentacao: float = 0
    plano_saude: Optional[float] = None
    outros_beneficios: Optional[float] = None
    numero_meses: int
    orcamento_1: Optional[float] = None
    orcamento_2: Optional[float] = None
    orcamento_3: Optional[float] = None
    valor_referencia_municipal: Optional[float] = None
    observacoes: Optional[str] = None
    justificativa_valor: Optional[str] = None


class DespesaMROSC(BaseModel):
    """Item de despesa do projeto MROSC conforme planilha SUCC/BH"""
    model_config = ConfigDict(extra="ignore")
    despesa_id: str
    projeto_id: str
    
    # Classificação da despesa
    natureza_despesa: str  # Código: 339030, 339039, etc
    codigo_item: Optional[str] = None  # Subitem: 01, 02, etc
    item_despesa: str  # Nome do item
    descricao: str
    
    # Quantificação
    unidade: str
    quantidade: float
    numero_meses: Optional[int] = None  # Para despesas recorrentes
    
    # Orçamentos (mínimo 3 cotações)
    orcamento_1: float
    fornecedor_1: Optional[str] = None
    cnpj_fornecedor_1: Optional[str] = None
    
    orcamento_2: float
    fornecedor_2: Optional[str] = None
    cnpj_fornecedor_2: Optional[str] = None
    
    orcamento_3: float
    fornecedor_3: Optional[str] = None
    cnpj_fornecedor_3: Optional[str] = None
    
    # Valores calculados
    media_orcamentos: float
    valor_unitario: float
    valor_total: float
    
    # Referência de preços
    referencia_preco_municipal: Optional[float] = None
    fonte_referencia: Optional[str] = None  # Banco de preços, pregão, etc
    
    # Observações e justificativas
    observacoes: Optional[str] = None
    justificativa: Optional[str] = None
    justificativa_menor_preco: Optional[str] = None  # Se não escolheu menor preço
    
    created_at: datetime


class DespesaMROSCCreate(BaseModel):
    """Criação de despesa MROSC"""
    natureza_despesa: str
    codigo_item: Optional[str] = None
    item_despesa: str
    descricao: str
    unidade: str
    quantidade: float
    numero_meses: Optional[int] = None
    orcamento_1: float
    fornecedor_1: Optional[str] = None
    cnpj_fornecedor_1: Optional[str] = None
    orcamento_2: float
    fornecedor_2: Optional[str] = None
    cnpj_fornecedor_2: Optional[str] = None
    orcamento_3: float
    fornecedor_3: Optional[str] = None
    cnpj_fornecedor_3: Optional[str] = None
    valor_unitario: float
    referencia_preco_municipal: Optional[float] = None
    fonte_referencia: Optional[str] = None
    observacoes: Optional[str] = None
    justificativa: Optional[str] = None
    justificativa_menor_preco: Optional[str] = None


class DocumentoMROSC(BaseModel):
    """Documento anexo à prestação de contas (PDF e JPG)"""
    model_config = ConfigDict(extra="ignore")
    documento_id: str
    projeto_id: str
    despesa_id: Optional[str] = None  # Vinculado a uma despesa específica
    rh_id: Optional[str] = None  # Vinculado a um RH específico
    
    # Informações do documento
    tipo_documento: str  # Nota Fiscal, Recibo, Foto, etc
    numero_documento: Optional[str] = None
    data_documento: Optional[datetime] = None
    valor: Optional[float] = None
    
    # Arquivo
    arquivo_url: str
    arquivo_nome: str
    arquivo_tipo: str  # "application/pdf", "image/jpeg", "image/png"
    arquivo_tamanho: int
    
    # Validação
    validado: bool = False
    validado_por: Optional[str] = None
    data_validacao: Optional[datetime] = None
    observacoes_validacao: Optional[str] = None
    
    # Observações
    descricao: Optional[str] = None
    observacoes: Optional[str] = None
    
    created_at: datetime


class DocumentoMROSCCreate(BaseModel):
    """Criação de documento MROSC"""
    tipo_documento: str
    numero_documento: Optional[str] = None
    data_documento: Optional[datetime] = None
    valor: Optional[float] = None
    despesa_id: Optional[str] = None
    rh_id: Optional[str] = None
    descricao: Optional[str] = None
    observacoes: Optional[str] = None


# ============ MODELOS PARA PORTAL DE TRANSPARÊNCIA (Recomendação MPC) ============

class ProjetoMROSCPublico(BaseModel):
    """Dados públicos do projeto para Portal de Transparência"""
    projeto_id: str
    nome_projeto: str
    objeto: str
    nome_osc: str
    cnpj_osc: str
    
    # Concedente
    tipo_concedente: Optional[str] = None
    nome_concedente: Optional[str] = None
    numero_emenda: Optional[str] = None
    numero_termo: Optional[str] = None
    
    # Gestor responsável (nome completo obrigatório MPC)
    gestor_responsavel: Optional[str] = None
    
    # Natureza da despesa (GND)
    naturezas_despesa: Optional[List[str]] = None
    
    # Valores
    valor_total: float
    valor_repasse_publico: float
    valor_contrapartida: float
    
    # Datas
    data_inicio: datetime
    data_fim: datetime
    data_disponibilizacao: Optional[datetime] = None
    
    # Conta bancária
    banco: Optional[str] = None
    conta_bancaria: Optional[str] = None
    
    # Status
    status: str
    aprovado_sus: Optional[bool] = None


class ResumoOrcamentarioMROSC(BaseModel):
    """Resumo orçamentário para relatórios"""
    projeto_id: str
    nome_projeto: str
    
    # Totais por categoria
    total_recursos_humanos: float
    total_encargos: float
    total_beneficios: float
    total_materiais: float
    total_servicos_pf: float
    total_servicos_pj: float
    total_equipamentos: float
    total_outras_despesas: float
    
    # Resumo geral
    total_despesas: float
    valor_total_projeto: float
    valor_repasse: float
    valor_contrapartida: float
    saldo_disponivel: float
    percentual_executado: float
    
    # Quantitativos
    quantidade_rh: int
    quantidade_despesas: int
    quantidade_documentos: int
    documentos_validados: int
    documentos_pendentes: int
