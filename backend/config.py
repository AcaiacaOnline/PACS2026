"""
Configurações globais da aplicação
Planejamento Acaiaca - Sistema de Gestão Municipal
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from reportlab.lib.units import mm

# ===== CONFIGURAÇÃO DO BANCO DE DADOS =====
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'planejamento_acaiaca')

# Cliente MongoDB
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# ===== CONFIGURAÇÕES DE EMAIL =====
SMTP_HOST = os.environ.get('SMTP_HOST', '')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASS = os.environ.get('SMTP_PASS', '')
SMTP_FROM = os.environ.get('SMTP_FROM', 'noreply@acaiaca.mg.gov.br')

# ===== CONFIGURAÇÕES JWT =====
JWT_SECRET = os.environ.get('JWT_SECRET', 'planejamento_acaiaca_jwt_secret_key_2024')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DAYS = 7

# ===== CONSTANTES DE MARGENS PADRONIZADAS (Lei 14.133/2021) =====
REPORT_MARGIN_LEFT = 20*mm    # 2cm
REPORT_MARGIN_RIGHT = 20*mm   # 2cm
REPORT_MARGIN_TOP = 25*mm     # 2.5cm
REPORT_MARGIN_BOTTOM = 20*mm  # 2cm

# ===== CONSTANTES PARA PAGINAÇÃO =====
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100
ITEMS_PER_PAGE = 15

# ===== MODALIDADES DE CONTRATAÇÃO =====
MODALIDADES_CONTRATACAO = [
    "Pregão Eletrônico",
    "Pregão Presencial", 
    "Concorrência",
    "Tomada de Preços",
    "Convite",
    "Concurso",
    "Leilão",
    "Dispensa de Licitação",
    "Inexigibilidade",
    "Adesão a Ata de Registro de Preços",
    "Chamamento Público",
    "Credenciamento"
]

# ===== STATUS DE PROCESSO =====
STATUS_PROCESSO = [
    "Em Elaboração",
    "Aguardando Aprovação",
    "Aprovado",
    "Em Licitação",
    "Homologado",
    "Contratado",
    "Em Execução",
    "Concluído",
    "Cancelado",
    "Suspenso",
    "Deserto",
    "Fracassado"
]

# ===== CLASSIFICAÇÃO DE OBRAS E SERVIÇOS =====
CLASSIFICACAO_OBRAS_SERVICOS = {
    "449051": {
        "nome": "Obras e Instalações",
        "subitens": [
            "01 - Obras em Andamento",
            "02 - Aquisição de Imóveis",
            "03 - Instalações",
            "91 - Obras em Andamento - Intra-OFSS",
            "92 - Aquisição de Imóveis - Intra-OFSS",
            "93 - Instalações - Intra-OFSS",
            "99 - Outras Obras e Instalações"
        ]
    },
    "339039": {
        "nome": "Outros Serviços de Terceiros - Pessoa Jurídica",
        "subitens": [
            "05 - Serviços Técnicos Profissionais",
            "16 - Manutenção e Conservação de Bens Imóveis",
            "17 - Manutenção e Conservação de Máquinas e Equipamentos",
            "19 - Manutenção e Conservação de Veículos",
            "69 - Seguros em Geral",
            "78 - Limpeza e Conservação",
            "79 - Serviço de Apoio Administrativo, Técnico e Operacional",
            "99 - Outros Serviços de Terceiros - Pessoa Jurídica"
        ]
    }
}

# ===== NATUREZAS DE DESPESA MROSC =====
NATUREZAS_DESPESA_MROSC = [
    {"codigo": "339030", "descricao": "Material de Consumo"},
    {"codigo": "339036", "descricao": "Outros Serviços de Terceiros - Pessoa Física"},
    {"codigo": "339039", "descricao": "Outros Serviços de Terceiros - Pessoa Jurídica"},
    {"codigo": "339047", "descricao": "Obrigações Tributárias e Contributivas"},
    {"codigo": "449052", "descricao": "Equipamentos e Material Permanente"}
]
