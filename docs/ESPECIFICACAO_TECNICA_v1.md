# Especificação Técnica - Novas Funcionalidades
## Sistema PAC - Prefeitura Municipal de Acaiaca

**Versão:** 1.0  
**Data:** 10/01/2026  
**Autor:** Equipe de Desenvolvimento  
**Referências Legais:** Lei 14.133/2021, Lei 13.019/2014 (MROSC), Portaria 448 do Ministério da Economia

---

## 1. VISÃO GERAL

### 1.1 Objetivo
Implementar novas funcionalidades no sistema PAC existente, incluindo:
- Reorganização de menus
- Novo módulo "PAC Geral Obras e Serviços"
- Ajustes no módulo de Processos
- Sistema completo de Prestação de Contas (MROSC)

### 1.2 Escopo
| Módulo | Prioridade | Complexidade |
|--------|------------|--------------|
| Menus Reorganizados | P1 | Baixa |
| PAC Geral Obras e Serviços | P1 | Média |
| Ajustes em Processos | P1 | Baixa |
| Sistema Prestação de Contas | P2 | Alta |

---

## 2. ESTRUTURA DE MENUS

### 2.1 Nova Organização de Menus

```
├── 📋 PACS
│   ├── PAC Individual
│   ├── PAC Geral
│   └── PAC Geral Obras e Serviços (NOVO)
│
├── 📁 PROCESSOS
│   ├── Gestão Processual
│   └── Dashboard de Processos
│
├── 📰 DIÁRIO OFICIAL
│   ├── Edições
│   ├── Publicações
│   └── Assinantes
│
├── 💰 PRESTAÇÃO DE CONTAS (NOVO)
│   ├── Projetos
│   ├── Recursos Humanos
│   ├── Despesas
│   └── Relatórios
│
└── ⚙️ ADMINISTRAÇÃO
    ├── Usuários
    ├── Backup
    └── Configurações
```

### 2.2 Implementação Frontend

```jsx
// /app/frontend/src/components/Sidebar.jsx - Estrutura de Menus

const menuItems = [
  {
    title: "PACS",
    icon: <FileText />,
    submenu: [
      { title: "PAC Individual", path: "/pacs" },
      { title: "PAC Geral", path: "/pacs-geral" },
      { title: "PAC Geral Obras", path: "/pacs-geral-obras" }
    ]
  },
  {
    title: "Processos",
    icon: <Folder />,
    submenu: [
      { title: "Gestão Processual", path: "/processos" },
      { title: "Dashboard", path: "/processos/dashboard" }
    ]
  },
  {
    title: "Diário Oficial",
    icon: <Newspaper />,
    submenu: [
      { title: "Edições", path: "/doem" },
      { title: "Publicações", path: "/doem/publicacoes" },
      { title: "Assinantes", path: "/doem/assinantes" }
    ]
  },
  {
    title: "Prestação de Contas",
    icon: <DollarSign />,
    submenu: [
      { title: "Projetos", path: "/prestacao-contas/projetos" },
      { title: "Recursos Humanos", path: "/prestacao-contas/rh" },
      { title: "Despesas", path: "/prestacao-contas/despesas" },
      { title: "Relatórios", path: "/prestacao-contas/relatorios" }
    ]
  }
];
```

---

## 3. MÓDULO PAC GERAL OBRAS E SERVIÇOS

### 3.1 Descrição
Módulo específico para gestão de contratações de obras e serviços, com classificação orçamentária conforme Lei 14.133/2021 e Portaria 448.

### 3.2 Códigos de Classificação Orçamentária

| Código | Descrição | Categoria |
|--------|-----------|-----------|
| **339040** | Serviços de TIC - Pessoa Jurídica | Serviços |
| **449051** | Obras e Instalações | Obras |
| **449052** | Equipamentos e Material Permanente | Material |
| **339039** | Outros Serviços de Terceiros - PJ | Serviços |
| **339036** | Outros Serviços de Terceiros - PF | Serviços |

