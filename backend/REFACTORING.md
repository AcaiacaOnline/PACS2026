# Refatoração do Backend - Planejamento Acaiaca

## Status: PARCIALMENTE CONCLUÍDO

### O que foi feito nesta sessão:

1. **Correções de Bugs Críticos**
   - Adicionada função `enviar_email_smtp` (estava faltando - linha 72)
   - Removida redefinição duplicada de `DocumentoMROSCCreate` (linha 5117)
   - Removida redefinição duplicada de `PageBreak` (linha 5952)
   - Adicionado endpoint `/api/health` para verificação de saúde

2. **Correções de Lint**
   - Corrigidos `except:` genéricos para tipos específicos
   - Removidos f-strings sem placeholders
   - Reduzido de 87 para 81 warnings

3. **Arquivos Criados para Refatoração Futura**
   - `/app/backend/config.py` - Configurações centralizadas
   - `/app/backend/shared.py` - Funções compartilhadas
   - `/app/backend/routes/auth_refactored.py` - Módulo de autenticação modular
   - `/app/backend/server_modular.py` - Template do servidor refatorado

### Estrutura Atual do server.py (6976 linhas)

```
Linhas    | Seção
----------|------------------------------------------
1-65      | Imports
66-110    | Configurações (SMTP, MongoDB, JWT)
111-280   | Modelos e Aliases
281-380   | Funções de Autenticação
381-640   | Funções Auxiliares de PDF
641-1100  | Endpoints de Autenticação e Usuários
1101-1700 | Endpoints de PAC Individual
1701-2200 | Endpoints de PAC Geral
2201-2700 | Endpoints de PAC Obras
2701-3200 | Endpoints de Processos/Licitações
3201-4600 | Funções de Exportação PDF
4601-5300 | Endpoints Públicos (Portal Transparência)
5301-6200 | Endpoints MROSC (Prestação de Contas)
6201-6700 | Analytics, Alertas, Relatórios
6701-6976 | Backup, Configurações, Rotas Finais
```

### Próximos Passos para Refatoração Completa

#### Fase 1: Modularização por Domínio
1. Mover endpoints de **Autenticação** para `/routes/auth.py`
2. Mover endpoints de **PAC** para `/routes/pac.py`
3. Mover endpoints de **Processos** para `/routes/processos.py`
4. Mover endpoints de **MROSC** para `/routes/mrosc.py`
5. Mover endpoints **Públicos** para `/routes/public.py`

#### Fase 2: Extração de Funções
1. Mover funções de PDF para `/utils/pdf_utils.py`
2. Mover funções de Email para `/utils/email_utils.py`
3. Mover funções de Validação para `/utils/validators.py`

#### Fase 3: Limpeza
1. Remover código morto e duplicado
2. Consolidar modelos no pacote `/models/`
3. Adicionar tipagem completa (mypy)
4. Criar testes unitários por módulo

### Warnings Restantes (81)

A maioria são falsos positivos:
- `F841 Local variable 'user' is assigned to but never used` - A variável `user` é usada indiretamente para validar autenticação via `get_current_user(request)`
- `E722 Do not use bare 'except'` - Alguns são intencionais para silenciar erros em operações não-críticas

### Riscos da Refatoração Completa

1. **Alto risco de regressão** - O código atual funciona e qualquer mudança pode introduzir bugs
2. **Tempo necessário** - Estimativa de 4-8 horas de trabalho para refatoração completa
3. **Testes** - Necessário criar suite de testes antes de refatorar

### Recomendação

Manter o server.py atual funcionando e fazer a refatoração gradualmente:
1. Criar testes de integração primeiro
2. Migrar um módulo de cada vez
3. Testar extensivamente após cada migração
4. Manter backup funcional

---

Última atualização: 04/03/2026
