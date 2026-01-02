# PAC Acaiaca 2026 - Product Requirements Document (PRD)

## Visão Geral
Sistema completo de Plano Anual de Contratações (PAC) para a Prefeitura Municipal de Acaiaca - MG, desenvolvido em conformidade com a Lei Federal nº 14.133/2021.

## Stack Tecnológica
- **Frontend**: React + TailwindCSS + Shadcn/UI + Recharts
- **Backend**: FastAPI (Python) + MongoDB
- **Autenticação**: JWT + Google OAuth (via Emergent)
- **Relatórios**: ReportLab (PDF) + OpenPyXL (Excel)
- **Email**: SMTP SSL (mail.acaiaca.mg.gov.br:465)

## Credenciais de Teste
- **Admin**: cristiano.abdo@acaiaca.mg.gov.br / Cris@820906
- **SMTP**: naoresponda@acaiaca.mg.gov.br / Pma@3120

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

### 5. DOEM - Diário Oficial Eletrônico Municipal ✨
- [x] **9 Segmentos de Publicação**:
  - Portarias
  - Leis
  - Decretos
  - Resoluções
  - Editais
  - Prestações de Contas
  - Processos Administrativos
  - Publicações do Legislativo
  - Publicações do Terceiro Setor
- [x] **Tipos dinâmicos por segmento** (ex: Decreto → "Decreto", "Decreto Regulamentar")
- [x] **Página Administrativa** (`/doem`)
  - Criar/editar edições
  - Importar arquivo RTF
  - Publicar com assinatura digital (SIMULADA)
  - Download PDF em formato de jornal oficial
- [x] **Portal Público** (`/doem-publico`)
  - Interface inspirada no jornalminasgerais.mg.gov.br
  - Busca de publicações
  - Download de PDFs

### 6. Sistema de Newsletter ✨ NOVO
- [x] **Gestão de Inscritos** (admin)
  - Adicionar manualmente
  - Ativar/desativar
  - Excluir
  - Estatísticas (total, ativos, pendentes, por tipo)
- [x] **Inscrição Pública**
  - Formulário público com confirmação por email
  - Seleção de segmentos de interesse
- [x] **Notificações Automáticas**
  - Envio via SMTP próprio ao publicar edição
  - Email HTML com lista de publicações
  - PDF anexo da edição

### 7. Portal de Transparência
- [x] Acesso público sem login
- [x] Dashboard com estatísticas
- [x] Visualização de PACs e Processos
- [x] Exportação pública PDF/XLSX
- [x] Link para DOEM público

### 8. Backup e Restauração
- [x] Exportação completa de dados (JSON)
- [x] Importação/restauração de backup
- [x] Proteção contra perda de dados

---

## Endpoints de API Principais

### DOEM
- `GET /api/doem/segmentos` - Lista 9 segmentos e tipos
- `GET /api/doem/edicoes` - Listar edições
- `POST /api/doem/edicoes` - Criar edição
- `POST /api/doem/edicoes/{id}/publicar` - Publicar (envia notificações)

### Newsletter
- `GET /api/newsletter/inscritos` - Listar inscritos (admin)
- `POST /api/newsletter/inscritos` - Adicionar inscrito (admin)
- `PUT /api/newsletter/inscritos/{id}/toggle` - Ativar/desativar
- `DELETE /api/newsletter/inscritos/{id}` - Remover
- `GET /api/newsletter/estatisticas` - Estatísticas
- `POST /api/public/newsletter/inscrever` - Inscrição pública

---

## Configuração SMTP

As credenciais estão em `/app/backend/.env`:
```
SMTP_SERVER=mail.acaiaca.mg.gov.br
SMTP_PORT=465
SMTP_EMAIL=naoresponda@acaiaca.mg.gov.br
SMTP_PASSWORD=Pma@3120
SMTP_USE_SSL=true
```

---

## Notas Técnicas

### Assinatura Digital
A assinatura digital do DOEM está **SIMULADA**:
- Gera hash SHA-256 do documento
- Não usa certificado ICP-Brasil real

### Margens de Relatórios
- Esquerda/Direita: 5cm (50mm)
- Superior/Inferior: 3cm (30mm)

### Débito Técnico
- O arquivo `server.py` possui +4500 linhas e precisa de refatoração

---

## Próximas Tarefas (Backlog)

### P0 - Alta Prioridade
- [ ] Integrar assinatura digital real com certificado ICP-Brasil

### P1 - Média Prioridade
- [ ] Refatorar backend em módulos separados
- [ ] Melhorar layout do PDF do DOEM

### P2 - Baixa Prioridade
- [ ] Finalizar versão cPanel (PHP/MySQL)
- [ ] Histórico de alterações

---

## Histórico de Versões

### v1.4.0 - 02/01/2026
- ✅ Expandido DOEM com 9 segmentos de publicação
- ✅ Tipos de publicação dinâmicos por segmento
- ✅ Sistema completo de Newsletter
- ✅ Gestão de inscritos (admin)
- ✅ Inscrição pública com confirmação por email
- ✅ Notificações automáticas via SMTP próprio

### v1.3.0 - 02/01/2026
- ✅ Filtro de ano para PAC, PAC Geral e Processos
- ✅ Módulo DOEM básico

### v1.2.0 - 01/01/2026
- Sistema de Backup e Restauração
- Portal Público de Transparência

### v1.1.0
- Gestão Processual com Dashboard

### v1.0.0
- MVP inicial com PAC Individual e PAC Geral
