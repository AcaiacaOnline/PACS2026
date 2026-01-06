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

#### Módulo 1: Paginação Configurável
- Componente `Pagination.jsx` reutilizável
- Hook `usePagination()` com persistência em localStorage
- Opções: 20, 30, 50 ou 100 itens por página
- Implementado em: Gestão Processual
- **Status**: COMPLETO E TESTADO

#### Módulo 2: Campos de Assinatura Digital do Usuário
- Novos campos no cadastro de usuário:
  - CPF (com máscara XXX.XXX.XXX-XX)
  - Cargo Ocupado
  - Telefone (com máscara (XX) XXXXX-XXXX)
  - CEP (com máscara XXXXX-XXX)
  - Endereço Completo
- Seção "Dados para Assinatura Digital" no formulário
- **Status**: COMPLETO E TESTADO

#### Módulo 3: Assinatura Digital Visual em PDFs
- Selo de assinatura na lateral direita de todas as páginas
- Informações exibidas:
  - Nome do assinante
  - Cargo
  - CPF mascarado (conformidade LGPD)
  - Data e hora da assinatura
  - Código de validação
  - QR Code para validação rápida
- **Status**: COMPLETO E TESTADO

#### Módulo 4: Painel de Validação de Documentos
- URL pública: `/validar`
- API: `POST /api/validar/verificar`
- Funcionalidades:
  - Inserção de código de validação
  - Verificação de autenticidade
  - Exibição de dados do documento
  - Dados dos assinantes com CPF mascarado
- **Status**: COMPLETO E TESTADO

#### Módulo DOEM (Anterior)
- Gestão de edições do Diário Oficial
- Importação de RTF
- Publicação com assinatura digital
- Portal público de consulta
- Sistema de Newsletter com 9 segmentos
- Notificações por email via SMTP
- **Status**: COMPLETO

#### Máscaras de Input (Anterior)
- TelefoneInput, CPFInput, CNPJInput
- CEPInput, CurrencyInput, EmailInput
- Aplicadas em: PACEditor, PACGeralEditor, GestaoProcessual, Users
- **Status**: COMPLETO

---

## Arquitetura Técnica

### Frontend (React)
```
/app/frontend/src/
├── components/
│   ├── Layout.jsx
│   ├── Pagination.jsx          # NOVO
│   └── ui/                     # Shadcn components
├── pages/
│   ├── ValidarDocumento.jsx    # NOVO
│   ├── DOEM.jsx
│   ├── DOEMPublico.jsx
│   ├── Users.jsx               # ATUALIZADO
│   ├── GestaoProcessual.jsx    # ATUALIZADO
│   └── ...
└── utils/
    ├── api.js
    └── masks.jsx
```

### Backend (FastAPI)
```
/app/backend/
├── server.py                   # ~5300+ linhas (PRECISA REFATORAÇÃO)
├── brasao_doem_small.png
├── rodape_doem_small.jpg
└── requirements.txt
```

### Banco de Dados (MongoDB)
Collections principais:
- `users` - Usuários com signature_data
- `pacs` - PACs individuais
- `pacs_geral` - PACs consolidados
- `processos` - Processos licitatórios
- `doem_edicoes` - Edições do DOEM
- `document_signatures` - Assinaturas para validação
- `newsletter_subscribers` - Assinantes da newsletter

---

## Próximos Passos (Backlog)

### P1 - Alta Prioridade
1. **Refatoração do server.py**
   - Dividir em múltiplos APIRouters
   - Arquitetura sugerida:
     ```
     /app/backend/
     ├── routes/
     │   ├── auth.py
     │   ├── pacs.py
     │   ├── processos.py
     │   ├── doem.py
     │   └── validation.py
     ├── models/
     ├── services/
     └── server.py (apenas bootstrap)
     ```

### P2 - Média Prioridade
2. **Aplicar assinatura digital em todos os relatórios**
   - PDFs de PAC
   - PDFs de PAC Geral
   - Relatórios de Processos

3. **Paginação em outras listagens**
   - PACList
   - PACGeralList

### P3 - Baixa Prioridade
4. **Versão cPanel (PHP/MySQL)**
   - Pasta: `/app/cpanel-version`
   - Status: Em espera

---

## Credenciais de Teste

| Tipo | Email | Senha |
|------|-------|-------|
| Admin | cristiano.abdo@acaiaca.mg.gov.br | Cris@820906 |

---

## URLs Importantes

| Recurso | URL |
|---------|-----|
| Portal Público | `/` |
| DOEM Público | `/doem-publico` |
| Validar Documento | `/validar` |
| Dashboard Admin | `/dashboard` |
| Gestão Processual | `/gestao-processual` |
| DOEM Admin | `/doem` |

---

## Última Atualização
**Data**: 06/01/2026
**Versão**: 2.4.0

### Changelog desta sessão:
- Implementada paginação configurável (Módulo 1)
- Adicionados campos de assinatura no cadastro de usuário (Módulo 4)
- Implementado sistema de assinatura digital visual em PDFs (Módulo 2)
- Criado painel público de validação de documentos (Módulo 3)
- Corrigido bug crítico: validation codes não eram salvos no banco
- Todos os módulos testados e funcionando
