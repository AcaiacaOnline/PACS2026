# Planejamento Acaiaca - Sistema de Gestão Municipal
## Prefeitura Municipal de Acaiaca - CNPJ: 18.295.287/0001-90

### Visão Geral
Sistema completo de gestão municipal que inclui:
- **PAC (Plano Anual de Contratações)** - Gestão individual por secretaria
- **PAC Geral** - Visão consolidada de todas as secretarias
- **PAC Geral Obras e Serviços** - Módulo específico para obras e serviços de engenharia ✅
- **Gestão Processual** - Controle de processos licitatórios com campos atualizados ✅
- **DOEM (Diário Oficial Eletrônico Municipal)** - Publicações oficiais com assinatura digital
- **Portal de Transparência** - Acesso público com menus dropdown ✅
- **Prestação de Contas MROSC** - Sistema completo com workflow de aprovação ✅ ATUALIZADO v2.0
- **Dashboard Analítico** - Visão consolidada com gráficos e KPIs ✅
- **Sistema de Alertas** - Monitoramento de prazos e pendências ✅
- **Workflow de Prestação de Contas** - Submissão, análise, correção e aprovação ✅
- **Tipos de Usuário** - Servidor e Pessoa Externa (OSC) ✅
- **Notificações por Email** - Alertas automáticos sobre mudanças de status ✅
- **Relatórios Gerenciais Consolidados** - PDF com todos os módulos ✅
- **Backup Completo v2.1** - Corrigido e funcional ✅ CORRIGIDO
- **Menu Configurações** - Dropdown com Assinaturas, Usuários, Backup ✅
- **Sistema de Instalação** - Similar ao WordPress ✅ NOVO
- **Upload de Imagens** - Suporte a PDF, JPG, PNG no MROSC ✅ NOVO
- **Newsletter** - Sistema de notificações por email
- **Histórico de Assinaturas** - Visualização de documentos assinados

---

## Última Atualização: 18/01/2026 (Sessão 8)

### Changelog - Sessão 8 (18/01/2026)

#### ✅ 1. RELATÓRIO PDF CONSOLIDADO MROSC
Implementado endpoint `/api/mrosc/projetos/{id}/relatorio/consolidado` que gera PDF completo com:
- Capa com dados do projeto e valor total
- Dados do projeto e concedente
- Tabela de Recursos Humanos com custos
- Tabela de Despesas com valores
- Resumo Financeiro
- Lista de documentos anexados
- **Anexos incorporados** - PDFs e imagens convertidas para PDF são mesclados no documento final

#### ✅ 2. PAINEL DE ANALYTICS EM TEMPO REAL
Nova página `/analytics` com métricas em tempo real:
- **Uso por Secretaria**: Gráfico de barras com valor total por secretaria
- **Atividade por Horário**: Gráfico de área mostrando picos de uso nos últimos 7 dias
- **Tendência de Gastos**: Gráfico de linha com evolução dos últimos 6 meses
- **Top 10 Usuários Ativos**: Ranking de usuários por documentos criados
- **Status dos Módulos**: Cards com status de cada módulo (PAC, Processos, MROSC, etc.)
- **Métricas de Desempenho**: Usuários ativos, documentos criados hoje/semana
- **Auto-refresh**: Atualização automática a cada 30 segundos

#### ✅ 3. TESTES CORRIGIDOS
Arquivos de teste atualizados para corresponder à estrutura real da API:
- `test_auth.py` - Testes de autenticação
- `test_backup.py` - Testes de backup
- `test_pac.py` - Testes de PAC (ajustados para estrutura de resposta)
- `test_processos.py` - Testes de processos
- `test_public.py` - Testes públicos
- `test_mrosc.py` - Testes MROSC
- Configuração do pytest com httpx síncrono

**Testes passando:** 21 de 25 (4 falhas são rotas não implementadas no server.py original)

---

### Changelog - Sessão 7 (18/01/2026)

#### ✅ 1. REFATORAÇÃO DO BACKEND (Iniciada)
Criação de arquivos modulares de rotas em `/app/backend/routes/`:

**Novos Arquivos Criados:**
- `pac.py` - Rotas completas de PAC Individual (CRUD, export PDF/XLSX, import)
- `pac_geral.py` - Rotas completas de PAC Geral (CRUD, export, import)
- `pac_obras.py` - Rotas de PAC Obras (CRUD, export, classificação obras)
- `gestao_processual.py` - Rotas de Processos (CRUD, stats, import/export)
- `public.py` - Rotas públicas do Portal da Transparência
- `mrosc.py` - Rotas completas do MROSC (projetos, RH, despesas, documentos, workflow)
- `analytics.py` - Dashboard analítico, sistema de alertas, relatórios gerenciais
- `__init__.py` - Exportação de todos os routers e funções setup

**Status:** Os módulos foram criados com toda a lógica extraída. O `server.py` original ainda está funcional como fallback.

#### ✅ 2. VERSÃO cPANEL (Completa)
Pacote completo para hospedagem compartilhada em `/app/cpanel-version/`:

- `install.php` - Instalador interativo similar ao WordPress
  - Verificação de requisitos (PHP 7.4+, extensões)
  - Teste de conexão MySQL
  - Execução automática do schema
  - Criação de arquivo de configuração
  - Interface visual com passos guiados

- `schema.sql` - Esquema completo do banco MySQL
  - Todas as tabelas (users, pacs, pac_items, processos, mrosc_*, doem_*)
  - Índices otimizados
  - Foreign keys
  - Usuário admin padrão (admin@acaiaca.mg.gov.br / Admin@123)

- `README.md` - Documentação de instalação

#### ✅ 3. TESTES UNITÁRIOS (Estrutura Criada)
Diretório `/app/backend/tests/` com:

- `conftest.py` - Fixtures (db, client, admin_token, sample data)
- `test_auth.py` - Testes de autenticação e usuários
- `test_backup.py` - Testes de backup e classificação
- `test_pac.py` - Testes de PAC Individual, Geral e Obras
- `test_processos.py` - Testes de Gestão Processual
- `test_mrosc.py` - Testes do módulo MROSC
- `test_public.py` - Testes das rotas públicas
- `pytest.ini` - Configuração do pytest

**Comando para executar:** `cd /app/backend && python -m pytest tests/ -v`

---

### Changelog - Sessão 6 (18/01/2026)

#### ✅ 1. CORREÇÃO DO BACKUP - ERRO CRÍTICO RESOLVIDO
- **Problema:** `Object of type datetime is not JSON serializable`
- **Causa:** Campos datetime não estavam sendo convertidos corretamente
- **Solução:** 
  - Criada função `serialize_for_json()` para conversão recursiva
  - Criada função `serialize_document()` para documentos MongoDB
  - Adicionado `default=str` no json.dumps como fallback
- **Versão:** Backup atualizado para v2.1
- **Testado:** ✅ Funcionando (HTTP 200, JSON válido)

#### ✅ 2. MODELO DE DADOS MROSC APRIMORADO
Baseado na planilha orçamentária SUCC/BH e Recomendação MPC 01/2025:

**Novas Naturezas de Despesa:**
- 319011 - Vencimentos e Vantagens Fixas
- 319013 - Obrigações Patronais
- 319092 - Despesas de Exercícios Anteriores
- 339014 - Diárias
- 339030 - Material de Consumo
- 339031 - Premiações Culturais
- 339032 - Material de Distribuição Gratuita
- 339033 - Passagens e Locomoção
- 339035 - Serviços de Consultoria
- 339036 - Serviços Terceiros PF
- 339039 - Serviços Terceiros PJ
- 339046 - Auxílio-Alimentação
- 339049 - Auxílio-Transporte
- 449051 - Obras e Instalações
- 449052 - Equipamentos Permanentes

**Novos Campos (Recomendação MPC):**
- Dados do Concedente (tipo, nome, emenda, termo)
- Conta Bancária Específica (banco, agência, conta)
- Gestor Responsável (nome, CPF, cargo)
- Plano de Trabalho Estruturado
- 3 Orçamentos com Fornecedores/CNPJ
- Referência de Preços Municipal

