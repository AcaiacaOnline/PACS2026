"""
Rotas de Gestão Processual - Planejamento Acaiaca
"""
from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/api", tags=["Gestão Processual"])


def setup_processos_routes(db, get_current_user, Processo, ProcessoCreate, ProcessoUpdate):
    """Configura as rotas de Gestão Processual"""
    
    @router.get("/processos/anos")
    async def get_anos_processos(request: Request):
        """Retorna os anos disponíveis nos processos"""
        user = await get_current_user(request)
        pipeline = [
            {"$group": {"_id": "$ano"}},
            {"$sort": {"_id": -1}}
        ]
        anos = await db.processos.aggregate(pipeline).to_list(100)
        anos_list = [a['_id'] for a in anos if a['_id']]
        if not anos_list:
            anos_list = [str(datetime.now().year)]
        return anos_list

    @router.get("/processos", response_model=List[Processo])
    async def get_processos(
        request: Request,
        ano: str = None,
        status: str = None,
        modalidade: str = None,
        secretaria: str = None
    ):
        """Lista todos os processos"""
        user = await get_current_user(request)
        query = {}
        if ano:
            query['ano'] = ano
        if status:
            query['status'] = status
        if modalidade:
            query['modalidade_contratacao'] = modalidade
        if secretaria:
            query['secretaria'] = {'$regex': secretaria, '$options': 'i'}
        
        processos = await db.processos.find(query, {'_id': 0}).sort('created_at', -1).to_list(10000)
        return processos

    @router.get("/processos/paginado")
    async def get_processos_paginado(
        request: Request,
        ano: str = None,
        status: str = None,
        modalidade: str = None,
        secretaria: str = None,
        busca: str = None,
        page: int = 1,
        limit: int = 20
    ):
        """Lista processos com paginação"""
        user = await get_current_user(request)
        query = {}
        if ano:
            query['ano'] = ano
        if status:
            query['status'] = status
        if modalidade:
            query['modalidade_contratacao'] = modalidade
        if secretaria:
            query['secretaria'] = {'$regex': secretaria, '$options': 'i'}
        if busca:
            query['$or'] = [
                {'numero_processo': {'$regex': busca, '$options': 'i'}},
                {'objeto': {'$regex': busca, '$options': 'i'}},
                {'responsavel': {'$regex': busca, '$options': 'i'}}
            ]
        
        skip = (page - 1) * limit
        total = await db.processos.count_documents(query)
        processos = await db.processos.find(query, {'_id': 0}).sort('created_at', -1).skip(skip).limit(limit).to_list(limit)
        
        return {
            'data': processos,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        }

    @router.get("/processos/stats")
    async def get_processos_stats(request: Request, ano: str = None):
        """Retorna estatísticas dos processos"""
        user = await get_current_user(request)
        query = {}
        if ano:
            query['ano'] = ano
        
        processos = await db.processos.find(query, {'_id': 0}).to_list(10000)
        
        stats = {
            'total': len(processos),
            'por_status': {},
            'por_modalidade': {},
            'por_secretaria': {}
        }
        
        for proc in processos:
            status = proc.get('status', 'Não definido')
            modalidade = proc.get('modalidade_contratacao', 'Não definida')
            secretaria = proc.get('secretaria', 'Não definida')
            
            stats['por_status'][status] = stats['por_status'].get(status, 0) + 1
            stats['por_modalidade'][modalidade] = stats['por_modalidade'].get(modalidade, 0) + 1
            stats['por_secretaria'][secretaria] = stats['por_secretaria'].get(secretaria, 0) + 1
        
        return stats

    @router.post("/processos", response_model=Processo)
    async def create_processo(processo: ProcessoCreate, request: Request):
        """Cria um novo processo"""
        user = await get_current_user(request)
        proc_dict = processo.model_dump()
        proc_dict['processo_id'] = f"proc_{uuid.uuid4().hex[:12]}"
        proc_dict['user_id'] = user.user_id
        proc_dict['created_at'] = datetime.now(timezone.utc)
        proc_dict['updated_at'] = datetime.now(timezone.utc)
        
        await db.processos.insert_one(proc_dict)
        proc_dict.pop('_id', None)
        return Processo(**proc_dict)

    @router.get("/processos/{processo_id}", response_model=Processo)
    async def get_processo(processo_id: str, request: Request):
        """Obtém um processo específico"""
        user = await get_current_user(request)
        processo = await db.processos.find_one({'processo_id': processo_id}, {'_id': 0})
        if not processo:
            raise HTTPException(status_code=404, detail="Processo não encontrado")
        return Processo(**processo)

    @router.put("/processos/{processo_id}", response_model=Processo)
    async def update_processo(processo_id: str, processo: ProcessoUpdate, request: Request):
        """Atualiza um processo"""
        user = await get_current_user(request)
        existing = await db.processos.find_one({'processo_id': processo_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Processo não encontrado")
        
        update_data = {k: v for k, v in processo.model_dump().items() if v is not None}
        update_data['updated_at'] = datetime.now(timezone.utc)
        
        await db.processos.update_one({'processo_id': processo_id}, {'$set': update_data})
        updated = await db.processos.find_one({'processo_id': processo_id}, {'_id': 0})
        return Processo(**updated)

    @router.delete("/processos/{processo_id}")
    async def delete_processo(processo_id: str, request: Request):
        """Exclui um processo"""
        user = await get_current_user(request)
        result = await db.processos.delete_one({'processo_id': processo_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Processo não encontrado")
        return {'message': 'Processo excluído com sucesso'}

    @router.get("/processos/modalidades/lista")
    async def get_modalidades(request: Request):
        """Lista todas as modalidades de contratação"""
        user = await get_current_user(request)
        modalidades = [
            "Pregão Eletrônico",
            "Pregão Presencial",
            "Concorrência",
            "Tomada de Preços",
            "Convite",
            "Dispensa de Licitação",
            "Inexigibilidade",
            "Leilão",
            "Concurso",
            "Diálogo Competitivo",
            "Adesão a Ata de Registro de Preços",
            "Chamamento Público"
        ]
        return modalidades

    @router.get("/processos/status/lista")
    async def get_status_lista(request: Request):
        """Lista todos os status possíveis"""
        user = await get_current_user(request)
        status_list = [
            "Em Elaboração",
            "Aguardando Aprovação",
            "Aprovado",
            "Em Andamento",
            "Publicado",
            "Em Fase de Lances",
            "Em Análise de Propostas",
            "Homologado",
            "Adjudicado",
            "Contratado",
            "Em Execução",
            "Concluído",
            "Cancelado",
            "Suspenso",
            "Deserto",
            "Fracassado"
        ]
        return status_list

    return router
