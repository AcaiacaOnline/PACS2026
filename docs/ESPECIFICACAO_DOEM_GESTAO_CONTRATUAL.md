# ESPECIFICAÇÃO TÉCNICA - MÓDULOS GESTÃO CONTRATUAL E DOEM

## PAC Acaiaca 2026 - Sistema de Gestão Municipal

**Versão:** 2.0  
**Data:** 02 de Janeiro de 2026  
**Autor:** Arquiteto de Software Sênior  
**Revisão:** Especialista em Sistemas de Gestão Pública

---

# PARTE I - MÓDULO DE GESTÃO CONTRATUAL (Aprimoramentos)

## 1. Sistema de Filtragem por Ano

### 1.1 Visão Geral
O sistema implementará filtros por ano em todos os módulos de gestão (Processos, PAC Individual e PAC Geral), permitindo aos usuários visualizar dados históricos de forma organizada.

### 1.2 Especificações Funcionais

#### 1.2.1 Interface de Filtro por Ano
```
┌─────────────────────────────────────────────────────────────────┐
│  📁 2026  ▼  │  [Lista de Anos Disponíveis]                    │
│              │  ┌──────────────────────┐                       │
│              │  │ 📁 2026 (atual)      │                       │
│              │  │ 📁 2025              │                       │
│              │  │ 📁 2024              │                       │
│              │  └──────────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

#### 1.2.2 Regras de Negócio

| Módulo | Ano Inicial | Regra de Incremento |
|--------|-------------|---------------------|
| **Processos** | 2025 | Sequencial (2025, 2026, 2027...) |
| **PAC Individual** | 2025 | Sequencial (2025, 2026, 2027...) |
| **PAC Geral** | 2026 | Sequencial (2026, 2027, 2028...) |

#### 1.2.3 Comportamento do Filtro
1. **Padrão**: Ano atual é selecionado por padrão
2. **Persistência**: Seleção do usuário é mantida durante a sessão
3. **Atualização Dinâmica**: Lista de anos é atualizada quando novos registros são criados
4. **Ícone Visual**: Pasta com o ano exibido claramente

### 1.3 Modelo de Dados

```python
# Índice composto para consultas eficientes
db.processos.create_index([("ano", 1), ("created_at", -1)])
db.pacs.create_index([("ano", 1), ("created_at", -1)])
db.pacs_geral.create_index([("ano", 1), ("created_at", -1)])
```

### 1.4 Endpoints da API

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/processos/anos` | Lista anos disponíveis |
| GET | `/api/processos?ano=2026` | Filtra processos por ano |
| GET | `/api/pacs/anos` | Lista anos de PACs |
| GET | `/api/pacs?ano=2026` | Filtra PACs por ano |
| GET | `/api/pacs-geral/anos` | Lista anos de PACs Gerais |
| GET | `/api/pacs-geral?ano=2026` | Filtra PACs Gerais por ano |

---

## 2. Configurações de Relatórios e Planilhas

### 2.1 Margens Padrão

```
┌─────────────────────────────────────────────────────────────────┐
│                         3cm (superior)                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │                                                           │  │
│5cm│                    ÁREA DE CONTEÚDO                      │5cm│
│(E)│                                                           │(D)│
│  │                                                           │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                         3cm (inferior)                          │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Especificações de Margem

| Parâmetro | Valor (cm) | Valor (mm) | Valor (pontos) |
|-----------|------------|------------|----------------|
| Margem Esquerda | 5.0 | 50 | 141.7 |
| Margem Direita | 5.0 | 50 | 141.7 |
| Margem Superior | 3.0 | 30 | 85.0 |
| Margem Inferior | 3.0 | 30 | 85.0 |

### 2.3 Área Útil Calculada (A4)

| Orientação | Largura Útil | Altura Útil |
|------------|--------------|-------------|
| Retrato | 110mm (21cm - 10cm) | 237mm (29.7cm - 6cm) |
| Paisagem | 197mm (29.7cm - 10cm) | 150mm (21cm - 6cm) |

### 2.4 Configuração ReportLab

```python
REPORT_MARGINS = {
    'leftMargin': 50*mm,    # 5cm
    'rightMargin': 50*mm,   # 5cm
    'topMargin': 30*mm,     # 3cm
    'bottomMargin': 30*mm   # 3cm
}
```

---

# PARTE II - MÓDULO DOEM (Diário Oficial Eletrônico Municipal)

## 1. Visão Geral do Sistema

### 1.1 Objetivo
Criar um sistema completo de Diário Oficial Eletrônico Municipal para a Prefeitura de Acaiaca - MG, permitindo a publicação, gestão e consulta de atos oficiais em conformidade com a legislação vigente.

### 1.2 Referência Visual
O design será inspirado no portal `https://jornalminasgerais.mg.gov.br/`, adaptado para as necessidades municipais.

