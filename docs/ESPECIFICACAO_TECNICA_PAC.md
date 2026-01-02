# ESPECIFICAÇÃO TÉCNICA - SISTEMA PAC ACAIACA 2026

## Documento de Requisitos e Especificações para Relatórios e Portal Público

**Versão:** 1.0  
**Data:** 29 de Dezembro de 2025  
**Autor:** Sistema PAC Acaiaca 2026  
**Revisão:** Especialista em Programação e Formatação de Documentos para Licitações

---

# PARTE I - DIRETRIZES DE FORMATAÇÃO E CONTEÚDO DOS RELATÓRIOS

## 1. Especificações de Página e Margens

### 1.1 Formato de Página
- **Tamanho:** A4 (210mm x 297mm)
- **Orientação Padrão:** Paisagem (297mm x 210mm) - maximiza área útil
- **Orientação Alternativa:** Retrato - disponível para impressão convencional

### 1.2 Sistema de Margens

| Margem | Paisagem | Retrato | Justificativa |
|--------|----------|---------|---------------|
| Esquerda | 8mm | 10mm | Maximizar área de conteúdo |
| Direita | 25mm | 30mm | **RESERVADA PARA ASSINATURA DIGITAL** |
| Superior | 8mm | 10mm | Cabeçalho compacto |
| Inferior | 8mm | 10mm | Rodapé com informações |

### 1.3 Área Útil Calculada
- **Paisagem:** 264mm x 194mm (área efetiva para conteúdo)
- **Retrato:** 170mm x 277mm (área efetiva para conteúdo)

---

## 2. Campos Obrigatórios nos Relatórios de Itens

### 2.1 Estrutura de Colunas - SEM ABREVIAÇÕES

| # | Campo | Descrição | Largura Mínima |
|---|-------|-----------|----------------|
| 1 | **Código CATMAT/CATSER** | Código completo do item | 15mm |
| 2 | **Unidade** | Unidade de medida (UN, CX, KG, etc.) | 12mm |
| 3 | **Descrição do Objeto** | Descrição completa sem truncamento | 60mm |
| 4 | **Quantidade Total** | Soma de todas as secretarias | 15mm |
| 5 | **Valor Unitário (R$)** | Valor formatado com 2 decimais | 22mm |
| 6 | **Valor Total (R$)** | Qtd × Valor Unit. | 25mm |
| 7 | **Prioridade** | Alta/Média/Baixa - completo | 12mm |
| 8 | **Justificativa da Contratação** | Texto integral sem cortes | 50mm |
| 9 | **Código de Classificação Orçamentária** | Ex: 339030 | 15mm |
| 10 | **Subitem da Classificação** | Descrição completa do subitem | 45mm |

### 2.2 Regras de Exibição de Conteúdo

1. **PROIBIDO:** Truncar textos com "..." ou cortar descrições
2. **PROIBIDO:** Usar abreviações não padronizadas
3. **OBRIGATÓRIO:** Quebra de linha automática em células grandes
4. **OBRIGATÓRIO:** Fonte mínima de 7pt para legibilidade
5. **PERMITIDO:** Redução proporcional de fonte até 6pt se necessário

### 2.3 Abreviações Padronizadas Permitidas

| Termo | Abreviação | Uso |
|-------|------------|-----|
| Unidade | UN | Apenas na coluna Unidade |
| Caixa | CX | Apenas na coluna Unidade |
| Quilograma | KG | Apenas na coluna Unidade |
| Metro | M | Apenas na coluna Unidade |
| Litro | L | Apenas na coluna Unidade |
| Pacote | PCT | Apenas na coluna Unidade |

---

## 3. Cabeçalhos Específicos por Tipo de Relatório

### 3.1 PAC Individual
```
PREFEITURA MUNICIPAL DE ACAIACA - MG
PAC ACAIACA 2026 - PLANO ANUAL DE CONTRATAÇÕES
Lei Federal nº 14.133/2021

Secretaria: [Nome Completo]
Secretário(a): [Nome Completo]
Fiscal do Contrato: [Nome Completo]
Telefone: [Completo] | E-mail: [Completo]
Endereço: [Completo]
```

### 3.2 PAC Geral (Consolidado)
```
PREFEITURA MUNICIPAL DE ACAIACA - MG
PAC ACAIACA 2026 - PLANO ANUAL DE CONTRATAÇÕES COMPARTILHADO
Lei Federal nº 14.133/2021

Secretaria Responsável: [Nome]
Secretário(a): [Nome]
Fiscal do Contrato: [Nome]
Secretarias Participantes: [Lista completa separada por vírgulas]
```

### 3.3 Gestão Processual
```
PREFEITURA MUNICIPAL DE ACAIACA - MG
GESTÃO PROCESSUAL - RELATÓRIO DE PROCESSOS
Lei Federal nº 14.133/2021

Data de Geração: [DD/MM/YYYY às HH:MM]
Total de Processos: [N]
```

