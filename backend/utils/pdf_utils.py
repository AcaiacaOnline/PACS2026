"""
PDF Utilities - Funções para geração e manipulação de PDFs
Planejamento Acaiaca - Sistema de Gestão Municipal
Layout baseado no DOEM (Diário Oficial Eletrônico Municipal)
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

# Informações institucionais padronizadas
PREFEITURA_INFO = {
    'nome': 'PREFEITURA MUNICIPAL DE ACAIACA',
    'estado': 'ESTADO DE MINAS GERAIS',
    'cnpj': '18.295.287/0001-90',
    'endereco': 'Praça Tancredo Neves, Número 35, Centro, Acaiaca - MG',
    'cep': 'CEP: 35.438-000',
    'telefone': '(31) 3887 - 1650',
    'telefone_obs': '(Atendimento Automático)',
    'portal': 'https://acaiaca.mg.gov.br/',
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


class DOEMPageTemplate:
    """
    Template de página no estilo DOEM para todos os PDFs do sistema.
    Adiciona cabeçalho e rodapé padronizados em todas as páginas.
    """
    
    def __init__(self, titulo_documento="DOCUMENTO", subtitulo=None, 
                 assinante_nome=None, assinante_cargo=None, assinante_cpf=None,
                 data_assinatura=None, validation_code=None):
        self.titulo_documento = titulo_documento
        self.subtitulo = subtitulo
        self.assinante_nome = assinante_nome
        self.assinante_cargo = assinante_cargo
        self.assinante_cpf = assinante_cpf
        self.data_assinatura = data_assinatura or datetime.now().strftime('%d/%m/%Y')
        self.validation_code = validation_code or generate_validation_code()
        self.page_count = 0
        self.total_pages = 1
    
    def set_total_pages(self, total):
        """Define o total de páginas para exibição"""
        self.total_pages = total
    
    def draw_header(self, canvas, doc):
        """Desenha o cabeçalho no estilo DOEM"""
        page_width, page_height = doc.pagesize
        
        # Incrementar contador de páginas
        self.page_count += 1
        
        # ===== CABEÇALHO =====
        header_top = page_height - 15*mm
        
        # Brasão à esquerda
        brasao_path = get_brasao_path()
        if brasao_path:
            try:
                brasao_size = 20*mm
                canvas.drawImage(
                    brasao_path,
                    doc.leftMargin,
                    header_top - brasao_size + 5*mm,
                    width=brasao_size,
                    height=brasao_size,
                    preserveAspectRatio=True,
                    mask='auto'
                )
            except Exception as e:
                logging.warning(f"Erro ao carregar brasão: {e}")
        
        # DOEM e títulos - Centro/Esquerda do brasão
        text_x = doc.leftMargin + 25*mm
        
        # "DOEM" em preto grande
        canvas.setFillColor(colors.black)
        canvas.setFont("Helvetica-Bold", 24)
        canvas.drawString(text_x, header_top - 3*mm, "DOEM")
        
        # "Diário Oficial Eletrônico Municipal"
        canvas.setFont("Helvetica", 10)
        canvas.drawString(text_x, header_top - 10*mm, "Diário Oficial Eletrônico Municipal")
        
        # "de Acaiaca - MG"
        canvas.setFont("Helvetica", 9)
        canvas.drawString(text_x, header_top - 16*mm, "de Acaiaca - MG")
        
        # Assinatura digital no canto direito (se houver assinante)
        if self.assinante_nome:
            sig_x = page_width - doc.rightMargin
            sig_y = header_top - 2*mm
            
            canvas.setFillColor(colors.HexColor('#DC2626'))  # Vermelho
            canvas.setFont("Helvetica-Bold", 6)
            
            # Nome do assinante
            canvas.drawRightString(sig_x, sig_y, f"ASSINADO: {self.assinante_nome.upper()}")
            
            # Cargo
            if self.assinante_cargo:
                canvas.setFont("Helvetica", 5)
                canvas.drawRightString(sig_x, sig_y - 4*mm, f"({self.assinante_cargo})")
            
            # CPF mascarado
            cpf_masked = mask_cpf(self.assinante_cpf) if self.assinante_cpf else "***.***.***-**"
            canvas.drawRightString(sig_x, sig_y - 8*mm, f"CPF: {cpf_masked}")
            
            # Data
            canvas.drawRightString(sig_x, sig_y - 12*mm, f"Data: {self.data_assinatura}")
            
            # Código de validação
            canvas.setFont("Helvetica", 5)
            canvas.drawRightString(sig_x, sig_y - 16*mm, f"Código: {self.validation_code}")
            canvas.drawRightString(sig_x, sig_y - 20*mm, "Valide: pac.acaiaca.mg.gov.br/validar")
        
        # Linha separadora preta
        linha_y = header_top - 22*mm
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(1)
        canvas.line(doc.leftMargin, linha_y, page_width - doc.rightMargin, linha_y)
        
        # Título do documento (centralizado abaixo da linha)
        canvas.setFillColor(colors.HexColor('#1F4E78'))
        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawCentredString(page_width / 2, linha_y - 8*mm, self.titulo_documento)
        
        # Subtítulo (se houver)
        if self.subtitulo:
            canvas.setFont("Helvetica", 9)
            canvas.setFillColor(colors.HexColor('#4A5568'))
            canvas.drawCentredString(page_width / 2, linha_y - 14*mm, self.subtitulo)
    
    def draw_footer(self, canvas, doc):
        """Desenha o rodapé padronizado"""
        page_width, page_height = doc.pagesize
        
        # Posição do rodapé
        footer_y = 25*mm
        
        # Linha separadora
        canvas.setStrokeColor(colors.HexColor('#E5E7EB'))
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, footer_y + 8*mm, page_width - doc.rightMargin, footer_y + 8*mm)
        
        # Endereço
        canvas.setFillColor(colors.HexColor('#374151'))
        canvas.setFont("Helvetica", 7)
        canvas.drawCentredString(page_width / 2, footer_y + 4*mm, PREFEITURA_INFO['endereco'])
        
        # Telefone
        telefone_text = f"Contato Telefônico: {PREFEITURA_INFO['telefone']} {PREFEITURA_INFO['telefone_obs']}"
        canvas.drawCentredString(page_width / 2, footer_y, telefone_text)
        
        # Portal
        canvas.drawCentredString(page_width / 2, footer_y - 4*mm, f"Portal: {PREFEITURA_INFO['portal']}")
        
        # E-mail
        canvas.drawCentredString(page_width / 2, footer_y - 8*mm, f"e-mail: {PREFEITURA_INFO['email']}")
        
        # Número da página à direita
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.black)
        page_text = f"Página {self.page_count}"
        if self.total_pages > 1:
            page_text = f"Página {self.page_count} de {self.total_pages}"
        canvas.drawRightString(page_width - doc.rightMargin, footer_y - 8*mm, page_text)
    
    def __call__(self, canvas, doc):
        """Callback para SimpleDocTemplate"""
        canvas.saveState()
        self.draw_header(canvas, doc)
        self.draw_footer(canvas, doc)
        canvas.restoreState()


def create_doem_header_elements(styles, titulo_documento="DOCUMENTO", subtitulo=None,
                                 assinante_nome=None, assinante_cargo=None, assinante_cpf=None,
                                 data_assinatura=None, validation_code=None):
    """
    Cria elementos do cabeçalho DOEM para uso com SimpleDocTemplate.build()
    Retorna uma lista de elementos (Paragraph, Spacer, Table, etc.)
    """
    from reportlab.platypus import HRFlowable
    
    elements = []
    
    # Obter caminho do brasão
    brasao_path = get_brasao_path()
    validation_code = validation_code or generate_validation_code()
    data_assinatura = data_assinatura or datetime.now().strftime('%d/%m/%Y')
    
    # ===== CABEÇALHO COM BRASÃO E DOEM =====
    if brasao_path:
        try:
            brasao_img = Image(brasao_path, width=20*mm, height=20*mm)
            
            # Textos DOEM
            doem_text = """
            <font size="24"><b>DOEM</b></font><br/>
            <font size="10">Diário Oficial Eletrônico Municipal</font><br/>
            <font size="9">de Acaiaca - MG</font>
            """
            doem_style = ParagraphStyle(
                'DOEMText',
                fontSize=24,
                fontName='Helvetica-Bold',
                textColor=colors.black,
                leading=14
            )
            doem_para = Paragraph(doem_text, doem_style)
            
            # Informações de assinatura (se houver)
            if assinante_nome:
                cpf_masked = mask_cpf(assinante_cpf) if assinante_cpf else "***.***.***-**"
                sig_text = f"""
                <font size="6" color="#DC2626"><b>ASSINADO: {assinante_nome.upper()}</b></font><br/>
                <font size="5" color="#DC2626">({assinante_cargo or ''})</font><br/>
                <font size="5" color="#DC2626">CPF: {cpf_masked}</font><br/>
                <font size="5" color="#DC2626">Data: {data_assinatura}</font><br/>
                <font size="5" color="#DC2626">Código: {validation_code}</font><br/>
                <font size="5" color="#DC2626">Valide: pac.acaiaca.mg.gov.br/validar</font>
                """
                sig_style = ParagraphStyle(
                    'SigText',
                    fontSize=6,
                    fontName='Helvetica',
                    textColor=colors.HexColor('#DC2626'),
                    alignment=TA_RIGHT,
                    leading=7
                )
                sig_para = Paragraph(sig_text, sig_style)
            else:
                sig_para = Paragraph("", ParagraphStyle('Empty', fontSize=6))
            
            # Tabela com brasão | doem | assinatura
            header_table = Table(
                [[brasao_img, doem_para, sig_para]],
                colWidths=[25*mm, None, 50*mm]
            )
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'LEFT'),
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
            doem_style = ParagraphStyle(
                'DOEM',
                fontSize=24,
                fontName='Helvetica-Bold',
                textColor=colors.black
            )
            elements.append(Paragraph('<b>DOEM</b>', doem_style))
            elements.append(Paragraph('Diário Oficial Eletrônico Municipal de Acaiaca - MG', 
                                     ParagraphStyle('SubDOEM', fontSize=10)))
    else:
        # Sem brasão
        doem_style = ParagraphStyle(
            'DOEM',
            fontSize=24,
            fontName='Helvetica-Bold',
            textColor=colors.black
        )
        elements.append(Paragraph('<b>DOEM</b>', doem_style))
        elements.append(Paragraph('Diário Oficial Eletrônico Municipal de Acaiaca - MG', 
                                 ParagraphStyle('SubDOEM', fontSize=10)))
    
    # Linha separadora preta
    elements.append(Spacer(1, 3*mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceBefore=2*mm, spaceAfter=4*mm))
    
    # Título do documento
    titulo_style = ParagraphStyle(
        'TituloDoc',
        fontSize=14,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1F4E78'),
        alignment=TA_CENTER,
        spaceBefore=2*mm,
        spaceAfter=2*mm
    )
    elements.append(Paragraph(titulo_documento, titulo_style))
    
    # Subtítulo (se houver)
    if subtitulo:
        subtitulo_style = ParagraphStyle(
            'SubtituloDoc',
            fontSize=9,
            fontName='Helvetica',
            textColor=colors.HexColor('#4A5568'),
            alignment=TA_CENTER,
            spaceAfter=4*mm
        )
        elements.append(Paragraph(subtitulo, subtitulo_style))
    
    elements.append(Spacer(1, 4*mm))
    
    return elements


def create_doem_footer_elements():
    """
    Cria elementos do rodapé DOEM para uso com SimpleDocTemplate.
    """
    from reportlab.platypus import HRFlowable
    
    elements = []
    
    # Linha separadora
    elements.append(Spacer(1, 6*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E5E7EB'), spaceBefore=2*mm, spaceAfter=2*mm))
    
    # Informações do rodapé
    footer_style = ParagraphStyle(
        'Footer',
        fontSize=7,
        fontName='Helvetica',
        textColor=colors.HexColor('#374151'),
        alignment=TA_CENTER,
        leading=10
    )
    
    footer_text = f"""
    {PREFEITURA_INFO['endereco']}<br/>
    Contato Telefônico: {PREFEITURA_INFO['telefone']} {PREFEITURA_INFO['telefone_obs']}<br/>
    Portal: {PREFEITURA_INFO['portal']}<br/>
    e-mail: {PREFEITURA_INFO['email']}
    """
    
    elements.append(Paragraph(footer_text, footer_style))
    
    return elements


def create_page_callback(titulo_documento="DOCUMENTO", subtitulo=None,
                         assinante_nome=None, assinante_cargo=None, assinante_cpf=None,
                         data_assinatura=None, validation_code=None, total_pages=1):
    """
    Cria função de callback para cabeçalho/rodapé DOEM em todas as páginas.
    
    Uso:
        doc = SimpleDocTemplate(buffer, pagesize=A4, ...)
        callback = create_page_callback(titulo_documento="MEU RELATÓRIO", ...)
        doc.build(elements, onFirstPage=callback, onLaterPages=callback)
    """
    template = DOEMPageTemplate(
        titulo_documento=titulo_documento,
        subtitulo=subtitulo,
        assinante_nome=assinante_nome,
        assinante_cargo=assinante_cargo,
        assinante_cpf=assinante_cpf,
        data_assinatura=data_assinatura,
        validation_code=validation_code
    )
    template.set_total_pages(total_pages)
    
    return template


# ===== FUNÇÕES DE COMPATIBILIDADE (para código existente) =====

def get_professional_styles():
    """Retorna estilos profissionais para relatórios PDF"""
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1F4E78')
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


# Alias para compatibilidade
def create_header_elements(*args, **kwargs):
    """Alias para create_doem_header_elements"""
    # Mapear argumentos antigos para novos
    title = kwargs.pop('title', None)
    subtitle = kwargs.pop('subtitle', None)
    show_brasao = kwargs.pop('show_brasao', True)
    
    return create_doem_header_elements(
        kwargs.get('styles', getSampleStyleSheet()),
        titulo_documento=title or "DOCUMENTO",
        subtitulo=subtitle,
        **kwargs
    )


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


# Constantes para cores DOEM (compatibilidade)
AZUL_ROYAL = colors.HexColor('#1E3A8A')
CINZA_LINHA = colors.HexColor('#D1D5DB')
AZUL_LINK = colors.HexColor('#1E40AF')
