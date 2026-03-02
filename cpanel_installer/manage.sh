#!/bin/bash
#============================================================================
# Planejamento Acaiaca - Script de Gerenciamento
# Uso: ./manage.sh {start|stop|restart|status|logs|backup|update}
#============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="${SCRIPT_DIR}/backend"
PID_FILE="${BACKEND_DIR}/app.pid"
LOG_FILE="${BACKEND_DIR}/logs/app.log"
VENV_DIR="${BACKEND_DIR}/venv"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Carregar variáveis de ambiente
if [ -f "${BACKEND_DIR}/.env" ]; then
    export $(grep -v '^#' "${BACKEND_DIR}/.env" | xargs)
fi

start() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo -e "${YELLOW}Aplicação já está rodando (PID: $(cat $PID_FILE))${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Iniciando Planejamento Acaiaca...${NC}"
    
    cd "$BACKEND_DIR"
    
    # Ativar ambiente virtual
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
    fi
    
    # Iniciar com uvicorn
    nohup uvicorn server:app \
        --host 0.0.0.0 \
        --port ${PORT:-8001} \
        --workers ${WORKERS:-2} \
        --log-level info \
        >> "$LOG_FILE" 2>&1 &
    
    echo $! > "$PID_FILE"
    
    sleep 2
    
    if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo -e "${GREEN}✅ Aplicação iniciada (PID: $(cat $PID_FILE))${NC}"
    else
        echo -e "${RED}❌ Falha ao iniciar aplicação${NC}"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            echo -e "${YELLOW}Parando aplicação (PID: $PID)...${NC}"
            kill $PID
            sleep 2
            
            # Forçar se ainda estiver rodando
            if kill -0 $PID 2>/dev/null; then
                kill -9 $PID 2>/dev/null
            fi
        fi
        rm -f "$PID_FILE"
        echo -e "${GREEN}✅ Aplicação parada${NC}"
    else
        echo -e "${YELLOW}Aplicação não está rodando${NC}"
    fi
}

restart() {
    stop
    sleep 2
    start
}

status() {
    echo -e "${GREEN}=== Planejamento Acaiaca - Status ===${NC}"
    echo ""
    
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        PID=$(cat "$PID_FILE")
        echo -e "Status: ${GREEN}RODANDO${NC} (PID: $PID)"
        
        # Informações do processo
        echo ""
        echo "Uso de memória:"
        ps -o rss,vsz -p $PID | tail -1 | awk '{printf "  RSS: %.1f MB, VSZ: %.1f MB\n", $1/1024, $2/1024}'
        
        # Verificar health endpoint
        echo ""
        echo "Health check:"
        HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:${PORT:-8001}/api/health 2>/dev/null || echo "000")
        if [ "$HEALTH" = "200" ]; then
            echo -e "  API: ${GREEN}OK${NC}"
        else
            echo -e "  API: ${RED}ERRO (HTTP $HEALTH)${NC}"
        fi
    else
        echo -e "Status: ${RED}PARADO${NC}"
    fi
    
    echo ""
    echo "Logs recentes:"
    tail -5 "$LOG_FILE" 2>/dev/null | sed 's/^/  /'
}

logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo -e "${RED}Arquivo de log não encontrado${NC}"
    fi
}

backup() {
    echo -e "${GREEN}Iniciando backup...${NC}"
    if [ -f "${SCRIPT_DIR}/scripts/daily_backup.sh" ]; then
        bash "${SCRIPT_DIR}/scripts/daily_backup.sh"
    elif [ -f "${BACKEND_DIR}/scripts/daily_backup.sh" ]; then
        bash "${BACKEND_DIR}/scripts/daily_backup.sh"
    else
        echo -e "${RED}Script de backup não encontrado${NC}"
        return 1
    fi
}

update() {
    echo -e "${GREEN}Atualizando dependências...${NC}"
    
    cd "$BACKEND_DIR"
    
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
        pip install -r requirements.txt --upgrade
        deactivate
        echo -e "${GREEN}✅ Dependências atualizadas${NC}"
    else
        echo -e "${RED}Ambiente virtual não encontrado${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}Reiniciando aplicação...${NC}"
    restart
}

help() {
    echo ""
    echo "Planejamento Acaiaca - Script de Gerenciamento"
    echo ""
    echo "Uso: $0 {comando}"
    echo ""
    echo "Comandos disponíveis:"
    echo "  start   - Iniciar a aplicação"
    echo "  stop    - Parar a aplicação"
    echo "  restart - Reiniciar a aplicação"
    echo "  status  - Verificar status da aplicação"
    echo "  logs    - Ver logs em tempo real"
    echo "  backup  - Executar backup manualmente"
    echo "  update  - Atualizar dependências e reiniciar"
    echo ""
}

case "$1" in
    start)   start ;;
    stop)    stop ;;
    restart) restart ;;
    status)  status ;;
    logs)    logs ;;
    backup)  backup ;;
    update)  update ;;
    help)    help ;;
    *)
        echo -e "${RED}Comando inválido: $1${NC}"
        help
        exit 1
        ;;
esac
