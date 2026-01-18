#!/usr/bin/env python3
"""
Sistema de Instalação - Planejamento Acaiaca
Similar ao WordPress, permite configuração inicial do sistema
"""

import os
import sys
import asyncio
import uuid
import bcrypt
from datetime import datetime, timezone
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient

# Cores para o terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header():
    print(f"""
{Colors.OKBLUE}
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║  {Colors.BOLD}PLANEJAMENTO ACAIACA - SISTEMA DE INSTALAÇÃO{Colors.ENDC}{Colors.OKBLUE}                    ║
║                                                                   ║
║  Sistema de Gestão Municipal                                      ║
║  Prefeitura Municipal de Acaiaca - MG                             ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
{Colors.ENDC}
""")


def print_step(step, total, message):
    print(f"{Colors.OKCYAN}[{step}/{total}]{Colors.ENDC} {message}")


def print_success(message):
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message):
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_warning(message):
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def get_input(prompt, default=None, required=True):
    """Obtém input do usuário com valor padrão opcional"""
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "
    
    value = input(full_prompt).strip()
    
    if not value and default:
        return default
    
    if not value and required:
        print_error("Este campo é obrigatório!")
        return get_input(prompt, default, required)
    
    return value


def get_password(prompt):
    """Obtém senha do usuário (oculta)"""
    import getpass
    return getpass.getpass(f"{prompt}: ")


def validate_email(email):
    """Valida formato de email"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_cnpj(cnpj):
    """Valida formato de CNPJ"""
    import re
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    return len(cnpj) == 14


async def test_mongodb_connection(mongo_url):
    """Testa conexão com MongoDB"""
    try:
        client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
        await client.server_info()
        return True, client
    except Exception as e:
        return False, str(e)


async def create_indexes(db):
    """Cria índices necessários para performance"""
    print_step(6, 8, "Criando índices do banco de dados...")
    
    try:
        # Índices para users
        await db.users.create_index("email", unique=True)
        await db.users.create_index("user_id", unique=True)
        
        # Índices para PACs
        await db.pacs.create_index("pac_id", unique=True)
        await db.pac_items.create_index("pac_id")
        await db.pac_items.create_index("item_id", unique=True)
        
        # Índices para PAC Geral
        await db.pacs_geral.create_index("pac_geral_id", unique=True)
        await db.pac_geral_items.create_index("pac_geral_id")
        
        # Índices para PAC Obras
        await db.pacs_geral_obras.create_index("pac_obras_id", unique=True)
        await db.pac_geral_obras_items.create_index("pac_obras_id")
        
        # Índices para Processos
        await db.processos.create_index("processo_id", unique=True)
        await db.processos.create_index("numero_processo")
        await db.processos.create_index("status")
        
        # Índices para MROSC
        await db.mrosc_projetos.create_index("projeto_id", unique=True)
        await db.mrosc_projetos.create_index("user_id")
        await db.mrosc_projetos.create_index("status")
        await db.mrosc_rh.create_index("projeto_id")
        await db.mrosc_despesas.create_index("projeto_id")
        await db.mrosc_documentos.create_index("projeto_id")
        await db.mrosc_documentos.create_index("documento_id", unique=True)
        
        # Índices para DOEM
        await db.doem_edicoes.create_index("edicao_id", unique=True)
        await db.doem_edicoes.create_index("numero_edicao")
        await db.doem_newsletter.create_index("email", unique=True)
        
        # Índices para Assinaturas
        await db.document_signatures.create_index("validation_code", unique=True)
        
        print_success("Índices criados com sucesso!")
        return True
    except Exception as e:
        print_warning(f"Alguns índices podem já existir: {str(e)}")
        return True


async def create_admin_user(db, name, email, password):
    """Cria usuário administrador"""
    print_step(7, 8, "Criando usuário administrador...")
    
    # Verifica se já existe
    existing = await db.users.find_one({'email': email})
    if existing:
        print_warning(f"Usuário {email} já existe. Atualizando como administrador...")
        await db.users.update_one(
            {'email': email},
            {'$set': {'is_admin': True, 'is_active': True}}
        )
        return True
    
    # Hash da senha
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    user_doc = {
        'user_id': f"user_{uuid.uuid4().hex[:12]}",
        'email': email,
        'name': name,
        'password_hash': password_hash,
        'is_admin': True,
        'is_active': True,
        'tipo_usuario': 'servidor',
        'created_at': datetime.now(timezone.utc),
        'signature_data': None
    }
    
    await db.users.insert_one(user_doc)
    print_success(f"Administrador criado: {email}")
    return True


def create_env_file(config):
    """Cria arquivo .env com as configurações"""
    print_step(5, 8, "Criando arquivo de configuração...")
    
    env_content = f"""# Planejamento Acaiaca - Configuração do Sistema
