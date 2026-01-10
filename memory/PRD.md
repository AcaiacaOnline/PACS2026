# Planejamento Acaiaca - Sistema de Gestão Municipal
## Prefeitura Municipal de Acaiaca - CNPJ: 18.295.287/0001-90

### Visão Geral
Sistema completo de gestão municipal que inclui:
- **PAC (Plano Anual de Contratações)** - Gestão individual por secretaria
- **PAC Geral** - Visão consolidada de todas as secretarias
- **PAC Geral Obras e Serviços** - Módulo específico para obras e serviços de engenharia ✅
- **Gestão Processual** - Controle de processos licitatórios com campos atualizados ✅
- **DOEM (Diário Oficial Eletrônico Municipal)** - Publicações oficiais com assinatura digital
- **Portal de Transparência** - Acesso público às informações ✅ ATUALIZADO
- **Prestação de Contas MROSC** - Sistema conforme Lei 13.019/2014 ✅ COMPLETO
- **Dashboard Analítico** - Visão consolidada com gráficos e KPIs ✅
- **Sistema de Alertas** - Monitoramento de prazos e pendências ✅
- **Workflow de Prestação de Contas** - Submissão, análise, correção e aprovação ✅
- **Tipos de Usuário** - Servidor e Pessoa Externa (OSC) ✅
- **Notificações por Email** - Alertas automáticos sobre mudanças de status ✅
- **Relatórios Gerenciais Consolidados** - PDF com todos os módulos ✅
- **Newsletter** - Sistema de notificações por email
- **Histórico de Assinaturas** - Visualização de documentos assinados

---

## Última Atualização: 10/01/2026 (Sessão 5)

### Changelog - Sessão 5 (10/01/2026)

#### ✅ 1. Portal da Transparência - Menus Alinhados com Backend
- Adicionada aba **PAC Obras** no Portal Público
- Navegação agora inclui: Dashboard, PAC Individual, PAC Geral, **PAC Obras**, Processos, DOEM
- Alinhamento completo com os menus do sistema administrativo

#### ✅ 2. API Pública para PAC Geral Obras
- `GET /api/public/pacs-geral-obras` - Lista todos os PACs de Obras
- `GET /api/public/pacs-geral-obras/{id}` - Detalhes de um PAC
- `GET /api/public/pacs-geral-obras/{id}/items` - Itens do PAC
- `GET /api/public/pacs-geral-obras/{id}/export/pdf` - Exportação PDF

#### 📋 Tarefas Pendentes (P0)
1. **Refatoração do `server.py` em módulos** - Backend monolítico (8100+ linhas)
   - Estrutura de rotas já existe em `/app/backend/routes/`
   - Modelos já modularizados em `/app/backend/models/`
   - Requer migração gradual das rotas

2. **Versão cPanel** - Pacote para hospedagem compartilhada
   - Não iniciado

---

### Changelog - Sessão 4 (10/01/2026)

#### ✅ 1. Notificações por Email no MROSC
- Envio automático quando projeto é submetido (notifica admins)
- Envio quando correção é solicitada (notifica criador)
- Envio quando projeto é aprovado (notifica criador)
- HTML formatado com branding da prefeitura

#### ✅ 2. Relatórios Gerenciais Consolidados
- Endpoint `GET /api/relatorios/consolidado/pdf`
- PDF com resumo de todos os módulos
- Totais: PACs, Processos, MROSC
- Processos por Status
- Botão "Relatório PDF" no Dashboard Analítico

#### ✅ 3. Estrutura de Menus Organizada
- Menu dropdown **PACs** (Individual, Geral, Obras)
- Menu dropdown **Processos** (Gestão, Dashboard)
- Menu dropdown **DOEM**
- Botão **Analítico** (azul)
- Botão **MROSC** (verde)

---

### Changelog - Sessão 3 (10/01/2026)

#### ✅ 1. Tipos de Usuário no Registro
- **SERVIDOR**: Acesso completo ao sistema
- **PESSOA_EXTERNA**: Acesso restrito apenas ao módulo MROSC
- Seleção visual no formulário de registro
- Permissões automáticas baseadas no tipo
- Redirecionamento automático após login

#### ✅ 2. Workflow de Prestação de Contas (MROSC)
- **Submeter**: Usuário externo submete prestação para análise
- **Receber**: Admin confirma recebimento
- **Solicitar Correção**: Admin pede ajustes (habilita edição)
- **Aprovar**: Admin aprova prestação de contas
- **Histórico**: Rastreamento de todas as ações
- Bloqueio de edição após submissão
- Desbloqueio automático após pedido de correção

#### ✅ 3. Restrição de Acesso para Pessoa Externa
- Layout dedicado roxo para usuários externos
- Navegação limitada apenas ao MROSC
- Redirecionamento automático se tentar acessar outras páginas

