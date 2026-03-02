#!/bin/bash
#============================================================================
# Planejamento Acaiaca - Backup Automático Diário
# Este script deve ser executado via cron job
# 
# Configuração do Cron (cPanel > Cron Jobs):
# 0 3 * * * /home/$USER/planejamento-acaiaca/scripts/daily_backup.sh
#
# Executa todos os dias às 3:00 AM
#============================================================================

set -e

# Configurações
INSTALL_DIR="${HOME}/planejamento-acaiaca"
BACKUP_DIR="${INSTALL_DIR}/backups"
LOG_FILE="${INSTALL_DIR}/backend/logs/backup_cron.log"
MAX_BACKUPS=7  # Manter últimos 7 dias
DATE=$(date +%Y%m%d_%H%M%S)

# Carregar variáveis de ambiente
if [ -f "${INSTALL_DIR}/backend/.env" ]; then
    export $(grep -v '^#' "${INSTALL_DIR}/backend/.env" | xargs)
fi

# Função de log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Criar diretório de backup se não existir
mkdir -p "$BACKUP_DIR"

log "========== Iniciando backup diário =========="

# 1. Backup do MongoDB
log "Fazendo backup do MongoDB..."
MONGO_BACKUP_DIR="${BACKUP_DIR}/mongodb_${DATE}"

if command -v mongodump &> /dev/null; then
    mongodump --uri="$MONGO_URL" --out="$MONGO_BACKUP_DIR" 2>> "$LOG_FILE"
    
    # Compactar backup do MongoDB
    cd "$BACKUP_DIR"
    tar -czf "mongodb_${DATE}.tar.gz" "mongodb_${DATE}"
    rm -rf "$MONGO_BACKUP_DIR"
    log "Backup MongoDB concluído: mongodb_${DATE}.tar.gz"
else
    log "AVISO: mongodump não encontrado. Pulando backup do MongoDB."
fi

# 2. Backup dos arquivos de upload
log "Fazendo backup dos uploads..."
UPLOADS_DIR="${INSTALL_DIR}/backend/uploads"
if [ -d "$UPLOADS_DIR" ] && [ "$(ls -A $UPLOADS_DIR)" ]; then
    tar -czf "${BACKUP_DIR}/uploads_${DATE}.tar.gz" -C "${INSTALL_DIR}/backend" uploads
    log "Backup uploads concluído: uploads_${DATE}.tar.gz"
else
    log "Nenhum arquivo de upload para backup."
fi

# 3. Backup das configurações
log "Fazendo backup das configurações..."
CONFIG_BACKUP="${BACKUP_DIR}/config_${DATE}"
mkdir -p "$CONFIG_BACKUP"
cp "${INSTALL_DIR}/backend/.env" "$CONFIG_BACKUP/" 2>/dev/null || true
cp "${INSTALL_DIR}/frontend/.env" "$CONFIG_BACKUP/" 2>/dev/null || true
tar -czf "${BACKUP_DIR}/config_${DATE}.tar.gz" -C "$BACKUP_DIR" "config_${DATE}"
rm -rf "$CONFIG_BACKUP"
log "Backup configurações concluído: config_${DATE}.tar.gz"

# 4. Backup via API (dados completos em JSON)
log "Fazendo backup via API..."
API_URL="http://127.0.0.1:8001"

# Tentar fazer backup via API (requer autenticação)
if [ -n "$BACKUP_API_TOKEN" ]; then
    curl -s -X GET "${API_URL}/api/backup/export" \
        -H "Authorization: Bearer $BACKUP_API_TOKEN" \
        -o "${BACKUP_DIR}/api_backup_${DATE}.json" 2>> "$LOG_FILE"
    
    if [ -f "${BACKUP_DIR}/api_backup_${DATE}.json" ]; then
        gzip "${BACKUP_DIR}/api_backup_${DATE}.json"
        log "Backup API concluído: api_backup_${DATE}.json.gz"
    fi
else
    log "AVISO: BACKUP_API_TOKEN não configurado. Backup via API pulado."
fi

# 5. Limpar backups antigos
log "Limpando backups antigos (mantendo últimos $MAX_BACKUPS dias)..."
find "$BACKUP_DIR" -name "mongodb_*.tar.gz" -mtime +$MAX_BACKUPS -delete 2>> "$LOG_FILE"
find "$BACKUP_DIR" -name "uploads_*.tar.gz" -mtime +$MAX_BACKUPS -delete 2>> "$LOG_FILE"
find "$BACKUP_DIR" -name "config_*.tar.gz" -mtime +$MAX_BACKUPS -delete 2>> "$LOG_FILE"
find "$BACKUP_DIR" -name "api_backup_*.json.gz" -mtime +$MAX_BACKUPS -delete 2>> "$LOG_FILE"

# 6. Calcular tamanho total dos backups
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log "Tamanho total dos backups: $TOTAL_SIZE"

# 7. Listar backups atuais
log "Backups disponíveis:"
ls -lh "$BACKUP_DIR"/*.tar.gz "$BACKUP_DIR"/*.gz 2>/dev/null | while read line; do
    log "  $line"
done

log "========== Backup diário concluído =========="
log ""

# Opcional: Enviar notificação por email
if [ -n "$ADMIN_EMAIL" ] && command -v mail &> /dev/null; then
    echo "Backup diário do Planejamento Acaiaca concluído em $(date '+%Y-%m-%d %H:%M:%S'). Tamanho total: $TOTAL_SIZE" | \
        mail -s "[Planejamento Acaiaca] Backup Diário Concluído" "$ADMIN_EMAIL"
fi

exit 0
