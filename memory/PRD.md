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

## Arquitetura Modular (REFATORADA)

### Estrutura de Diretórios
```
/app/backend/
├── server.py           # Arquivo principal (~6000 linhas)
├── models/             # Modelos Pydantic
│   ├── base.py         # User, PAC, Processo
│   ├── doem.py         # DOEM
│   └── newsletter.py   # Newsletter
├── routes/             # Routers da API
│   └── auth.py         # Autenticação
├── services/           # Serviços compartilhados
│   ├── email.py        # Envio de emails
│   └── pdf.py          # Geração de PDFs
├── utils/              # Utilitários
│   ├── database.py     # Conexão MongoDB
│   └── auth.py         # JWT, hash passwords
└── README.md           # Documentação
```

### Status da Refatoração
- ✅ Modelos extraídos para `/models/`
- ✅ Serviços de email e PDF para `/services/`
- ✅ Utilitários de database e auth para `/utils/`
- ✅ Estrutura de rotas preparada em `/routes/`
- 🔄 Rotas ainda no `server.py` (funcional, migração gradual)

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
- **Status**: COMPLETO E TESTADO

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
2. 🔄 Migrar rotas gradualmente para arquivos separados
3. 🔄 Reduzir server.py para < 1000 linhas

### P2 - Média Prioridade
- Tornar CPF e Cargo obrigatórios para assinatura

### P3 - Baixa Prioridade
- Versão cPanel (PHP/MySQL)

---

## Última Atualização
**Data**: 10/01/2026
**Versão**: 3.1.0

### Changelog desta sessão:
- Estrutura modular criada:
  - `/models/` - Modelos Pydantic
  - `/routes/` - Routers da API
  - `/services/` - Email, PDF
  - `/utils/` - Database, Auth
- README.md de documentação criado
- Todos os testes passando

### Testes Automatizados
- `/app/test_reports/iteration_11.json` - 9 testes passando
- Autenticação, PACs, Processos funcionando
