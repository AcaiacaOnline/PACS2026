"""
Shared Functions - Funções compartilhadas entre módulos
Planejamento Acaiaca - Sistema de Gestão Municipal
"""
from fastapi import HTTPException, Request
from datetime import datetime, timezone, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import hashlib
import uuid
import jwt
import os

# Configuração JWT
JWT_SECRET = os.environ.get('JWT_SECRET', 'pac-acaiaca-secret-key-2026')
JWT_ALGORITHM = 'HS256'

# Database reference
db = None

def set_database(database):
    """Define a referência global do banco de dados"""
    global db
    db = database


def get_database():
    """Retorna a referência do banco de dados"""
    return db


def truncate_text(text, max_chars=100):
    """Trunca texto longo para evitar overflow no PDF"""
    if not text:
        return ''
    text = str(text)
    if len(text) > max_chars:
        return text[:max_chars-3] + '...'
    return text


def mask_cpf(cpf: str) -> str:
    """Mascara CPF para exibição (XXX.XXX.XXX-XX -> ***.***.XXX-XX)"""
    if not cpf or len(cpf) < 11:
        return cpf
    clean_cpf = ''.join(filter(str.isdigit, cpf))
    if len(clean_cpf) != 11:
        return cpf
    return f"***.***{clean_cpf[6:9]}-{clean_cpf[9:]}"


def generate_validation_code() -> str:
    """Gera código de validação único para documentos assinados"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_part = uuid.uuid4().hex[:8].upper()
    return f"ACAI{timestamp}{random_part}"


async def get_current_user_from_request(request: Request):
    """
    Obtém usuário atual a partir do token JWT no header Authorization.
    Esta função é usada como dependência em rotas protegidas.
    """
    from models import User
    
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get('user_id')
        user_data = await db.users.find_one({'user_id': user_id}, {'_id': 0, 'password_hash': 0})
        
        if not user_data:
            raise HTTPException(status_code=401, detail="User not found")
        if not user_data.get('is_active', True):
            raise HTTPException(status_code=403, detail="User account is disabled")
        
        return User(**user_data)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


def create_pdf_styles():
    """Cria estilos padrão para PDFs"""
    styles = getSampleStyleSheet()
    
    custom_styles = {
        'title': ParagraphStyle(
            'CustomTitle', 
            parent=styles['Heading1'], 
            fontSize=14,
            textColor=colors.HexColor('#1F4788'), 
            spaceAfter=4,
            alignment=TA_CENTER, 
            fontName='Helvetica-Bold'
        ),
        'subtitle': ParagraphStyle(
            'CustomSubtitle', 
            parent=styles['Heading2'], 
            fontSize=11,
            textColor=colors.HexColor('#1F4788'), 
            spaceAfter=6,
            alignment=TA_CENTER, 
            fontName='Helvetica-Bold'
        ),
        'normal': styles['Normal'],
        'footer': ParagraphStyle(
            'Footer', 
            alignment=TA_CENTER, 
            textColor=colors.grey,
            fontSize=8
        )
    }
    
    return custom_styles


def create_table_style(header_color='#1F4788'):
    """Cria estilo padrão para tabelas"""
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(header_color)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('FONTSIZE', (0, 1), (-1, -1), 6),
        ('ALIGN', (0, 1), (2, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ])


def json_serialize(obj):
    """Serializa objetos para JSON (datetime, ObjectId, etc)"""
    from bson import ObjectId
    
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, bytes):
        return obj.decode('utf-8')
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    return str(obj)
