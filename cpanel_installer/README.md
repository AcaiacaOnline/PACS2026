# Planejamento Acaiaca - Sistema de Gestão Municipal

## Instalador cPanel v2.0

### Requisitos do Servidor

- **cPanel/WHM** com acesso SSH
- **Python 3.9+** instalado
- **MongoDB 5.0+** instalado e configurado
- **Node.js 18+** (apenas para desenvolvimento)
- **mod_proxy** habilitado no Apache

### Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                     CLIENTE                          │
│                   (Navegador)                        │
└─────────────────────┬───────────────────────────────┘
                      │ HTTPS
                      ▼
┌─────────────────────────────────────────────────────┐
│                    APACHE                            │
│              (Proxy Reverso)                         │
│    /api/* → localhost:8001                          │
│    /*     → Frontend Estático                        │
└─────────────────────┬───────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
┌─────────────────┐      ┌─────────────────┐
│    BACKEND      │      │    FRONTEND     │
│   (FastAPI)     │      │    (React)      │
│   Port: 8001    │      │   (Estático)    │
└────────┬────────┘      └─────────────────┘
         │
         ▼
┌─────────────────┐
│    MONGODB      │
│   Port: 27017   │
└─────────────────┘
```

### Instalação Rápida

1. **Fazer upload do pacote** para o servidor via cPanel File Manager ou FTP

2. **Acessar o servidor via SSH**:
   ```bash
   ssh usuario@seu-servidor.com
   ```

3. **Extrair o pacote**:
   ```bash
   cd ~
   unzip planejamento-acaiaca-cpanel.zip
   cd planejamento-acaiaca-cpanel
   ```

4. **Executar o instalador**:
   ```bash
   chmod +x install.sh
   ./install.sh nome_banco usuario_db senha_db seu-dominio.com
   ```

### Parâmetros de Instalação

| Parâmetro | Descrição | Obrigatório |
|-----------|-----------|-------------|
| `db_name` | Nome do banco MongoDB | Sim |
| `db_user` | Usuário do MongoDB | Sim |
| `db_password` | Senha do MongoDB | Sim |
| `domain` | Domínio da aplicação | Não |

### Estrutura de Diretórios Após Instalação

```
~/planejamento-acaiaca/
├── backend/
│   ├── server.py           # Servidor FastAPI
│   ├── models/             # Modelos Pydantic
│   ├── routes/             # Rotas modulares
│   ├── utils/              # Utilitários
│   ├── services/           # Serviços (email, PDF)
│   ├── static/             # Arquivos estáticos
│   ├── uploads/            # Uploads de usuários
│   ├── logs/               # Logs da aplicação
│   ├── venv/               # Ambiente virtual Python
│   ├── .env                # Configurações
│   └── start.sh            # Script de inicialização
├── frontend/
│   └── build/              # Build do React
└── manage.sh               # Script de gerenciamento

~/public_html/
├── index.html              # Aplicação React
├── static/                 # Assets do frontend
└── .htaccess               # Configuração Apache
```

### Gerenciamento da Aplicação

```bash
# Iniciar
~/planejamento-acaiaca/manage.sh start

# Parar
~/planejamento-acaiaca/manage.sh stop

# Reiniciar
~/planejamento-acaiaca/manage.sh restart

# Ver status
~/planejamento-acaiaca/manage.sh status

# Ver logs em tempo real
~/planejamento-acaiaca/manage.sh logs
```

### Configuração do MongoDB no cPanel

1. Acesse **cPanel > Software > MongoDB**
2. Crie um novo banco de dados
3. Crie um usuário com permissões de leitura/escrita
4. Anote as credenciais para usar na instalação

### Configuração de Email (Opcional)

Edite o arquivo `~/planejamento-acaiaca/backend/.env`:

```env
SMTP_HOST=mail.seu-dominio.com
SMTP_PORT=587
SMTP_USER=noreply@seu-dominio.com
SMTP_PASS=sua-senha-smtp
```

### SSL/HTTPS

O cPanel geralmente configura SSL automaticamente via Let's Encrypt. Certifique-se de que:

1. O certificado SSL está instalado
2. O domínio está apontando corretamente
3. Force HTTPS está habilitado

### Troubleshooting

#### Aplicação não inicia

```bash
# Verificar logs
tail -100 ~/planejamento-acaiaca/backend/logs/app.log

# Verificar se a porta está em uso
lsof -i :8001

# Testar conexão MongoDB
python3 -c "from pymongo import MongoClient; c = MongoClient('sua-uri'); print(c.list_database_names())"
```

#### Erro 502 Bad Gateway

1. Verifique se o backend está rodando:
   ```bash
   ~/planejamento-acaiaca/manage.sh status
   ```

2. Verifique se mod_proxy está habilitado:
   ```bash
   httpd -M | grep proxy
   ```

#### Erro de permissão

```bash
chmod -R 755 ~/planejamento-acaiaca
chmod -R 777 ~/planejamento-acaiaca/backend/logs
chmod -R 777 ~/planejamento-acaiaca/backend/uploads
```

### Backup

```bash
# Backup do banco de dados
mongodump --uri="mongodb://user:pass@localhost:27017/db_name" --out=./backup

# Backup dos arquivos
tar -czvf backup-planejamento.tar.gz ~/planejamento-acaiaca
```

### Atualização

1. Faça backup dos dados
2. Pare a aplicação
3. Substitua os arquivos
4. Reinicie a aplicação

```bash
~/planejamento-acaiaca/manage.sh stop
# Atualizar arquivos
~/planejamento-acaiaca/manage.sh start
```

### Suporte

- **Email**: suporte@prefeitura-acaiaca.mg.gov.br
- **Documentação API**: https://seu-dominio.com/api/docs

---

## Changelog v2.0

### Melhorias de Performance
- Otimização de queries MongoDB com índices
- Lazy loading no frontend
- Compressão de assets
- Cache de responses frequentes

### Segurança
- JWT com rotação automática
- Rate limiting em endpoints sensíveis
- Sanitização de inputs
- Headers de segurança (CSP, HSTS)

### Refatoração
- Modularização do backend (routes, services, utils)
- Redução de código duplicado
- Padronização de responses
- Melhor tratamento de erros

### Novos Recursos
- Sistema de backup automatizado
- Logs estruturados
- Health checks
- Métricas de performance

---

**Versão**: 2.0.0  
**Data**: 06/02/2026  
**Licença**: Proprietária - Prefeitura Municipal de Acaiaca