### 3.3 Subitens de Classificação (Portaria 448)

#### 339040 - Serviços de TIC
```
01 - Consultoria em TI
02 - Desenvolvimento de Software
03 - Suporte Técnico
04 - Manutenção de Sistemas
05 - Licenciamento de Software
06 - Hospedagem e Cloud Computing
07 - Conectividade e Redes
08 - Segurança da Informação
```

#### 449051 - Obras e Instalações
```
01 - Construção de Edifícios Públicos
02 - Reforma e Ampliação
03 - Pavimentação e Urbanização
04 - Saneamento Básico
05 - Instalações Elétricas
06 - Instalações Hidráulicas
07 - Sistemas de Drenagem
08 - Construção de Pontes e Viadutos
09 - Obras de Contenção
```

### 3.4 Modelo de Dados

```python
# /app/backend/models/pac_obras.py

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class PACGeralObras(BaseModel):
    """PAC Geral Obras e Serviços"""
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
    secretarias_selecionadas: List[str]
    tipo_contratacao: str  # "OBRAS" ou "SERVICOS"
    created_at: datetime
    updated_at: datetime

class PACGeralObrasItem(BaseModel):
    """Item do PAC Geral Obras"""
    item_id: str
    pac_obras_id: str
    
    # Identificação
    catmat: str  # Código CATMAT/CATSER
    descricao: str
    unidade: str
    
    # Classificação Orçamentária (Lei 14.133/2021)
    codigo_classificacao: str  # Ex: 449051, 339040
    subitem_classificacao: str  # Ex: "01 - Construção de Edifícios"
    
    # Quantidades por Secretaria
    qtd_administracao: float = 0
    qtd_fazenda: float = 0
    qtd_saude: float = 0
    qtd_educacao: float = 0
    qtd_assistencia: float = 0
    qtd_agricultura: float = 0
    qtd_obras: float = 0
    qtd_transporte: float = 0
    qtd_cultura: float = 0
    quantidade_total: float
    
    # Valores
    valorUnitario: float
    valorTotal: float
    
    # Metadados
    prioridade: str  # ALTA, MÉDIA, BAIXA
    justificativa: Optional[str] = None
    prazo_execucao: Optional[int] = None  # em meses
    created_at: datetime
```

### 3.5 Endpoints da API

```
# PAC Geral Obras - CRUD
POST   /api/pacs-geral-obras              # Criar novo PAC Obras
GET    /api/pacs-geral-obras              # Listar todos
GET    /api/pacs-geral-obras/{id}         # Obter por ID
PUT    /api/pacs-geral-obras/{id}         # Atualizar
DELETE /api/pacs-geral-obras/{id}         # Excluir

# Itens
POST   /api/pacs-geral-obras/{id}/items   # Adicionar item
GET    /api/pacs-geral-obras/{id}/items   # Listar itens
PUT    /api/pacs-geral-obras/{id}/items/{item_id}
DELETE /api/pacs-geral-obras/{id}/items/{item_id}

# Exportação
GET    /api/pacs-geral-obras/{id}/export/pdf
GET    /api/pacs-geral-obras/{id}/export/excel

# Classificação
GET    /api/classificacao/obras           # Códigos de obras
GET    /api/classificacao/servicos        # Códigos de serviços
```

---

## 4. AJUSTES NO MÓDULO DE PROCESSOS

### 4.1 Alterações de Campos

| Campo Atual | Novo Campo | Tipo | Obrigatório |
|-------------|------------|------|-------------|
| `status` | `modalidade_contratacao` | String | Sim |
| `situacao` | `status` | String | Sim |
| `numero_processo` | `numero_processo` | String | **Sim*** |

### 4.2 Valores para Modalidade de Contratação