#### ✅ 3. UPLOAD DE IMAGENS (PDF + JPG + PNG)
- **Endpoint atualizado:** `/api/mrosc/projetos/{id}/documentos/upload`
- **Formatos aceitos:** PDF, JPG, JPEG, PNG
- **Limite:** 10MB por arquivo
- **Content-Type dinâmico** baseado na extensão
- **Tipos de documento expandidos:** 17 tipos disponíveis

#### ✅ 4. SISTEMA DE INSTALAÇÃO (WordPress-like)
- **Arquivo:** `/app/backend/install.py`
- **Funcionalidades:**
  - Configuração interativa via terminal
  - Teste de conexão MongoDB
  - Criação automática de índices
  - Criação de usuário administrador
  - Geração de arquivo .env
  - Criação de diretório uploads
- **Uso:** `python install.py`

#### ✅ 5. PORTAL DE TRANSPARÊNCIA ATUALIZADO
- Campos obrigatórios conforme Recomendação MPC 01/2025
- Dados não sensíveis expostos publicamente
- APIs públicas para MROSC funcionando

---

### Requisitos Implementados - Recomendação MPC 01/2025

| Item | Requisito | Status |
|------|-----------|--------|
| 1 | Concedente (parlamentar/órgão) | ✅ |
| 2 | Número da Emenda/Termo | ✅ |
| 3 | Beneficiário e CNPJ | ✅ |
| 4 | Gestor Responsável | ✅ |
| 5 | Objeto Detalhado | ✅ |
| 6 | Natureza da Despesa (GND) | ✅ |
| 7 | Valores e Datas | ✅ |
| 8 | Conta Bancária | ✅ |
| 9 | Data Disponibilização | ✅ |
| 10 | Rastreabilidade | ✅ |

---

### Changelog - Sessão 5 (10/01/2026)

#### ✅ 1. Menu Configurações
- Novo dropdown "Configurações" no menu principal
- Contém: Assinaturas, Usuários (admin), Backup (admin)
- Nome do usuário visível (ex: "Cristiano") com ícone de admin
- Botão "Sair" em destaque vermelho

#### ✅ 2. MROSC - Ações de Workflow Corrigidas
- **7 botões de ação** agora visíveis para projetos submetidos:
  - Editar/Gerenciar, Histórico, Download PDF
  - Confirmar Recebimento (admin)
  - Pedir Correção (admin)
  - Aprovar Prestação (admin)
  - Excluir
- Lógica corrigida para detectar status submetido

#### ✅ 3. Cadastro de Usuário - Tipo de Usuário
- Formulário de registro JÁ POSSUI seleção de tipo:
  - Servidor Municipal (acesso completo)
  - Pessoa Externa/OSC (acesso apenas ao MROSC)
- Alerta informativo para Pessoa Externa

#### ✅ 4. Portal da Transparência
- Menus dropdown funcionando (PACs, Processos, DOEM)
- Seção MROSC com estatísticas e projetos

#### ✅ 5. Backup Completo v2.0
- Inclui todos os módulos (PAC Obras, MROSC, DOEM, Assinaturas)

#### 📋 Tarefas Pendentes (P0) - ATUALIZADAS
1. ~~**Refatoração do `server.py` em módulos**~~ - ✅ Módulos criados (necessário integração final)
2. ~~**Versão cPanel**~~ - ✅ Pacote completo criado
3. ~~**Testes Unitários**~~ - ✅ Estrutura criada e corrigida
4. ~~**Relatório PDF Consolidado MROSC**~~ - ✅ Implementado com anexos
5. ~~**Painel Analytics Tempo Real**~~ - ✅ Implementado

#### 📋 Tarefas P1 (Próximas)
1. **Integração final dos módulos** - Refatorar server.py para usar os novos routers de forma definitiva
2. **Documentação API (Swagger)** - Gerar documentação automática
3. **Sistema de logs centralizado** - Implementar logging estruturado

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