---

## 4. Seção de Assinaturas

### 4.1 Layout de Assinaturas
```
________________________________________    ________________________________________
[Nome do Secretário]                        [Nome do Fiscal do Contrato]
Secretário(a) Responsável                   Fiscal do Contrato


________________________________________    ________________________________________
[Nome do Prefeito se aplicável]             [Carimbo/Data]
Prefeito Municipal                          Data: ___/___/______
```

### 4.2 Espaço Reservado para Assinatura Digital
- **Margem direita ampliada:** 25-30mm
- **Área de assinatura:** 40mm × 20mm por assinatura
- **Posicionamento:** Alinhado à margem direita

---

## 5. Dashboard - Identificação por Subitem

### 5.1 Exibição Proeminente
O Dashboard deve exibir o **Subitem da Classificação** como identificador principal do PAC a ser licitado:

```
╔════════════════════════════════════════════════════════════════╗
║  MATERIAL DE EXPEDIENTE                                        ║
║  Código: 339030 - Material de Consumo                          ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║  Total de Itens: 45  |  Valor Total: R$ 125.430,00             ║
║  Secretarias: ADM, SAU, EDU, OBR                               ║
╚════════════════════════════════════════════════════════════════╝
```

### 5.2 Hierarquia Visual
1. **Nível 1 (Destaque):** Subitem da Classificação
2. **Nível 2:** Código de Classificação Orçamentária
3. **Nível 3:** Valores e Quantidades
4. **Nível 4:** Secretarias envolvidas

---

# PARTE II - ESPECIFICAÇÃO DO PORTAL PÚBLICO EXTERNO

## 1. Visão Geral do Sistema

### 1.1 Objetivo
Criar um portal web público que permita a qualquer cidadão consultar, visualizar e exportar informações dos Planos Anuais de Contratação (PAC) e processos licitatórios da Prefeitura Municipal de Acaiaca - MG, garantindo transparência e conformidade com a Lei de Acesso à Informação.

### 1.2 Público-Alvo
- Cidadãos em geral
- Fornecedores e licitantes
- Órgãos de controle
- Imprensa
- Pesquisadores

### 1.3 URL Sugerida
```
https://pac.acaiaca.mg.gov.br
```

---

## 2. Arquitetura Técnica

### 2.1 Stack Tecnológico Recomendado

| Camada | Tecnologia | Justificativa |
|--------|------------|---------------|
| **Frontend** | Next.js 14+ | SSR para SEO, performance |
| **Estilização** | TailwindCSS | Responsividade, manutenibilidade |
| **Backend** | FastAPI (Python) | Reutilização do código existente |
| **Banco de Dados** | MongoDB (leitura) | Consistência com sistema interno |
| **Cache** | Redis | Performance em consultas públicas |
| **CDN** | Cloudflare | Distribuição global, DDoS protection |
| **Hospedagem** | Vercel / AWS | Escalabilidade automática |

### 2.2 Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTERNET                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CLOUDFLARE CDN                                │
│              (Cache, DDoS Protection, SSL)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│   FRONTEND (Next.js)    │     │   API PÚBLICA (FastAPI) │
│   - SSR/SSG Pages       │     │   - Endpoints Read-Only │
│   - Exportações         │     │   - Rate Limiting       │
│   - PWA Support         │     │   - Validação           │
└─────────────────────────┘     └─────────────────────────┘
              │                               │
              └───────────────┬───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        REDIS CACHE                               │
│              (Consultas frequentes, 5min TTL)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   MONGODB (Read Replica)                         │
│              (Dados sincronizados do sistema interno)            │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Sincronização de Dados

```python
# Estratégia de Sincronização
SYNC_CONFIG = {
    "frequency": "every 5 minutes",
    "method": "incremental",
    "collections": [
        "pacs",
        "pac_items",
        "pacs_geral",
        "pac_geral_items",
        "processos"
    ],
    "exclude_fields": [
        "user_id",
        "password_hash",
        "internal_notes"
    ]
}
```

---

## 3. Endpoints da API Pública

### 3.1 Estrutura Base
```
BASE_URL: https://api.pac.acaiaca.mg.gov.br/v1
```

