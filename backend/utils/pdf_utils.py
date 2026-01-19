"""
PDF Utilities - Sistema de Gestão Municipal de Acaiaca
Geração de PDFs no formato DOEM (Diário Oficial Eletrônico Municipal)
"""
import uuid
import logging
import hashlib
import os
from io import BytesIO
from pathlib import Path
from datetime import datetime, timezone
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdf_canvas

# Diretório raiz do backend
BACKEND_DIR = Path(__file__).parent.parent

# Cor azul escuro padrão (usado em todo o layout)
AZUL_DOEM = colors.HexColor('#000080')  # Navy blue

# Informações institucionais
PREFEITURA_INFO = {
    'nome': 'ACAIACA',
    'cnpj': '18.295.287/0001-90',
    'endereco': 'Praça Tancredo Neves, Número 35, Centro de Acaiaca - MG',
    'cep': 'CEP: 35.438-000',
    'telefone': '(31) 3887-1650',
    'portal': 'https://acaiaca.mg.gov.br',
    'email': 'administracao@acaiaca.mg.gov.br',
    'doem_url': 'https://pac.acaiaca.mg.gov.br/doem'
}

# Caminho para o brasão
BRASAO_PATH = BACKEND_DIR / 'static' / 'brasao_acaiaca.png'


def get_brasao_path():
    """Retorna o caminho do brasão se existir"""
    if BRASAO_PATH.exists():
        return str(BRASAO_PATH)
    return None


def mask_cpf(cpf: str) -> str:
    """Mascara CPF: ***999.456-**"""
    import re
    if not cpf:
        return "***.***.***-**"
    cpf_clean = re.sub(r'[^\d]', '', cpf)
    if len(cpf_clean) != 11:
        return "***.***.***-**"
    return f"***{cpf_clean[3:6]}.{cpf_clean[6:9]}-**"


def generate_validation_code() -> str:
    """Gera código de validação único"""
    return f"DOC-{uuid.uuid4().hex[:8].upper()}-{datetime.now().strftime('%Y%m%d')}"


def format_data_extenso(data=None):
    """Formata: Acaiaca, Sábado, 17 de Janeiro de 2026."""
    dias = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
    meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    
    if data is None:
        data = datetime.now()
    elif isinstance(data, str):
        try:
            data = datetime.fromisoformat(data.replace('Z', '+00:00'))
        except:
            data = datetime.now()
    
    return f"Acaiaca, {dias[data.weekday()]}, {data.day} de {meses[data.month - 1]} de {data.year}."


