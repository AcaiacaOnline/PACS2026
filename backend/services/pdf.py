"""
PDF Service - Funções de geração de PDF
"""
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from io import BytesIO
from datetime import datetime
import logging

def get_professional_styles():
    """Retorna estilos profissionais para relatórios PDF"""
    styles = getSampleStyleSheet()
    
    cor_primaria = colors.HexColor('#1F4E78')
    cor_secundaria = colors.HexColor('#2E75B6')
    cor_destaque = colors.HexColor('#FFC000')
    cor_texto = colors.HexColor('#333333')
    cor_subtexto = colors.HexColor('#666666')
    
    custom_styles = {
        'title': ParagraphStyle(
            'ProfTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=cor_primaria,
            alignment=TA_CENTER,
            spaceAfter=4,
            fontName='Helvetica-Bold',
            leading=22
        ),
        'subtitle': ParagraphStyle(
            'ProfSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=cor_primaria,
            alignment=TA_CENTER,
            spaceAfter=3,
            fontName='Helvetica-Bold'
        ),
        'section_header': ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading3'],
            fontSize=11,
            textColor=cor_primaria,
            alignment=TA_LEFT,
            spaceAfter=6,
            spaceBefore=12,
            fontName='Helvetica-Bold',
            borderPadding=4
        ),
        'body': ParagraphStyle(
            'ProfBody',
            parent=styles['Normal'],
            fontSize=10,
            textColor=cor_texto,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            leading=14
        ),
        'small': ParagraphStyle(
            'ProfSmall',
            parent=styles['Normal'],
            fontSize=8,
            textColor=cor_subtexto,
            alignment=TA_LEFT,
            spaceAfter=2
        ),
        'legal': ParagraphStyle(
            'Legal',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique',
            spaceAfter=8
        ),
        'footer': ParagraphStyle(
            'ProfFooter',
            parent=styles['Normal'],
            fontSize=7,
            textColor=colors.grey,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        ),
        'table_cell': ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontSize=7,
            textColor=cor_texto,
            alignment=TA_LEFT,
            leading=9
        ),
        'table_header': ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontSize=7,
            textColor=colors.white,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
    }
    
    return custom_styles, cor_primaria, cor_secundaria, cor_destaque

def create_footer_text():
    """Cria texto de rodapé padrão"""
    return f'<font size=7><i>Documento gerado pelo Sistema PAC Acaiaca em {datetime.now().strftime("%d/%m/%Y às %H:%M")} | Desenvolvido por Cristiano Abdo de Souza</i></font>'
