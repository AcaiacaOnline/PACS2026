"""
Models Package - Export all models
"""
from .user import (
    User, UserCreate, UserUpdate, UserLogin, UserListItem,
    UserPermissions, UserSignatureData
)
from .pac import (
    PAC, PACCreate, PACUpdate, PACItem, PACItemCreate, PACItemUpdate,
    PACGeral, PACGeralCreate, PACGeralUpdate, PACGeralItem, PACGeralItemCreate, PACGeralItemUpdate
)
from .processo import (
    Processo, ProcessoCreate, ProcessoUpdate, PaginatedResponse
)
from .doem import (
    DOEMPublicacao, DOEMPublicacaoCreate, DOEMAssinante, DOEMAssinatura,
    DOEMEdicao, DOEMEdicaoCreate, DOEMEdicaoUpdate, DOEMConfig, DOEMConfigUpdate,
    DOEM_SEGMENTOS, DOEM_TIPOS_PUBLICACAO
)
from .newsletter import (
    NewsletterInscrito, NewsletterInscricaoPublica, NewsletterInscricaoManual
)

__all__ = [
    # User models
    'User', 'UserCreate', 'UserUpdate', 'UserLogin', 'UserListItem',
    'UserPermissions', 'UserSignatureData',
    # PAC models
    'PAC', 'PACCreate', 'PACUpdate', 'PACItem', 'PACItemCreate', 'PACItemUpdate',
    'PACGeral', 'PACGeralCreate', 'PACGeralUpdate', 'PACGeralItem', 'PACGeralItemCreate', 'PACGeralItemUpdate',
    # Processo models
    'Processo', 'ProcessoCreate', 'ProcessoUpdate', 'PaginatedResponse',
    # DOEM models
    'DOEMPublicacao', 'DOEMPublicacaoCreate', 'DOEMAssinante', 'DOEMAssinatura',
    'DOEMEdicao', 'DOEMEdicaoCreate', 'DOEMEdicaoUpdate', 'DOEMConfig', 'DOEMConfigUpdate',
    'DOEM_SEGMENTOS', 'DOEM_TIPOS_PUBLICACAO',
    # Newsletter models
    'NewsletterInscrito', 'NewsletterInscricaoPublica', 'NewsletterInscricaoManual',
]
