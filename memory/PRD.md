# Sistema PAC - Prefeitura Municipal de Acaiaca
## Plano Anual de Contratações e Gestão Municipal

### Visão Geral
Sistema completo de gestão municipal que inclui:
- **PAC (Plano Anual de Contratações)** - Gestão individual por secretaria
- **PAC Geral** - Visão consolidada de todas as secretarias
- **Gestão Processual** - Controle de processos licitatórios
- **DOEM (Diário Oficial Eletrônico Municipal)** - Publicações oficiais com assinatura digital
- **Portal de Transparência** - Acesso público às informações
- **Newsletter** - Sistema de notificações por email
- **Histórico de Assinaturas** - Visualização de documentos assinados

---

## Status das Funcionalidades

### ✅ IMPLEMENTADO E FUNCIONANDO

#### Módulo 1: Geração de PDF Profissional - REFATORADO
- **Design Profissional**:
  - Cabeçalho institucional: "PREFEITURA MUNICIPAL DE ACAIACA - Estado de Minas Gerais"
  - Título do documento com referência à Lei Federal nº 14.133/2021
  - Caixa de informações com dados do órgão/secretaria
  - Tabela de itens com cores alternadas (#FFFFFF / #D6EAF8)
  - Seção de assinaturas e validação
  - Rodapé com informações de geração
- **Paginação de 15 itens por página**:
  - Constante `ITEMS_PER_PAGE = 15`
  - Cabeçalho resumido em páginas de continuação
  - Indicador "Itens X a Y de Z | Página N de M"
- **Selo de Assinatura Digital**:
  - Posição: lateral direita
  - QR Code para validação
  - Código de validação único
  - Nome, cargo e CPF mascarado do assinante
- **Status**: COMPLETO E TESTADO (20/20 testes passaram)

#### Módulo 2: Paginação Configurável com Backend
- **Backend**: Endpoints paginados implementados:
  - `/api/processos/paginado` - Gestão Processual
  - `/api/pacs/paginado` - PAC
  - `/api/pacs-geral/paginado` - PAC Geral
- **Frontend**: Componente `Pagination.jsx` reutilizável
- Opções: 20, 30, 50 ou 100 itens por página
- **Default**: 20 itens por página
- **Status**: COMPLETO E TESTADO (15/15 testes passaram)

#### Módulo 3: Campos de Assinatura Digital do Usuário
- CPF, Cargo, Telefone, CEP, Endereço
- Máscaras de formatação automática
- **Status**: COMPLETO E TESTADO

#### Módulo 4: Painel de Validação de Documentos
- URL: `/validar`
- API: `POST /api/validar/verificar`
- Validação de múltiplos assinantes
- **Status**: COMPLETO E TESTADO

#### Módulo 5: Assinatura em Lote
- Interface para adicionar múltiplos assinantes antes de publicar
- PDF exibe todos os assinantes no selo
- QR Code único valida todas as assinaturas
- **Status**: COMPLETO E TESTADO

#### Módulo 6: Notificações por Email para Assinantes
- Cada assinante recebe email de confirmação
- Template HTML profissional com código de validação
- Enviado automaticamente na publicação
- **Status**: COMPLETO

#### Módulo 7: Histórico de Assinaturas
- **Backend**: `/api/assinaturas/historico` e `/api/assinaturas/estatisticas`
- **Frontend**: Página `/historico-assinaturas`
- **Status**: COMPLETO E TESTADO (11/11 testes passaram)

---

## Endpoints de API Importantes

### Exportação de PDF
```
GET /api/pacs/{pac_id}/export/pdf?orientation=landscape
GET /api/pacs-geral/{pac_geral_id}/export/pdf?orientation=landscape
Headers de Resposta:
  - Content-Type: application/pdf
  - X-Validation-Code: DOC-XXXXXXXX-YYYYMMDD
```

### Paginação
```
GET /api/processos/paginado?page=1&page_size=20&ano=2025&search=texto
GET /api/pacs/paginado?page=1&page_size=20&ano=2026&search=texto
GET /api/pacs-geral/paginado?page=1&page_size=20&ano=2026&search=texto
Response: { items: [], total: 74, page: 1, page_size: 20, total_pages: 4 }
```

### Validação de Documentos
```
GET /api/validar/{codigo}
POST /api/validar/verificar { validation_code: "DOC-XXX" }
```

### Histórico de Assinaturas
```
GET /api/assinaturas/historico?page=1&page_size=10
GET /api/assinaturas/estatisticas
```

---

## Arquitetura Técnica

### Funções Auxiliares de PDF (Novas)
- `get_professional_styles()` - Retorna estilos profissionais
- `create_professional_header()` - Cabeçalho institucional
- `create_info_box()` - Caixa de informações do órgão
- `create_items_table_paginated()` - Tabela com formatação profissional
- `create_total_row()` - Linha de total destacada
- `create_signature_section()` - Seção de assinaturas
- `draw_signature_seal()` - Selo de assinatura digital

### Constantes
- `ITEMS_PER_PAGE = 15` - Máximo de itens por página no PDF
- Cores do tema:
  - Primária: #1F4E78 (azul escuro)
  - Secundária: #2E75B6 (azul médio)
  - Destaque: #FFC000 (amarelo dourado)
  - Linhas alternadas: #D6EAF8 (azul claro)

### Dependências
- `reportlab` - Geração de PDFs
- `PyPDF2` - Manipulação de PDFs
- `qrcode` - Geração de QR Codes

---

## Próximos Passos (Backlog)

### P1 - Alta Prioridade
1. **Refatoração do server.py** (~6000 linhas)
   - Dividir em múltiplos APIRouters
   - Organizar em módulos: auth, pacs, processos, doem, assinaturas

### P2 - Média Prioridade
2. Tornar CPF e Cargo obrigatórios para assinatura digital

### P3 - Baixa Prioridade
3. Versão cPanel (PHP/MySQL)

---

## Última Atualização
**Data**: 06/01/2026
**Versão**: 2.9.0

### Changelog desta sessão:
- Refatoração completa da geração de PDFs
- Design profissional com cabeçalho institucional
- Paginação de 15 itens por página implementada
- Cores alternadas na tabela (#FFFFFF / #D6EAF8)
- Selo de assinatura digital na lateral direita
- Funções auxiliares reutilizáveis criadas
- 20 testes automatizados de PDF passando

### Testes Automatizados
- `/app/tests/test_pdf_export.py` - 20 testes passando
- `/app/tests/test_pagination_endpoints.py` - 15 testes passando
- `/app/tests/test_historico_assinaturas.py` - 11 testes passando
- `/app/test_reports/iteration_9.json` - Relatório completo