### 1.3 Público-Alvo
- **Administradores**: Publicação e gestão de conteúdo
- **Cidadãos**: Consulta pública das publicações
- **Órgãos de Controle**: Verificação de publicações oficiais

---

## 2. Arquitetura do Sistema

### 2.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOEM - ACAIACA                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │  PORTAL PÚBLICO │    │ ÁREA DE GESTÃO  │    │   STORAGE   │ │
│  │  (Consulta)     │◄──►│ (Publicação)    │◄──►│ (MongoDB)   │ │
│  └─────────────────┘    └─────────────────┘    └─────────────┘ │
│           │                      │                     │        │
│           ▼                      ▼                     ▼        │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │  VISUALIZADOR   │    │ IMPORTADOR RTF  │    │ GERADOR PDF │ │
│  │  (Jornal)       │    │ (Parser)        │    │ (ReportLab) │ │
│  └─────────────────┘    └─────────────────┘    └─────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Stack Tecnológico

| Componente | Tecnologia | Justificativa |
|------------|------------|---------------|
| Backend | FastAPI | Consistência com sistema existente |
| Frontend | React + TailwindCSS | Interface responsiva |
| Parser RTF | striprtf (Python) | Extração de texto RTF |
| PDF Generator | ReportLab | Geração de documentos oficiais |
| Storage | MongoDB + GridFS | Armazenamento de arquivos |
| Assinatura Digital | PyPDF2 + cryptography | Certificação digital |

---

## 3. Modelo de Dados

### 3.1 Coleção: `doem_edicoes`

```javascript
{
  "_id": ObjectId,
  "edicao_id": "doem_uuid",
  "numero_edicao": 1234,
  "ano": 2026,
  "data_publicacao": ISODate("2026-01-15"),
  "data_criacao": ISODate("2026-01-14T15:30:00Z"),
  "status": "publicado",  // rascunho, agendado, publicado
  "publicacoes": [
    {
      "publicacao_id": "pub_uuid",
      "titulo": "Decreto nº 001/2026",
      "texto": "Conteúdo completo...",
      "secretaria": "Gabinete do Prefeito",
      "tipo": "decreto",  // decreto, portaria, lei, edital, aviso, etc.
      "ordem": 1
    }
  ],
  "criado_por": "user_id",
  "pdf_url": "/doem/2026/edicao_1234.pdf",
  "assinatura_digital": {
    "assinado": true,
    "data_assinatura": ISODate("2026-01-15T00:00:01Z"),
    "hash": "sha256:abc123...",
    "certificado": "ICP-Brasil"
  }
}
```

### 3.2 Coleção: `doem_config`

```javascript
{
  "_id": ObjectId,
  "config_id": "doem_config_main",
  "nome_municipio": "Acaiaca",
  "uf": "MG",
  "brasao_url": "/assets/brasao_acaiaca.png",
  "prefeito": "Nome do Prefeito",
  "ano_inicio": 2026,
  "ultimo_numero_edicao": 1234,
  "tipos_publicacao": [
    "Decreto", "Portaria", "Lei", "Edital", 
    "Aviso", "Extrato de Contrato", "Ata", "Outros"
  ]
}
```

