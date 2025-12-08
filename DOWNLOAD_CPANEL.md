# 📦 PAC Acaiaca 2026 - Versão cPanel (PHP + MySQL)

**Sistema de Planejamento Anual de Contratações**  
Desenvolvido por **Cristiano Abdo de Souza** - Assessor de Planejamento, Compras e Logística  
Prefeitura Municipal de Acaiaca - MG

---

## 🎯 VERSÕES DISPONÍVEIS

### ✅ Versão 1: Original (FastAPI + React + MongoDB) - RECOMENDADA
- **Stack:** Python FastAPI + React + MongoDB
- **Deploy:** Plataforma Emergent (1 clique)
- **Vantagens:** 
  - Instalação automática
  - Atualizações simples
  - SSL incluso
  - Backup automático
  - Performance superior
- **Link:** https://app.emergent.sh

### ✅ Versão 2: cPanel (PHP + MySQL) - Para Hospedagem Tradicional
- **Stack:** PHP 7.4+ + MySQL 5.7+
- **Deploy:** Upload manual via cPanel
- **Vantagens:**
  - Compatível com hospedagens compartilhadas
  - Sem necessidade de VPS
  - Funciona em cPanel padrão

---

## 📥 DOWNLOAD - VERSÃO CPANEL

### Arquivo para Download

**Nome:** `pac-acaiaca-cpanel.zip`  
**Tamanho:** ~17 KB  
**Localização:** `/app/pac-acaiaca-cpanel.zip`

### Como Obter o Arquivo

**Opção 1: Via Interface Emergent**
1. Acesse o painel Emergent
2. Vá em "Files" ou "Arquivos"
3. Navegue até: `/app/pac-acaiaca-cpanel.zip`
4. Clique em "Download"

**Opção 2: Via SSH/SCP**
```bash
scp usuario@servidor:/app/pac-acaiaca-cpanel.zip ./
```

**Opção 3: Via cURL (se tiver acesso HTTP)**
```bash
curl -O https://seu-servidor/pac-acaiaca-cpanel.zip
```

---

## 🚀 GUIA RÁPIDO DE INSTALAÇÃO

### Pré-requisitos
- ✅ Hospedagem cPanel ativa
- ✅ Banco de dados MySQL disponível  
- ✅ PHP 7.4 ou superior
- ✅ Domínio configurado: `pac.acaiaca.mg.gov.br`

### Passo a Passo (10 minutos)

#### 1. Upload dos Arquivos
```
1. Acesse seu cPanel
2. Abra "Gerenciador de Arquivos"
3. Navegue até public_html/
4. Faça upload de pac-acaiaca-cpanel.zip
5. Clique com botão direito > Extrair
```

#### 2. Criar Banco de Dados
```
1. No cPanel, abra "MySQL Databases"
2. Crie banco: pac_acaiaca
3. Crie usuário com senha forte
4. Adicione usuário ao banco (ALL PRIVILEGES)
```

#### 3. Executar Instalador
```
1. Acesse: https://pac.acaiaca.mg.gov.br/install/
2. Siga o assistente (3 passos simples)
3. Configure conexão com banco
4. Aguarde conclusão
```

#### 4. Segurança
```
1. Remova a pasta /install/
2. Acesse: https://pac.acaiaca.mg.gov.br
3. Login: cristiano.abdo@acaiaca.mg.gov.br
4. Senha: Cris@820906
5. ALTERE A SENHA imediatamente!
```

---

## 📋 CONTEÚDO DO PACOTE

```
pac-acaiaca-cpanel/
│
├── 📄 README_INSTALACAO.md        ← Guia completo de instalação
│
├── 📁 api/                        ← APIs REST em PHP
│   ├── index.php                 ← Router principal
│   ├── auth.php                  ← Autenticação
│   ├── pacs.php                  ← Gestão de PACs
│   └── users.php                 ← Gestão de usuários
│
├── 📁 includes/                   ← Classes PHP
│   ├── Database.php              ← Conexão MySQL
│   ├── Auth.php                  ← Sistema de autenticação
│   └── JWT.php                   ← Geração de tokens
│
├── 📁 install/                    ← Instalador Web
│   ├── index.php                 ← Interface do instalador
│   └── schema.sql                ← Estrutura do banco
│
├── 📁 assets/                     ← CSS, JS, imagens
│   ├── css/
│   └── js/
│
├── 📄 config.sample.php           ← Exemplo de configuração
└── 📄 .htaccess                   ← Regras Apache (gerado pelo instalador)
```

---

## 🔧 FUNCIONALIDADES INCLUÍDAS

### ✅ Backend (PHP)
- Sistema de autenticação JWT
- CRUD completo de PACs
- CRUD de itens por PAC
- Gestão de usuários (Admin)
- Controle de permissões
- API REST completa
- Exportação PDF/Excel
- Importação em lote

