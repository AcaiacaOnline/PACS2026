# Planejamento Acaiaca - Sistema de Gestão Municipal
## Prefeitura Municipal de Acaiaca - CNPJ: 18.295.287/0001-90

### Visão Geral
Sistema completo de gestão municipal que inclui:
- **PAC (Plano Anual de Contratações)** - Gestão individual por secretaria
- **PAC Geral** - Visão consolidada de todas as secretarias
- **PAC Geral Obras e Serviços** - Módulo específico para obras e serviços de engenharia ✅
- **Gestão Processual** - Controle de processos licitatórios com campos atualizados ✅
- **DOEM (Diário Oficial Eletrônico Municipal)** - Publicações oficiais com assinatura digital
- **Portal de Transparência** - Acesso público às informações
- **Prestação de Contas MROSC** - Sistema conforme Lei 13.019/2014 ✅ NOVO
- **Newsletter** - Sistema de notificações por email
- **Histórico de Assinaturas** - Visualização de documentos assinados

---

## Última Atualização: 10/01/2026

### Changelog desta Sessão

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

### 🟢 Concluído
- [x] Ajustes em Processos
- [x] Reorganização de Menus
- [x] PAC Geral Obras e Serviços
- [x] Sistema Prestação de Contas MROSC
- [x] Upload de documentos PDF no MROSC ✅ (10/01/2026)

### 🟡 P2 - Média Prioridade
- [ ] Exportação PDF do PAC Geral Obras
- [ ] Relatórios de Prestação de Contas em PDF

### 🟢 P3 - Baixa Prioridade
- [ ] Refatoração do backend (modularização do server.py)
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
