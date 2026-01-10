# Sistema PAC - Prefeitura Municipal de Acaiaca
## Plano Anual de Contratações e Gestão Municipal

### Visão Geral
Sistema completo de gestão municipal que inclui:
- **PAC (Plano Anual de Contratações)** - Gestão individual por secretaria
- **PAC Geral** - Visão consolidada de todas as secretarias
- **Gestão Processual** - Controle de processos licitatórios
- **DOEM (Diário Oficial Eletrônico Municipal)** - Publicações oficiais com assinatura digital
- **Portal de Transparência** - Acesso público às informações com paginação
- **Newsletter** - Sistema de notificações por email
- **Histórico de Assinaturas** - Visualização de documentos assinados

---

## Arquitetura Modular

### Estrutura de Diretórios (Atualizada)
```
/app/backend/
├── server.py           # Arquivo principal (~6000 linhas)
├── models/             # Modelos Pydantic ✅
│   ├── __init__.py     # Exporta todos os modelos
│   ├── user.py         # User, UserCreate, UserUpdate, UserPermissions
│   ├── pac.py          # PAC, PACItem, PACGeral, PACGeralItem
│   ├── processo.py     # Processo, ProcessoCreate, ProcessoUpdate
│   ├── doem.py         # DOEMPublicacao, DOEMEdicao, DOEMConfig
│   └── newsletter.py   # NewsletterInscrito
├── routes/             # Routers da API ✅
│   ├── __init__.py     # Exporta todos os routers
│   ├── auth.py         # Autenticação (login, register, logout)
│   ├── users.py        # CRUD de usuários (admin)
│   ├── classificacao.py# Códigos de classificação orçamentária
│   ├── backup.py       # Backup e restauração
│   └── validacao.py    # Validação de documentos
├── services/           # Serviços compartilhados ✅
│   ├── email.py        # Envio de emails SMTP
│   └── pdf.py          # Geração de PDFs
├── utils/              # Utilitários ✅
│   ├── database.py     # Conexão MongoDB
│   └── auth.py         # JWT, hash passwords
└── README.md           # Documentação completa
```

### Status da Refatoração
- ✅ Modelos Pydantic extraídos e organizados em `/models/`
- ✅ Rotas de autenticação preparadas em `/routes/auth.py`
- ✅ Rotas de usuários em `/routes/users.py`
- ✅ Rotas de classificação orçamentária em `/routes/classificacao.py`
- ✅ Rotas de backup/restore em `/routes/backup.py`
- ✅ Rotas de validação de documentos em `/routes/validacao.py`
- ✅ Serviços de email e PDF em `/services/`
- ✅ Utilitários de database e auth em `/utils/`
- 🔄 Rotas ainda no `server.py` (funcional, migração gradual pendente)

---

## Status das Funcionalidades

### ✅ IMPLEMENTADO E FUNCIONANDO

#### Módulo 1: Geração de PDF Profissional
- Design profissional com cabeçalho institucional
- Tabela com cores alternadas (#FFFFFF / #D6EAF8)
- Selo de assinatura digital na lateral direita
- **Status**: COMPLETO E TESTADO

#### Módulo 2: Paginação
- **Backend**: `/api/processos/paginado`, `/api/pacs/paginado`, `/api/pacs-geral/paginado`
- **Frontend Editores**: 15, 30, 50, 100 itens por página
- **Portal Transparência**: 20, 40, 60, 80, 100 itens por página
- **Status**: COMPLETO E TESTADO

#### Módulo 3: DOEM Público
- Acesso sem login via `publicApi`
- Botões de navegação (Portal Principal, Acesso Admin)
- **Status**: COMPLETO E TESTADO (9/9 testes)

#### Módulo 4: Dashboard de Processos
- 4 KPIs em cards coloridos
- Gráficos de pizza e barras
- Toggle para mostrar/ocultar
- **Status**: COMPLETO E TESTADO

#### Módulo 5: Validação de Documentos
- URL: `https://pac.acaiaca.mg.gov.br/validar?code=...`
- Preenchimento automático do código via URL
- **Status**: COMPLETO E TESTADO

#### Módulo 6: Assinatura Digital
- Selo na lateral direita com QR Code
- Código de validação único
- **CPF e Cargo obrigatórios para assinatura** ✅ NOVO
- **Status**: COMPLETO E TESTADO (15/15 testes)

---

## Regras de Negócio

### Assinatura Digital (ATUALIZADO)
- **CPF é OBRIGATÓRIO** para assinar documentos
- **Cargo é OBRIGATÓRIO** para assinar documentos
- Usuários sem CPF/Cargo recebem erro 400 ao tentar exportar PDF assinado
- Mensagens de erro claras direcionam o usuário a atualizar seu perfil
- Validação aplicada em:
  - Exportação de PDF do PAC Individual
  - Exportação de PDF do PAC Geral
  - Exportação de PDF de Processos
  - Publicação de Edições do DOEM

---

## Endpoints de API

### Paginação
```
GET /api/processos/paginado?page=1&page_size=20
GET /api/pacs/paginado?page=1&page_size=20
GET /api/pacs-geral/paginado?page=1&page_size=20
```

### Públicos
```
GET /api/public/doem/anos
GET /api/public/doem/edicoes
GET /api/public/processos
GET /api/public/dashboard/stats
```

### Validação
```
POST /api/validar/verificar { validation_code: "DOC-XXX" }
```

---

## Próximos Passos (Backlog)

### P1 - Alta Prioridade (Refatoração)
1. ✅ Criar estrutura modular (models, routes, services, utils)
2. ✅ CPF e Cargo obrigatórios para assinatura
3. 🔄 Integrar routers modulares no `server.py` principal
4. 🔄 Migrar rotas gradualmente para arquivos separados (auth → pac → processos → doem)
5. 🔄 Reduzir server.py para < 1000 linhas

### P2 - Média Prioridade
- Nenhuma tarefa pendente

### P3 - Baixa Prioridade
- Versão cPanel (PHP/MySQL) - se solicitado pelo usuário

---

## Última Atualização
**Data**: 10/01/2026
**Versão**: 3.2.0

### Changelog desta sessão (10/01/2026):
- ✅ **CPF e Cargo obrigatórios para assinatura** - Implementado e testado
  - Backend: Validação em `add_signature_to_pdf` (linha ~4617)
  - Backend: Validação em `publicar_edicao` (linha ~5077)
  - Frontend: Campos CPF e Cargo marcados com asterisco vermelho
  - Frontend: Bordas destacadas em campos vazios (cor âmbar)
  - Frontend: Mensagens explicativas abaixo dos campos
- ✅ **Estrutura modular expandida**
  - Novos arquivos em `/routes/`: users.py, classificacao.py, backup.py, validacao.py
  - Modelos Pydantic completos em `/models/`: user.py, pac.py, processo.py
  - README.md atualizado com documentação completa
- ✅ **15 testes automatizados passando**
  - Login e autenticação
  - Validação de CPF/Cargo para exportação de PDF
  - Atualização de dados de assinatura
  - Endpoints públicos
  - Dashboard

### Testes Automatizados
- `/app/test_reports/iteration_12.json` - 15/15 testes passando
- `/app/tests/test_cpf_cargo_validation.py` - Testes de validação CPF/Cargo

---

## Credenciais de Teste
- **Admin**:
  - Email: `cristiano.abdo@acaiaca.mg.gov.br`
  - Senha: `Cris@820906`
  - CPF: `123.456.789-00`
  - Cargo: `Assessor de Planejamento`
