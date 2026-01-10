# Sistema PAC - Prefeitura Municipal de Acaiaca
## Plano Anual de Contratações e Gestão Municipal

### Visão Geral
Sistema completo de gestão municipal que inclui:
- **PAC (Plano Anual de Contratações)** - Gestão individual por secretaria
- **PAC Geral** - Visão consolidada de todas as secretarias
- **PAC Geral Obras e Serviços** - Módulo específico para obras e serviços de engenharia ✅ NOVO
- **Gestão Processual** - Controle de processos licitatórios com campos atualizados
- **DOEM (Diário Oficial Eletrônico Municipal)** - Publicações oficiais com assinatura digital
- **Portal de Transparência** - Acesso público às informações
- **Newsletter** - Sistema de notificações por email
- **Histórico de Assinaturas** - Visualização de documentos assinados

---

## Última Atualização: 10/01/2026

### Changelog desta Sessão

#### ✅ 1. Ajustes no Módulo de Processos (COMPLETO)
- **Campo "Status" renomeado para "Modalidade de Contratação"**
- **Campo "Situação" renomeado para "Status"**
- **Número do Processo agora é obrigatório** (*)
- Novas opções de modalidade: Pregão Eletrônico, Pregão Presencial, Concorrência, Tomada de Preços, Convite, Concurso, Leilão, Dispensa de Licitação, Dispensa por Limite, Dispensa por Justificativa, Inexigibilidade, Chamamento Público, Adesão a Ata de Registro de Preços, Contratação Direta
- Novos status: Em Elaboração, Aguardando Aprovação, Aprovado, Em Licitação, Homologado, Contratado, Em Execução, Concluído, Cancelado, Suspenso
- **73 processos migrados automaticamente** via endpoint `/api/processos/migrate-fields`

#### ✅ 2. Reorganização de Menus (COMPLETO)
- Menus agora organizados em dropdowns:
  - **PACs**: PAC Individual, PAC Geral, PAC Geral Obras
  - **Processos**: Gestão Processual, Dashboard
  - **DOEM**: Edições, Publicações

#### ✅ 3. Novo Módulo: PAC Geral Obras e Serviços (COMPLETO)
- Backend: Modelos `PACGeralObras`, `PACGeralObrasItem`
- Backend: Endpoints CRUD completos em `/api/pacs-geral-obras`
- Frontend: `PACGeralObrasList.jsx` - Lista de PACs de Obras
- Frontend: `PACGeralObrasEditor.jsx` - Editor de itens com classificação
- **Classificação Orçamentária conforme Lei 14.133/2021:**
  - 339040 - Serviços de TIC - PJ
  - 449051 - Obras e Instalações
  - 339039 - Serviços de Terceiros - PJ
- **Subitens conforme Portaria 448/ME**

#### ✅ 4. CPF e Cargo Obrigatórios para Assinatura (Sessão Anterior)
- Validação implementada em `add_signature_to_pdf`
- Frontend: Campos destacados com asterisco vermelho

---

## Arquitetura do Sistema

### Backend (FastAPI + MongoDB)
```
/app/backend/
├── server.py           # ~6500 linhas (ainda monolítico)
├── models/             # Modelos Pydantic
│   ├── user.py, pac.py, processo.py, doem.py, newsletter.py
├── routes/             # Routers preparados
│   ├── auth.py, users.py, classificacao.py, backup.py, validacao.py
├── services/           # Serviços
└── utils/              # Utilitários
```

### Frontend (React + TailwindCSS)
```
/app/frontend/src/
├── pages/
│   ├── PACGeralObrasList.jsx      # NOVO
│   ├── PACGeralObrasEditor.jsx    # NOVO
│   ├── GestaoProcessual.jsx       # ATUALIZADO (novos campos)
│   └── ...
├── components/
│   └── Layout.jsx                 # ATUALIZADO (menus dropdown)
└── App.js                         # ATUALIZADO (novas rotas)
```

---

## Endpoints de API

### PAC Geral Obras (NOVOS)
```
GET    /api/pacs-geral-obras              # Listar
POST   /api/pacs-geral-obras              # Criar
GET    /api/pacs-geral-obras/{id}         # Obter
PUT    /api/pacs-geral-obras/{id}         # Atualizar
DELETE /api/pacs-geral-obras/{id}         # Excluir
GET    /api/pacs-geral-obras/{id}/items   # Listar itens
POST   /api/pacs-geral-obras/{id}/items   # Criar item
PUT    /api/pacs-geral-obras/{id}/items/{item_id}
DELETE /api/pacs-geral-obras/{id}/items/{item_id}
GET    /api/classificacao/obras-servicos  # Códigos de classificação
```

### Processos (ATUALIZADOS)
```
POST   /api/processos/migrate-fields      # Migrar campos antigos
GET    /api/processos                     # Lista com novos campos
POST   /api/processos                     # Criar com modalidade_contratacao
```

---

## Próximos Passos (Backlog)

### 🔴 P1 - Alta Prioridade
- [ ] Sistema de Prestação de Contas (MROSC - Lei 13.019/2014)
  - Projetos de parceria com OSCs
  - Recursos Humanos com cálculos automáticos (CLT)
  - Despesas com 3 orçamentos
  - Upload de documentos PDF
  - Relatórios de prestação de contas

### 🟡 P2 - Média Prioridade
- [ ] Exportação PDF do PAC Geral Obras
- [ ] Integrar routers modulares no server.py
- [ ] Reduzir server.py para < 2000 linhas

### 🟢 P3 - Baixa Prioridade
- [ ] Versão cPanel (PHP/MySQL)

---

## Credenciais de Teste
- **Admin**:
  - Email: `cristiano.abdo@acaiaca.mg.gov.br`
  - Senha: `Cris@820906`
  - CPF: `123.456.789-00`
  - Cargo: `Assessor de Planejamento`

---

## Documentos Relacionados
- `/app/docs/ESPECIFICACAO_TECNICA_v1.md` - Especificação completa das novas funcionalidades
- `/app/test_reports/iteration_12.json` - Testes da sessão anterior