```python
MODALIDADES_CONTRATACAO = [
    "PREGÃO ELETRÔNICO",
    "PREGÃO PRESENCIAL",
    "CONCORRÊNCIA",
    "TOMADA DE PREÇOS",
    "CONVITE",
    "CONCURSO",
    "LEILÃO",
    "DISPENSA DE LICITAÇÃO",
    "INEXIGIBILIDADE",
    "CHAMAMENTO PÚBLICO",
    "ADESÃO A ATA DE REGISTRO DE PREÇOS",
    "CONTRATAÇÃO DIRETA"
]
```

### 4.3 Valores para Status (antigo Situação)

```python
STATUS_PROCESSO = [
    "EM ELABORAÇÃO",
    "AGUARDANDO APROVAÇÃO",
    "APROVADO",
    "EM LICITAÇÃO",
    "HOMOLOGADO",
    "CONTRATADO",
    "EM EXECUÇÃO",
    "CONCLUÍDO",
    "CANCELADO",
    "SUSPENSO",
    "REVOGADO",
    "ANULADO"
]
```

### 4.4 Modelo Atualizado

```python
# /app/backend/models/processo.py - ATUALIZADO

class ProcessoUpdate(BaseModel):
    numero_processo: Optional[str] = None  # OBRIGATÓRIO na criação
    modalidade_contratacao: Optional[str] = None  # Antigo "status"
    status: Optional[str] = None  # Antigo "situação"
    objeto: Optional[str] = None
    responsavel: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_autuacao: Optional[datetime] = None
    data_contrato: Optional[datetime] = None
    secretaria: Optional[str] = None
    secretario: Optional[str] = None
    ano: Optional[int] = None
    observacoes: Optional[str] = None

class ProcessoCreate(BaseModel):
    numero_processo: str  # OBRIGATÓRIO *
    modalidade_contratacao: str
    status: str
    objeto: str
    responsavel: str
    secretaria: str
    secretario: str
    # ... demais campos
```

### 4.5 Script de Migração de Dados

```python
# Script de migração para processos existentes
async def migrate_processos_fields():
    """
    Migrar campos antigos para nova nomenclatura:
    - status -> modalidade_contratacao
    - situacao -> status
    """
    processos = await db.processos.find({}).to_list(None)
    
    for proc in processos:
        update_data = {}
        
        # Migrar status antigo para modalidade_contratacao
        if 'status' in proc and 'modalidade_contratacao' not in proc:
            update_data['modalidade_contratacao'] = proc['status']
        
        # Migrar situacao para status
        if 'situacao' in proc:
            update_data['status'] = proc['situacao']
        
        if update_data:
            await db.processos.update_one(
                {'processo_id': proc['processo_id']},
                {'$set': update_data}
            )
    
    print(f"Migração concluída: {len(processos)} processos atualizados")
```

---

## 5. SISTEMA DE PRESTAÇÃO DE CONTAS (MROSC)

### 5.1 Visão Geral
Sistema completo para gestão de prestação de contas conforme Lei 13.019/2014, baseado na estrutura da planilha orçamentária analisada.

### 5.2 Estrutura de Dados

#### 5.2.1 Projeto

```python
class ProjetoMROSC(BaseModel):
    """Projeto de parceria conforme MROSC"""
    projeto_id: str
    user_id: str
    
    # Dados do Projeto
    nome_projeto: str
    objeto: str
    organizacao_parceira: str  # OSC
    cnpj_parceira: str
    responsavel_osc: str
    
    # Vigência
    data_inicio: datetime
    data_conclusao: datetime
    prazo_meses: int
    
    # Valores
    valor_total: float
    valor_repasse_publico: float
    valor_contrapartida: float
    
    # Status
    status: str  # ELABORAÇÃO, APROVADO, EXECUÇÃO, PRESTAÇÃO_CONTAS, CONCLUÍDO
    
    # Metadados
    created_at: datetime
    updated_at: datetime
```

#### 5.2.2 Naturezas de Despesa