class DOEMTemplate:
    """
    Template DOEM para geração de PDFs padronizados.
    Cabeçalho: Brasões + ACAIACA + Linha + Info publicação + Linha
    Rodapé: Informações da prefeitura centralizadas
    """
    
    def __init__(self, titulo="DOCUMENTO", ano=134, numero=1, paginas=1, data=None):
        self.titulo = titulo
        self.ano = ano
        self.numero = numero
        self.paginas = paginas
        self.data = data or datetime.now()
        self.page_count = 0
    
    def header_footer(self, canvas, doc):
        """Desenha cabeçalho e rodapé em cada página"""
        canvas.saveState()
        self._draw_header(canvas, doc)
        self._draw_footer(canvas, doc)
        canvas.restoreState()
    
    def _draw_header(self, canvas, doc):
        """Desenha o cabeçalho no estilo DOEM"""
        page_width, page_height = doc.pagesize
        self.page_count += 1
        
        # Posições
        header_top = page_height - 12*mm
        brasao_size = 22*mm
        
        # ===== BRASÕES NAS LATERAIS =====
        brasao = get_brasao_path()
        if brasao:
            try:
                # Brasão esquerdo
                canvas.drawImage(
                    brasao,
                    doc.leftMargin,
                    header_top - brasao_size,
                    width=brasao_size,
                    height=brasao_size,
                    preserveAspectRatio=True,
                    mask='auto'
                )
                # Brasão direito
                canvas.drawImage(
                    brasao,
                    page_width - doc.rightMargin - brasao_size,
                    header_top - brasao_size,
                    width=brasao_size,
                    height=brasao_size,
                    preserveAspectRatio=True,
                    mask='auto'
                )
            except Exception as e:
                logging.warning(f"Erro ao carregar brasão: {e}")
        
        # ===== TEXTO "ACAIACA" CENTRALIZADO =====
        canvas.setFillColor(AZUL_DOEM)
        canvas.setFont("Times-Bold", 32)
        canvas.drawCentredString(page_width / 2, header_top - 18*mm, "ACAIACA")
        
        # ===== LINHA AZUL FINA =====
        linha1_y = header_top - 24*mm
        canvas.setStrokeColor(AZUL_DOEM)
        canvas.setLineWidth(1)
        canvas.line(doc.leftMargin + 5*mm, linha1_y, page_width - doc.rightMargin - 5*mm, linha1_y)
        
        # ===== INFORMAÇÕES DE PUBLICAÇÃO =====
        info_y = linha1_y - 5*mm
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(AZUL_DOEM)
        
        # URL à esquerda
        canvas.drawString(doc.leftMargin + 5*mm, info_y, PREFEITURA_INFO['doem_url'])
        
        # ANO - Nº - PÁGINAS centralizado
        info_centro = f"ANO {self.ano} - Nº {self.numero} - {self.paginas} PÁGINAS"
        canvas.drawCentredString(page_width / 2, info_y, info_centro)
        
        # Data à direita
        data_texto = format_data_extenso(self.data)
        canvas.drawRightString(page_width - doc.rightMargin - 5*mm, info_y, data_texto)
        
        # ===== LINHA AZUL GROSSA =====
        linha2_y = info_y - 5*mm
        canvas.setLineWidth(3)
        canvas.line(doc.leftMargin, linha2_y, page_width - doc.rightMargin, linha2_y)
        
        # ===== TÍTULO DO DOCUMENTO =====
        if self.titulo:
            canvas.setFont("Helvetica-Bold", 11)
            canvas.setFillColor(AZUL_DOEM)
            canvas.drawCentredString(page_width / 2, linha2_y - 8*mm, self.titulo)
    
    def _draw_footer(self, canvas, doc):
        """Desenha o rodapé padronizado"""
        page_width, page_height = doc.pagesize
        
        footer_y = 18*mm
        
        # Linha separadora
        canvas.setStrokeColor(colors.HexColor('#CCCCCC'))
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, footer_y + 12*mm, page_width - doc.rightMargin, footer_y + 12*mm)
        
        # Textos do rodapé em azul
        canvas.setFillColor(AZUL_DOEM)
        canvas.setFont("Helvetica", 8)
        
        # Linha 1: Prefeitura | CNPJ
        linha1 = f"Prefeitura Municipal de Acaiaca - MG | CNPJ: {PREFEITURA_INFO['cnpj']}"
        canvas.drawCentredString(page_width / 2, footer_y + 6*mm, linha1)
        
        # Linha 2: Endereço, CEP
        linha2 = f"{PREFEITURA_INFO['endereco']}, {PREFEITURA_INFO['cep']}"
        canvas.drawCentredString(page_width / 2, footer_y + 1*mm, linha2)
        
        # Linha 3: Tel | Portal | Email
        linha3 = f"Tel.: {PREFEITURA_INFO['telefone']} | Portal: {PREFEITURA_INFO['portal']} | E-mail: {PREFEITURA_INFO['email']}"
        canvas.drawCentredString(page_width / 2, footer_y - 4*mm, linha3)
        
        # Número da página à direita
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(page_width - doc.rightMargin, footer_y - 4*mm, f"Página {self.page_count}")


def create_doem_callback(titulo="DOCUMENTO", ano=134, numero=1, paginas=1, data=None):
    """
    Cria callback para cabeçalho/rodapé DOEM.
    
    Uso:
        callback = create_doem_callback(titulo="MEU RELATÓRIO", ...)
        doc.build(elements, onFirstPage=callback, onLaterPages=callback)
    """
    template = DOEMTemplate(titulo=titulo, ano=ano, numero=numero, paginas=paginas, data=data)
    return template.header_footer


# ===== FUNÇÕES AUXILIARES =====

def get_professional_styles():
    """Retorna estilos para relatórios"""
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=15,
        alignment=TA_CENTER,
        textColor=AZUL_DOEM
    ))
    
    styles.add(ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=11,
        spaceAfter=10,
        spaceBefore=12,
        textColor=colors.HexColor('#333333')
    ))
    
    styles.add(ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=6,
        alignment=TA_JUSTIFY
    ))
    
    styles.add(ParagraphStyle(
        'SmallText',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.HexColor('#666666')
    ))
    
    return styles


