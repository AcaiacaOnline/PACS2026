# PAC Acaiaca 2026 - Product Requirements Document (PRD)

## Visão Geral
Sistema completo de Plano Anual de Contratações (PAC) para a Prefeitura Municipal de Acaiaca - MG, desenvolvido em conformidade com a Lei Federal nº 14.133/2021.

## Stack Tecnológica
- **Frontend**: React + TailwindCSS + Shadcn/UI + Recharts
- **Backend**: FastAPI (Python) + MongoDB
- **Autenticação**: JWT + Google OAuth (via Emergent)
- **Relatórios**: ReportLab (PDF) + OpenPyXL (Excel)

## Credenciais de Teste
- **Admin**: cristiano.abdo@acaiaca.mg.gov.br / Cris@820906

---

## Módulos Implementados

### 1. Autenticação e Gestão de Usuários
- [x] Login com email/senha (JWT)
- [x] Login com Google OAuth
- [x] Gestão de usuários (admin only)
- [x] Permissões granulares por módulo

### 2. PAC Individual
- [x] CRUD completo de PACs
- [x] Itens do PAC com cálculos automáticos
- [x] **Filtro por ano** (2025, 2026, etc.)
- [x] Exportação PDF/XLSX com margens padronizadas

### 3. PAC Geral (Compartilhado)
- [x] CRUD completo
- [x] Itens compartilhados entre secretarias
- [x] **Filtro por ano**
- [x] Exportação PDF/XLSX

### 4. Gestão Processual
- [x] CRUD completo de processos
- [x] Status workflow (Iniciado → Publicado → Homologado → Concluído)
- [x] **Filtro por ano**
- [x] Dashboard analítico
- [x] Importação em massa (Excel)
- [x] Exportação PDF/XLSX

### 5. DOEM - Diário Oficial Eletrônico Municipal ✨ NOVO
- [x] **Página administrativa** (/doem)
  - Criar/editar edições
  - Adicionar publicações (decreto, portaria, lei, edital, etc.)
  - Importar arquivo RTF
  - Publicar edição com assinatura digital (SIMULADA)
  - Download PDF em formato de jornal oficial
- [x] **Portal público** (/doem-publico)
  - Visualização por ano (acordeão)
  - Busca de publicações
  - Download de PDFs
  - Interface inspirada no jornalminasgerais.mg.gov.br

### 6. Portal de Transparência
- [x] Acesso público sem login
- [x] Dashboard com estatísticas
- [x] Visualização de PACs e Processos
- [x] Exportação pública PDF/XLSX
- [x] Link para DOEM público

### 7. Backup e Restauração
- [x] Exportação completa de dados (JSON)
- [x] Importação/restauração de backup
- [x] Proteção contra perda de dados

### 8. Relatórios
- [x] PDF com margens padronizadas (5cm E/D, 3cm S/I)
- [x] Excel formatado
- [x] Quebra de linha automática

---

## Endpoints de API Principais

### Autenticação
- `POST /api/auth/login` - Login JWT
- `POST /api/auth/register` - Registro
- `GET /api/auth/me` - Usuário atual
- `GET /api/auth/google-login` - OAuth Google

### PAC Individual
- `GET /api/pacs/anos` - Anos disponíveis
- `GET /api/pacs?ano=2026` - Listar com filtro
- `POST /api/pacs` - Criar PAC
- `GET /api/pacs/{id}/export/pdf` - Exportar PDF

### PAC Geral
- `GET /api/pacs-geral/anos` - Anos disponíveis
- `GET /api/pacs-geral?ano=2026` - Listar com filtro

### Processos
- `GET /api/processos/anos` - Anos disponíveis
- `GET /api/processos?ano=2025` - Listar com filtro

### DOEM
- `GET /api/doem/config` - Configuração
- `GET /api/doem/edicoes` - Listar edições
- `POST /api/doem/edicoes` - Criar edição
- `POST /api/doem/import-rtf` - Importar RTF
- `POST /api/doem/edicoes/{id}/publicar` - Publicar
- `GET /api/doem/edicoes/{id}/pdf` - Download PDF

### Públicos
- `GET /api/public/doem/edicoes` - Edições publicadas
- `GET /api/public/doem/busca?q=termo` - Buscar
- `GET /api/public/doem/edicoes/{id}/pdf` - Download

---

## Notas Técnicas

### Assinatura Digital
A assinatura digital do DOEM está **SIMULADA**:
- Gera hash SHA-256 do documento
- Não usa certificado ICP-Brasil real
- O certificado .pfx do usuário foi anexado mas não integrado
- Para produção: integrar com biblioteca `endesive` ou similar

### Margens de Relatórios
Todas as exportações PDF usam margens padronizadas:
- Esquerda/Direita: 5cm (50mm)
- Superior/Inferior: 3cm (30mm)

### Débito Técnico
- O arquivo `server.py` possui +4000 linhas e precisa de refatoração
- Recomendado: dividir em routers por módulo (pacs, processos, doem, etc.)

---

## Próximas Tarefas (Backlog)

### P0 - Alta Prioridade
- [ ] Integrar assinatura digital real com certificado ICP-Brasil

### P1 - Média Prioridade
- [ ] Refatorar backend em módulos separados
- [ ] Melhorar layout do PDF do DOEM

### P2 - Baixa Prioridade
- [ ] Finalizar versão cPanel (PHP/MySQL)
- [ ] Notificações por email
- [ ] Histórico de alterações

---

## Histórico de Versões

### v1.3.0 - 02/01/2026
- ✅ Implementado filtro de ano para PAC, PAC Geral e Processos
- ✅ Criado módulo DOEM completo (admin + público)
- ✅ Importação de RTF para publicações
- ✅ Geração de PDF em formato jornal oficial
- ✅ Assinatura digital simulada
- ✅ Link DOEM no Portal de Transparência

### v1.2.0 - 01/01/2026
- Sistema de Backup e Restauração
- Portal Público de Transparência
- Correção Google OAuth
- Melhorias nas margens dos PDFs

### v1.1.0
- Gestão Processual com Dashboard
- Importação de processos em massa
- Permissões granulares

### v1.0.0
- MVP inicial com PAC Individual e PAC Geral
- Autenticação JWT e Google OAuth
- Relatórios PDF/XLSX
