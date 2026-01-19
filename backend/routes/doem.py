"""
DOEM Routes - Diário Oficial Eletrônico Municipal
Handles DOEM editions, publications, and digital signatures
"""
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
import uuid
import logging

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Frame, PageTemplate, BaseDocTemplate
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from striprtf.striprtf import rtf_to_text

router = APIRouter(prefix="/api/doem", tags=["DOEM"])
public_router = APIRouter(prefix="/api/public/doem", tags=["DOEM Público"])

# Reference to root directory
ROOT_DIR = Path(__file__).parent.parent

# DOEM Segments and Publication Types
DOEM_SEGMENTOS = [
    'Decretos', 'Leis', 'Portarias', 'Editais', 'Contratos', 
    'Atas', 'Avisos', 'Resoluções', 'Atos Oficiais', 'Outros'
]

DOEM_TIPOS_PUBLICACAO = [
    'Decreto', 'Lei Ordinária', 'Lei Complementar', 'Portaria',
    'Edital de Licitação', 'Edital de Concurso', 'Contrato',
    'Ata de Registro de Preços', 'Aviso', 'Resolução', 
    'Ato Oficial', 'Errata', 'Outros'
]


def setup_doem_routes(db, get_current_user, User, DOEMEdicao, DOEMEdicaoCreate, DOEMEdicaoUpdate, 
                      DOEMConfig, DOEMConfigUpdate, DOEMPublicacao, draw_signature_seal, generate_validation_code):
    """Configure DOEM routes with injected dependencies"""
    
    async def get_doem_config() -> dict:
        """Get or create default DOEM configuration"""
        config = await db.doem_config.find_one({'config_id': 'doem_config_main'}, {'_id': 0})
        if not config:
            config = {
                'config_id': 'doem_config_main',
                'nome_municipio': 'Acaiaca',
                'uf': 'MG',
                'cnpj': '18.296.673/0001-10',
                'endereco': 'Praça Antônio Carlos, 10 - Centro',
                'telefone': '(31) 3554-1222',
                'email': 'gabinete@acaiaca.mg.gov.br',
                'created_at': datetime.now(timezone.utc)
            }
            await db.doem_config.insert_one(config)
        return config

    async def get_next_edicao_number() -> int:
        """Get next edition number"""
        config = await get_doem_config()
        next_num = config.get('ultimo_numero_edicao', 0) + 1
        await db.doem_config.update_one(
            {'config_id': 'doem_config_main'},
            {'$set': {'ultimo_numero_edicao': next_num}}
        )
        return next_num

    # ===== ADMIN ENDPOINTS =====
    
    @router.get("/config")
    async def get_config(request: Request):
        """Get DOEM configuration"""
        await get_current_user(request)
        return await get_doem_config()

    @router.put("/config")
    async def update_config(config_update: DOEMConfigUpdate, request: Request):
        """Update DOEM configuration"""
        user = await get_current_user(request)
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="Apenas administradores podem alterar configurações")
        
        update_data = {k: v for k, v in config_update.model_dump().items() if v is not None}
        if update_data:
            await db.doem_config.update_one(
                {'config_id': 'doem_config_main'},
                {'$set': update_data},
                upsert=True
            )
        return await get_doem_config()

    @router.get("/edicoes")
    async def list_edicoes(request: Request, ano: int = None, status: str = None):
        """List all DOEM editions"""
        await get_current_user(request)
        query = {}
        if ano:
            query['ano'] = ano
        if status:
            query['status'] = status
        edicoes = await db.doem_edicoes.find(query, {'_id': 0}).sort('data_publicacao', -1).to_list(500)
        return edicoes

    @router.get("/edicoes/anos")
    async def get_doem_anos(request: Request):
        """Get available years in DOEM"""
        await get_current_user(request)
        pipeline = [
            {"$group": {"_id": "$ano"}},
            {"$sort": {"_id": -1}}
        ]
        anos = await db.doem_edicoes.aggregate(pipeline).to_list(100)
        anos_list = [a['_id'] for a in anos if a['_id']]
        if not anos_list:
            anos_list = [datetime.now().year]
        return anos_list

    @router.post("/edicoes")
    async def create_edicao(edicao: DOEMEdicaoCreate, request: Request):
        """Create new DOEM edition"""
        user = await get_current_user(request)
        
        edicao_dict = edicao.model_dump()
        edicao_dict['edicao_id'] = f"doem_{uuid.uuid4().hex[:12]}"
        edicao_dict['numero_edicao'] = await get_next_edicao_number()
        edicao_dict['ano'] = edicao.ano or datetime.now().year
        edicao_dict['status'] = 'rascunho'
        edicao_dict['publicacoes'] = []
        edicao_dict['created_by'] = user.user_id
        edicao_dict['created_at'] = datetime.now(timezone.utc)
        edicao_dict['updated_at'] = datetime.now(timezone.utc)
        
        await db.doem_edicoes.insert_one(edicao_dict)
        
        return {k: v for k, v in edicao_dict.items() if k != '_id'}

    @router.get("/edicoes/{edicao_id}")
    async def get_edicao(edicao_id: str, request: Request):
        """Get specific DOEM edition"""
        await get_current_user(request)
        edicao = await db.doem_edicoes.find_one({'edicao_id': edicao_id}, {'_id': 0})
        if not edicao:
            raise HTTPException(status_code=404, detail="Edição não encontrada")
        return edicao

    @router.put("/edicoes/{edicao_id}")
    async def update_edicao(edicao_id: str, edicao_update: DOEMEdicaoUpdate, request: Request):
        """Update DOEM edition"""
        user = await get_current_user(request)
        
        existing = await db.doem_edicoes.find_one({'edicao_id': edicao_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Edição não encontrada")
        
        if existing.get('status') == 'publicado':
            raise HTTPException(status_code=400, detail="Edições publicadas não podem ser alteradas")
        
        update_data = {k: v for k, v in edicao_update.model_dump().items() if v is not None}
        update_data['updated_at'] = datetime.now(timezone.utc)
        update_data['updated_by'] = user.user_id
        
        await db.doem_edicoes.update_one({'edicao_id': edicao_id}, {'$set': update_data})
        
        return await db.doem_edicoes.find_one({'edicao_id': edicao_id}, {'_id': 0})

    @router.delete("/edicoes/{edicao_id}")
    async def delete_edicao(edicao_id: str, request: Request):
        """Delete DOEM edition"""
        user = await get_current_user(request)
        
        existing = await db.doem_edicoes.find_one({'edicao_id': edicao_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Edição não encontrada")
        
        if existing.get('status') == 'publicado':
            raise HTTPException(status_code=400, detail="Edições publicadas não podem ser excluídas")
        
        await db.doem_edicoes.delete_one({'edicao_id': edicao_id})
        return {"message": "Edição excluída com sucesso"}

    @router.get("/edicoes/{edicao_id}/assinantes")
    async def get_assinantes(edicao_id: str, request: Request):
        """Get edition signers"""
        await get_current_user(request)
        
        edicao = await db.doem_edicoes.find_one({'edicao_id': edicao_id}, {'_id': 0})
        if not edicao:
            raise HTTPException(status_code=404, detail="Edição não encontrada")
        
        assinantes = edicao.get('assinantes', [])
        return assinantes

    @router.post("/edicoes/{edicao_id}/assinantes")
    async def add_assinante(edicao_id: str, request: Request, user_id: str = None):
        """Add signer to edition"""
        current_user = await get_current_user(request)
        
        edicao = await db.doem_edicoes.find_one({'edicao_id': edicao_id})
        if not edicao:
            raise HTTPException(status_code=404, detail="Edição não encontrada")
        
        target_user_id = user_id or current_user.user_id
        user_doc = await db.users.find_one({'user_id': target_user_id}, {'_id': 0})
        if not user_doc:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        signature_data = user_doc.get('signature_data', {})
        if not signature_data.get('cpf'):
            raise HTTPException(status_code=400, detail="Usuário precisa ter CPF cadastrado para assinar")
        
        assinantes = edicao.get('assinantes', [])
        if any(a.get('user_id') == target_user_id for a in assinantes):
            raise HTTPException(status_code=400, detail="Usuário já é assinante desta edição")
        
        novo_assinante = {
            'user_id': target_user_id,
            'nome': user_doc.get('name', ''),
            'email': user_doc.get('email', ''),
            'cpf': signature_data.get('cpf', ''),
            'cargo': signature_data.get('cargo', ''),
            'adicionado_em': datetime.now(timezone.utc).isoformat(),
            'adicionado_por': current_user.user_id
        }
        
        assinantes.append(novo_assinante)
        await db.doem_edicoes.update_one(
            {'edicao_id': edicao_id},
            {'$set': {'assinantes': assinantes, 'updated_at': datetime.now(timezone.utc)}}
        )
        
        return assinantes

    @router.delete("/edicoes/{edicao_id}/assinantes/{user_id}")
    async def remove_assinante(edicao_id: str, user_id: str, request: Request):
        """Remove signer from edition"""
        await get_current_user(request)
        
        edicao = await db.doem_edicoes.find_one({'edicao_id': edicao_id})
        if not edicao:
            raise HTTPException(status_code=404, detail="Edição não encontrada")
        
        if edicao.get('status') == 'publicado':
            raise HTTPException(status_code=400, detail="Não é possível remover assinantes de edições publicadas")
        
        assinantes = edicao.get('assinantes', [])
        assinantes = [a for a in assinantes if a.get('user_id') != user_id]
        
        await db.doem_edicoes.update_one(
            {'edicao_id': edicao_id},
            {'$set': {'assinantes': assinantes, 'updated_at': datetime.now(timezone.utc)}}
        )
        
        return assinantes

    @router.get("/usuarios-disponiveis")
    async def get_usuarios_disponiveis(request: Request):
        """Get available users for signing"""
        await get_current_user(request)
        
        usuarios = await db.users.find(
            {'is_active': True, 'signature_data.cpf': {'$exists': True, '$ne': ''}},
            {'_id': 0, 'user_id': 1, 'name': 1, 'email': 1, 'signature_data': 1}
        ).to_list(500)
        
        return [
            {
                'user_id': u['user_id'],
                'nome': u.get('name', ''),
                'email': u.get('email', ''),
                'cpf': u.get('signature_data', {}).get('cpf', ''),
                'cargo': u.get('signature_data', {}).get('cargo', '')
            }
            for u in usuarios
        ]

    @router.post("/import-rtf")
    async def import_rtf(request: Request, file: UploadFile = File(...)):
        """Import RTF file content"""
        await get_current_user(request)
        
        content = await file.read()
        try:
            text = rtf_to_text(content.decode('utf-8', errors='ignore'))
        except Exception:
            text = rtf_to_text(content.decode('latin-1', errors='ignore'))
        
        return {"content": text}

    @router.get("/segmentos")
    async def get_doem_segmentos(request: Request):
        """Get DOEM segments"""
        await get_current_user(request)
        return {"segmentos": DOEM_SEGMENTOS, "tipos_publicacao": DOEM_TIPOS_PUBLICACAO}

    # ===== PUBLIC ENDPOINTS =====
    
    @public_router.get("/edicoes")
    async def public_list_edicoes(ano: int = None, limit: int = 20):
        """Public list of published DOEM editions"""
        query = {'status': 'publicado'}
        if ano:
            query['ano'] = ano
        edicoes = await db.doem_edicoes.find(query, {'_id': 0}).sort('data_publicacao', -1).to_list(limit)
        return edicoes

    @public_router.get("/edicoes/{edicao_id}")
    async def public_get_edicao(edicao_id: str):
        """Public get specific DOEM edition"""
        edicao = await db.doem_edicoes.find_one(
            {'edicao_id': edicao_id, 'status': 'publicado'},
            {'_id': 0}
        )
        if not edicao:
            raise HTTPException(status_code=404, detail="Edição não encontrada ou não publicada")
        return edicao

    @public_router.get("/anos")
    async def public_get_anos():
        """Public get available years"""
        pipeline = [
            {"$match": {"status": "publicado"}},
            {"$group": {"_id": "$ano"}},
            {"$sort": {"_id": -1}}
        ]
        anos = await db.doem_edicoes.aggregate(pipeline).to_list(100)
        return [a['_id'] for a in anos if a['_id']]

    @public_router.get("/segmentos")
    async def public_get_segmentos():
        """Public get DOEM segments"""
        return {"segmentos": DOEM_SEGMENTOS, "tipos_publicacao": DOEM_TIPOS_PUBLICACAO}

    @public_router.get("/buscar")
    async def public_buscar(q: str, ano: int = None):
        """Public search in DOEM"""
        query = {
            'status': 'publicado',
            '$or': [
                {'publicacoes.titulo': {'$regex': q, '$options': 'i'}},
                {'publicacoes.conteudo': {'$regex': q, '$options': 'i'}},
                {'publicacoes.orgao': {'$regex': q, '$options': 'i'}}
            ]
        }
        if ano:
            query['ano'] = ano
        
        edicoes = await db.doem_edicoes.find(query, {'_id': 0}).sort('data_publicacao', -1).to_list(50)
        return edicoes

    return router, public_router, get_doem_config
