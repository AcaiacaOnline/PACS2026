"""
Public Routes - Portal da Transparência
Public endpoints for transparency portal access
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER

router = APIRouter(prefix="/api/public", tags=["Portal da Transparência"])


def setup_public_routes(db):
    """Configure public routes for transparency portal"""

    # ===== PACs =====
    @router.get("/pacs")
    async def get_public_pacs(ano: str = None, secretaria: str = None, page: int = 1, limit: int = 20):
        """List public PACs"""
        query = {}
        if ano:
            query['ano'] = ano
        if secretaria:
            query['secretaria'] = {'$regex': secretaria, '$options': 'i'}
        
        skip = (page - 1) * limit
        total = await db.pacs.count_documents(query)
        pacs = await db.pacs.find(query, {'_id': 0, 'user_id': 0}).sort('created_at', -1).skip(skip).limit(limit).to_list(limit)
        
        return {
            'data': pacs,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        }

    @router.get("/pacs/{pac_id}")
    async def get_public_pac(pac_id: str):
        """Gets a specific public PAC"""
        pac = await db.pacs.find_one({'pac_id': pac_id}, {'_id': 0, 'user_id': 0})
        if not pac:
            raise HTTPException(status_code=404, detail="PAC não encontrado")
        return pac

    @router.get("/pacs/{pac_id}/items")
    async def get_public_pac_items(pac_id: str):
        """Lists items of a public PAC"""
        items = await db.pac_items.find({'pac_id': pac_id}, {'_id': 0}).to_list(10000)
        return items

    # ===== PACs Geral =====
    @router.get("/pacs-geral")
    async def get_public_pacs_geral(ano: str = None, page: int = 1, limit: int = 20):
        """List public PACs Geral"""
        query = {}
        if ano:
            query['ano'] = ano
        
        skip = (page - 1) * limit
        total = await db.pacs_geral.count_documents(query)
        pacs = await db.pacs_geral.find(query, {'_id': 0, 'user_id': 0}).sort('created_at', -1).skip(skip).limit(limit).to_list(limit)
        
        return {
            'data': pacs,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        }

    @router.get("/pacs-geral/{pac_geral_id}")
    async def get_public_pac_geral(pac_geral_id: str):
        """Gets a specific public PAC Geral"""
        pac = await db.pacs_geral.find_one({'pac_geral_id': pac_geral_id}, {'_id': 0, 'user_id': 0})
        if not pac:
            raise HTTPException(status_code=404, detail="PAC Geral não encontrado")
        return pac

    @router.get("/pacs-geral/{pac_geral_id}/items")
    async def get_public_pac_geral_items(pac_geral_id: str):
        """Lists items of a public PAC Geral"""
        items = await db.pac_geral_items.find({'pac_geral_id': pac_geral_id}, {'_id': 0}).to_list(10000)
        return items

    # ===== PACs Obras =====
    @router.get("/pacs-geral-obras")
    async def get_public_pacs_obras(ano: str = None):
        """List public PACs Obras"""
        query = {}
        if ano:
            query['ano'] = ano
        pacs = await db.pacs_geral_obras.find(query, {'_id': 0, 'user_id': 0}).sort('created_at', -1).to_list(1000)
        return pacs

    @router.get("/pacs-geral-obras/{pac_obras_id}")
    async def get_public_pac_obras(pac_obras_id: str):
        """Gets a specific public PAC Obras"""
        pac = await db.pacs_geral_obras.find_one({'pac_obras_id': pac_obras_id}, {'_id': 0, 'user_id': 0})
        if not pac:
            raise HTTPException(status_code=404, detail="PAC Obras não encontrado")
        return pac

    @router.get("/pacs-geral-obras/{pac_obras_id}/items")
    async def get_public_pac_obras_items(pac_obras_id: str):
        """Lists items of a public PAC Obras"""
        items = await db.pac_obras_items.find({'pac_obras_id': pac_obras_id}, {'_id': 0}).to_list(10000)
        return items

    # ===== Processos =====
    @router.get("/processos")
    async def get_public_processos(ano: int = None, status: str = None, modalidade: str = None, page: int = 1, limit: int = 20):
        """List public processes"""
        query = {}
        if ano:
            query['ano'] = ano
        if status:
            query['status'] = status
        if modalidade:
            query['modalidade_contratacao'] = modalidade
        
        skip = (page - 1) * limit
        total = await db.processos.count_documents(query)
        processos = await db.processos.find(query, {'_id': 0, 'user_id': 0}).sort('created_at', -1).skip(skip).limit(limit).to_list(limit)
        
        return {
            'data': processos,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        }

    @router.get("/processos/{processo_id}")
    async def get_public_processo(processo_id: str):
        """Gets a specific public process"""
        processo = await db.processos.find_one({'processo_id': processo_id}, {'_id': 0, 'user_id': 0})
        if not processo:
            raise HTTPException(status_code=404, detail="Processo não encontrado")
        return processo

    # ===== Dashboard Stats =====
    @router.get("/dashboard/stats")
    async def get_public_dashboard_stats():
        """Returns public dashboard statistics"""
        pacs_count = await db.pacs.count_documents({})
        pacs_geral_count = await db.pacs_geral.count_documents({})
        pacs_obras_count = await db.pacs_geral_obras.count_documents({})
        processos_count = await db.processos.count_documents({})
        
        pac_items = await db.pac_items.find({}, {'valorTotal': 1, '_id': 0}).to_list(100000)
        total_pac = sum(i.get('valorTotal', 0) for i in pac_items)
        
        pac_geral_items = await db.pac_geral_items.find({}, {'valorTotal': 1, '_id': 0}).to_list(100000)
        total_pac_geral = sum(i.get('valorTotal', 0) for i in pac_geral_items)
        
        pac_obras_items = await db.pac_obras_items.find({}, {'valorTotal': 1, '_id': 0}).to_list(100000)
        total_pac_obras = sum(i.get('valorTotal', 0) for i in pac_obras_items)
        
        return {
            'pacs': {'total': pacs_count, 'valor_total': total_pac},
            'pacs_geral': {'total': pacs_geral_count, 'valor_total': total_pac_geral},
            'pacs_obras': {'total': pacs_obras_count, 'valor_total': total_pac_obras},
            'processos': {'total': processos_count},
            'valor_total_geral': total_pac + total_pac_geral + total_pac_obras
        }

    # ===== Classifications =====
    @router.get("/classificacoes")
    async def get_public_classificacoes():
        """Returns public classification codes"""
        return {
            "339030": {"nome": "Material de Consumo"},
            "339036": {"nome": "Outros Serviços de Terceiros (PF)"},
            "339039": {"nome": "Outros Serviços de Terceiros (PJ)"},
            "449052": {"nome": "Equipamentos e Material Permanente"}
        }

    # ===== MROSC Public =====
    @router.get("/mrosc/projetos")
    async def get_public_mrosc_projetos():
        """List public MROSC projects (only approved/published)"""
        projetos = await db.mrosc_projetos.find(
            {'status': {'$in': ['APROVADO', 'CONCLUIDO', 'EXECUCAO']}},
            {'_id': 0, 'user_id': 0}
        ).to_list(100)
        return projetos

    @router.get("/mrosc/projetos/{projeto_id}")
    async def get_public_mrosc_projeto(projeto_id: str):
        """Gets a specific public MROSC project"""
        projeto = await db.mrosc_projetos.find_one(
            {'projeto_id': projeto_id, 'status': {'$in': ['APROVADO', 'CONCLUIDO', 'EXECUCAO']}},
            {'_id': 0, 'user_id': 0}
        )
        if not projeto:
            raise HTTPException(status_code=404, detail="Projeto não encontrado ou não publicado")
        return projeto

    @router.get("/mrosc/projetos/{projeto_id}/resumo")
    async def get_public_mrosc_resumo(projeto_id: str):
        """Gets public summary of MROSC project"""
        projeto = await db.mrosc_projetos.find_one(
            {'projeto_id': projeto_id},
            {'_id': 0, 'user_id': 0}
        )
        if not projeto:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        
        rhs = await db.mrosc_rh.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(100)
        despesas = await db.mrosc_despesas.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(100)
        
        total_rh = sum(rh.get('custo_total_projeto', 0) for rh in rhs)
        total_despesas = sum(d.get('valor_total', 0) for d in despesas)
        
        return {
            'projeto': projeto,
            'resumo_financeiro': {
                'total_rh': total_rh,
                'total_despesas': total_despesas,
                'total_geral': total_rh + total_despesas
            }
        }

    @router.get("/mrosc/estatisticas")
    async def get_public_mrosc_estatisticas():
        """Returns public MROSC statistics"""
        projetos = await db.mrosc_projetos.find({}, {'_id': 0}).to_list(100)
        
        stats = {
            'total_projetos': len(projetos),
            'por_status': {},
            'valor_total': 0
        }
        
        for p in projetos:
            status = p.get('status', 'ELABORACAO')
            stats['por_status'][status] = stats['por_status'].get(status, 0) + 1
            stats['valor_total'] += p.get('valor_total', 0)
        
        return stats

    # ===== PDF Exports =====
    @router.get("/pacs/{pac_id}/export/pdf")
    async def export_public_pac_pdf(pac_id: str):
        """Exports public PAC to PDF"""
        pac = await db.pacs.find_one({'pac_id': pac_id}, {'_id': 0})
        if not pac:
            raise HTTPException(status_code=404, detail="PAC não encontrado")
        
        items = await db.pac_items.find({'pac_id': pac_id}, {'_id': 0}).to_list(10000)
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=15*mm, rightMargin=15*mm, topMargin=20*mm, bottomMargin=15*mm)
        
        elements = []
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=14, textColor=colors.HexColor('#1F4E78'), alignment=TA_CENTER, spaceAfter=10)
        
        elements.append(Paragraph(f"PAC INDIVIDUAL - {pac.get('secretaria', 'N/A')}", title_style))
        elements.append(Paragraph(f"Ano: {pac.get('ano', '2026')} - Portal da Transparência", ParagraphStyle('Sub', fontSize=10, alignment=TA_CENTER)))
        elements.append(Spacer(1, 10))
        
        table_data = [['#', 'Descrição', 'Unid.', 'Qtd', 'V.Unit', 'V.Total', 'Prior.']]
        total = 0
        for i, item in enumerate(items, 1):
            valor_total = item.get('valorTotal', 0)
            total += valor_total
            table_data.append([
                str(i),
                item.get('descricao', '')[:50],
                item.get('unidade', ''),
                str(item.get('quantidade', 0)),
                f"R$ {item.get('valorUnitario', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                f"R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                item.get('prioridade', '')
            ])
        
        table_data.append(['', '', '', '', 'TOTAL:', f"R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), ''])
        
        table = Table(table_data, colWidths=[25, 200, 35, 40, 60, 70, 50])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8E8E8')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(table)
        
        doc.build(elements)
        buffer.seek(0)
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=PAC_Publico_{pac_id}.pdf"}
        )

    return router
