"""
PDF Utilities - Funções para geração e manipulação de PDFs
Planejamento Acaiaca - Sistema de Gestão Municipal
Estilo baseado no Diário Oficial Eletrônico Municipal
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
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdf_canvas

# Diretório raiz do backend
BACKEND_DIR = Path(__file__).parent.parent

# Cores do tema DOEM
AZUL_ROYAL = colors.HexColor('#1E3A8A')  # Azul royal para texto principal
CINZA_LINHA = colors.HexColor('#D1D5DB')  # Cinza para linha separadora
AZUL_LINK = colors.HexColor('#1E40AF')   # Azul para links

# Informações institucionais padronizadas
PREFEITURA_INFO = {
    'nome': 'ACAIACA',
    'estado': 'ESTADO DE MINAS GERAIS',
    'cnpj': '18.295.287/0001-90',
    'endereco': 'Praça Tancredo Neves, Número 35, Centro de Acaiaca - MG',
    'cep': 'CEP: 35.438-000',
    'telefone': '(31) 3887-1650',
    'portal': 'https://pac.acaiaca.mg.gov.br/doem',
    'email': 'administracao@acaiaca.mg.gov.br'
}

# Caminho para o brasão
BRASAO_PATH = BACKEND_DIR / 'static' / 'brasao_acaiaca.png'


def get_brasao_path():
    """Retorna o caminho do brasão se existir"""
    if BRASAO_PATH.exists():
        return str(BRASAO_PATH)
    return None


def mask_cpf(cpf: str) -> str:
    """Mascara o CPF para exibição (LGPD): ***456.789-**"""
    import re
    if not cpf:
        return "***.***.***-**"
    cpf_clean = re.sub(r'[^\d]', '', cpf)
    if len(cpf_clean) != 11:
        return "***.***.***-**"
    return f"***{cpf_clean[3:6]}.{cpf_clean[6:9]}-**"


def generate_validation_code() -> str:
    """Gera código único para validação de documento"""
    return f"DOC-{uuid.uuid4().hex[:8].upper()}-{datetime.now().strftime('%Y%m%d')}"


def get_professional_styles():
    """Retorna estilos profissionais para relatórios PDF"""
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a365d')
    ))
    
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
    
    styles.add(ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8,
        alignment=TA_JUSTIFY
    ))
    
    styles.add(ParagraphStyle(
        'SmallText',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#718096')
    ))
    
    styles.add(ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.white,
        alignment=TA_CENTER
    ))
    
    styles.add(ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_LEFT
    ))
    
    return styles


def draw_doem_header(canvas, doc, ano=None, numero_edicao=None, num_paginas=None, data_publicacao=None, titulo_documento=None):
    """
    Desenha o cabeçalho no estilo DOEM (Diário Oficial Eletrônico Municipal)
    Com brasão espelhado nas laterais e "ACAIACA" em azul grande no centro.
    
    Args:
        canvas: Canvas do reportlab
        doc: Documento SimpleDocTemplate
        ano: Ano da publicação (ex: 134)
        numero_edicao: Número da edição (ex: 10)
        num_paginas: Total de páginas
        data_publicacao: Data da publicação
        titulo_documento: Título específico do documento (opcional)
    """
    page_width, page_height = doc.pagesize
    
    # Obter número da página atual
    page_num = canvas.getPageNumber()
    
    # Se não tiver ano definido, usar ano atual
    if not ano:
        ano = datetime.now().year
    if not numero_edicao:
        numero_edicao = 1
    if not num_paginas:
        num_paginas = 1
    if not data_publicacao:
        data_publicacao = datetime.now()
    
    # Formatar data
    dias_semana = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
    meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    
    if isinstance(data_publicacao, str):
        try:
            data_publicacao = datetime.fromisoformat(data_publicacao.replace('Z', '+00:00'))
        except:
            data_publicacao = datetime.now()
    
    dia_semana = dias_semana[data_publicacao.weekday()]
    data_formatada = f"Acaiaca, {dia_semana}, {data_publicacao.day} de {meses[data_publicacao.month - 1]} de {data_publicacao.year}."
    
    # ===== CONFIGURAÇÃO DO CABEÇALHO =====
    header_top = page_height - 8*mm
    brasao_size = 25*mm
    
    # ===== DESENHAR BRASÃO ESQUERDO =====
    brasao_path = get_brasao_path()
    if brasao_path:
        try:
            brasao_x_left = doc.leftMargin
            brasao_y = header_top - brasao_size
            canvas.drawImage(
                brasao_path, 
                brasao_x_left, 
                brasao_y, 
                width=brasao_size, 
                height=brasao_size,
                preserveAspectRatio=True,
                mask='auto'
            )
            
            # Brasão direito (espelhado)
            brasao_x_right = page_width - doc.rightMargin - brasao_size
            canvas.drawImage(
                brasao_path, 
                brasao_x_right, 
                brasao_y, 
                width=brasao_size, 
                height=brasao_size,
                preserveAspectRatio=True,
                mask='auto'
            )
        except Exception as e:
            logging.warning(f"Erro ao carregar brasão: {e}")
    
    # ===== TEXTO "ACAIACA" CENTRAL EM AZUL GRANDE =====
    canvas.setFillColor(AZUL_ROYAL)
    canvas.setFont("Helvetica-Bold", 36)
    canvas.drawCentredString(page_width / 2, header_top - 18*mm, "ACAIACA")
    
    # ===== LINHA CINZA SEPARADORA =====
    linha_y = header_top - 28*mm
    canvas.setStrokeColor(CINZA_LINHA)
    canvas.setLineWidth(2)
    canvas.line(doc.leftMargin, linha_y, page_width - doc.rightMargin, linha_y)
    
    # ===== INFORMAÇÕES DE PUBLICAÇÃO =====
    info_y = linha_y - 6*mm
    canvas.setFillColor(AZUL_ROYAL)
    canvas.setFont("Helvetica", 9)
    
    # URL do portal
    canvas.drawString(doc.leftMargin, info_y, PREFEITURA_INFO['portal'])
    
    # Informações centrais
    info_central = f"ANO {ano} - Nº {numero_edicao} - {num_paginas} PÁGINA(S)"
    canvas.drawCentredString(page_width / 2, info_y, info_central)
    
    # Data à direita
    canvas.drawRightString(page_width - doc.rightMargin, info_y, data_formatada)
    
    # ===== LINHA AZUL INFERIOR =====
    linha_azul_y = info_y - 5*mm
    canvas.setStrokeColor(AZUL_ROYAL)
    canvas.setLineWidth(3)
    canvas.line(doc.leftMargin, linha_azul_y, page_width - doc.rightMargin, linha_azul_y)
    
    # ===== TÍTULO DO DOCUMENTO (se fornecido) =====
    if titulo_documento:
        canvas.setFillColor(colors.HexColor('#1F4E78'))
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawCentredString(page_width / 2, linha_azul_y - 8*mm, titulo_documento)


def draw_doem_footer(canvas, doc, page_number=None, total_pages=None):
    """
    Desenha o rodapé padronizado no estilo DOEM.
    
    Args:
        canvas: Canvas do reportlab
        doc: Documento SimpleDocTemplate
        page_number: Número da página atual
        total_pages: Total de páginas
    """
    page_width, page_height = doc.pagesize
    
    # Posição do rodapé
    footer_y = 15*mm
    
    # Linha separadora superior
    canvas.setStrokeColor(CINZA_LINHA)
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, footer_y + 8*mm, page_width - doc.rightMargin, footer_y + 8*mm)
    
    # Informações da prefeitura
    canvas.setFillColor(colors.HexColor('#6B7280'))
    canvas.setFont("Helvetica", 7)
    
    linha1 = f"Prefeitura Municipal de Acaiaca - MG | CNPJ: {PREFEITURA_INFO['cnpj']}"
    linha2 = f"{PREFEITURA_INFO['endereco']}, {PREFEITURA_INFO['cep']}"
    linha3 = f"Tel.: {PREFEITURA_INFO['telefone']} | E-mail: {PREFEITURA_INFO['email']}"
    
    canvas.drawCentredString(page_width / 2, footer_y + 4*mm, linha1)
    canvas.drawCentredString(page_width / 2, footer_y, linha2)
    canvas.drawCentredString(page_width / 2, footer_y - 4*mm, linha3)
    
    # Número da página e data
    if page_number:
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor('#374151'))
        
        # Data de geração à esquerda
        data_geracao = datetime.now().strftime('%d/%m/%Y %H:%M')
        canvas.drawString(doc.leftMargin, footer_y - 4*mm, f"Gerado em: {data_geracao}")
        
        # Página à direita
        page_text = f"Página {page_number}"
        if total_pages:
            page_text = f"Página {page_number} de {total_pages}"
        canvas.drawRightString(page_width - doc.rightMargin, footer_y - 4*mm, page_text)


def create_header_elements(styles, title=None, subtitle=None, show_brasao=True, ano=None, numero_edicao=None, num_paginas=None, data_publicacao=None):
    """
    Cria elementos do cabeçalho DOEM para uso com SimpleDocTemplate.build()
    Retorna uma lista de elementos (Paragraph, Spacer, Table, etc.)
    """
    from reportlab.platypus import HRFlowable
    
    elements = []
    
    # Obter caminho do brasão
    brasao_path = get_brasao_path() if show_brasao else None
    
    # Valores padrão
    if not ano:
        ano = datetime.now().year
    if not numero_edicao:
        numero_edicao = 1
    if not num_paginas:
        num_paginas = 1
    if not data_publicacao:
        data_publicacao = datetime.now()
    
    # Formatar data
    dias_semana = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
    meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    
    if isinstance(data_publicacao, str):
        try:
            data_publicacao = datetime.fromisoformat(data_publicacao.replace('Z', '+00:00'))
        except:
            data_publicacao = datetime.now()
    
    dia_semana = dias_semana[data_publicacao.weekday()]
    data_formatada = f"Acaiaca, {dia_semana}, {data_publicacao.day} de {meses[data_publicacao.month - 1]} de {data_publicacao.year}."
    
    # ===== CABEÇALHO COM BRASÃO E NOME =====
    if brasao_path:
        try:
            brasao_img_left = Image(brasao_path, width=22*mm, height=22*mm)
            brasao_img_right = Image(brasao_path, width=22*mm, height=22*mm)
            
            # Texto central
            nome_style = ParagraphStyle(
                'NomeAcaiaca',
                fontSize=32,
                fontName='Helvetica-Bold',
                textColor=AZUL_ROYAL,
                alignment=TA_CENTER,
                leading=36
            )
            nome_para = Paragraph('ACAIACA', nome_style)
            
            # Tabela com brasão | nome | brasão
            header_table = Table(
                [[brasao_img_left, nome_para, brasao_img_right]],
                colWidths=[30*mm, None, 30*mm]
            )
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            
            elements.append(header_table)
        except Exception as e:
            logging.warning(f"Erro ao criar cabeçalho com brasão: {e}")
            # Fallback
            nome_style = ParagraphStyle(
                'NomeAcaiaca',
                fontSize=32,
                fontName='Helvetica-Bold',
                textColor=AZUL_ROYAL,
                alignment=TA_CENTER
            )
            elements.append(Paragraph('ACAIACA', nome_style))
    else:
        nome_style = ParagraphStyle(
            'NomeAcaiaca',
            fontSize=32,
            fontName='Helvetica-Bold',
            textColor=AZUL_ROYAL,
            alignment=TA_CENTER
        )
        elements.append(Paragraph('ACAIACA', nome_style))
    
    elements.append(Spacer(1, 3*mm))
    
    # ===== LINHA CINZA SEPARADORA =====
    elements.append(HRFlowable(width="100%", thickness=2, color=CINZA_LINHA, spaceBefore=2*mm, spaceAfter=2*mm))
    
    # ===== INFORMAÇÕES DE PUBLICAÇÃO =====
    info_style = ParagraphStyle(
        'InfoPublicacao',
        fontSize=9,
        fontName='Helvetica',
        textColor=AZUL_ROYAL,
        alignment=TA_CENTER
    )
    
    info_text = f"{PREFEITURA_INFO['portal']}    |    ANO {ano} - Nº {numero_edicao} - {num_paginas} PÁGINA(S)    |    {data_formatada}"
    elements.append(Paragraph(info_text, info_style))
    
    # ===== LINHA AZUL INFERIOR =====
    elements.append(HRFlowable(width="100%", thickness=3, color=AZUL_ROYAL, spaceBefore=2*mm, spaceAfter=4*mm))
    
    # ===== TÍTULO DO DOCUMENTO =====
    if title:
        titulo_style = ParagraphStyle(
            'TituloDoc',
            fontSize=14,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1F4E78'),
            alignment=TA_CENTER,
            spaceBefore=4*mm,
            spaceAfter=2*mm
        )
        elements.append(Paragraph(title, titulo_style))
        
        if subtitle:
            subtitulo_style = ParagraphStyle(
                'SubtituloDoc',
                fontSize=10,
                fontName='Helvetica',
                textColor=colors.HexColor('#4A5568'),
                alignment=TA_CENTER,
                spaceAfter=4*mm
            )
            elements.append(Paragraph(subtitle, subtitulo_style))
    
    elements.append(Spacer(1, 4*mm))
    
    return elements


def create_footer_elements(styles=None):
    """
    Cria elementos do rodapé para uso com SimpleDocTemplate.
    """
    from reportlab.platypus import HRFlowable
    
    elements = []
    
    # Linha separadora
    elements.append(Spacer(1, 6*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=CINZA_LINHA, spaceBefore=2*mm, spaceAfter=2*mm))
    
    # Informações
    footer_style = ParagraphStyle(
        'Footer',
        fontSize=7,
        fontName='Helvetica',
        textColor=colors.HexColor('#6B7280'),
        alignment=TA_CENTER,
        leading=10
    )
    
    footer_text = f"""
    Prefeitura Municipal de Acaiaca - MG | CNPJ: {PREFEITURA_INFO['cnpj']}<br/>
    {PREFEITURA_INFO['endereco']}, {PREFEITURA_INFO['cep']}<br/>
    Tel.: {PREFEITURA_INFO['telefone']} | E-mail: {PREFEITURA_INFO['email']}
    """
    
    elements.append(Paragraph(footer_text, footer_style))
    
    return elements


def create_page_callback(show_header=True, show_footer=True, ano=None, numero_edicao=None, num_paginas=None, data_publicacao=None, titulo_documento=None):
    """
    Cria função de callback para cabeçalho/rodapé em todas as páginas.
    
    Uso:
        doc = SimpleDocTemplate(buffer, pagesize=A4, ...)
        callback = create_page_callback(...)
        doc.build(elements, onFirstPage=callback, onLaterPages=callback)
    """
    # Contador de páginas
    page_counter = {'current': 0}
    
    def _header_footer(canvas, doc):
        canvas.saveState()
        page_counter['current'] += 1
        
        if show_header:
            draw_doem_header(
                canvas, doc, 
                ano=ano, 
                numero_edicao=numero_edicao, 
                num_paginas=num_paginas,
                data_publicacao=data_publicacao,
                titulo_documento=titulo_documento
            )
        
        if show_footer:
            draw_doem_footer(canvas, doc, page_number=page_counter['current'], total_pages=num_paginas)
        
        canvas.restoreState()
    
    return _header_footer


def draw_signature_seal(canvas, page_width, page_height, signers: list, validation_code: str, qr_code_url: str = None, signature_date: str = None):
    """
    Desenha o selo de assinatura digital na LATERAL DIREITA da página.
    Layout profissional: QR Code no topo + 3 linhas de texto vertical vermelho.
    """
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
    
    # ===== DESENHAR LINHAS =====
    for idx, (x, texto, is_bold) in enumerate([
        (x1, texto_linha1, True),
        (x2, texto_linha2, False),
        (x3, texto_linha3, False)
    ]):
        canvas.saveState()
        canvas.translate(x, start_y)
        canvas.rotate(-90)
        canvas.setFillColor(VERMELHO)
        canvas.setFont("Helvetica-Bold" if is_bold else "Helvetica", font_size)
        canvas.drawString(0, 0, texto)
        canvas.restoreState()


def create_signature_page_mrosc(signers: list, validation_code: str, doc_info: dict = None) -> BytesIO:
    """
    Cria uma página de assinaturas no estilo do documento de referência (Lei 14.063).
    """
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
