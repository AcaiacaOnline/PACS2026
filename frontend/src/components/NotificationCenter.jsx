import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Bell, X, Check, AlertTriangle, Info, CheckCircle, Clock, FileText, Users } from 'lucide-react';
import { toast } from 'sonner';

const NOTIFICATION_ICONS = {
  processo_criado: FileText,
  processo_atualizado: FileText,
  pac_criado: FileText,
  pac_atualizado: FileText,
  mrosc_submetido: Clock,
  mrosc_aprovado: CheckCircle,
  mrosc_correcao: AlertTriangle,
  prazo_vencendo: Clock,
  prazo_vencido: AlertTriangle,
  documento_upload: FileText,
  alerta_sistema: AlertTriangle,
  backup_concluido: CheckCircle,
  usuario_login: Users,
  mensagem: Info,
};

const PRIORITY_COLORS = {
  low: 'bg-gray-100 border-gray-300',
  normal: 'bg-blue-50 border-blue-300',
  high: 'bg-orange-50 border-orange-400',
  urgent: 'bg-red-50 border-red-400 animate-pulse',
};

const NotificationItem = ({ notification, onDismiss }) => {
  const Icon = NOTIFICATION_ICONS[notification.type] || Info;
  const priorityClass = PRIORITY_COLORS[notification.priority] || PRIORITY_COLORS.normal;
  
  const formatTime = (isoString) => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Agora';
    if (diffMins < 60) return `${diffMins}m atrás`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h atrás`;
    return date.toLocaleDateString('pt-BR');
  };

  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg border ${priorityClass} transition-all hover:shadow-md`}>
      <div className={`p-2 rounded-full ${
        notification.priority === 'urgent' ? 'bg-red-200' :
        notification.priority === 'high' ? 'bg-orange-200' :
        'bg-blue-200'
      }`}>
        <Icon className={`h-4 w-4 ${
          notification.priority === 'urgent' ? 'text-red-600' :
          notification.priority === 'high' ? 'text-orange-600' :
          'text-blue-600'
        }`} />
      </div>
      
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm text-gray-900 truncate">{notification.title}</p>
        <p className="text-xs text-gray-600 mt-0.5 line-clamp-2">{notification.message}</p>
        <p className="text-xs text-gray-400 mt-1">{formatTime(notification.created_at)}</p>
      </div>
      
      <button 
        onClick={() => onDismiss(notification)}
        className="p-1 hover:bg-gray-200 rounded-full transition-colors"
      >
        <X className="h-4 w-4 text-gray-400" />
      </button>
    </div>
  );
};

const NotificationCenter = ({ userId }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connectWebSocket = useCallback(() => {
    if (!userId) return;

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/ws/notifications/${userId}`;
    
    try {
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket conectado');
        setIsConnected(true);
        // Enviar ping a cada 30 segundos
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);
        ws.pingInterval = pingInterval;
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'pong') {
            return; // Ignorar pong
          }
          
          // Nova notificação
          setNotifications(prev => [data, ...prev].slice(0, 50)); // Manter últimas 50
          setUnreadCount(prev => prev + 1);
          
          // Mostrar toast para notificações importantes
          if (data.priority === 'high' || data.priority === 'urgent') {
            toast(data.title, {
              description: data.message,
              duration: 5000,
            });
          }
        } catch (e) {
          console.error('Erro ao processar mensagem:', e);
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket desconectado');
        setIsConnected(false);
        clearInterval(ws.pingInterval);
        
        // Tentar reconectar após 5 segundos
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, 5000);
      };
      
      ws.onerror = (error) => {
        console.error('Erro WebSocket:', error);
        setIsConnected(false);
      };
      
      wsRef.current = ws;
    } catch (error) {
      console.error('Erro ao criar WebSocket:', error);
    }
  }, [userId]);

  useEffect(() => {
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        clearInterval(wsRef.current.pingInterval);
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connectWebSocket]);

  const dismissNotification = (notification) => {
    setNotifications(prev => prev.filter(n => n !== notification));
  };

  const clearAll = () => {
    setNotifications([]);
    setUnreadCount(0);
  };

  const markAllRead = () => {
    setUnreadCount(0);
  };

  return (
    <div className="relative">
      {/* Botão do sino */}
      <button
        onClick={() => {
          setIsOpen(!isOpen);
          if (!isOpen) markAllRead();
        }}
        className="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-full transition-colors"
        data-testid="notification-bell"
      >
        <Bell className={`h-5 w-5 ${isConnected ? 'text-gray-600' : 'text-gray-400'}`} />
        
        {/* Indicador de conexão */}
        <span className={`absolute top-1 right-1 w-2 h-2 rounded-full ${
          isConnected ? 'bg-green-500' : 'bg-gray-400'
        }`} />
        
        {/* Badge de não lidas */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1 font-bold">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Painel de notificações */}
      {isOpen && (
        <>
          {/* Overlay para fechar ao clicar fora */}
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Painel */}
          <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-xl shadow-xl border border-gray-200 z-50 overflow-hidden"
               data-testid="notification-panel">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b">
              <div className="flex items-center gap-2">
                <Bell className="h-5 w-5 text-blue-600" />
                <h3 className="font-semibold text-gray-900">Notificações</h3>
                <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-400'}`} 
                      title={isConnected ? 'Conectado' : 'Desconectado'} />
              </div>
              
              {notifications.length > 0 && (
                <button 
                  onClick={clearAll}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  Limpar todas
                </button>
              )}
            </div>
            
            {/* Lista de notificações */}
            <div className="max-h-96 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="px-4 py-8 text-center text-gray-500">
                  <Bell className="h-12 w-12 mx-auto text-gray-300 mb-3" />
                  <p className="font-medium">Nenhuma notificação</p>
                  <p className="text-sm">Você será notificado quando houver novidades</p>
                </div>
              ) : (
                <div className="p-2 space-y-2">
                  {notifications.map((notification, index) => (
                    <NotificationItem 
                      key={`${notification.created_at}-${index}`}
                      notification={notification}
                      onDismiss={dismissNotification}
                    />
                  ))}
                </div>
              )}
            </div>
            
            {/* Footer */}
            {notifications.length > 0 && (
              <div className="px-4 py-2 bg-gray-50 border-t text-center">
                <span className="text-xs text-gray-500">
                  {notifications.length} notificação(ões)
                </span>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default NotificationCenter;
