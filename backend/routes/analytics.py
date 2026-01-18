"""
Analytics and Reports Routes - Planejamento Acaiaca
Dashboard analytics, alerts, and consolidated reports
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime, timezone, timedelta
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER

analytics_router = APIRouter(prefix="/api/analytics", tags=["Dashboard Analítico"])
alertas_router = APIRouter(prefix="/api/alertas", tags=["Sistema de Alertas"])
relatorios_router = APIRouter(prefix="/api/relatorios", tags=["Relatórios Gerenciais"])


def setup_analytics_routes(db, get_current_user):
    """Configure analytics routes"""

    @analytics_router.get("/dashboard")
    async def get_analytics_dashboard(request: Request, ano: str = None):
        """Returns complete analytics dashboard data"""
        user = await get_current_user(request)
        
        query = {}
        if ano:
            query['ano'] = ano
        
        # Counts
        pacs_count = await db.pacs.count_documents(query)
        pacs_geral_count = await db.pacs_geral.count_documents(query)
        pacs_obras_count = await db.pacs_geral_obras.count_documents(query)
        processos_count = await db.processos.count_documents({'ano': int(ano)} if ano else {})
        mrosc_count = await db.mrosc_projetos.count_documents({})
        
        # Values
        pac_items = await db.pac_items.find({}, {'valorTotal': 1, '_id': 0}).to_list(100000)
        total_pac = sum(i.get('valorTotal', 0) for i in pac_items)
        
        pac_geral_items = await db.pac_geral_items.find({}, {'valorTotal': 1, '_id': 0}).to_list(100000)
        total_pac_geral = sum(i.get('valorTotal', 0) for i in pac_geral_items)
        
        pac_obras_items = await db.pac_obras_items.find({}, {'valorTotal': 1, '_id': 0}).to_list(100000)
        total_pac_obras = sum(i.get('valorTotal', 0) for i in pac_obras_items)
        
        # Process status distribution
        processos = await db.processos.find({'ano': int(ano)} if ano else {}, {'status': 1, '_id': 0}).to_list(10000)
        status_dist = {}
        for p in processos:
            s = p.get('status', 'Não definido')
            status_dist[s] = status_dist.get(s, 0) + 1
        
        # Monthly evolution
        monthly_data = {}
        all_pacs = await db.pacs.find(query, {'created_at': 1, '_id': 0}).to_list(10000)
        for pac in all_pacs:
            created = pac.get('created_at')
            if created:
                if isinstance(created, datetime):
                    mes = created.strftime('%Y-%m')
                else:
                    mes = str(created)[:7]
                monthly_data[mes] = monthly_data.get(mes, 0) + 1
        
        return {
            'resumo': {
                'pacs_individual': {'count': pacs_count, 'valor': total_pac},
                'pacs_geral': {'count': pacs_geral_count, 'valor': total_pac_geral},
                'pacs_obras': {'count': pacs_obras_count, 'valor': total_pac_obras},
                'processos': {'count': processos_count},
                'mrosc': {'count': mrosc_count},
                'total_geral': total_pac + total_pac_geral + total_pac_obras
            },
            'processos_por_status': status_dist,
            'evolucao_mensal': monthly_data
        }

    return analytics_router


def setup_alertas_routes(db, get_current_user):
    """Configure alerts routes"""

    @alertas_router.get("/")
    async def get_alertas(request: Request):
        """Returns system alerts"""
        user = await get_current_user(request)
        alertas = []
        
        # Processes without status
        processos_sem_status = await db.processos.count_documents({'status': {'$in': [None, '', 'Não definido']}})
        if processos_sem_status > 0:
            alertas.append({
                'tipo': 'warning',
                'modulo': 'Processos',
                'mensagem': f'{processos_sem_status} processo(s) sem status definido',
                'acao': '/processos'
            })
        
        # PACs without items
        pacs = await db.pacs.find({}, {'pac_id': 1, '_id': 0}).to_list(1000)
        for pac in pacs:
            items_count = await db.pac_items.count_documents({'pac_id': pac['pac_id']})
            if items_count == 0:
                alertas.append({
                    'tipo': 'info',
                    'modulo': 'PAC Individual',
                    'mensagem': f'PAC {pac["pac_id"][:12]} sem itens cadastrados',
                    'acao': f'/pac-individual/{pac["pac_id"]}'
                })
        
        # MROSC projects pending analysis
        mrosc_pendentes = await db.mrosc_projetos.count_documents({'status': 'SUBMETIDO'})
        if mrosc_pendentes > 0:
            alertas.append({
                'tipo': 'warning',
                'modulo': 'MROSC',
                'mensagem': f'{mrosc_pendentes} projeto(s) aguardando análise',
                'acao': '/mrosc'
            })
        
        # MROSC documents not validated
        docs_pendentes = await db.mrosc_documentos.count_documents({'validado': False})
        if docs_pendentes > 0:
            alertas.append({
                'tipo': 'info',
                'modulo': 'MROSC',
                'mensagem': f'{docs_pendentes} documento(s) aguardando validação',
                'acao': '/mrosc'
            })
        
        return alertas

    @alertas_router.get("/resumo")
    async def get_alertas_resumo(request: Request):
        """Returns summary of alerts"""
        user = await get_current_user(request)
        
        alertas = await get_alertas(request)
        
        return {
            'total': len(alertas),
            'por_tipo': {
                'warning': len([a for a in alertas if a['tipo'] == 'warning']),
                'info': len([a for a in alertas if a['tipo'] == 'info']),
                'error': len([a for a in alertas if a['tipo'] == 'error'])
            }
        }

    return alertas_router


def setup_relatorios_routes(db, get_current_user):
    """Configure reports routes"""

    @relatorios_router.get("/consolidado/pdf")
    async def gerar_relatorio_consolidado(request: Request):
        """Generates consolidated PDF report"""
        user = await get_current_user(request)
        
        # Fetch all data
        pacs = await db.pacs.find({}, {'_id': 0}).to_list(10000)
        pacs_geral = await db.pacs_geral.find({}, {'_id': 0}).to_list(10000)
        pacs_obras = await db.pacs_geral_obras.find({}, {'_id': 0}).to_list(10000)
        processos = await db.processos.find({}, {'_id': 0}).to_list(10000)
        projetos_mrosc = await db.mrosc_projetos.find({}, {'_id': 0}).to_list(100)
        
        # Items
        pac_items = await db.pac_items.find({}, {'_id': 0}).to_list(100000)
        pac_geral_items = await db.pac_geral_items.find({}, {'_id': 0}).to_list(100000)
        pac_obras_items = await db.pac_obras_items.find({}, {'_id': 0}).to_list(100000)
        
        # Totals
        total_pac = sum(i.get('valorTotal', 0) for i in pac_items)
        total_pac_geral = sum(i.get('valorTotal', 0) for i in pac_geral_items)
        total_obras = sum(i.get('valorTotal', 0) for i in pac_obras_items)
        total_mrosc = sum(p.get('valor_total', 0) for p in projetos_mrosc)
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
        
        elements = []
        styles = getSampleStyleSheet()
        titulo_style = ParagraphStyle('Titulo', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#1F4E78'), alignment=TA_CENTER, spaceAfter=6*mm)
        subtitulo_style = ParagraphStyle('Subtitulo', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#2E7D32'), spaceBefore=6*mm, spaceAfter=3*mm)
        
        # Header
        elements.append(Paragraph('PREFEITURA MUNICIPAL DE ACAIACA - MG', titulo_style))
        elements.append(Paragraph('CNPJ: 18.295.287/0001-90', ParagraphStyle('CNPJ', alignment=TA_CENTER, fontSize=9)))
        elements.append(Spacer(1, 4*mm))
        elements.append(Paragraph('<b>RELATÓRIO GERENCIAL CONSOLIDADO</b>', ParagraphStyle('TitDoc', alignment=TA_CENTER, fontSize=14, textColor=colors.HexColor('#1F4E78'))))
        elements.append(Paragraph(f'Gerado em: {datetime.now().strftime("%d/%m/%Y às %H:%M")}', ParagraphStyle('Data', alignment=TA_CENTER, fontSize=8, textColor=colors.gray)))
        elements.append(Spacer(1, 8*mm))
        
        # Executive Summary
        elements.append(Paragraph('1. RESUMO EXECUTIVO', subtitulo_style))
        resumo_data = [
            ['Indicador', 'Quantidade', 'Valor Total'],
            ['PACs Individuais', str(len(pacs)), f"R$ {total_pac:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')],
            ['PACs Gerais', str(len(pacs_geral)), f"R$ {total_pac_geral:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')],
            ['PACs Obras', str(len(pacs_obras)), f"R$ {total_obras:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')],
            ['Processos', str(len(processos)), '-'],
            ['Projetos MROSC', str(len(projetos_mrosc)), f"R$ {total_mrosc:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')],
            ['TOTAL GERAL', '-', f"R$ {(total_pac + total_pac_geral + total_obras + total_mrosc):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')]
        ]
        
        resumo_table = Table(resumo_data, colWidths=[80*mm, 40*mm, 50*mm])
        resumo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BBDEFB')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E3F2FD')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(resumo_table)
        
        # Processes by Status
        elements.append(Paragraph('2. PROCESSOS POR STATUS', subtitulo_style))
        status_count = {}
        for p in processos:
            s = p.get('status', 'Não Definido')
            status_count[s] = status_count.get(s, 0) + 1
        
        status_data = [['Status', 'Quantidade']]
        for s, c in sorted(status_count.items(), key=lambda x: x[1], reverse=True):
            status_data.append([s, str(c)])
        
        status_table = Table(status_data, colWidths=[100*mm, 40*mm])
        status_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#C8E6C9')),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(status_table)
        
        # Footer
        elements.append(Spacer(1, 15*mm))
        user_name = user.name if hasattr(user, 'name') else 'Admin'
        elements.append(Paragraph('_' * 50, ParagraphStyle('Linha', alignment=TA_CENTER)))
        elements.append(Paragraph(f'<b>{user_name}</b>', ParagraphStyle('Assinatura', alignment=TA_CENTER, fontSize=10)))
        elements.append(Paragraph('Responsável pelo Relatório', ParagraphStyle('Cargo', alignment=TA_CENTER, fontSize=8, textColor=colors.gray)))
        
        doc.build(elements)
        buffer.seek(0)
        
        filename = f"Relatorio_Consolidado_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        return StreamingResponse(buffer, media_type='application/pdf', headers={'Content-Disposition': f'attachment; filename="{filename}"'})

    return relatorios_router