def draw_signature_seal(canvas, page_width, page_height, signers: list, validation_code: str, qr_code_url: str = None, signature_date: str = None):
    """
    Desenha selo de assinatura digital na lateral direita.
    """
    import qrcode
    
    VERMELHO = colors.HexColor("#DC2626")
    
    if signature_date:
        data_assinatura = signature_date
    else:
        data_assinatura = datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S')
    
    if signers:
        nome = signers[0].get('nome', 'N/A').upper()
        cpf = signers[0].get('cpf', '')
        cargo = signers[0].get('cargo', '')
        cpf_masked = mask_cpf(cpf)
    else:
        nome = 'N/A'
        cpf_masked = '***.***.***-**'
        cargo = ''
    
    # QR Code
    margin_right = 3*mm
    qr_size = 14*mm
    qr_x = page_width - qr_size - margin_right - 1*mm
    qr_y = page_height - qr_size - 10*mm
    
    if qr_code_url:
        try:
            qr = qrcode.QRCode(version=1, box_size=3, border=1)
            qr.add_data(qr_code_url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="#DC2626", back_color="#FFFFFF")
            
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            
            canvas.drawImage(ImageReader(qr_buffer), qr_x, qr_y, width=qr_size, height=qr_size)
        except Exception as e:
            logging.error(f"Erro QR Code: {e}")
    
    # Textos verticais
    texto1 = f"ASSINADO DIGITALMENTE: {nome}"
    if cargo:
        texto1 += f" ({cargo})"
    texto2 = f"CPF: {cpf_masked} • Data: {data_assinatura}"
    texto3 = f"Código: {validation_code} • Valide: pac.acaiaca.mg.gov.br/validar"
    
    font_size = 5.5
    line_spacing = 3*mm
    x1 = page_width - margin_right - 1*mm
    start_y = qr_y - 3*mm
    
    for idx, (x_offset, texto, bold) in enumerate([
        (0, texto1, True),
        (line_spacing, texto2, False),
        (line_spacing * 2, texto3, False)
    ]):
        canvas.saveState()
        canvas.translate(x1 - x_offset, start_y)
        canvas.rotate(-90)
        canvas.setFillColor(VERMELHO)
        canvas.setFont("Helvetica-Bold" if bold else "Helvetica", font_size)
        canvas.drawString(0, 0, texto)
        canvas.restoreState()


