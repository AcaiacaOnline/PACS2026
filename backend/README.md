# Backend Modular - PAC Acaiaca 2026

## Estrutura de Diretórios

```
/app/backend/
├── server.py              # Aplicação principal FastAPI (~6000 linhas)
├── models/                # Modelos Pydantic
│   ├── __init__.py        # Exporta todos os modelos
│   ├── user.py            # User, UserCreate, UserUpdate, UserLogin, etc.
│   ├── pac.py             # PAC, PACItem, PACGeral, PACGeralItem
│   ├── processo.py        # Processo, ProcessoCreate, ProcessoUpdate
│   ├── doem.py            # DOEMPublicacao, DOEMEdicao, DOEMConfig
│   └── newsletter.py      # NewsletterInscrito
├── routes/                # Módulos de rotas (APIRouters)
│   ├── __init__.py        # Exporta todos os routers
│   ├── auth.py            # Autenticação (login, register, logout)
│   ├── users.py           # CRUD de usuários (admin)
│   ├── classificacao.py   # Códigos de classificação orçamentária
│   ├── backup.py          # Backup e restauração
│   └── validacao.py       # Validação de documentos
├── services/              # Serviços de negócio
│   ├── __init__.py
│   ├── email.py           # Envio de emails SMTP
│   └── pdf.py             # Geração de PDFs
└── utils/                 # Utilitários
    ├── __init__.py
    ├── auth.py            # JWT, hash de senhas
    └── database.py        # Conexão MongoDB
```

## Status da Refatoração

### ✅ Concluído
- Modelos Pydantic extraídos para `/models/`
- Rotas de autenticação preparadas em `/routes/auth.py`
- Rotas de usuários em `/routes/users.py`
- Classificação orçamentária em `/routes/classificacao.py`
- Backup/Restore em `/routes/backup.py`
- Validação de documentos em `/routes/validacao.py`
- Validação de CPF/Cargo obrigatórios para assinatura

### 🔄 Em Progresso
- Migração gradual das rotas do `server.py` para os módulos

### 📋 Pendente
- Integrar routers no `server.py` principal
- Extrair rotas do PAC para `/routes/pac.py`
- Extrair rotas do PAC Geral para `/routes/pac_geral.py`
- Extrair rotas de Processos para `/routes/processos.py`
- Extrair rotas do DOEM para `/routes/doem.py`
- Extrair rotas públicas para `/routes/public.py`
- Extrair rotas de newsletter para `/routes/newsletter.py`

## Regras de Negócio Importantes

### Assinatura Digital
- **CPF é obrigatório** para assinar documentos
- **Cargo é obrigatório** para assinar documentos
- Usuários sem CPF/Cargo preenchidos receberão erro 400 ao tentar gerar PDF assinado

### Classificação Orçamentária
- Códigos conforme Lei Federal nº 14.133/2021
- 339030: Material de Consumo
- 339036: Serviços de Terceiros (PF)
- 339039: Serviços de Terceiros (PJ)
- 449052: Material Permanente

## Como Executar

```bash
# O backend é gerenciado pelo Supervisor
sudo supervisorctl status backend
sudo supervisorctl restart backend

# Verificar logs
tail -f /var/log/supervisor/backend.out.log
tail -f /var/log/supervisor/backend.err.log
```

## Endpoints Principais

### Autenticação
- `POST /api/auth/login` - Login
- `POST /api/auth/register` - Cadastro
- `GET /api/auth/me` - Usuário atual
- `POST /api/auth/logout` - Logout

### PAC
- `GET /api/pacs` - Listar PACs
- `GET /api/pacs/paginado` - PACs com paginação
- `POST /api/pacs` - Criar PAC
- `GET /api/pacs/{id}` - Obter PAC
- `PUT /api/pacs/{id}` - Atualizar PAC
- `DELETE /api/pacs/{id}` - Excluir PAC
- `GET /api/pacs/{id}/export/pdf` - Exportar PDF

### Processos
- `GET /api/processos` - Listar processos
- `GET /api/processos/stats` - Estatísticas
- `POST /api/processos` - Criar processo

### DOEM
- `GET /api/doem/edicoes` - Listar edições
- `POST /api/doem/edicoes` - Criar edição
- `POST /api/doem/edicoes/{id}/assinar` - Assinar edição

### Portal Público
- `GET /api/public/pacs` - PACs públicos
- `GET /api/public/processos` - Processos públicos
- `GET /api/public/doem/edicoes` - Edições publicadas

### Validação
- `GET /api/validar/{code}` - Validar documento
- `POST /api/validar/verificar` - Validar via formulário

## Última Atualização
- **Data**: Janeiro 2026
- **Versão**: 3.2.0
- **Alterações**: 
  - CPF e Cargo agora são obrigatórios para assinatura
  - Estrutura modular preparada para migração gradual