### 3.2 Endpoints Disponíveis

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/pacs` | Lista todos os PACs Individuais |
| GET | `/pacs/{id}` | Detalhes de um PAC específico |
| GET | `/pacs/{id}/items` | Itens de um PAC |
| GET | `/pacs/{id}/export/pdf` | Exporta PAC em PDF |
| GET | `/pacs/{id}/export/xlsx` | Exporta PAC em Excel |
| GET | `/pacs-geral` | Lista PACs Gerais |
| GET | `/pacs-geral/{id}` | Detalhes do PAC Geral |
| GET | `/pacs-geral/{id}/items` | Itens do PAC Geral |
| GET | `/pacs-geral/{id}/export/pdf` | Exporta PAC Geral em PDF |
| GET | `/pacs-geral/{id}/export/xlsx` | Exporta PAC Geral em Excel |
| GET | `/processos` | Lista processos licitatórios |
| GET | `/processos/{id}` | Detalhes de um processo |
| GET | `/processos/export/pdf` | Exporta processos em PDF |
| GET | `/processos/export/xlsx` | Exporta processos em Excel |
| GET | `/dashboard/stats` | Estatísticas consolidadas |
| GET | `/classificacoes` | Códigos de classificação orçamentária |

### 3.3 Parâmetros de Consulta

```
# Paginação
?page=1&limit=50

# Filtros
?secretaria=Administração
?ano=2026
?classificacao=339030
?prioridade=Alta

# Ordenação
?sort=valor_total&order=desc

# Busca
?search=material de expediente
```

### 3.4 Exemplo de Resposta

```json
{
  "success": true,
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 245,
      "pages": 5
    }
  },
  "meta": {
    "generated_at": "2026-01-15T10:30:00Z",
    "cache_ttl": 300
  }
}
```

---

## 4. Interface do Usuário (UI/UX)

### 4.1 Estrutura de Navegação

```
┌─────────────────────────────────────────────────────────────────┐
│  🏛️ PAC Acaiaca 2026 - Portal da Transparência                  │
├─────────────────────────────────────────────────────────────────┤
│  [Início] [PAC Individual] [PAC Geral] [Processos] [Dashboard]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🔍 Buscar: [________________________] [Pesquisar]              │
│                                                                  │
│  Filtros: [Secretaria ▼] [Ano ▼] [Classificação ▼] [Limpar]    │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  CONTEÚDO PRINCIPAL                                      │   │
│  │  - Tabelas de dados                                      │   │
│  │  - Cards informativos                                    │   │
│  │  - Gráficos (Dashboard)                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  [📄 Exportar PDF] [📊 Exportar Excel] [🖨️ Imprimir]           │
├─────────────────────────────────────────────────────────────────┤
│  Prefeitura Municipal de Acaiaca - MG | Lei 14.133/2021         │
│  Desenvolvido por Cristiano Abdo de Souza                       │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Páginas do Portal

#### 4.2.1 Página Inicial (Home)
- Resumo estatístico do PAC 2026
- Últimos PACs publicados
- Processos em andamento
- Acesso rápido às seções principais
- Notícias e avisos

#### 4.2.2 PAC Individual
- Lista de PACs por secretaria
- Filtros por secretaria, ano, valor
- Visualização detalhada de itens
- Exportação individual ou em lote

#### 4.2.3 PAC Geral (Consolidado)
- Visão consolidada por classificação orçamentária
- **Destaque para Subitem da Classificação**
- Distribuição por secretarias participantes
- Gráficos de composição

#### 4.2.4 Gestão Processual
- Lista de processos licitatórios
- Status visual (cores por situação)
- Timeline de processos
- Documentos anexos (se aplicável)

#### 4.2.5 Dashboard Público
- Gráficos interativos (Recharts)
- Indicadores de desempenho
- Comparativos anuais
- Ranking de secretarias

### 4.3 Design Responsivo

```css
/* Breakpoints */
mobile: 320px - 767px
tablet: 768px - 1023px
desktop: 1024px - 1439px
large: 1440px+

/* Adaptações */
- Tabelas: scroll horizontal em mobile
- Cards: empilhamento vertical em mobile
- Gráficos: simplificados em mobile
- Menu: hambúrguer em mobile/tablet
```

### 4.4 Acessibilidade (WCAG 2.1 AA)

- [x] Contraste mínimo 4.5:1
- [x] Textos redimensionáveis até 200%
- [x] Navegação por teclado
- [x] Leitores de tela compatíveis
- [x] Textos alternativos em imagens
- [x] Formulários com labels
- [x] Skip links para navegação
- [x] Modo alto contraste

---

## 5. Funcionalidades de Exportação

### 5.1 Exportação PDF

```python
# Configurações de PDF para Portal Público
PDF_CONFIG = {
    "page_size": "A4",
    "orientation": "landscape",  # Padrão
    "margins": {
        "left": 8,    # mm
        "right": 25,  # mm - ASSINATURA DIGITAL
        "top": 8,     # mm
        "bottom": 8   # mm
    },
    "font_size": {
        "title": 14,
        "subtitle": 11,
        "body": 8,
        "table": 7,
        "footer": 6
    },
    "watermark": "DOCUMENTO PÚBLICO - PAC ACAIACA 2026",
    "include_qrcode": True,  # Link para verificação
    "signature_area": {
        "width": 40,   # mm
        "height": 20,  # mm
        "position": "right"
    }
}
```