```python
NATUREZAS_DESPESA_MROSC = {
    "319011": {
        "nome": "Vencimentos e Vantagens Fixas - Pessoal Civil",
        "categoria": "RECURSOS_HUMANOS",
        "subitens": [
            "Vencimento ou Salário",
            "Gratificações",
            "Adicional Noturno",
            "Hora Extra",
            "Representação Mensal"
        ]
    },
    "319013": {
        "nome": "Obrigações Patronais",
        "categoria": "RECURSOS_HUMANOS",
        "subitens": [
            "FGTS",
            "INSS Patronal",
            "PIS/PASEP",
            "Contribuição Sindical"
        ]
    },
    "319094": {
        "nome": "Indenizações e Restituições Trabalhistas",
        "categoria": "RECURSOS_HUMANOS",
        "subitens": [
            "Indenização Férias",
            "Indenização 13º Salário",
            "Aviso Prévio Indenizado",
            "Multa FGTS 40%"
        ]
    },
    "339030": {
        "nome": "Material de Consumo",
        "categoria": "MATERIAIS",
        "subitens": [
            "Material de Escritório",
            "Material de Limpeza",
            "Gêneros Alimentícios",
            "Material Didático",
            "Combustíveis",
            "Material Hospitalar"
        ]
    },
    "339031": {
        "nome": "Premiações Culturais, Artísticas e Científicas",
        "categoria": "PREMIACOES"
    },
    "339035": {
        "nome": "Serviços de Consultoria",
        "categoria": "SERVICOS"
    },
    "339036": {
        "nome": "Outros Serviços de Terceiros - Pessoa Física",
        "categoria": "SERVICOS"
    },
    "339039": {
        "nome": "Outros Serviços de Terceiros - Pessoa Jurídica",
        "categoria": "SERVICOS"
    },
    "339046": {
        "nome": "Auxílio-Alimentação",
        "categoria": "BENEFICIOS"
    },
    "339049": {
        "nome": "Auxílio-Transporte",
        "categoria": "BENEFICIOS"
    },
    "339047": {
        "nome": "Obrigações Tributárias e Contributivas",
        "categoria": "TRIBUTOS"
    },
    "449051": {
        "nome": "Obras e Instalações",
        "categoria": "INVESTIMENTOS"
    },
    "449052": {
        "nome": "Equipamentos e Material Permanente",
        "categoria": "INVESTIMENTOS"
    }
}
```

#### 5.2.3 Recursos Humanos

```python
class RecursoHumanoMROSC(BaseModel):
    """Recurso Humano do projeto MROSC"""
    rh_id: str
    projeto_id: str
    
    # Identificação
    nome_funcao: str  # Ex: "Coordenador", "Assistente Social"
    regime_contratacao: str  # "CLT", "RPA", "AUTONOMO"
    carga_horaria_semanal: int
    
    # Valores Mensais
    salario_bruto: float
    
    # Provisões CLT (calculadas automaticamente)
    provisao_ferias: float  # 1/12 do salário
    provisao_13_salario: float  # 1/12 do salário
    fgts: float  # 8% sobre (salário + férias + 13º)
    inss_patronal: float  # Conforme tabela vigente
    
    # Benefícios
    vale_transporte: float
    vale_alimentacao: float
    
    # Cálculos
    custo_mensal_total: float
    numero_meses: int
    custo_total_projeto: float
    
    # Orçamentos
    orcamento_1: Optional[float] = None
    orcamento_2: Optional[float] = None
    orcamento_3: Optional[float] = None
    media_orcamentos: Optional[float] = None
    valor_previsto_execucao: float
    
    # Observações
    observacoes: Optional[str] = None
```

#### 5.2.4 Despesas

```python
class DespesaMROSC(BaseModel):
    """Item de despesa do projeto MROSC"""
    despesa_id: str
    projeto_id: str
    
    # Classificação
    natureza_despesa: str  # Código (ex: 339030)
    item_despesa: str  # Subitem (ex: "Material de Escritório")
    
    # Descrição
    descricao: str
    unidade: str
    quantidade: float
    
    # Orçamentos (múltiplas cotações)
    orcamento_1: float
    orcamento_2: float
    orcamento_3: float
    media_orcamentos: float  # Calculado
    
    # Valor Final
    valor_unitario: float
    valor_total: float
    
    # Referência
    referencia_preco_municipal: Optional[float] = None
    
    # Observações
    observacoes: Optional[str] = None
    justificativa: Optional[str] = None
    
    # Comprovantes
    comprovantes: List[str] = []  # IDs dos documentos PDF
```