---

## 4. Fluxo de Publicação

### 4.1 Diagrama de Fluxo

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   UPLOAD    │────►│   PARSER    │────►│   PREVIEW   │
│   (RTF)     │     │   (Texto)   │     │  (Edição)   │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  PUBLICADO  │◄────│   GERAR     │◄────│  AGENDAR    │
│  (Portal)   │     │   (PDF)     │     │  (Data)     │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 4.2 Etapas do Processo

1. **Upload**: Administrador faz upload do arquivo RTF
2. **Parser**: Sistema extrai título e texto do RTF (Arial 9)
3. **Preview**: Administrador revisa e edita se necessário
4. **Agendar**: Define data de publicação (padrão: dia seguinte)
5. **Gerar PDF**: Sistema gera PDF com layout de jornal
6. **Publicar**: Disponibiliza no portal público

---

## 5. Formato do Arquivo RTF

### 5.1 Estrutura Esperada

```rtf
{\rtf1\ansi\deff0
{\fonttbl{\f0 Arial;}}
\f0\fs18

=== TÍTULO DA PUBLICAÇÃO ===

Conteúdo do texto da publicação...
Lorem ipsum dolor sit amet...

===

}
```

### 5.2 Regras de Formatação

| Elemento | Formato | Exemplo |
|----------|---------|---------|
| Fonte | Arial | `{\f0 Arial;}` |
| Tamanho | 9pt (18 half-points) | `\fs18` |
| Título | Entre `===` | `=== DECRETO Nº 001/2026 ===` |
| Separador | `===` | Indica fim de uma publicação |

### 5.3 Parser Python

```python
import re
from striprtf.striprtf import rtf_to_text

def parse_rtf_publicacao(rtf_content: bytes) -> list:
    """
    Extrai publicações de arquivo RTF.
    Retorna lista de dicionários com título e texto.
    """
    text = rtf_to_text(rtf_content.decode('latin-1'))
    
    # Regex para extrair publicações
    pattern = r'===\s*(.+?)\s*===\s*(.*?)(?====|$)'
    matches = re.findall(pattern, text, re.DOTALL)
    
    publicacoes = []
    for titulo, texto in matches:
        publicacoes.append({
            'titulo': titulo.strip(),
            'texto': texto.strip()
        })
    
    return publicacoes
```

---

## 6. Layout do Jornal (PDF)

### 6.1 Estrutura da Página

