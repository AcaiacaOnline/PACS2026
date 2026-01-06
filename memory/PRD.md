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

---

## Status das Funcionalidades

### ✅ IMPLEMENTADO E FUNCIONANDO

#### Módulo 1: Paginação Configurável com Backend
- **Backend**: Endpoint `/api/processos/paginado` com parâmetros:
  - `page`, `page_size`, `ano`, `search`, `status`, `modalidade`
- **Frontend**: Componente `Pagination.jsx` reutilizável
- Opções: 20, 30, 50 ou 100 itens por página
- Implementado em: Gestão Processual, Usuários
- **Status**: COMPLETO E TESTADO

#### Módulo 2: Campos de Assinatura Digital do Usuário
- CPF, Cargo, Telefone, CEP, Endereço
- Máscaras de formatação automática
- **Status**: COMPLETO E TESTADO

#### Módulo 3: Assinatura Digital Compacta em PDFs
- **NOVO**: Selo compacto horizontal (12mm de altura) na parte inferior
- QR Code no lado esquerdo
- Lista de assinantes com CPF mascarado (LGPD)
- Código de validação
- Aplicado em: DOEM, PAC, Relatório de Processos
- **Status**: COMPLETO E TESTADO

#### Módulo 4: Painel de Validação de Documentos
- URL: `/validar`
- API: `POST /api/validar/verificar`
- Validação de múltiplos assinantes
- **Status**: COMPLETO E TESTADO

#### Módulo 5: Assinatura em Lote
- Interface para adicionar múltiplos assinantes antes de publicar
- PDF exibe todos os assinantes no selo compacto
- QR Code único valida todas as assinaturas
- **Status**: COMPLETO E TESTADO

#### Módulo 6: Notificações por Email para Assinantes
- **NOVO**: Cada assinante recebe email de confirmação
- Template HTML profissional com:
  - Código de validação
  - Link direto para validação
  - Dados da assinatura (nome, cargo, CPF mascarado)
- Enviado automaticamente na publicação
- **Status**: COMPLETO

---

## Endpoints de API Importantes

### Paginação
```
GET /api/processos/paginado?page=1&page_size=20&ano=2025&search=texto
Response: { items: [], total: 74, page: 1, page_size: 20, total_pages: 4 }
```

### Assinatura em Lote
```
GET /api/doem/usuarios-disponiveis
GET /api/doem/edicoes/{id}/assinantes
POST /api/doem/edicoes/{id}/assinantes { user_id: "xxx" }
DELETE /api/doem/edicoes/{id}/assinantes/{user_id}
```

### Validação de Documentos
```
GET /api/validar/{codigo}
POST /api/validar/verificar { validation_code: "DOC-XXX" }
```

---

## Arquitetura Técnica

### Dependências Novas
- `PyPDF2==3.0.1` - Manipulação de PDFs
- `qrcode==8.2` - Geração de QR Codes

### Banco de Dados
- `document_signatures` - Armazena assinaturas para validação
- `doem_edicoes.assinatura_digital.assinantes[]` - Lista de assinantes

---

## Próximos Passos (Backlog)

### P1 - Alta Prioridade
1. **Refatoração do server.py** (~5600 linhas)
   - Dividir em múltiplos APIRouters

### P2 - Média Prioridade
2. Aplicar paginação em outras listagens (PAC, PAC Geral)

### P3 - Baixa Prioridade
3. Versão cPanel (PHP/MySQL)

---

## Última Atualização
**Data**: 06/01/2026
**Versão**: 2.6.0

### Changelog desta sessão:
- Selo de assinatura reduzido para 2 linhas (12mm) na parte inferior
- Paginação implementada no backend (`/api/processos/paginado`)
- Assinatura digital aplicada em todos os relatórios (PAC, Processos)
- Notificações por email para assinantes implementadas
- Corrigidos bugs de indentação e imports