#### ✅ 4. Interface de Administrador MROSC
- Botão "Receber Prestação de Contas"
- Botão "Pedir Correção" com modal para motivo
- Botão "Aprovar"
- Banner informativo azul
- Visualização do histórico de ações

---

### Changelog - Sessão 2 (10/01/2026)

#### ✅ 1. Upload de Documentos PDF - MROSC
- Endpoint `POST /api/mrosc/projetos/{id}/documentos/upload` (multipart/form-data)
- Endpoint `GET /api/mrosc/projetos/{id}/documentos` (listar)
- Endpoint `GET /api/mrosc/documentos/{doc_id}/download` (visualizar/download)
- Endpoint `DELETE /api/mrosc/projetos/{id}/documentos/{doc_id}` (excluir)
- Endpoint `PUT /api/mrosc/projetos/{id}/documentos/{doc_id}/validar` (validar)
- Nova aba "Documentos" no frontend com tabela e resumo
- Modal de upload com campos: Tipo, Número, Data, Valor, Despesa vinculada
- Limite de 10MB, apenas PDF

#### ✅ 2. Relatório PDF - Prestação de Contas MROSC
- Endpoint `GET /api/mrosc/projetos/{id}/relatorio/pdf`
- PDF consolidado com: Dados do projeto, Resumo financeiro, RH, Despesas, Documentos
- Formatação profissional conforme Lei 13.019/2014
- Botão "Exportar PDF" no frontend

#### ✅ 3. Exportação PDF - PAC Geral Obras
- Endpoint `GET /api/pacs-geral-obras/{id}/export/pdf`
- PDF com classificação Lei 14.133/2021 e Portaria 448/ME
- Botão "PDF" no frontend do editor

#### ✅ 4. Refatoração Backend - Modelos
- Criados arquivos modulares em `/app/backend/models/`:
  - `user.py` - Modelos de usuário
  - `pac.py` - Modelos PAC Individual e Geral
  - `pac_obras.py` - Modelos PAC Obras com classificações
  - `mrosc.py` - Modelos MROSC completos
  - `processo.py` - Modelos de processos
  - `doem.py` - Modelos DOEM
  - `newsletter.py` - Modelos Newsletter
- Exportação centralizada em `__init__.py`

#### ✅ 5. Dashboard Analítico (NOVO)
- Página `/dashboard-analitico` com visão consolidada
- KPIs: Total Planejado, Processos, Projetos MROSC, Alertas
- Gráfico de pizza: Distribuição por Secretaria
- Gráfico de barras: Processos por Status
- Aba Orçamento: Execução MROSC, Top Itens
- Aba Alertas: Lista de alertas por prioridade
- Endpoint `GET /api/analytics/dashboard`

#### ✅ 6. Sistema de Alertas (NOVO)
- Endpoint `GET /api/alertas/` com alertas automáticos
- Tipos de alertas:
  - Prazos de projetos MROSC vencendo
  - Documentos pendentes de validação
  - Processos sem número
  - Processos abertos há muito tempo
  - Edições DOEM em rascunho
- Classificação por prioridade: CRITICA, ALTA, MEDIA, BAIXA
- Navegação direta para o item relacionado

---

### Changelog Sessão Anterior

#### ✅ 1. Renomeação do Sistema
- Nome alterado de "PAC Acaiaca 2026" para **"Planejamento Acaiaca"**
- CNPJ corrigido para **18.295.287/0001-90**

#### ✅ 2. Ajustes no Módulo de Processos
- `Status` → `Modalidade de Contratação`
- `Situação` → `Status`
- `Número do Processo` agora obrigatório (*)
- **73 processos migrados automaticamente**

#### ✅ 3. Reorganização de Menus
- Menus dropdown: PACs, Processos, DOEM
- Novo botão MROSC na barra de navegação

#### ✅ 4. PAC Geral Obras e Serviços
- Classificação conforme Lei 14.133/2021 (339040, 449051, 339039)
- Subitens conforme Portaria 448/ME

#### ✅ 5. Sistema Prestação de Contas - MROSC (NOVO)
- **Backend completo:**
  - Modelos: `ProjetoMROSC`, `RecursoHumanoMROSC`, `DespesaMROSC`, `DocumentoMROSC`
  - Endpoints CRUD para projetos, RH, despesas
  - Cálculos automáticos CLT (FGTS, 13º, Férias, INSS)
  - Média de 3 orçamentos automática
  - Resumo orçamentário com saldo
  
- **Frontend completo:**
  - `PrestacaoContasList.jsx` - Lista de projetos MROSC
  - `PrestacaoContasEditor.jsx` - Editor com tabs para RH e Despesas
  - Estatísticas: Total projetos, Em execução, Valor total, Repasse público
  - Cards com detalhes de cálculos CLT

- **Naturezas de Despesa disponíveis:**
  - 319011 - Vencimentos e Vantagens Fixas
  - 319013 - Obrigações Patronais
  - 339030 - Material de Consumo
  - 339035 - Serviços de Consultoria
  - 339036 - Serviços Terceiros - PF
  - 339039 - Serviços Terceiros - PJ
  - 449052 - Equipamentos Permanentes