# Gerado automaticamente pela instalação

# ============ BANCO DE DADOS ============
MONGO_URL={config['mongo_url']}
DB_NAME={config['db_name']}

# ============ SEGURANÇA ============
JWT_SECRET={config['jwt_secret']}

# ============ EMAIL (SMTP) ============
SMTP_SERVER={config.get('smtp_server', 'smtp.gmail.com')}
SMTP_PORT={config.get('smtp_port', '465')}
SMTP_EMAIL={config.get('smtp_email', '')}
SMTP_PASSWORD={config.get('smtp_password', '')}
SMTP_USE_SSL={config.get('smtp_use_ssl', 'true')}

# ============ PREFEITURA ============
PREFEITURA_NOME={config.get('prefeitura_nome', 'Prefeitura Municipal')}
PREFEITURA_CNPJ={config.get('prefeitura_cnpj', '')}
PREFEITURA_ESTADO={config.get('prefeitura_estado', 'MG')}
"""
    
    env_path = Path(__file__).parent / '.env'
    
    # Backup se existir
    if env_path.exists():
        backup_path = env_path.with_suffix('.env.backup')
        env_path.rename(backup_path)
        print_warning(f"Arquivo .env existente movido para {backup_path}")
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print_success(f"Arquivo .env criado em {env_path}")
    return True


def create_upload_directory():
    """Cria diretório para uploads"""
    upload_dir = Path(__file__).parent / 'uploads'
    upload_dir.mkdir(exist_ok=True)
    print_success(f"Diretório de uploads: {upload_dir}")
    return True


async def run_installation():
    """Executa o processo de instalação"""
    print_header()
    
    print(f"{Colors.BOLD}Bem-vindo ao assistente de instalação!{Colors.ENDC}")
    print("Este assistente irá configurar o sistema Planejamento Acaiaca.\n")
    
    # ============ ETAPA 1: Banco de Dados ============
    print(f"\n{Colors.HEADER}=== ETAPA 1: Configuração do Banco de Dados ==={Colors.ENDC}\n")
    
    mongo_url = get_input(
        "URL do MongoDB", 
        default="mongodb://localhost:27017",
        required=True
    )
    
    db_name = get_input(
        "Nome do banco de dados", 
        default="planejamento_acaiaca",
        required=True
    )
    
    print_step(1, 8, "Testando conexão com MongoDB...")
    success, result = await test_mongodb_connection(mongo_url)
    
    if not success:
        print_error(f"Não foi possível conectar ao MongoDB: {result}")
        print("Verifique se o MongoDB está rodando e a URL está correta.")
        return False
    
    print_success("Conexão com MongoDB estabelecida!")
    client = result
    db = client[db_name]
    
    # ============ ETAPA 2: Segurança ============
    print(f"\n{Colors.HEADER}=== ETAPA 2: Configurações de Segurança ==={Colors.ENDC}\n")
    
    jwt_secret = get_input(
        "Chave secreta JWT (deixe em branco para gerar automaticamente)",
        default=f"planejamento-acaiaca-{uuid.uuid4().hex}",
        required=False
    ) or f"planejamento-acaiaca-{uuid.uuid4().hex}"
    
    # ============ ETAPA 3: Dados da Prefeitura ============
    print(f"\n{Colors.HEADER}=== ETAPA 3: Dados da Prefeitura ==={Colors.ENDC}\n")
    
    prefeitura_nome = get_input(
        "Nome da Prefeitura",
        default="Prefeitura Municipal de Acaiaca",
        required=True
    )
    
    prefeitura_cnpj = get_input(
        "CNPJ da Prefeitura (apenas números)",
        default="18295287000190",
        required=False
    )
    
    prefeitura_estado = get_input(
        "Estado (UF)",
        default="MG",
        required=True
    )
    
    # ============ ETAPA 4: Email (Opcional) ============
    print(f"\n{Colors.HEADER}=== ETAPA 4: Configuração de Email (Opcional) ==={Colors.ENDC}\n")
    
    configurar_email = get_input(
        "Deseja configurar o envio de emails? (s/n)",
        default="n",
        required=False
    ).lower() == 's'
    
    smtp_config = {}
    if configurar_email:
        smtp_config['smtp_server'] = get_input("Servidor SMTP", default="smtp.gmail.com")
        smtp_config['smtp_port'] = get_input("Porta SMTP", default="465")
        smtp_config['smtp_email'] = get_input("Email remetente", required=True)
        smtp_config['smtp_password'] = get_password("Senha do email")
        smtp_config['smtp_use_ssl'] = get_input("Usar SSL? (true/false)", default="true")
    
    # ============ ETAPA 5: Administrador ============
    print(f"\n{Colors.HEADER}=== ETAPA 5: Usuário Administrador ==={Colors.ENDC}\n")
    
    admin_name = get_input("Nome completo do administrador", required=True)
    
    admin_email = get_input("Email do administrador", required=True)
    while not validate_email(admin_email):
        print_error("Email inválido!")
        admin_email = get_input("Email do administrador", required=True)
    
    admin_password = get_password("Senha do administrador (mínimo 8 caracteres)")
    while len(admin_password) < 8:
        print_error("A senha deve ter pelo menos 8 caracteres!")
        admin_password = get_password("Senha do administrador")
    
    # ============ CONFIRMAR ============
    print(f"\n{Colors.HEADER}=== RESUMO DA INSTALAÇÃO ==={Colors.ENDC}\n")
    print(f"  MongoDB: {mongo_url}")
    print(f"  Banco: {db_name}")
    print(f"  Prefeitura: {prefeitura_nome}")
    print(f"  Administrador: {admin_name} ({admin_email})")
    print()
    
    confirmar = get_input("Confirmar instalação? (s/n)", default="s", required=True)
    if confirmar.lower() != 's':
        print("Instalação cancelada.")
        return False
    
    # ============ EXECUTAR ============
    print(f"\n{Colors.HEADER}=== EXECUTANDO INSTALAÇÃO ==={Colors.ENDC}\n")
    
    config = {
        'mongo_url': mongo_url,
        'db_name': db_name,
        'jwt_secret': jwt_secret,
        'prefeitura_nome': prefeitura_nome,
        'prefeitura_cnpj': prefeitura_cnpj,
        'prefeitura_estado': prefeitura_estado,
        **smtp_config
    }
    
    # Criar arquivo .env
    create_env_file(config)
    
    # Criar diretório de uploads
    create_upload_directory()
    
    # Criar índices
    await create_indexes(db)
    
    # Criar administrador
    await create_admin_user(db, admin_name, admin_email, admin_password)
    
    # ============ FINALIZADO ============
    print_step(8, 8, "Finalizando instalação...")
    
    print(f"""
{Colors.OKGREEN}
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║  {Colors.BOLD}INSTALAÇÃO CONCLUÍDA COM SUCESSO!{Colors.ENDC}{Colors.OKGREEN}                             ║
║                                                                   ║
║  Para iniciar o sistema:                                          ║
║                                                                   ║
║  1. Backend:  cd backend && uvicorn server:app --reload           ║
║  2. Frontend: cd frontend && yarn start                           ║
║                                                                   ║
║  Acesse: http://localhost:3000                                    ║
║  Login: {admin_email:<50}   ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
{Colors.ENDC}
""")
    
    return True


def main():
    """Ponto de entrada principal"""
    try:
        asyncio.run(run_installation())
    except KeyboardInterrupt:
        print("\n\nInstalação interrompida pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Erro durante a instalação: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
