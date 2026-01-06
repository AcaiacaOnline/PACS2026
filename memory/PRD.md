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

#### Módulo 1: Paginação Configurável com Backend
- **Backend**: Endpoints paginados implementados:
  - `/api/processos/paginado` - Gestão Processual
  - `/api/pacs/paginado` - PAC (NOVO)
  - `/api/pacs-geral/paginado` - PAC Geral (NOVO)
- **Frontend**: Componente `Pagination.jsx` reutilizável
- Opções: 20, 30, 50 ou 100 itens por página
- **Default**: 20 itens por página
- **Status**: COMPLETO E TESTADO (15/15 testes passaram)

#### Módulo 2: Campos de Assinatura Digital do Usuário
- CPF, Cargo, Telefone, CEP, Endereço
- Máscaras de formatação automática
- **Status**: COMPLETO E TESTADO

#### Módulo 3: Assinatura Digital Refinada em PDFs
- **ATUALIZADO**: Design elegante e refinado
- Posição: lateral DIREITA do documento
- Esquema de cores: azul escuro elegante (#1a365d)
- Cantos arredondados com sombra sutil
- Header: "DOCUMENTO ASSINADO DIGITALMENTE"
- Informações do assinante com nome, cargo e CPF mascarado
- QR Code para validação
- Código de validação destacado
- Aplicado em: DOEM, PAC, PAC Geral, Relatório de Processos
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

### Paginação
```
GET /api/processos/paginado?page=1&page_size=20&ano=2025&search=texto
GET /api/pacs/paginado?page=1&page_size=20&ano=2026&search=texto
GET /api/pacs-geral/paginado?page=1&page_size=20&ano=2026&search=texto
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

### Histórico de Assinaturas
```
GET /api/assinaturas/historico?page=1&page_size=10
GET /api/assinaturas/estatisticas
```

---

## Arquitetura Técnica

### Dependências
- `PyPDF2==3.0.1` - Manipulação de PDFs
- `qrcode==8.2` - Geração de QR Codes

### Banco de Dados
- `document_signatures` - Armazena assinaturas para validação
- `doem_edicoes.assinatura_digital.assinantes[]` - Lista de assinantes

---

## Próximos Passos (Backlog)

### P1 - Alta Prioridade
1. **Refatoração do server.py** (~6000 linhas)
   - Dividir em múltiplos APIRouters
   - Organizar em módulos: auth, pacs, processos, doem, assinaturas

### P2 - Média Prioridade
2. Melhorar validação de dados de assinatura do usuário (CPF, Cargo obrigatórios)

### P3 - Baixa Prioridade
3. Versão cPanel (PHP/MySQL)

---

## Última Atualização
**Data**: 06/01/2026
**Versão**: 2.8.0

### Changelog desta sessão:
- Selo de assinatura refinado com design elegante (lateral direita)
- Endpoints paginados para PAC e PAC Geral implementados
- Frontend atualizado para usar paginação em PAC e PAC Geral
- Gestão Processual confirmada com 20 itens por página
- 15 testes automatizados de paginação passando
- Testes de PDF com assinatura digital passando

### Testes Automatizados
- `/app/tests/test_pagination_endpoints.py` - 15 testes passando
- `/app/tests/test_historico_assinaturas.py` - 11 testes passando
- `/app/test_reports/iteration_8.json` - Relatório completo
