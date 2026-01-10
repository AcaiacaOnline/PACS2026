"""
Routes Package - Export all routers
"""
from .auth import router as auth_router, setup_auth_routes, hash_password
from .users import router as users_router, setup_users_routes
from .classificacao import router as classificacao_router
from .backup import router as backup_router, setup_backup_routes
from .validacao import router as validacao_router, setup_validation_routes

__all__ = [
    'auth_router', 'setup_auth_routes', 'hash_password',
    'users_router', 'setup_users_routes',
    'classificacao_router',
    'backup_router', 'setup_backup_routes',
    'validacao_router', 'setup_validation_routes',
]