```
┌─────────────────────────────────────────────────────────────────┐
│  [BRASÃO]   DIÁRIO OFICIAL ELETRÔNICO            [DATA]         │
│             MUNICÍPIO DE ACAIACA - MG                           │
│             Edição nº 1234 | Ano I | 15 de Janeiro de 2026     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PODER EXECUTIVO                                                │
│  ═══════════════════════════════════════════════════════════   │
│                                                                  │
│  GABINETE DO PREFEITO                                           │
│  ───────────────────────────────────────────────────────────   │
│                                                                  │
│  DECRETO Nº 001/2026                                            │
│                                                                  │
│  Dispõe sobre medidas administrativas e dá outras              │
│  providências.                                                  │
│                                                                  │
│  O PREFEITO MUNICIPAL DE ACAIACA, no uso de suas               │
│  atribuições legais...                                         │
│                                                                  │
│  ───────────────────────────────────────────────────────────   │
│                                                                  │
│  PORTARIA Nº 001/2026                                           │
│  ...                                                            │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  Prefeitura Municipal de Acaiaca | CNPJ: XX.XXX.XXX/0001-XX    │
│  Este documento foi assinado digitalmente | Verificação: [URL] │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Especificações de Fonte

| Elemento | Fonte | Tamanho | Estilo |
|----------|-------|---------|--------|
| Cabeçalho Principal | Arial | 14pt | Bold |
| Subtítulo | Arial | 10pt | Normal |
| Seção (Poder) | Arial | 12pt | Bold, Maiúsculo |
| Secretaria | Arial | 10pt | Bold |
| Título Publicação | Arial | 10pt | Bold |
| Corpo do Texto | Arial | 9pt | Normal, Justificado |
| Rodapé | Arial | 7pt | Normal |

### 6.3 Margens do Jornal

```python
DOEM_MARGINS = {
    'leftMargin': 50*mm,    # 5cm
    'rightMargin': 50*mm,   # 5cm
    'topMargin': 30*mm,     # 3cm
    'bottomMargin': 30*mm   # 3cm
}
```

---

## 7. Interface do Usuário

### 7.1 Portal Público (Consulta)

```
┌─────────────────────────────────────────────────────────────────┐
│  🏛️ DOEM - Diário Oficial Eletrônico de Acaiaca                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🔍 Pesquisar: [________________________] [Buscar]              │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  📰 EDIÇÕES POR ANO                                      │   │
│  │                                                           │   │
│  │  📁 2026 (12 edições)                                    │   │
│  │    ├─ 📄 Edição 1234 - 15/01/2026                       │   │
│  │    ├─ 📄 Edição 1233 - 14/01/2026                       │   │
│  │    └─ 📄 Edição 1232 - 13/01/2026                       │   │
│  │                                                           │   │
│  │  📁 2025 (245 edições)                                   │   │
│  │                                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ÚLTIMA EDIÇÃO PUBLICADA                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  📰 Edição nº 1234 | 15/01/2026                         │   │
│  │  • Decreto nº 001/2026 - Gabinete do Prefeito           │   │
│  │  • Portaria nº 002/2026 - Sec. Administração            │   │
│  │  • Edital de Licitação - Sec. Obras                     │   │
│  │                                                           │   │
│  │  [Ver Completo] [Baixar PDF]                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Área Administrativa (Publicação)

```
┌─────────────────────────────────────────────────────────────────┐
│  📰 DOEM - Gestão de Publicações                [Admin]         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [+ Nova Edição]  [📤 Importar RTF]  [⚙️ Configurações]        │
│                                                                  │
│  EDIÇÕES RECENTES                                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  📰 Edição 1235 | 16/01/2026 | ⏳ Agendada              │   │
│  │  📰 Edição 1234 | 15/01/2026 | ✅ Publicada             │   │
│  │  📰 Edição 1233 | 14/01/2026 | ✅ Publicada             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  IMPORTAR PUBLICAÇÃO                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  📁 Arraste o arquivo RTF ou [Selecionar Arquivo]       │   │
│  │                                                           │   │
│  │  📅 Data de Publicação: [16/01/2026] (editável)         │   │
│  │                                                           │   │
│  │  Secretaria: [Selecionar ▼]                             │   │
│  │  Tipo: [Decreto ▼]                                       │   │
│  │                                                           │   │
│  │  [Pré-visualizar] [Publicar]                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Endpoints da API

### 8.1 API Pública (Consulta)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/public/doem/edicoes` | Lista edições por ano |
| GET | `/api/public/doem/edicoes/{id}` | Detalhes de uma edição |
| GET | `/api/public/doem/edicoes/{id}/pdf` | Download do PDF |
| GET | `/api/public/doem/busca?q=termo` | Busca em publicações |
| GET | `/api/public/doem/anos` | Lista anos disponíveis |

