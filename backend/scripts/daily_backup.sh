#!/bin/bash
#============================================================================
# Planejamento Acaiaca - Backup Automático
# 
# USO MANUAL:
#   cd /app/backend && bash scripts/daily_backup.sh
#
# CONFIGURAÇÃO CRON (cPanel):
#   0 3 * * * /home/$USER/planejamento-acaiaca/backend/scripts/daily_backup.sh
#============================================================================

set -e

# Detectar diretório de instalação
if [ -d "/app/backend" ]; then
    INSTALL_DIR="/app"
elif [ -d "$HOME/planejamento-acaiaca" ]; then
    INSTALL_DIR="$HOME/planejamento-acaiaca"
else
    echo "❌ Diretório de instalação não encontrado"
    exit 1
fi

BACKEND_DIR="${INSTALL_DIR}/backend"
BACKUP_DIR="${BACKEND_DIR}/backups"
LOG_DIR="${BACKEND_DIR}/logs"
LOG_FILE="${LOG_DIR}/backup_cron.log"
MAX_BACKUPS=7
DATE=$(date +%Y%m%d_%H%M%S)

# Criar diretórios se não existirem
mkdir -p "$BACKUP_DIR"
mkdir -p "$LOG_DIR"

# Carregar variáveis de ambiente
if [ -f "${BACKEND_DIR}/.env" ]; then
    export $(grep -v '^#' "${BACKEND_DIR}/.env" | xargs)
fi

# Função de log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========== Iniciando backup =========="
log "Diretório: $INSTALL_DIR"

# 1. Backup via API (JSON completo)
log "Fazendo backup via API..."
API_URL="${API_BASE_URL:-http://127.0.0.1:8001}"

# Tentar obter token de admin para backup
if [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then
    TOKEN=$(curl -s -X POST "${API_URL}/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\"}" | \
        python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null || echo "")
    
    if [ -n "$TOKEN" ]; then
        curl -s -X GET "${API_URL}/api/backup/export" \
            -H "Authorization: Bearer $TOKEN" \
            -o "${BACKUP_DIR}/backup_api_${DATE}.json" 2>/dev/null
        
        if [ -f "${BACKUP_DIR}/backup_api_${DATE}.json" ] && [ -s "${BACKUP_DIR}/backup_api_${DATE}.json" ]; then
            gzip "${BACKUP_DIR}/backup_api_${DATE}.json"
            log "✅ Backup API: backup_api_${DATE}.json.gz"
        else
            log "⚠️ Backup via API falhou ou arquivo vazio"
            rm -f "${BACKUP_DIR}/backup_api_${DATE}.json"
        fi
    else
        log "⚠️ Não foi possível autenticar para backup via API"
    fi
else
    log "⚠️ ADMIN_EMAIL/ADMIN_PASSWORD não configurados"
fi

# 2. Backup dos arquivos de upload
log "Fazendo backup dos uploads..."
UPLOADS_DIR="${BACKEND_DIR}/uploads"
if [ -d "$UPLOADS_DIR" ] && [ "$(ls -A $UPLOADS_DIR 2>/dev/null)" ]; then
    tar -czf "${BACKUP_DIR}/uploads_${DATE}.tar.gz" -C "${BACKEND_DIR}" uploads 2>/dev/null
    log "✅ Backup uploads: uploads_${DATE}.tar.gz"
else
    log "ℹ️ Nenhum arquivo de upload para backup"
fi

# 3. Backup das configurações (.env)
log "Fazendo backup das configurações..."
if [ -f "${BACKEND_DIR}/.env" ]; then
    cp "${BACKEND_DIR}/.env" "${BACKUP_DIR}/env_backup_${DATE}.txt"
    log "✅ Backup .env: env_backup_${DATE}.txt"
fi

# 4. Limpeza de backups antigos
log "Limpando backups com mais de $MAX_BACKUPS dias..."
find "$BACKUP_DIR" -name "backup_api_*.json.gz" -mtime +$MAX_BACKUPS -delete 2>/dev/null
find "$BACKUP_DIR" -name "uploads_*.tar.gz" -mtime +$MAX_BACKUPS -delete 2>/dev/null
find "$BACKUP_DIR" -name "env_backup_*.txt" -mtime +$MAX_BACKUPS -delete 2>/dev/null

# 5. Estatísticas
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR" 2>/dev/null | wc -l)

log "========== Backup concluído =========="
log "Total de arquivos: $BACKUP_COUNT"
log "Tamanho total: $BACKUP_SIZE"
log ""

# Listar backups
log "Backups disponíveis:"
ls -lh "$BACKUP_DIR"/ 2>/dev/null | tail -10 | while read line; do
    log "  $line"
done

exit 0
