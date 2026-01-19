"""
PDF Utilities - Funções para geração e manipulação de PDFs
Planejamento Acaiaca - Sistema de Gestão Municipal
"""
import uuid
import logging
import hashlib
from io import BytesIO
from datetime import datetime, timezone
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


def mask_cpf(cpf: str) -> str:
    """Mascara o CPF para exibição (LGPD): ***456.789-**"""
    import re
    if not cpf:
        return "***.***.***-**"
    # Remove formatação
    cpf_clean = re.sub(r'[^\d]', '', cpf)
    if len(cpf_clean) != 11:
        return "***.***.***-**"
    # Exibe apenas os dígitos centrais: ***456.789-**
    return f"***{cpf_clean[3:6]}.{cpf_clean[6:9]}-**"


def generate_validation_code() -> str:
    """Gera código único para validação de documento"""
    return f"DOC-{uuid.uuid4().hex[:8].upper()}-{datetime.now().strftime('%Y%m%d')}"


def get_professional_styles():
    """Retorna estilos profissionais para relatórios PDF"""
    styles = getSampleStyleSheet()
    
    # Título principal
    styles.add(ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a365d')
    ))
    
    # Subtítulo
    styles.add(ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=12,
        spaceBefore=15,
        textColor=colors.HexColor('#2d3748'),
        borderPadding=5,
        backColor=colors.HexColor('#f7fafc')
    ))
    
    # Corpo do texto
    styles.add(ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8,
        alignment=TA_JUSTIFY
    ))
    
    # Texto pequeno
    styles.add(ParagraphStyle(
        'SmallText',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#718096')
    ))
    
    # Cabeçalho de tabela
    styles.add(ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.white,
        alignment=TA_CENTER
    ))
    
    # Célula de tabela
    styles.add(ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_LEFT
    ))
    
    return styles


def draw_signature_seal(canvas, page_width, page_height, signers: list, validation_code: str, qr_code_url: str = None, signature_date: str = None):
    """
    Desenha o selo de assinatura digital na LATERAL DIREITA da página.
    Layout profissional: QR Code no topo + 3 linhas de texto vertical vermelho.
    
    Args:
        canvas: Canvas do reportlab
        page_width: Largura da página
        page_height: Altura da página
        signers: Lista de dicts com dados dos assinantes (nome, cpf, cargo)
        validation_code: Código para validação do documento
        qr_code_url: URL para o QR Code de validação (opcional)
        signature_date: Data da assinatura (formato DD/MM/YYYY HH:MM:SS)
    """
    from reportlab.lib.utils import ImageReader
    import qrcode
    
    # Cor vermelho oficial
    VERMELHO = colors.HexColor("#DC2626")
    
    # Usar a data da assinatura fornecida ou a atual
    if signature_date:
        data_assinatura = signature_date
    else:
        data_assinatura = datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S')
    
    # Preparar dados do assinante
    if signers:
        nome = signers[0].get('nome', 'N/A').upper()
        cpf = signers[0].get('cpf', '')
        cargo = signers[0].get('cargo', '')
        cpf_masked = mask_cpf(cpf)
    else:
        nome = 'N/A'
        cpf_masked = '***.***.***-**'
        cargo = ''
    
    # ===== CONFIGURAÇÕES DE LAYOUT =====
    margin_right = 3 * mm
    qr_size = 14 * mm
    qr_x = page_width - qr_size - margin_right - 1*mm
    qr_y = page_height - qr_size - 10 * mm
    
    # ===== DESENHAR QR CODE =====
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
            logging.error(f"Erro ao gerar QR Code: {e}")
    
    # ===== PREPARAR AS 3 LINHAS DE TEXTO =====
    texto_linha1 = f"ASSINADO DIGITALMENTE: {nome}"
    if cargo:
        texto_linha1 += f" ({cargo})"
    
    texto_linha2 = f"CPF: {cpf_masked} • Data: {data_assinatura}"
    texto_linha3 = f"Código: {validation_code} • Valide: pac.acaiaca.mg.gov.br/validar"
    
    # ===== POSIÇÕES DAS 3 LINHAS VERTICAIS =====
    font_size = 5.5
    line_spacing = 3 * mm
    
    x1 = page_width - margin_right - 1 * mm
    x2 = x1 - line_spacing
    x3 = x2 - line_spacing
    
    start_y = qr_y - 3 * mm
    
    # ===== DESENHAR LINHA 1 =====
    canvas.saveState()
    canvas.translate(x1, start_y)
    canvas.rotate(-90)
    canvas.setFillColor(VERMELHO)
    canvas.setFont("Helvetica-Bold", font_size)
    canvas.drawString(0, 0, texto_linha1)
    canvas.restoreState()
    
    # ===== DESENHAR LINHA 2 =====
    canvas.saveState()
    canvas.translate(x2, start_y)
    canvas.rotate(-90)
    canvas.setFillColor(VERMELHO)
    canvas.setFont("Helvetica", font_size)
    canvas.drawString(0, 0, texto_linha2)
    canvas.restoreState()
    
    # ===== DESENHAR LINHA 3 =====
    canvas.saveState()
    canvas.translate(x3, start_y)
    canvas.rotate(-90)
    canvas.setFillColor(VERMELHO)
    canvas.setFont("Helvetica", font_size)
    canvas.drawString(0, 0, texto_linha3)
    canvas.restoreState()