#### 5.2.5 Documentos/Comprovantes

```python
class DocumentoMROSC(BaseModel):
    """Documento anexo à prestação de contas"""
    documento_id: str
    projeto_id: str
    despesa_id: Optional[str] = None
    
    # Metadados
    tipo_documento: str  # NOTA_FISCAL, RECIBO, CONTRATO, COMPROVANTE
    numero_documento: str
    data_documento: datetime
    valor: float
    
    # Arquivo
    arquivo_url: str
    arquivo_nome: str
    arquivo_tamanho: int
    
    # Validação
    validado: bool = False
    validado_por: Optional[str] = None
    data_validacao: Optional[datetime] = None
    observacoes_validacao: Optional[str] = None
```

### 5.3 Endpoints da API - Prestação de Contas

```
# Projetos MROSC
POST   /api/mrosc/projetos              # Criar projeto
GET    /api/mrosc/projetos              # Listar projetos
GET    /api/mrosc/projetos/{id}         # Obter projeto
PUT    /api/mrosc/projetos/{id}         # Atualizar
DELETE /api/mrosc/projetos/{id}         # Excluir

# Recursos Humanos
POST   /api/mrosc/projetos/{id}/rh      # Adicionar RH
GET    /api/mrosc/projetos/{id}/rh      # Listar RH
PUT    /api/mrosc/projetos/{id}/rh/{rh_id}
DELETE /api/mrosc/projetos/{id}/rh/{rh_id}
POST   /api/mrosc/projetos/{id}/rh/{rh_id}/calcular  # Recalcular valores

# Despesas
POST   /api/mrosc/projetos/{id}/despesas
GET    /api/mrosc/projetos/{id}/despesas
PUT    /api/mrosc/projetos/{id}/despesas/{despesa_id}
DELETE /api/mrosc/projetos/{id}/despesas/{despesa_id}

# Documentos
POST   /api/mrosc/projetos/{id}/documentos  # Upload de documento
GET    /api/mrosc/projetos/{id}/documentos
DELETE /api/mrosc/projetos/{id}/documentos/{doc_id}
PUT    /api/mrosc/projetos/{id}/documentos/{doc_id}/validar

# Relatórios
GET    /api/mrosc/projetos/{id}/resumo-orcamentario
GET    /api/mrosc/projetos/{id}/export/pdf
GET    /api/mrosc/projetos/{id}/export/excel

# Classificações
GET    /api/mrosc/naturezas-despesa     # Lista de naturezas
GET    /api/mrosc/itens-despesa/{natureza}  # Itens por natureza
```

### 5.4 Cálculos Automáticos

```python
def calcular_encargos_clt(salario_bruto: float, meses: int) -> dict:
    """
    Calcula encargos trabalhistas CLT conforme MROSC
    """
    # Provisões
    provisao_ferias = salario_bruto / 12  # 1/12
    provisao_13_salario = salario_bruto / 12  # 1/12
    
    # Base para FGTS
    base_fgts = salario_bruto + provisao_ferias + provisao_13_salario
    fgts = base_fgts * 0.08  # 8%
    
    # INSS Patronal (simplificado)
    inss_patronal = salario_bruto * 0.20  # 20%
    
    # Custo mensal total
    custo_mensal = (
        salario_bruto +
        provisao_ferias +
        provisao_13_salario +
        fgts +
        inss_patronal
    )
    
    return {
        'salario_bruto': salario_bruto,
        'provisao_ferias': round(provisao_ferias, 2),
        'provisao_13_salario': round(provisao_13_salario, 2),
        'fgts': round(fgts, 2),
        'inss_patronal': round(inss_patronal, 2),
        'custo_mensal_total': round(custo_mensal, 2),
        'custo_total_projeto': round(custo_mensal * meses, 2)
    }

def calcular_media_orcamentos(orc1: float, orc2: float, orc3: float) -> float:
    """Calcula média dos três orçamentos"""
    valores = [v for v in [orc1, orc2, orc3] if v and v > 0]
    if not valores:
        return 0.0
    return round(sum(valores) / len(valores), 2)
```

