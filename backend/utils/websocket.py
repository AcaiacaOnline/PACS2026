"""
Planejamento Acaiaca - Sistema de Gestão Municipal
Módulo de WebSockets para Notificações em Tempo Real
"""
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from typing import Dict, List, Set, Optional
import json
import asyncio
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger("planejamento_acaiaca.websocket")

router = APIRouter(tags=["WebSocket Notifications"])


class NotificationType(str, Enum):
    """Tipos de notificação"""
    PROCESSO_CRIADO = "processo_criado"
    PROCESSO_ATUALIZADO = "processo_atualizado"
    PAC_CRIADO = "pac_criado"
    PAC_ATUALIZADO = "pac_atualizado"
    MROSC_SUBMETIDO = "mrosc_submetido"
    MROSC_APROVADO = "mrosc_aprovado"
    MROSC_CORRECAO = "mrosc_correcao"
    PRAZO_VENCENDO = "prazo_vencendo"
    PRAZO_VENCIDO = "prazo_vencido"
    DOCUMENTO_UPLOAD = "documento_upload"
    ALERTA_SISTEMA = "alerta_sistema"
    BACKUP_CONCLUIDO = "backup_concluido"
    USUARIO_LOGIN = "usuario_login"
    MENSAGEM = "mensagem"


@dataclass
class Notification:
    """Estrutura de uma notificação"""
    type: NotificationType
    title: str
    message: str
    data: Optional[dict] = None
    user_id: Optional[str] = None
    created_at: str = None
    priority: str = "normal"  # low, normal, high, urgent
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)
    
    def to_dict(self) -> dict:
        return asdict(self)


