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

#### Módulo 3: Assinatura Digital em PDFs - LATERAL ESQUERDA
- **ATUALIZADO**: Selo vertical compacto na LATERAL ESQUERDA
- QR Code para validação
- Lista de assinantes com CPF mascarado (LGPD)
- Código de validação único
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
- Cada assinante recebe email de confirmação
- Template HTML profissional com código de validação
- Enviado automaticamente na publicação
- **Status**: COMPLETO

#### Módulo 7: Histórico de Assinaturas - NOVO
- **Backend**:
  - `GET /api/assinaturas/historico` - Lista paginada de assinaturas do usuário
  - `GET /api/assinaturas/estatisticas` - Estatísticas de assinaturas
- **Frontend**: Página `/historico-assinaturas`
  - Cards de estatísticas (Total, Válidos, Últimos 30 dias, Tipos)
  - Tabela com documentos assinados
  - Busca e paginação
  - Link para validação de cada documento
- **Menu**: Link "Assinaturas" na navegação
- **Status**: COMPLETO E TESTADO (11/11 testes passaram)

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

### Histórico de Assinaturas (NOVO)
```
GET /api/assinaturas/historico?page=1&page_size=10
Response: { items: [{signature_id, document_type, validation_code, created_at, is_valid, total_signers, my_signature}], total, page, page_size, total_pages }

GET /api/assinaturas/estatisticas
Response: { total_assinaturas, assinaturas_validas, assinaturas_invalidas, ultimos_30_dias, por_tipo, ultima_assinatura }
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
1. **Refatoração do server.py** (~5500 linhas)
   - Dividir em múltiplos APIRouters
   - Organizar em módulos: auth, pacs, processos, doem, assinaturas

### P2 - Média Prioridade
2. Aplicar paginação em outras listagens (PAC, PAC Geral)

### P3 - Baixa Prioridade
3. Versão cPanel (PHP/MySQL)

---

## Última Atualização
**Data**: 06/01/2026
**Versão**: 2.7.0

### Changelog desta sessão:
- Selo de assinatura movido para LATERAL ESQUERDA do documento
- Implementado histórico de assinaturas completo (/historico-assinaturas)
- Adicionados endpoints /api/assinaturas/historico e /api/assinaturas/estatisticas
- Link "Assinaturas" adicionado ao menu de navegação
- 11 testes automatizados criados e passando

### Testes Automatizados
- `/app/tests/test_historico_assinaturas.py` - 11 testes passando
- `/app/test_reports/iteration_7.json` - Relatório completo