### 5.2 Exportação Excel

```python
EXCEL_CONFIG = {
    "sheets": [
        {
            "name": "Resumo",
            "content": "Cabeçalho e totais"
        },
        {
            "name": "Itens Detalhados",
            "content": "Tabela completa de itens"
        },
        {
            "name": "Por Classificação",
            "content": "Agrupado por código orçamentário"
        }
    ],
    "formatting": {
        "header_color": "#1F4788",
        "alternating_rows": True,
        "freeze_panes": "A2",
        "auto_filter": True,
        "column_width": "auto"
    }
}
```

### 5.3 Impressão Direta

```javascript
// Função de Impressão Otimizada
const printDocument = () => {
  const printStyles = `
    @media print {
      @page {
        size: A4 landscape;
        margin: 8mm 25mm 8mm 8mm;
      }
      .no-print { display: none; }
      table { page-break-inside: avoid; }
      .signature-area { 
        position: fixed;
        right: 0;
        width: 25mm;
      }
    }
  `;
  
  // Aplicar estilos e imprimir
  window.print();
};
```

---

## 6. Segurança

### 6.1 Medidas de Proteção

| Medida | Implementação |
|--------|---------------|
| **Rate Limiting** | 100 req/min por IP |
| **DDoS Protection** | Cloudflare Enterprise |
| **SSL/TLS** | Certificado EV |
| **CORS** | Apenas origens permitidas |
| **Input Validation** | Sanitização de parâmetros |
| **SQL Injection** | Consultas parametrizadas |
| **XSS** | CSP Headers |

### 6.2 Headers de Segurança

```nginx
# Nginx Configuration
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self';" always;
add_header Strict-Transport-Security "max-age=31536000" always;
```

### 6.3 Dados Sensíveis

**NUNCA expor no portal público:**
- user_id (identificação interna)
- password_hash
- Notas internas
- Logs de auditoria
- Informações de sessão

---

## 7. Performance e Escalabilidade

### 7.1 Métricas Alvo

| Métrica | Alvo | Crítico |
|---------|------|---------|
| **TTFB** | < 200ms | < 500ms |
| **FCP** | < 1.5s | < 3s |
| **LCP** | < 2.5s | < 4s |
| **CLS** | < 0.1 | < 0.25 |
| **Uptime** | 99.9% | 99.5% |

### 7.2 Estratégias de Cache

```python
CACHE_STRATEGY = {
    "static_assets": "1 year",
    "api_responses": "5 minutes",
    "pdf_exports": "1 hour",
    "dashboard_stats": "10 minutes",
    "search_results": "2 minutes"
}
```

### 7.3 Escalabilidade

```yaml
# Kubernetes Deployment
apiVersion: apps/v1
kind: Deployment
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
  template:
    spec:
      containers:
      - name: pac-portal
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
```

---

## 8. Monitoramento e Logs

### 8.1 Métricas Coletadas

- Requisições por endpoint
- Tempo de resposta
- Taxa de erros
- Downloads de exportação
- Acessos por região
- Dispositivos utilizados

### 8.2 Alertas

```yaml
alerts:
  - name: HighErrorRate
    condition: error_rate > 5%
    duration: 5m
    severity: critical
    
  - name: SlowResponse
    condition: p95_latency > 2s
    duration: 10m
    severity: warning
    
  - name: HighTraffic
    condition: requests_per_minute > 10000
    duration: 5m
    severity: info
```

---

## 9. Cronograma de Implementação

### Fase 1 - MVP (4 semanas)
- [ ] Configuração de infraestrutura
- [ ] API pública (endpoints básicos)
- [ ] Frontend (páginas principais)
- [ ] Exportação PDF/Excel básica

### Fase 2 - Melhorias (3 semanas)
- [ ] Dashboard interativo
- [ ] Filtros avançados
- [ ] Otimização de performance
- [ ] Testes de carga

### Fase 3 - Produção (2 semanas)
- [ ] Segurança e auditoria
- [ ] Documentação
- [ ] Treinamento
- [ ] Go-live

---

## 10. Conclusão

Esta especificação técnica estabelece os padrões para:

1. **Relatórios Internos:** Formatação otimizada para licitações com campos completos e área reservada para assinatura digital.

2. **Portal Público:** Sistema transparente e acessível para consulta cidadã, com exportações em múltiplos formatos.

3. **Conformidade:** Atendimento à Lei 14.133/2021 (Licitações) e Lei 12.527/2011 (Acesso à Informação).

---

**Aprovado por:**

_______________________________
Cristiano Abdo de Souza
Assessor de Planejamento, Compras e Logística

_______________________________
[Nome do Gestor]
Secretário de Administração

**Data:** ___/___/______
