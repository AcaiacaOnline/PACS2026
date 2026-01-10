# Backend - Estrutura Modular

## Estrutura de Diretórios

```
/app/backend/
├── server.py           # Arquivo principal (ponto de entrada)
├── models/             # Modelos Pydantic
│   ├── __init__.py     # Exportações centralizadas
│   ├── base.py         # Modelos de User, PAC, Processo
│   ├── doem.py         # Modelos do DOEM
│   └── newsletter.py   # Modelos de Newsletter
├── routes/             # Routers da API
│   ├── __init__.py     # Exportações centralizadas
│   └── auth.py         # Rotas de autenticação (exemplo)
├── services/           # Serviços compartilhados
│   ├── __init__.py     # Exportações centralizadas
│   ├── email.py        # Serviço de email
│   └── pdf.py          # Serviço de geração de PDF
├── utils/              # Utilitários
│   ├── __init__.py     # Exportações centralizadas
│   ├── database.py     # Conexão com MongoDB
│   └── auth.py         # Funções de autenticação
└── tests/              # Testes automatizados
```

## Módulos

### models/
Contém os modelos Pydantic para validação de dados:
- `base.py`: User, PAC, PACItem, PACGeral, PACGeralItem, Processo
- `doem.py`: DOEMEdicao, DOEMPublicacao, DOEMConfig
- `newsletter.py`: NewsletterInscrito

### routes/
Contém os routers da API (APIRouter):
- `auth.py`: Login, registro, logout, perfil do usuário

### services/
Contém lógica de negócio reutilizável:
- `email.py`: Envio de emails via SMTP
- `pdf.py`: Geração de PDFs com ReportLab

### utils/
Contém funções utilitárias:
- `database.py`: Conexão com MongoDB
- `auth.py`: Hash de senhas, JWT, middleware de autenticação

## Migração Gradual

O arquivo `server.py` ainda contém todas as rotas para manter compatibilidade.
A migração para módulos separados está em andamento:

1. ✅ Modelos extraídos para `/models/`
2. ✅ Serviços de email e PDF extraídos para `/services/`
3. ✅ Utilitários de database e auth extraídos para `/utils/`
4. 🔄 Rotas ainda no `server.py` (migração gradual)

## Como Usar

### Importar Modelos
```python
from models import User, PAC, Processo
```

### Importar Serviços
```python
from services import send_email, get_professional_styles
```

### Importar Utilitários
```python
from utils import db, get_current_user
```

## Próximos Passos

1. Migrar rotas de autenticação para `routes/auth.py`
2. Migrar rotas de PAC para `routes/pac.py`
3. Migrar rotas de Processos para `routes/processos.py`
4. Migrar rotas de DOEM para `routes/doem.py`
5. Migrar rotas públicas para `routes/public.py`
6. Remover código duplicado do `server.py`

## Versão
- Data: 2026-01-10
- Linhas no server.py: ~6000 (em processo de modularização)