### 5.5 Interface do Usuário

#### Tela de Projeto MROSC
```
┌─────────────────────────────────────────────────────────────┐
│ 📋 DADOS DO PROJETO                                         │
├─────────────────────────────────────────────────────────────┤
│ Nome do Projeto: [____________________________________]     │
│ Organização Parceira (OSC): [_________________________]     │
│ CNPJ: [__________________]                                  │
│                                                             │
│ Vigência: [__/__/____] até [__/__/____]   Meses: [__]      │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ RESUMO FINANCEIRO                                       ││
│ │ ├── Valor Total do Projeto:     R$ XXX.XXX,XX          ││
│ │ ├── Repasse Público:            R$ XXX.XXX,XX          ││
│ │ └── Contrapartida OSC:          R$ XXX.XXX,XX          ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ [Tab: Recursos Humanos] [Tab: Despesas] [Tab: Documentos]   │
└─────────────────────────────────────────────────────────────┘
```

#### Tela de Recursos Humanos
```
┌─────────────────────────────────────────────────────────────┐
│ 👥 RECURSOS HUMANOS                        [+ Adicionar RH] │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Função: Coordenador de Projeto                          ││
│ │ Regime: CLT    Carga: 40h/semana    Meses: 12          ││
│ │ ─────────────────────────────────────────────────────── ││
│ │ Salário Bruto:           R$ 5.000,00                   ││
│ │ + Provisão Férias:       R$   416,67                   ││
│ │ + Provisão 13º:          R$   416,67                   ││
│ │ + FGTS (8%):             R$   466,67                   ││
│ │ + INSS Patronal:         R$ 1.000,00                   ││
│ │ ─────────────────────────────────────────────────────── ││
│ │ CUSTO MENSAL TOTAL:      R$ 7.300,01                   ││
│ │ CUSTO TOTAL (12 meses):  R$ 87.600,12                  ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ TOTAL RECURSOS HUMANOS: R$ XXX.XXX,XX                       │
└─────────────────────────────────────────────────────────────┘
```

