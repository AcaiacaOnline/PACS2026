"""
PDF Utilities - Funções para geração e manipulação de PDFs
Planejamento Acaiaca - Sistema de Gestão Municipal
Layout DOEM - Diário Oficial Eletrônico Municipal
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

# Cores do layout DOEM
AZUL_ACAIACA = colors.HexColor('#0000CD')  # Azul royal/médio para o texto ACAIACA
AZUL_INFO = colors.HexColor('#0000FF')     # Azul para informações de publicação
CINZA_LINHA = colors.HexColor('#C0C0C0')   # Cinza para linha separadora
CINZA_RODAPE = colors.HexColor('#B0B0B0')  # Cinza claro para texto do rodapé

# Informações institucionais padronizadas
PREFEITURA_INFO = {
    'nome': 'PREFEITURA MUNICIPAL DE ACAIACA',
    'estado': 'ESTADO DE MINAS GERAIS',
    'cnpj': '18.295.287/0001-90',
    'endereco': 'Praça Antônio Carlos, 10 - Centro',
    'cep': 'CEP: 35444-000',
    'telefone': '(31) 3887 - 1650',
    'telefone_obs': '(Atendimento Automático)',
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


def format_data_completa(data=None):
    """Formata data no estilo: Acaiaca, Sábado, 17 de Janeiro de 2026."""
    dias_semana = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
    meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    
    if data is None:
        data = datetime.now()
    elif isinstance(data, str):
        try:
            data = datetime.fromisoformat(data.replace('Z', '+00:00'))
        except:
            data = datetime.now()
    
    dia_semana = dias_semana[data.weekday()]
    return f"Acaiaca, {dia_semana}, {data.day} de {meses[data.month - 1]} de {data.year}."


class DOEMPageTemplate:
    """
    Template de página no estilo DOEM para todos os PDFs do sistema.
    Cabeçalho: Brasões nas laterais + ACAIACA em azul 3D + linha cinza + info publicação + linha azul
    Rodapé: Texto em cinza claro (marca d'água) centralizado
    """
    
    def __init__(self, titulo_documento="DOCUMENTO", subtitulo=None, 
                 ano=134, numero_edicao=1, num_paginas=1, data_publicacao=None,
                 assinante_nome=None, assinante_cargo=None, assinante_cpf=None,
                 data_assinatura=None, validation_code=None):
        self.titulo_documento = titulo_documento
        self.subtitulo = subtitulo
        self.ano = ano
        self.numero_edicao = numero_edicao
        self.num_paginas = num_paginas
        self.data_publicacao = data_publicacao or datetime.now()
        self.assinante_nome = assinante_nome
        self.assinante_cargo = assinante_cargo
        self.assinante_cpf = assinante_cpf
        self.data_assinatura = data_assinatura or datetime.now().strftime('%d/%m/%Y')
        self.validation_code = validation_code or generate_validation_code()
        self.page_count = 0
        self.total_pages = num_paginas
    
    def set_total_pages(self, total):
        """Define o total de páginas para exibição"""
        self.total_pages = total
        self.num_paginas = total
    
    def draw_header(self, canvas, doc):
        """Desenha o cabeçalho no estilo DOEM com brasões espelhados"""
        page_width, page_height = doc.pagesize
        
        # Incrementar contador de páginas
        self.page_count += 1
        
        # ===== CONFIGURAÇÃO DO CABEÇALHO =====
        header_top = page_height - 10*mm
        brasao_size = 25*mm
        
        # ===== BRASÃO ESQUERDO =====
        brasao_path = get_brasao_path()
        if brasao_path:
            try:
                # Brasão esquerdo
                canvas.drawImage(
                    brasao_path,
                    doc.leftMargin,
                    header_top - brasao_size,
                    width=brasao_size,
                    height=brasao_size,
                    preserveAspectRatio=True,
                    mask='auto'
                )
                
                # Brasão direito (espelhado)
                canvas.drawImage(
                    brasao_path,
                    page_width - doc.rightMargin - brasao_size,
                    header_top - brasao_size,
                    width=brasao_size,
                    height=brasao_size,
                    preserveAspectRatio=True,
                    mask='auto'
                )
            except Exception as e:
                logging.warning(f"Erro ao carregar brasão: {e}")
        
        # ===== TEXTO "ACAIACA" EM AZUL 3D COM SOMBRA =====
        # Sombra (cinza, deslocada)
        canvas.setFillColor(colors.HexColor('#808080'))
        canvas.setFont("Helvetica-Bold", 36)
        canvas.drawCentredString(page_width / 2 + 1.5, header_top - 18*mm - 1.5, "ACAIACA")
        
        # Texto principal (azul)
        canvas.setFillColor(AZUL_ACAIACA)
        canvas.setFont("Helvetica-Bold", 36)
        canvas.drawCentredString(page_width / 2, header_top - 18*mm, "ACAIACA")
        
        # ===== LINHA CINZA SEPARADORA =====
        linha_cinza_y = header_top - 28*mm
        canvas.setStrokeColor(CINZA_LINHA)
        canvas.setLineWidth(8)
        canvas.line(doc.leftMargin + 10*mm, linha_cinza_y, page_width - doc.rightMargin - 10*mm, linha_cinza_y)
        
        # ===== INFORMAÇÕES DE PUBLICAÇÃO EM AZUL =====
        info_y = linha_cinza_y - 8*mm
        canvas.setFillColor(AZUL_INFO)
        canvas.setFont("Helvetica-Bold", 10)
        
        # URL à esquerda
        canvas.drawString(doc.leftMargin, info_y, PREFEITURA_INFO['portal'])
        
        # ANO - Nº - PÁGINAS no centro
        info_central = f"ANO {self.ano} - Nº {self.numero_edicao} - {self.num_paginas} PÁGINAS"
        canvas.drawCentredString(page_width / 2, info_y, info_central)
        
        # Data à direita
        data_formatada = format_data_completa(self.data_publicacao)
        canvas.drawRightString(page_width - doc.rightMargin, info_y, data_formatada)
        
        # ===== LINHA AZUL INFERIOR =====
        linha_azul_y = info_y - 8*mm
        canvas.setStrokeColor(AZUL_ACAIACA)
        canvas.setLineWidth(6)
        canvas.line(doc.leftMargin, linha_azul_y, page_width - doc.rightMargin, linha_azul_y)
        
        # ===== TÍTULO DO DOCUMENTO (centralizado abaixo) =====
        if self.titulo_documento:
            canvas.setFillColor(colors.HexColor('#1F4E78'))
            canvas.setFont("Helvetica-Bold", 12)
            canvas.drawCentredString(page_width / 2, linha_azul_y - 8*mm, self.titulo_documento)
            
            if self.subtitulo:
                canvas.setFont("Helvetica", 9)
                canvas.setFillColor(colors.HexColor('#4A5568'))
                canvas.drawCentredString(page_width / 2, linha_azul_y - 14*mm, self.subtitulo)
    
    def draw_footer(self, canvas, doc):
        """Desenha o rodapé em cinza claro (estilo marca d'água) centralizado"""
        page_width, page_height = doc.pagesize
        
        # Posição do rodapé
        footer_y = 20*mm
        
        # Linha separadora fina
        canvas.setStrokeColor(colors.HexColor('#E0E0E0'))
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, footer_y + 10*mm, page_width - doc.rightMargin, footer_y + 10*mm)
        
        # ===== TEXTO DO RODAPÉ EM CINZA CLARO =====
        canvas.setFillColor(CINZA_RODAPE)
        canvas.setFont("Helvetica", 9)
        
        # Linha 1: Prefeitura Municipal de Acaiaca - MG | CNPJ: 18.295.287/0001-90
        linha1 = f"Prefeitura Municipal de Acaiaca - MG | CNPJ: {PREFEITURA_INFO['cnpj']}"
        canvas.drawCentredString(page_width / 2, footer_y + 4*mm, linha1)
        
        # Linha 2: Praça Antônio Carlos, 10 - Centro - CEP: 35444-000
        linha2 = f"{PREFEITURA_INFO['endereco']} - {PREFEITURA_INFO['cep']}"
        canvas.drawCentredString(page_width / 2, footer_y, linha2)
        
        # Número da página à direita (em cinza mais escuro para legibilidade)
        canvas.setFillColor(colors.HexColor('#666666'))
        canvas.setFont("Helvetica", 8)
        page_text = f"Página {self.page_count}"
        if self.total_pages > 1:
            page_text = f"Página {self.page_count} de {self.total_pages}"
        canvas.drawRightString(page_width - doc.rightMargin, footer_y, page_text)
    
    def __call__(self, canvas, doc):
        """Callback para SimpleDocTemplate"""
        canvas.saveState()
        self.draw_header(canvas, doc)
        self.draw_footer(canvas, doc)
        canvas.restoreState()


def create_page_callback(titulo_documento="DOCUMENTO", subtitulo=None,
                         ano=134, numero_edicao=1, num_paginas=1, data_publicacao=None,
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
        ano=ano,
        numero_edicao=numero_edicao,
        num_paginas=num_paginas or total_pages,
        data_publicacao=data_publicacao,
        assinante_nome=assinante_nome,
        assinante_cargo=assinante_cargo,
        assinante_cpf=assinante_cpf,
        data_assinatura=data_assinatura,
        validation_code=validation_code
    )
    template.set_total_pages(total_pages or num_paginas)
    
    return template


def create_doem_header_elements(styles, titulo_documento="DOCUMENTO", subtitulo=None,
                                 ano=134, numero_edicao=1, num_paginas=1, data_publicacao=None):
    """
    Cria elementos do cabeçalho DOEM para uso com SimpleDocTemplate.build()
    NOTA: Use create_page_callback para cabeçalho em TODAS as páginas
    """
    from reportlab.platypus import HRFlowable
    
    elements = []
    
    # Este método é mantido para compatibilidade, mas o cabeçalho principal
    # deve ser desenhado via callback para aparecer em todas as páginas
    
    # Espaço para o cabeçalho que será desenhado pelo callback
    elements.append(Spacer(1, 10*mm))
    
    return elements


# ===== FUNÇÕES DE COMPATIBILIDADE =====

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
    return create_doem_header_elements(
        kwargs.get('styles', getSampleStyleSheet()),
        titulo_documento=kwargs.get('title', "DOCUMENTO"),
        subtitulo=kwargs.get('subtitle', None)
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


# Constantes para compatibilidade
AZUL_ROYAL = colors.HexColor('#1E3A8A')
AZUL_LINK = colors.HexColor('#1E40AF')