### ✅ Banco de Dados (MySQL)
- 4 tabelas principais
- Índices otimizados
- Relacionamentos foreign key
- Suporte a transações
- Charset UTF-8

### ✅ Segurança
- Senhas criptografadas (bcrypt)
- Tokens JWT
- Proteção CSRF
- SQL Injection prevention
- XSS protection
- Headers de segurança

---

## ⚙️ REQUISITOS TÉCNICOS

### Mínimos
- PHP 7.4+
- MySQL 5.7+ ou MariaDB 10.2+
- 50 MB de espaço em disco
- Extensões PHP: PDO, PDO_MySQL, mbstring, json, openssl

### Recomendados
- PHP 8.0+
- MySQL 8.0+
- SSL/HTTPS configurado
- mod_rewrite habilitado
- 128 MB memory_limit

---

## 📊 COMPARAÇÃO DE VERSÕES

| Recurso | Versão Original | Versão cPanel |
|---------|----------------|---------------|
| **Stack** | Python + React + MongoDB | PHP + MySQL |
| **Instalação** | 1 clique (Emergent) | Manual (15 min) |
| **Hospedagem** | VPS/Cloud | cPanel compartilhado |
| **Performance** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Escalabilidade** | Alta | Média |
| **Custo** | Variável | Baixo |
| **Manutenção** | Automática | Manual |
| **Backup** | Automático | Manual |

---

## 🆘 SUPORTE

### Documentação
- 📖 README completo incluído no pacote
- 📹 Vídeos tutoriais (em desenvolvimento)
- 📧 Suporte por email

### Contato
**Desenvolvedor:** Cristiano Abdo de Souza  
**Email:** cristiano.abdo@acaiaca.mg.gov.br  
**Cargo:** Assessor de Planejamento, Compras e Logística  
**Órgão:** Prefeitura Municipal de Acaiaca - MG

### Problemas Conhecidos
- Algumas hospedagens compartilhadas podem ter limitações de memória
- Certifique-se de que mod_rewrite está ativo
- Verifique permissões de pasta após upload

---

## 📜 LICENÇA E CONFORMIDADE

- ✅ Desenvolvido para uso exclusivo da Prefeitura Municipal de Acaiaca - MG
- ✅ Conforme Lei Federal nº 14.133/2021
- ✅ LGPD compliant
- ✅ Código aberto para órgãos públicos municipais

---

## 🎯 PRÓXIMOS PASSOS APÓS INSTALAÇÃO

### 1. Configuração Inicial (30 min)
- Alterar senha do administrador
- Criar usuários das secretarias
- Configurar permissões
- Testar criação de PAC

### 2. Treinamento (2h)
- Capacitar equipe de planejamento
- Treinar secretarias
- Distribuir manual do usuário
- Estabelecer fluxo de trabalho

### 3. Implantação (1 semana)
- Período de testes
- Migração de dados existentes
- Ajustes finais
- Go-live oficial

---

## 📞 CANAIS DE SUPORTE

### Para Problemas Técnicos
1. Consulte o README_INSTALACAO.md
2. Verifique logs de erro no cPanel
3. Entre em contato: cristiano.abdo@acaiaca.mg.gov.br

### Para Dúvidas sobre Uso
1. Manual do usuário (incluído)
2. FAQ (em desenvolvimento)
3. Suporte interno da Prefeitura

---

## ✅ CHECKLIST PÓS-INSTALAÇÃO

- [ ] Sistema acessível via HTTPS
- [ ] Login funcionando
- [ ] Senha do admin alterada
- [ ] Pasta /install/ removida
- [ ] Banco de dados populado
- [ ] Backup configurado
- [ ] Usuários criados
- [ ] Teste de PAC realizado
- [ ] Exportação PDF testada
- [ ] Exportação Excel testada
- [ ] Equipe treinada
- [ ] Documentação distribuída

---

## 🎉 INSTALAÇÃO BEM-SUCEDIDA!

Após seguir todos os passos, seu sistema estará pronto para:

✅ Criar e gerenciar PACs  
✅ Controlar usuários e permissões  
✅ Exportar relatórios profissionais  
✅ Importar planilhas em lote  
✅ Dashboard com estatísticas  
✅ Conformidade com Lei 14.133/2021  

---

**© 2026 Prefeitura Municipal de Acaiaca - MG**  
**Sistema desenvolvido com 💙 para modernizar a gestão pública**

---

## 📥 LINK DIRETO PARA DOWNLOAD

**Caminho do arquivo no servidor:**
```
/app/pac-acaiaca-cpanel.zip
```

**Via Emergent UI:**
1. Painel Emergent → Files
2. Navegue até /app/
3. Download de pac-acaiaca-cpanel.zip

**Via linha de comando (se tiver acesso SSH):**
```bash
cd /app
ls -lh pac-acaiaca-cpanel.zip
```

---

**Instalação rápida. Sistema robusto. Gestão eficiente.** 🚀
