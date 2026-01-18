"""
Planejamento Acaiaca - Sistema de Gestão Municipal
Módulo de Logging Centralizado
"""
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Optional
import os

# Diretório de logs
LOG_DIR = Path("/app/backend/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

class JSONFormatter(logging.Formatter):
    """Formatter que gera logs em JSON estruturado"""
    
    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Adicionar exception info se houver
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        # Adicionar campos extras
        if hasattr(record, 'user_id'):
            log_record["user_id"] = record.user_id
        if hasattr(record, 'request_id'):
            log_record["request_id"] = record.request_id
        if hasattr(record, 'endpoint'):
            log_record["endpoint"] = record.endpoint
        if hasattr(record, 'method'):
            log_record["method"] = record.method
        if hasattr(record, 'status_code'):
            log_record["status_code"] = record.status_code
        if hasattr(record, 'duration_ms'):
            log_record["duration_ms"] = record.duration_ms
            
        return json.dumps(log_record, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Formatter com cores para console"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    app_name: str = "planejamento_acaiaca",
    log_level: str = "INFO",
    json_logs: bool = True,
    log_to_file: bool = True
) -> logging.Logger:
    """
    Configura logging centralizado para a aplicação
    
    Args:
        app_name: Nome da aplicação para o logger
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Se True, usa formato JSON para arquivos
        log_to_file: Se True, salva logs em arquivo
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Limpar handlers existentes
    logger.handlers = []
    
    # Console Handler (colorido)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_format = ColoredFormatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File Handler (JSON)
    if log_to_file:
        log_file = LOG_DIR / f"{app_name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        if json_logs:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_format = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(name)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s'
            )
            file_handler.setFormatter(file_format)
        
        logger.addHandler(file_handler)
        
        # Error log separado
        error_file = LOG_DIR / f"{app_name}_errors_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.FileHandler(error_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter() if json_logs else file_format)
        logger.addHandler(error_handler)
    
    return logger


class RequestLogger:
    """Logger para requisições HTTP com contexto"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        extra: Optional[dict] = None
    ):
        """Loga uma requisição HTTP"""
        record = self.logger.makeRecord(
            self.logger.name,
            logging.INFO if status_code < 400 else logging.WARNING if status_code < 500 else logging.ERROR,
            "",
            0,
            f"{method} {path} - {status_code} ({duration_ms:.2f}ms)",
            (),
            None
        )
        record.method = method
        record.endpoint = path
        record.status_code = status_code
        record.duration_ms = duration_ms
        if user_id:
            record.user_id = user_id
        if request_id:
            record.request_id = request_id
        if extra:
            for key, value in extra.items():
                setattr(record, key, value)
        
        self.logger.handle(record)
    
    def log_error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        user_id: Optional[str] = None,
        extra: Optional[dict] = None
    ):
        """Loga um erro"""
        self.logger.error(
            message,
            exc_info=exception is not None,
            extra={
                'user_id': user_id,
                **(extra or {})
            }
        )
    
    def log_audit(
        self,
        action: str,
        user_id: str,
        resource_type: str,
        resource_id: str,
        details: Optional[dict] = None
    ):
        """Loga uma ação de auditoria"""
        self.logger.info(
            f"AUDIT: {action} on {resource_type}:{resource_id} by user {user_id}",
            extra={
                'user_id': user_id,
                'action': action,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'details': details
            }
        )


# Criar logger global
app_logger = setup_logging()
request_logger = RequestLogger(app_logger)

# Exportar funções de conveniência
def get_logger(name: str = None) -> logging.Logger:
    """Obtém um logger com o nome especificado"""
    if name:
        return logging.getLogger(f"planejamento_acaiaca.{name}")
    return app_logger


def log_info(message: str, **kwargs):
    """Log de informação"""
    app_logger.info(message, extra=kwargs)


def log_warning(message: str, **kwargs):
    """Log de aviso"""
    app_logger.warning(message, extra=kwargs)


def log_error(message: str, exception: Exception = None, **kwargs):
    """Log de erro"""
    app_logger.error(message, exc_info=exception is not None, extra=kwargs)


def log_debug(message: str, **kwargs):
    """Log de debug"""
    app_logger.debug(message, extra=kwargs)