class ConnectionManager:
    """
    Gerenciador de conexões WebSocket
    Mantém registro de todas as conexões ativas e permite broadcast de mensagens
    """
    
    def __init__(self):
        # Conexões ativas por user_id
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Conexões por sala/tópico
        self.rooms: Dict[str, Set[str]] = {}
        # Fila de notificações pendentes (para usuários offline)
        self.pending_notifications: Dict[str, List[Notification]] = {}
        # Lock para operações thread-safe
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Aceita uma nova conexão WebSocket"""
        await websocket.accept()
        
        async with self._lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            self.active_connections[user_id].append(websocket)
        
        logger.info(f"WebSocket connected: user={user_id}")
        
        # Enviar notificações pendentes
        await self._send_pending_notifications(user_id)
        
        # Notificar conexão
        await self.send_personal_notification(
            user_id,
            Notification(
                type=NotificationType.MENSAGEM,
                title="Conectado",
                message="Você está conectado às notificações em tempo real",
                priority="low"
            )
        )
    
    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove uma conexão WebSocket"""
        async with self._lock:
            if user_id in self.active_connections:
                if websocket in self.active_connections[user_id]:
                    self.active_connections[user_id].remove(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
        
        logger.info(f"WebSocket disconnected: user={user_id}")
    
    async def send_personal_notification(self, user_id: str, notification: Notification):
        """Envia notificação para um usuário específico"""
        notification.user_id = user_id
        
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(notification.to_json())
                except Exception as e:
                    logger.warning(f"Failed to send to {user_id}: {e}")
                    disconnected.append(connection)
            
            # Remover conexões falhas
            for conn in disconnected:
                await self.disconnect(conn, user_id)
        else:
            # Usuário offline - salvar para enviar depois
            await self._queue_notification(user_id, notification)
    
    async def broadcast(self, notification: Notification, exclude_user: str = None):
        """Envia notificação para todos os usuários conectados"""
        async with self._lock:
            users = list(self.active_connections.keys())
        
        for user_id in users:
            if user_id != exclude_user:
                await self.send_personal_notification(user_id, notification)
    
    async def broadcast_to_admins(self, notification: Notification, db):
        """Envia notificação apenas para administradores"""
        admins = await db.users.find(
            {'is_admin': True, 'is_active': True},
            {'user_id': 1}
        ).to_list(100)
        
        for admin in admins:
            await self.send_personal_notification(admin['user_id'], notification)
    
    async def join_room(self, user_id: str, room: str):
        """Adiciona usuário a uma sala"""
        async with self._lock:
            if room not in self.rooms:
                self.rooms[room] = set()
            self.rooms[room].add(user_id)
    
    async def leave_room(self, user_id: str, room: str):
        """Remove usuário de uma sala"""
        async with self._lock:
            if room in self.rooms and user_id in self.rooms[room]:
                self.rooms[room].remove(user_id)
    
    async def broadcast_to_room(self, room: str, notification: Notification):
        """Envia notificação para todos os usuários de uma sala"""
        if room not in self.rooms:
            return
        
        for user_id in self.rooms[room]:
            await self.send_personal_notification(user_id, notification)
    
    async def _queue_notification(self, user_id: str, notification: Notification):
        """Adiciona notificação à fila de pendentes"""
        async with self._lock:
            if user_id not in self.pending_notifications:
                self.pending_notifications[user_id] = []
            
            # Limitar a 50 notificações pendentes por usuário
            if len(self.pending_notifications[user_id]) < 50:
                self.pending_notifications[user_id].append(notification)
    
    async def _send_pending_notifications(self, user_id: str):
        """Envia notificações pendentes para um usuário"""
        async with self._lock:
            if user_id not in self.pending_notifications:
                return
            
            notifications = self.pending_notifications.pop(user_id, [])
        
        for notification in notifications:
            if user_id in self.active_connections:
                for connection in self.active_connections[user_id]:
                    try:
                        await connection.send_text(notification.to_json())
                    except Exception:
                        pass
    
    def get_connected_users(self) -> List[str]:
        """Retorna lista de usuários conectados"""
        return list(self.active_connections.keys())
    
    def get_connection_count(self) -> int:
        """Retorna número total de conexões"""
        return sum(len(conns) for conns in self.active_connections.values())


# Instância global do gerenciador
manager = ConnectionManager()


@router.websocket("/ws/notifications/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    Endpoint WebSocket para notificações em tempo real
    
    Conecte-se usando: ws://host/api/ws/notifications/{user_id}
    
    Mensagens recebidas no formato JSON:
    {
        "type": "tipo_da_notificacao",
        "title": "Título",
        "message": "Mensagem",
        "data": {...},
        "priority": "normal",
        "created_at": "2026-01-18T12:00:00Z"
    }
    """
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Aguardar mensagens do cliente (ping/pong, comandos, etc.)
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                # Processar comandos do cliente
                if message.get('type') == 'ping':
                    await websocket.send_text(json.dumps({
                        'type': 'pong',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }))
                elif message.get('type') == 'subscribe':
                    room = message.get('room')
                    if room:
                        await manager.join_room(user_id, room)
                        await websocket.send_text(json.dumps({
                            'type': 'subscribed',
                            'room': room
                        }))
                elif message.get('type') == 'unsubscribe':
                    room = message.get('room')
                    if room:
                        await manager.leave_room(user_id, room)
                        await websocket.send_text(json.dumps({
                            'type': 'unsubscribed',
                            'room': room
                        }))
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        await manager.disconnect(websocket, user_id)


@router.get("/ws/status")
async def websocket_status():
    """Retorna status das conexões WebSocket"""
    return {
        "connected_users": len(manager.get_connected_users()),
        "total_connections": manager.get_connection_count(),
        "users": manager.get_connected_users(),
        "rooms": {room: list(users) for room, users in manager.rooms.items()}
    }


# ===== FUNÇÕES DE NOTIFICAÇÃO =====

async def notify_processo_created(db, processo: dict, user_id: str):
    """Notifica criação de processo"""
    notification = Notification(
        type=NotificationType.PROCESSO_CRIADO,
        title="Novo Processo Criado",
        message=f"Processo {processo.get('numero_processo', 'N/A')} foi criado",
        data={
            'processo_id': processo.get('processo_id'),
            'numero': processo.get('numero_processo'),
            'modalidade': processo.get('modalidade_contratacao')
        },
        priority="normal"
    )
    await manager.broadcast_to_admins(notification, db)


async def notify_processo_updated(db, processo: dict, changes: dict, user_id: str):
    """Notifica atualização de processo"""
    notification = Notification(
        type=NotificationType.PROCESSO_ATUALIZADO,
        title="Processo Atualizado",
        message=f"Processo {processo.get('numero_processo', 'N/A')} foi atualizado",
        data={
            'processo_id': processo.get('processo_id'),
            'changes': changes
        },
        priority="normal"
    )
    await manager.broadcast_to_admins(notification, db)


async def notify_mrosc_submitted(db, projeto: dict, user_id: str):
    """Notifica submissão de projeto MROSC"""
    notification = Notification(
        type=NotificationType.MROSC_SUBMETIDO,
        title="Projeto MROSC Submetido",
        message=f"Projeto '{projeto.get('nome_projeto', 'N/A')}' foi submetido para análise",
        data={
            'projeto_id': projeto.get('projeto_id'),
            'nome': projeto.get('nome_projeto'),
            'organizacao': projeto.get('organizacao_parceira')
        },
        priority="high"
    )
    await manager.broadcast_to_admins(notification, db)


async def notify_mrosc_approved(projeto: dict, user_id: str):
    """Notifica aprovação de projeto MROSC"""
    notification = Notification(
        type=NotificationType.MROSC_APROVADO,
        title="Projeto MROSC Aprovado! ✅",
        message=f"Seu projeto '{projeto.get('nome_projeto', 'N/A')}' foi aprovado",
        data={
            'projeto_id': projeto.get('projeto_id'),
            'nome': projeto.get('nome_projeto')
        },
        priority="high"
    )
    # Notificar o criador do projeto
    await manager.send_personal_notification(user_id, notification)


async def notify_mrosc_correction(projeto: dict, user_id: str, observacao: str):
    """Notifica solicitação de correção MROSC"""
    notification = Notification(
        type=NotificationType.MROSC_CORRECAO,
        title="Correção Solicitada ⚠️",
        message=f"Correções solicitadas para o projeto '{projeto.get('nome_projeto', 'N/A')}'",
        data={
            'projeto_id': projeto.get('projeto_id'),
            'nome': projeto.get('nome_projeto'),
            'observacao': observacao
        },
        priority="urgent"
    )
    await manager.send_personal_notification(user_id, notification)


async def notify_prazo_vencendo(db, recurso_tipo: str, recurso_id: str, prazo: str, dias_restantes: int):
    """Notifica prazo próximo do vencimento"""
    notification = Notification(
        type=NotificationType.PRAZO_VENCENDO,
        title=f"Prazo Vencendo em {dias_restantes} dias ⏰",
        message=f"O prazo de {recurso_tipo} está próximo do vencimento: {prazo}",
        data={
            'tipo': recurso_tipo,
            'id': recurso_id,
            'prazo': prazo,
            'dias_restantes': dias_restantes
        },
        priority="high" if dias_restantes <= 3 else "normal"
    )
    await manager.broadcast_to_admins(notification, db)


async def notify_system_alert(db, title: str, message: str, priority: str = "normal"):
    """Envia alerta do sistema para todos os admins"""
    notification = Notification(
        type=NotificationType.ALERTA_SISTEMA,
        title=title,
        message=message,
        priority=priority
    )
    await manager.broadcast_to_admins(notification, db)


async def notify_backup_completed(db, backup_info: dict):
    """Notifica conclusão de backup"""
    notification = Notification(
        type=NotificationType.BACKUP_CONCLUIDO,
        title="Backup Concluído ✅",
        message=f"Backup realizado com sucesso: {backup_info.get('total_records', 0)} registros",
        data=backup_info,
        priority="low"
    )
    await manager.broadcast_to_admins(notification, db)
