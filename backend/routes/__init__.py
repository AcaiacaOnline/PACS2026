"""
Routes Package - Export all routers
Planejamento Acaiaca - Sistema de Gestão Municipal
"""
from .auth import router as auth_router, setup_auth_routes, hash_password
from .users import router as users_router, setup_users_routes
from .classificacao import router as classificacao_router
from .backup import router as backup_router, setup_backup_routes
from .validacao import router as validacao_router, setup_validation_routes
from .pac import router as pac_router, setup_pac_routes
from .pac_geral import router as pac_geral_router, setup_pac_geral_routes
from .pac_obras import router as pac_obras_router, setup_pac_obras_routes, CLASSIFICACAO_OBRAS_SERVICOS
from .gestao_processual import router as processos_router, setup_processos_routes, MODALIDADES_CONTRATACAO, STATUS_PROCESSO
from .public import router as public_router, setup_public_routes
from .mrosc import router as mrosc_router, setup_mrosc_routes, NATUREZAS_DESPESA_MROSC
from .analytics import analytics_router, alertas_router, relatorios_router, setup_analytics_routes, setup_alertas_routes, setup_relatorios_routes
from .doem import router as doem_router, public_router as doem_public_router, setup_doem_routes, DOEM_SEGMENTOS, DOEM_TIPOS_PUBLICACAO

__all__ = [
    # Auth
    'auth_router', 'setup_auth_routes', 'hash_password',
    # Users
    'users_router', 'setup_users_routes',
    # Classification
    'classificacao_router',
    # Backup
    'backup_router', 'setup_backup_routes',
    # Validation
    'validacao_router', 'setup_validation_routes',
    # PAC Individual
    'pac_router', 'setup_pac_routes',
    # PAC Geral
    'pac_geral_router', 'setup_pac_geral_routes',
    # PAC Obras
    'pac_obras_router', 'setup_pac_obras_routes', 'CLASSIFICACAO_OBRAS_SERVICOS',
    # Processos
    'processos_router', 'setup_processos_routes', 'MODALIDADES_CONTRATACAO', 'STATUS_PROCESSO',
    # Public
    'public_router', 'setup_public_routes',
    # MROSC
    'mrosc_router', 'setup_mrosc_routes', 'NATUREZAS_DESPESA_MROSC',
    # Analytics
    'analytics_router', 'alertas_router', 'relatorios_router',
    'setup_analytics_routes', 'setup_alertas_routes', 'setup_relatorios_routes',
    # DOEM
    'doem_router', 'doem_public_router', 'setup_doem_routes', 'DOEM_SEGMENTOS', 'DOEM_TIPOS_PUBLICACAO',
]
