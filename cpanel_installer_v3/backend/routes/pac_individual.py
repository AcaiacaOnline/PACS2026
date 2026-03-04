"""
Rotas de PAC Individual - Planejamento Acaiaca
"""
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from typing import List, Optional
from datetime import datetime, timezone
from io import BytesIO
import uuid
import logging

# Imports serão configurados pelo servidor principal
router = APIRouter(prefix="/api", tags=["PAC Individual"])


def setup_pac_routes(db, get_current_user, PAC, PACItem, PACCreate, PACUpdate, PACItemCreate, PACItemUpdate):
    """Configura as rotas de PAC Individual com dependências injetadas"""
    
    @router.get("/pacs/anos")
    async def get_anos_pacs(request: Request):
        """Retorna os anos disponíveis nos PACs"""
        user = await get_current_user(request)
        pipeline = [
            {"$group": {"_id": "$ano"}},
            {"$sort": {"_id": -1}}
        ]
        anos = await db.pacs.aggregate(pipeline).to_list(100)
        anos_list = [a['_id'] for a in anos if a['_id']]
        if not anos_list:
            anos_list = [str(datetime.now().year)]
        return anos_list

    @router.get("/pacs", response_model=List[PAC])
    async def get_pacs(request: Request, ano: str = None, secretaria: str = None):
        """Lista todos os PACs do usuário"""
        user = await get_current_user(request)
        query = {}
        if ano:
            query['ano'] = ano
        if secretaria:
            query['nome_secretaria'] = {'$regex': secretaria, '$options': 'i'}
        pacs = await db.pacs.find(query, {'_id': 0}).sort('created_at', -1).to_list(1000)
        return pacs

    @router.get("/pacs/paginado")
    async def get_pacs_paginado(
        request: Request,
        ano: str = None,
        secretaria: str = None,
        page: int = 1,
        limit: int = 20
    ):
        """Lista PACs com paginação"""
        user = await get_current_user(request)
        query = {}
        if ano:
            query['ano'] = ano
        if secretaria:
            query['nome_secretaria'] = {'$regex': secretaria, '$options': 'i'}
        
        skip = (page - 1) * limit
        total = await db.pacs.count_documents(query)
        pacs = await db.pacs.find(query, {'_id': 0}).sort('created_at', -1).skip(skip).limit(limit).to_list(limit)
        
        return {
            'data': pacs,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        }

    @router.get("/pacs/stats")
    async def get_pacs_stats(request: Request, ano: str = None):
        """Retorna estatísticas dos PACs"""
        user = await get_current_user(request)
        query = {}
        if ano:
            query['ano'] = ano
        
        pacs = await db.pacs.find(query, {'_id': 0}).to_list(1000)
        
        stats = {
            'total_pacs': len(pacs),
            'por_secretaria': {},
            'valor_total': 0,
            'total_items': 0
        }
        
        for pac in pacs:
            secretaria = pac.get('nome_secretaria', 'Não definida')
            if secretaria not in stats['por_secretaria']:
                stats['por_secretaria'][secretaria] = {
                    'quantidade': 0,
                    'valor_total': 0,
                    'quantidade_items': 0
                }
            
            stats['por_secretaria'][secretaria]['quantidade'] += 1
            
            # Buscar itens do PAC
            items = await db.pac_items.find({'pac_id': pac['pac_id']}, {'_id': 0}).to_list(10000)
            valor_pac = sum(item.get('valor_total', 0) for item in items)
            
            stats['por_secretaria'][secretaria]['valor_total'] += valor_pac
            stats['por_secretaria'][secretaria]['quantidade_items'] += len(items)
            stats['valor_total'] += valor_pac
            stats['total_items'] += len(items)
        
        return stats

    @router.post("/pacs", response_model=PAC)
    async def create_pac(pac: PACCreate, request: Request):
        """Cria um novo PAC"""
        user = await get_current_user(request)
        pac_dict = pac.model_dump()
        pac_dict['pac_id'] = f"pac_{uuid.uuid4().hex[:12]}"
        pac_dict['user_id'] = user.user_id
        pac_dict['created_at'] = datetime.now(timezone.utc)
        pac_dict['updated_at'] = datetime.now(timezone.utc)
        await db.pacs.insert_one(pac_dict)
        return PAC(**pac_dict)

    @router.get("/pacs/{pac_id}", response_model=PAC)
    async def get_pac(pac_id: str, request: Request):
        """Obtém um PAC específico"""
        user = await get_current_user(request)
        pac = await db.pacs.find_one({'pac_id': pac_id}, {'_id': 0})
        if not pac:
            raise HTTPException(status_code=404, detail="PAC não encontrado")
        return PAC(**pac)

    @router.put("/pacs/{pac_id}", response_model=PAC)
    async def update_pac(pac_id: str, pac: PACUpdate, request: Request):
        """Atualiza um PAC"""
        user = await get_current_user(request)
        existing = await db.pacs.find_one({'pac_id': pac_id})
        if not existing:
            raise HTTPException(status_code=404, detail="PAC não encontrado")
        
        update_data = {k: v for k, v in pac.model_dump().items() if v is not None}
        update_data['updated_at'] = datetime.now(timezone.utc)
        
        await db.pacs.update_one({'pac_id': pac_id}, {'$set': update_data})
        updated = await db.pacs.find_one({'pac_id': pac_id}, {'_id': 0})
        return PAC(**updated)

    @router.delete("/pacs/{pac_id}")
    async def delete_pac(pac_id: str, request: Request):
        """Exclui um PAC e seus itens"""
        user = await get_current_user(request)
        result = await db.pacs.delete_one({'pac_id': pac_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="PAC não encontrado")
        await db.pac_items.delete_many({'pac_id': pac_id})
        return {'message': 'PAC excluído com sucesso'}

    # ===== ROTAS DE ITENS =====
    @router.get("/pacs/{pac_id}/items", response_model=List[PACItem])
    async def get_pac_items(pac_id: str, request: Request):
        """Lista itens de um PAC"""
        user = await get_current_user(request)
        items = await db.pac_items.find({'pac_id': pac_id}, {'_id': 0}).to_list(10000)
        return items

    @router.post("/pacs/{pac_id}/items", response_model=PACItem)
    async def create_pac_item(pac_id: str, item: PACItemCreate, request: Request):
        """Adiciona um item ao PAC"""
        user = await get_current_user(request)
        pac = await db.pacs.find_one({'pac_id': pac_id})
        if not pac:
            raise HTTPException(status_code=404, detail="PAC não encontrado")
        
        item_dict = item.model_dump()
        item_dict['item_id'] = f"item_{uuid.uuid4().hex[:12]}"
        item_dict['pac_id'] = pac_id
        item_dict['created_at'] = datetime.now(timezone.utc)
        
        await db.pac_items.insert_one(item_dict)
        return PACItem(**item_dict)

    @router.put("/pacs/{pac_id}/items/{item_id}", response_model=PACItem)
    async def update_pac_item(pac_id: str, item_id: str, item: PACItemUpdate, request: Request):
        """Atualiza um item do PAC"""
        user = await get_current_user(request)
        existing = await db.pac_items.find_one({'item_id': item_id, 'pac_id': pac_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Item não encontrado")
        
        update_data = {k: v for k, v in item.model_dump().items() if v is not None}
        await db.pac_items.update_one({'item_id': item_id}, {'$set': update_data})
        updated = await db.pac_items.find_one({'item_id': item_id}, {'_id': 0})
        return PACItem(**updated)

    @router.delete("/pacs/{pac_id}/items/{item_id}")
    async def delete_pac_item(pac_id: str, item_id: str, request: Request):
        """Exclui um item do PAC"""
        user = await get_current_user(request)
        result = await db.pac_items.delete_one({'item_id': item_id, 'pac_id': pac_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Item não encontrado")
        return {'message': 'Item excluído com sucesso'}

    return router