### 8.2 API Administrativa

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/doem/edicoes` | Lista todas as edições |
| POST | `/api/doem/edicoes` | Criar nova edição |
| PUT | `/api/doem/edicoes/{id}` | Editar edição |
| DELETE | `/api/doem/edicoes/{id}` | Excluir edição (rascunho) |
| POST | `/api/doem/import-rtf` | Importar arquivo RTF |
| POST | `/api/doem/edicoes/{id}/publicar` | Publicar edição |
| POST | `/api/doem/edicoes/{id}/gerar-pdf` | Gerar PDF |
| GET | `/api/doem/config` | Configurações do DOEM |
| PUT | `/api/doem/config` | Atualizar configurações |

---

## 9. Assinatura Digital

### 9.1 Processo de Assinatura

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   GERAR PDF     │────►│  CALCULAR HASH  │────►│   ASSINAR COM   │
│   (Conteúdo)    │     │   (SHA-256)     │     │   CERTIFICADO   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   ARMAZENAR     │◄────│   ADICIONAR     │◄────│   CARIMBO DE    │
│   (MongoDB)     │     │   METADADOS     │     │   DATA/HORA     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 9.2 Metadados de Assinatura

```python
assinatura = {
    'algoritmo': 'SHA256withRSA',
    'hash_documento': hashlib.sha256(pdf_bytes).hexdigest(),
    'data_assinatura': datetime.now(timezone.utc).isoformat(),
    'certificado': {
        'tipo': 'ICP-Brasil',
        'titular': 'Prefeitura Municipal de Acaiaca',
        'validade': '2027-12-31'
    },
    'carimbo_tempo': {
        'servidor': 'tsa.example.com',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
}
```

---

## 10. Plano de Desenvolvimento

### 10.1 Fase 1 - Gestão Contratual (1 semana)

| Tarefa | Prioridade | Estimativa |
|--------|------------|------------|
| Implementar filtro por ano (Processos) | Alta | 4h |
| Implementar filtro por ano (PAC) | Alta | 4h |
| Implementar filtro por ano (PAC Geral) | Alta | 4h |
| Atualizar margens dos relatórios | Alta | 2h |
| Testes e ajustes | Média | 6h |

### 10.2 Fase 2 - DOEM Backend (2 semanas)

| Tarefa | Prioridade | Estimativa |
|--------|------------|------------|
| Criar modelos de dados | Alta | 4h |
| Implementar CRUD de edições | Alta | 8h |
| Parser de arquivos RTF | Alta | 6h |
| Gerador de PDF (layout jornal) | Alta | 12h |
| Sistema de assinatura digital | Média | 8h |
| Endpoints públicos | Alta | 4h |

### 10.3 Fase 3 - DOEM Frontend (2 semanas)

| Tarefa | Prioridade | Estimativa |
|--------|------------|------------|
| Portal público de consulta | Alta | 16h |
| Área administrativa | Alta | 16h |
| Importação de RTF | Alta | 8h |
| Visualizador de jornal | Média | 8h |
| Botão no Dashboard | Alta | 2h |

### 10.4 Fase 4 - Testes e Deploy (1 semana)

| Tarefa | Prioridade | Estimativa |
|--------|------------|------------|
| Testes unitários | Alta | 8h |
| Testes de integração | Alta | 8h |
| Documentação | Média | 4h |
| Deploy e monitoramento | Alta | 8h |

---

## 11. Critérios de Aceitação

### 11.1 Gestão Contratual
- [ ] Filtro por ano funcional em Processos, PAC e PAC Geral
- [ ] Anos listados corretamente (Processos: 2025+, PAC: 2025+, PAC Geral: 2026+)
- [ ] Margens de relatórios: 5cm (E/D), 3cm (S/I)
- [ ] Planilhas ocupam área útil corretamente

### 11.2 DOEM
- [ ] Importação de RTF com extração de título/texto
- [ ] Data de publicação editável pelo admin
- [ ] PDF gerado com layout de jornal
- [ ] Carimbo de data e assinatura digital no PDF
- [ ] Portal público com organização por ano (pastas)
- [ ] Busca textual em publicações
- [ ] Download de PDF público

---

## 12. Conclusão

Esta especificação técnica estabelece os requisitos completos para:

1. **Gestão Contratual**: Sistema de filtragem por ano com margens padronizadas
2. **DOEM**: Portal completo de Diário Oficial Eletrônico

A implementação seguirá as melhores práticas de desenvolvimento, garantindo:
- Segurança e integridade dos dados
- Interface intuitiva para todos os usuários
- Performance otimizada
- Conformidade com requisitos legais

---

**Aprovado por:**

_______________________________
Cristiano Abdo de Souza
Assessor de Planejamento, Compras e Logística

**Data:** ___/___/______
