"""
Backup and Restore Routes - Refactored Module
Handles system data backup and restoration
"""
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone
from io import BytesIO
import json

router = APIRouter(prefix="/api/backup", tags=["Backup & Restore"])

def setup_backup_routes(db, get_current_user):
    """Setup backup routes with dependencies"""

    @router.get("/export")
    async def export_backup(request: Request):
        """
        Exports all system data to a JSON file.
        Admin only.
        """
        user = await get_current_user(request)
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="Apenas administradores podem fazer backup")
        
        try:
            backup_data = {
                'metadata': {
                    'version': '1.0',
                    'exported_at': datetime.now(timezone.utc).isoformat(),
                    'exported_by': user.email,
                    'system': 'PAC Acaiaca 2026'
                },
                'users': [],
                'pacs': [],
                'pac_items': [],
                'pacs_geral': [],
                'pac_geral_items': [],
                'processos': []
            }
            
            # Export users
            users = await db.users.find({}, {'_id': 0}).to_list(10000)
            for u in users:
                if 'created_at' in u and isinstance(u['created_at'], datetime):
                    u['created_at'] = u['created_at'].isoformat()
                backup_data['users'].append(u)
            
            # Export PACs
            pacs = await db.pacs.find({}, {'_id': 0}).to_list(10000)
            for p in pacs:
                if 'created_at' in p and isinstance(p['created_at'], datetime):
                    p['created_at'] = p['created_at'].isoformat()
                if 'updated_at' in p and isinstance(p['updated_at'], datetime):
                    p['updated_at'] = p['updated_at'].isoformat()
                backup_data['pacs'].append(p)
            
            # Export PAC Items
            pac_items = await db.pac_items.find({}, {'_id': 0}).to_list(100000)
            for item in pac_items:
                if 'created_at' in item and isinstance(item['created_at'], datetime):
                    item['created_at'] = item['created_at'].isoformat()
                backup_data['pac_items'].append(item)
            
            # Export PACs Geral
            pacs_geral = await db.pacs_geral.find({}, {'_id': 0}).to_list(10000)
            for pg in pacs_geral:
                if 'created_at' in pg and isinstance(pg['created_at'], datetime):
                    pg['created_at'] = pg['created_at'].isoformat()
                if 'updated_at' in pg and isinstance(pg['updated_at'], datetime):
                    pg['updated_at'] = pg['updated_at'].isoformat()
                backup_data['pacs_geral'].append(pg)
            
            # Export PAC Geral Items
            pac_geral_items = await db.pac_geral_items.find({}, {'_id': 0}).to_list(100000)
            for item in pac_geral_items:
                if 'created_at' in item and isinstance(item['created_at'], datetime):
                    item['created_at'] = item['created_at'].isoformat()
                backup_data['pac_geral_items'].append(item)
            
            # Export Processos
            processos = await db.processos.find({}, {'_id': 0}).to_list(100000)
            for proc in processos:
                for field in ['created_at', 'updated_at', 'data_inicio', 'data_autuacao', 'data_contrato']:
                    if field in proc and isinstance(proc[field], datetime):
                        proc[field] = proc[field].isoformat()
                backup_data['processos'].append(proc)
            
            json_content = json.dumps(backup_data, ensure_ascii=False, indent=2)
            buffer = BytesIO(json_content.encode('utf-8'))
            buffer.seek(0)
            
            filename = f"backup_pac_acaiaca_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            return StreamingResponse(
                buffer,
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao gerar backup: {str(e)}")

    @router.post("/restore")
    async def restore_backup(request: Request, file: UploadFile = File(...)):
        """
        Restores all system data from a backup JSON file.
        WARNING: This operation replaces ALL existing data!
        Admin only.
        """
        user = await get_current_user(request)
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="Apenas administradores podem restaurar backup")
        
        try:
            contents = await file.read()
            backup_data = json.loads(contents.decode('utf-8'))
            
            required_keys = ['metadata', 'users', 'pacs', 'pac_items', 'pacs_geral', 'pac_geral_items', 'processos']
            for key in required_keys:
                if key not in backup_data:
                    raise HTTPException(status_code=400, detail=f"Arquivo de backup inválido: falta a chave '{key}'")
            
            stats = {
                'users': 0,
                'pacs': 0,
                'pac_items': 0,
                'pacs_geral': 0,
                'pac_geral_items': 0,
                'processos': 0
            }
            
            current_admin_email = user.email
            for u in backup_data['users']:
                if u.get('email') == current_admin_email:
                    continue
                if 'created_at' in u and isinstance(u['created_at'], str):
                    u['created_at'] = datetime.fromisoformat(u['created_at'].replace('Z', '+00:00'))
                await db.users.update_one({'user_id': u['user_id']}, {'$set': u}, upsert=True)
                stats['users'] += 1
            
            for p in backup_data['pacs']:
                for field in ['created_at', 'updated_at']:
                    if field in p and isinstance(p[field], str):
                        p[field] = datetime.fromisoformat(p[field].replace('Z', '+00:00'))
                await db.pacs.update_one({'pac_id': p['pac_id']}, {'$set': p}, upsert=True)
                stats['pacs'] += 1
            
            for item in backup_data['pac_items']:
                if 'created_at' in item and isinstance(item['created_at'], str):
                    item['created_at'] = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                await db.pac_items.update_one({'item_id': item['item_id']}, {'$set': item}, upsert=True)
                stats['pac_items'] += 1
            
            for pg in backup_data['pacs_geral']:
                for field in ['created_at', 'updated_at']:
                    if field in pg and isinstance(pg[field], str):
                        pg[field] = datetime.fromisoformat(pg[field].replace('Z', '+00:00'))
                await db.pacs_geral.update_one({'pac_geral_id': pg['pac_geral_id']}, {'$set': pg}, upsert=True)
                stats['pacs_geral'] += 1
            
            for item in backup_data['pac_geral_items']:
                if 'created_at' in item and isinstance(item['created_at'], str):
                    item['created_at'] = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                await db.pac_geral_items.update_one({'item_id': item['item_id']}, {'$set': item}, upsert=True)
                stats['pac_geral_items'] += 1
            
            for proc in backup_data['processos']:
                for field in ['created_at', 'updated_at', 'data_inicio', 'data_autuacao', 'data_contrato']:
                    if field in proc and isinstance(proc[field], str):
                        try:
                            proc[field] = datetime.fromisoformat(proc[field].replace('Z', '+00:00'))
                        except:
                            proc[field] = None
                await db.processos.update_one({'processo_id': proc['processo_id']}, {'$set': proc}, upsert=True)
                stats['processos'] += 1
            
            return {
                'success': True,
                'message': 'Backup restaurado com sucesso!',
                'stats': stats,
                'backup_metadata': backup_data.get('metadata', {})
            }
        
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Arquivo de backup inválido: não é um JSON válido")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao restaurar backup: {str(e)}")

    @router.get("/info")
    async def get_backup_info(request: Request):
        """Returns information about current system data for backup."""
        user = await get_current_user(request)
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="Apenas administradores podem ver informações de backup")
        
        users_count = await db.users.count_documents({})
        pacs_count = await db.pacs.count_documents({})
        pac_items_count = await db.pac_items.count_documents({})
        pacs_geral_count = await db.pacs_geral.count_documents({})
        pac_geral_items_count = await db.pac_geral_items.count_documents({})
        processos_count = await db.processos.count_documents({})
        
        return {
            'system': 'PAC Acaiaca 2026',
            'current_data': {
                'users': users_count,
                'pacs': pacs_count,
                'pac_items': pac_items_count,
                'pacs_geral': pacs_geral_count,
                'pac_geral_items': pac_geral_items_count,
                'processos': processos_count
            },
            'total_records': users_count + pacs_count + pac_items_count + pacs_geral_count + pac_geral_items_count + processos_count,
            'backup_available': True,
            'restore_available': True
        }

    return router