def create_signature_page_mrosc(signers: list, validation_code: str, doc_info: dict = None) -> BytesIO:
    """Cria página de assinaturas Lei 14.063"""
    import qrcode
    
    buffer = BytesIO()
    c = pdf_canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4
    
    azul_escuro = colors.HexColor("#1a365d")
    azul_medio = colors.HexColor("#2563eb")
    verde = colors.HexColor("#059669")
    cinza = colors.HexColor("#6b7280")
    cinza_claro = colors.HexColor("#e5e7eb")
    
    # Cabeçalho
    c.setFillColor(azul_escuro)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(page_width/2, page_height - 40, "ASSINATURAS ELETRÔNICAS")
    
    c.setFillColor(cinza)
    c.setFont("Helvetica", 9)
    c.drawCentredString(page_width/2, page_height - 55, "Com fundamento na Lei Nº 14.063, de 23 de Setembro de 2020")
    
    c.setStrokeColor(cinza_claro)
    c.setLineWidth(1)
    c.line(50, page_height - 65, page_width - 50, page_height - 65)
    
    # Blocos de assinatura
    current_y = page_height - 100
    block_width = 230
    block_height = 130
    margin = 30
    blocks_per_row = 2
    start_x = (page_width - (blocks_per_row * block_width + (blocks_per_row - 1) * margin)) / 2
    
    for i, signer in enumerate(signers):
        col = i % blocks_per_row
        row = i // blocks_per_row
        
        x = start_x + col * (block_width + margin)
        y = current_y - row * (block_height + 20)
        
        if y < 150:
            c.showPage()
            current_y = page_height - 80
            y = current_y
        
        c.setStrokeColor(cinza_claro)
        c.setLineWidth(0.5)
        c.roundRect(x, y - block_height + 20, block_width, block_height, 5, stroke=1, fill=0)
        
        # Selo
        seal_x = x + 15
        seal_y = y - 25
        c.setStrokeColor(azul_medio)
        c.setLineWidth(1.5)
        c.circle(seal_x, seal_y, 18, stroke=1, fill=0)
        c.circle(seal_x, seal_y, 14, stroke=1, fill=0)
        
        c.setFillColor(azul_medio)
        c.setFont("Helvetica-Bold", 4)
        c.drawCentredString(seal_x, seal_y + 5, "Lei Federal")
        c.drawCentredString(seal_x, seal_y + 1, "14.063")
        c.setFont("Helvetica", 3.5)
        c.drawCentredString(seal_x, seal_y - 4, "ASSINATURA")
        c.drawCentredString(seal_x, seal_y - 7.5, "ELETRÔNICA")
        
        # QR Code
        try:
            qr_url = f"https://pac.acaiaca.mg.gov.br/validar?code={validation_code}"
            qr = qrcode.QRCode(version=1, box_size=2, border=1)
            qr.add_data(qr_url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="#1a365d", back_color="#ffffff")
            
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            
            qr_size = 35
            c.drawImage(ImageReader(qr_buffer), x + block_width - qr_size - 15, y - qr_size - 5, width=qr_size, height=qr_size)
        except:
            pass
        
        # Nome
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 9)
        nome = signer.get('nome', 'N/A')[:30]
        c.drawString(x + 45, y - 15, nome.upper())
        
        # Cargo
        c.setFillColor(cinza)
        c.setFont("Helvetica", 7)
        cargo = signer.get('cargo', '')[:35]
        c.drawString(x + 45, y - 28, cargo)
        
        # Data
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 7)
        data_hora = signer.get('data_hora', datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S'))
        c.drawString(x + 10, y - 55, f"em {data_hora}")
        
        # Código
        c.setFillColor(verde)
        c.setFont("Helvetica", 6)
        signer_code = f"{validation_code[:4]}.{uuid.uuid4().hex[:4].upper()}.{uuid.uuid4().hex[:4].upper()}"
        c.drawString(x + 10, y - 70, f"Cód. Autenticidade: {signer_code}")
        
        c.setFillColor(cinza)
        c.setFont("Helvetica-Oblique", 6)
        c.drawString(x + 10, y - 85, "Lei Nº 14.063/2020")
    
    # Info do documento
    c.setStrokeColor(cinza_claro)
    c.line(50, 120, page_width - 50, 120)
    
    c.setFillColor(azul_escuro)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 100, "Informações do Documento")
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8)
    
    doc_tipo = doc_info.get('tipo', 'DOCUMENTO') if doc_info else 'DOCUMENTO'
    doc_id = doc_info.get('id', validation_code) if doc_info else validation_code
    doc_titulo = doc_info.get('titulo', 'Documento') if doc_info else 'Documento'
    
    c.drawString(50, 85, f"ID: {doc_id}")
    c.drawString(50, 73, f"Tipo: {doc_tipo}")
    c.drawString(50, 61, f"Título: {doc_titulo[:60]}")
    c.drawString(50, 49, f"Data: {datetime.now(timezone.utc).strftime('%d/%m/%Y às %H:%M:%S')}")
    
    c.setFillColor(verde)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(50, 33, f"Código: {validation_code}")
    
    c.setFillColor(azul_medio)
    c.setFont("Helvetica", 7)
    c.drawString(50, 20, "Verifique: https://pac.acaiaca.mg.gov.br/validar")
    
    c.save()
    buffer.seek(0)
    return buffer


# Aliases para compatibilidade
def create_page_callback(titulo_documento="DOCUMENTO", subtitulo=None, **kwargs):
    """Alias para create_doem_callback"""
    titulo = titulo_documento
    if subtitulo:
        titulo = f"{titulo_documento}"
    return create_doem_callback(
        titulo=titulo,
        ano=kwargs.get('ano', 134),
        numero=kwargs.get('numero_edicao', 1),
        paginas=kwargs.get('num_paginas', kwargs.get('total_pages', 1)),
        data=kwargs.get('data_publicacao', None)
    )

def create_header_elements(styles, title=None, subtitle=None, **kwargs):
    """Compatibilidade - retorna lista vazia pois o cabeçalho é via callback"""
    return [Spacer(1, 5*mm)]

def create_doem_header_elements(styles, titulo_documento="DOCUMENTO", **kwargs):
    """Compatibilidade - retorna lista vazia"""
    return [Spacer(1, 5*mm)]