---

## Endpoints de API

### MROSC (NOVOS)
```
GET    /api/mrosc/naturezas-despesa           # Lista naturezas
GET    /api/mrosc/projetos                     # Lista projetos
POST   /api/mrosc/projetos                     # Criar projeto
GET    /api/mrosc/projetos/{id}                # Obter projeto
PUT    /api/mrosc/projetos/{id}                # Atualizar
DELETE /api/mrosc/projetos/{id}                # Excluir
GET    /api/mrosc/projetos/{id}/rh             # Lista RH
POST   /api/mrosc/projetos/{id}/rh             # Adicionar RH (cálculos CLT automáticos)
DELETE /api/mrosc/projetos/{id}/rh/{rh_id}     # Excluir RH
GET    /api/mrosc/projetos/{id}/despesas       # Lista despesas
POST   /api/mrosc/projetos/{id}/despesas       # Adicionar despesa (média automática)
DELETE /api/mrosc/projetos/{id}/despesas/{id}  # Excluir despesa
GET    /api/mrosc/projetos/{id}/resumo         # Resumo orçamentário
# Documentos/Comprovantes (10/01/2026)
GET    /api/mrosc/projetos/{id}/documentos              # Lista documentos
POST   /api/mrosc/projetos/{id}/documentos/upload       # Upload PDF (multipart/form-data)
GET    /api/mrosc/documentos/{doc_id}/download          # Download/visualizar PDF
DELETE /api/mrosc/projetos/{id}/documentos/{doc_id}     # Excluir documento
PUT    /api/mrosc/projetos/{id}/documentos/{doc_id}/validar  # Validar documento
# Relatório PDF (10/01/2026)
GET    /api/mrosc/projetos/{id}/relatorio/pdf           # Exportar relatório consolidado PDF
```

### PAC Geral Obras (10/01/2026)
```
GET    /api/pacs-geral-obras/{id}/export/pdf    # Exportar PAC Obras para PDF
```

### Processos (ATUALIZADOS)
```
POST   /api/processos/migrate-fields           # Migrar campos antigos
```

---

## Cálculos Automáticos CLT

```
Salário Bruto:           R$ X.XXX,XX
+ Provisão Férias:       1/12 do salário
+ Provisão 13º:          1/12 do salário
+ FGTS:                  8% sobre (salário + férias + 13º)
+ INSS Patronal:         20% sobre salário
+ Vale Transporte:       R$ XXX,XX
+ Vale Alimentação:      R$ XXX,XX
─────────────────────────────────────
= CUSTO MENSAL TOTAL:    R$ X.XXX,XX
× Número de Meses:       XX
─────────────────────────────────────
= CUSTO TOTAL PROJETO:   R$ XX.XXX,XX
```

---

## Próximos Passos (Backlog)

### 🟢 Concluído (Sessão 10/01/2026)
- [x] Ajustes em Processos
- [x] Reorganização de Menus
- [x] PAC Geral Obras e Serviços
- [x] Sistema Prestação de Contas MROSC
- [x] Upload de documentos PDF no MROSC ✅
- [x] Exportação PDF do PAC Geral Obras ✅
- [x] Relatório PDF de Prestação de Contas MROSC ✅
- [x] Refatoração de modelos (parcial) ✅
- [x] Dashboard Analítico com gráficos ✅
- [x] Sistema de Alertas automáticos ✅

### 🟡 P1 - Alta Prioridade
- [ ] Continuar refatoração do `server.py` (migrar rotas para módulos)

### 🟢 P3 - Baixa Prioridade
- [ ] Notificações de alertas por email
- [ ] Versão cPanel (PHP/MySQL)

---

## Credenciais de Teste
- **Admin**:
  - Email: `cristiano.abdo@acaiaca.mg.gov.br`
  - Senha: `Cris@820906`
  - CPF: `123.456.789-00`
  - Cargo: `Assessor de Planejamento`

---

## Estrutura de Arquivos

### Frontend (Novas páginas)
```
/app/frontend/src/pages/
├── PACGeralObrasList.jsx          # Lista PAC Obras
├── PACGeralObrasEditor.jsx        # Editor PAC Obras
├── PrestacaoContasList.jsx        # Lista projetos MROSC
└── PrestacaoContasEditor.jsx      # Editor projeto MROSC
```

### Backend (Novos endpoints)
- Linha ~660: Modelos MROSC
- Linha ~6512: Endpoints MROSC (mrosc_router)

---

## Conformidade Legal
- **Lei 14.133/2021** - Licitações e Contratos (PAC, PAC Geral Obras)
- **Lei 13.019/2014** - MROSC (Prestação de Contas)
- **Portaria 448/ME** - Classificação de Despesas
- **LGPD** - Proteção de dados pessoais