#### Tela de Despesas
```
┌─────────────────────────────────────────────────────────────┐
│ 💰 DESPESAS                               [+ Adicionar Item]│
├─────────────────────────────────────────────────────────────┤
│ Natureza: [▼ 339030 - Material de Consumo]                  │
│ Item: [▼ Material de Escritório]                            │
│                                                             │
│ Descrição: [________________________________________]       │
│ Unidade: [____]  Quantidade: [____]                         │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ ORÇAMENTOS (mínimo 3 cotações)                          ││
│ │ Orçamento 1: R$ [________]                              ││
│ │ Orçamento 2: R$ [________]                              ││
│ │ Orçamento 3: R$ [________]                              ││
│ │ ─────────────────────────────────────────────────────── ││
│ │ Média dos Orçamentos: R$ X.XXX,XX                       ││
│ │ Ref. Preço Municipal:  R$ X.XXX,XX                      ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ Valor Unitário Final: R$ [________]                         │
│ VALOR TOTAL: R$ XX.XXX,XX                                   │
│                                                             │
│ Observações: [________________________________________]     │
│                                                             │
│ 📎 Anexar Comprovantes: [Selecionar PDFs...]               │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. DIAGRAMA DE FLUXO DE DADOS

```
┌─────────────────────────────────────────────────────────────────┐
│                    SISTEMA PAC ACAIACA                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐     │
│  │   PAC   │    │   PAC   │    │  PAC    │    │PRESTAÇÃO│     │
│  │Individual    │  Geral  │    │ Obras   │    │ CONTAS  │     │
│  └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘     │
│       │              │              │              │           │
│       └──────────────┴──────────────┴──────────────┘           │
│                          │                                      │
│                          ▼                                      │
│              ┌───────────────────────┐                         │
│              │  CLASSIFICAÇÃO        │                         │
│              │  ORÇAMENTÁRIA         │                         │
│              │  (Lei 14.133/2021)    │                         │
│              │  (Portaria 448)       │                         │
│              └───────────┬───────────┘                         │
│                          │                                      │
│       ┌──────────────────┼──────────────────┐                  │
│       ▼                  ▼                  ▼                  │
│  ┌─────────┐      ┌─────────────┐     ┌─────────┐             │
│  │PROCESSOS│      │   DOEM      │     │RELATÓRIOS│            │
│  │         │      │(Publicações)│     │   PDF    │            │
│  └─────────┘      └─────────────┘     └─────────┘             │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    MONGODB                               │   │
│  │  ├── users                                               │   │
│  │  ├── pacs                                                │   │
│  │  ├── pacs_geral                                          │   │
│  │  ├── pacs_geral_obras (NOVO)                            │   │
│  │  ├── processos                                           │   │
│  │  ├── doem_edicoes                                        │   │
│  │  ├── mrosc_projetos (NOVO)                              │   │
│  │  ├── mrosc_recursos_humanos (NOVO)                      │   │
│  │  ├── mrosc_despesas (NOVO)                              │   │
│  │  └── mrosc_documentos (NOVO)                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. REQUISITOS NÃO FUNCIONAIS

### 7.1 Segurança
- Validação de CPF/CNPJ em campos obrigatórios
- Upload de documentos apenas em formato PDF
- Limite de tamanho de arquivo: 10MB
- Validação de permissões por módulo

### 7.2 Performance
- Paginação em listagens (20-100 itens)
- Cache de classificações orçamentárias
- Lazy loading de documentos anexos

### 7.3 Usabilidade
- Cálculos automáticos em tempo real
- Validação de formulários inline
- Tooltips explicativos para campos técnicos
- Exportação para PDF e Excel

### 7.4 Conformidade Legal
- Lei 14.133/2021 - Licitações e Contratos
- Lei 13.019/2014 - MROSC
- Portaria 448 - Classificação de Despesas
- LGPD - Proteção de dados pessoais

---

## 8. PLANO DE IMPLEMENTAÇÃO

### Fase 1 - Reorganização de Menus (1 dia)
- [ ] Atualizar componente Sidebar
- [ ] Criar rotas para novos módulos
- [ ] Testar navegação

### Fase 2 - Ajustes em Processos (1 dia)
- [ ] Atualizar modelo de dados
- [ ] Migrar dados existentes
- [ ] Atualizar formulários frontend
- [ ] Testar CRUD completo

### Fase 3 - PAC Geral Obras (2-3 dias)
- [ ] Criar modelos backend
- [ ] Implementar endpoints API
- [ ] Criar páginas frontend
- [ ] Implementar classificação orçamentária
- [ ] Testes E2E

### Fase 4 - Prestação de Contas MROSC (5-7 dias)
- [ ] Criar modelos de dados completos
- [ ] Implementar endpoints CRUD
- [ ] Sistema de upload de documentos
- [ ] Cálculos automáticos de encargos
- [ ] Relatórios PDF/Excel
- [ ] Testes completos

---

## 9. PRÓXIMOS PASSOS

1. **Aprovação**: Revisar e aprovar esta especificação
2. **Priorização**: Definir ordem de implementação
3. **Desenvolvimento**: Seguir plano de implementação
4. **Testes**: Validação com usuários finais
5. **Deploy**: Implantação em produção

---

**Documento elaborado conforme requisitos do cliente e legislação vigente.**