def create_signature_page_mrosc(signers: list, validation_code: str, doc_info: dict = None) -> BytesIO:
    """
    Cria uma página de assinaturas no estilo do documento de referência (Lei 14.063).
    """
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.utils import ImageReader
    import qrcode
    
    buffer = BytesIO()
    c = pdf_canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4
    
    # Cores
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
    
    # Linha separadora
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
            c.setFont("Helvetica-Bold", 12)
            c.setFillColor(azul_escuro)
            c.drawCentredString(page_width/2, page_height - 40, "ASSINATURAS ELETRÔNICAS (continuação)")
            current_y = page_height - 80
            y = current_y - row * (block_height + 20)
        
        # Borda do bloco
        c.setStrokeColor(cinza_claro)
        c.setLineWidth(0.5)
        c.roundRect(x, y - block_height + 20, block_width, block_height, 5, stroke=1, fill=0)
        
        # Selo circular
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
            c.drawImage(ImageReader(qr_buffer), x + block_width - qr_size - 15, y - qr_size - 5, 
                       width=qr_size, height=qr_size)
        except Exception as e:
            logging.error(f"Erro ao gerar QR Code: {e}")
        
        # Nome do assinante
        c.setFillColor(azul_escuro)
        c.setFont("Helvetica-Bold", 9)
        nome = signer.get('nome', 'N/A')
        if len(nome) > 30:
            nome = nome[:27] + "..."
        c.drawString(x + 45, y - 15, nome.upper())
        
        # Cargo
        c.setFillColor(cinza)
        c.setFont("Helvetica", 7)
        cargo = signer.get('cargo', '')
        if len(cargo) > 35:
            cargo = cargo[:32] + "..."
        c.drawString(x + 45, y - 28, cargo)
        
        # Data/hora
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 7)
        data_hora = signer.get('data_hora', datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S'))
        c.drawString(x + 10, y - 55, f"em {data_hora}")
        
        # Código de autenticidade
        c.setFillColor(verde)
        c.setFont("Helvetica", 6)
        signer_code = f"{validation_code[:4]}.{uuid.uuid4().hex[:4].upper()}.{uuid.uuid4().hex[:4].upper()}"
        c.drawString(x + 10, y - 70, f"Cód. Autenticidade da Assinatura: {signer_code}")
        
        # Fundamento legal
        c.setFillColor(cinza)
        c.setFont("Helvetica-Oblique", 6)
        c.drawString(x + 10, y - 85, "Com fundamento na Lei Nº 14.063,")
        c.drawString(x + 10, y - 93, "de 23 de Setembro de 2020.")
    
    # Informações do documento no rodapé
    c.setStrokeColor(cinza_claro)
    c.line(50, 120, page_width - 50, 120)
    
    c.setFillColor(azul_escuro)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 100, "Informações do Documento")
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8)
    
    doc_tipo = doc_info.get('tipo', 'PRESTAÇÃO DE CONTAS') if doc_info else 'PRESTAÇÃO DE CONTAS'
    doc_id = doc_info.get('id', validation_code) if doc_info else validation_code
    doc_titulo = doc_info.get('titulo', 'Relatório de Prestação de Contas MROSC') if doc_info else 'Relatório de Prestação de Contas MROSC'
    
    c.drawString(50, 85, f"ID do Documento: {doc_id}")
    c.drawString(50, 73, f"Tipo: {doc_tipo}")
    c.drawString(50, 61, f"Título: {doc_titulo[:60]}{'...' if len(doc_titulo) > 60 else ''}")
    c.drawString(50, 49, f"Data de Elaboração: {datetime.now(timezone.utc).strftime('%d/%m/%Y às %H:%M:%S')}")
    
    c.setFillColor(verde)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(50, 33, f"Código de Autenticidade deste Documento: {validation_code}")
    
    c.setFillColor(azul_medio)
    c.setFont("Helvetica", 7)
    c.drawString(50, 20, "Verifique a autenticidade em: https://pac.acaiaca.mg.gov.br/validar")
    
    c.save()
    buffer.seek(0)
    return buffer
