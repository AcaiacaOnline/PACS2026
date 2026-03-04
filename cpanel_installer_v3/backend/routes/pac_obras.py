"""
PAC Obras Routes - Planejamento Acaiaca
Handles CRUD operations for PAC Obras (Works and Engineering Services)
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import List
from datetime import datetime, timezone
from io import BytesIO
import uuid

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER

router = APIRouter(prefix="/api", tags=["PAC Obras"])

# Classification according to Law 14.133/2021 and Ordinance 448/ME
CLASSIFICACAO_OBRAS_SERVICOS = {
    "339040": {
        "nome": "Serviços de Tecnologia da Informação e Comunicação - PJ",
        "categoria": "SERVICOS_TIC",
        "subitens": [
            "01 - Consultoria em TI",
            "02 - Desenvolvimento de Software",
            "03 - Suporte Técnico",
            "04 - Manutenção de Sistemas",
            "05 - Licenciamento de Software",
            "06 - Hospedagem e Cloud Computing",
            "07 - Conectividade e Redes",
            "08 - Segurança da Informação"
        ]
    },
    "449051": {
        "nome": "Obras e Instalações",
        "categoria": "OBRAS",
        "subitens": [
            "01 - Construção de Edifícios Públicos",
            "02 - Reforma e Ampliação",
            "03 - Pavimentação e Urbanização",
            "04 - Saneamento Básico",
            "05 - Instalações Elétricas",
            "06 - Instalações Hidráulicas",
            "07 - Sistemas de Drenagem",
            "08 - Construção de Pontes e Viadutos",
            "09 - Obras de Contenção",
            "10 - Terraplanagem"
        ]
    },
    "339039": {
        "nome": "Outros Serviços de Terceiros - Pessoa Jurídica",
        "categoria": "SERVICOS_PJ",
        "subitens": [
            "01 - Serviços de Engenharia",
            "02 - Serviços de Arquitetura",
            "03 - Laudos e Perícias Técnicas",
            "04 - Elaboração de Projetos",
            "05 - Fiscalização de Obras",
            "06 - Gerenciamento de Obras",
            "07 - Topografia e Georreferenciamento"
        ]
    }
}


def setup_pac_obras_routes(db, get_current_user, PACGeralObras, PACGeralObrasCreate, PACGeralObrasUpdate, PACGeralObrasItem, PACGeralObrasItemCreate, PACGeralObrasItemUpdate):
    """Configure PAC Obras routes with injected dependencies"""

    @router.get("/classificacao/obras-servicos")
    async def get_classificacao_obras_servicos():
        """Returns classification codes for works and services"""
        return CLASSIFICACAO_OBRAS_SERVICOS

    # ===== CRUD =====
    @router.get("/pacs-geral-obras", response_model=List[PACGeralObras])
    async def get_pacs_geral_obras(request: Request, ano: str = None):
        """List all PACs Obras"""
        user = await get_current_user(request)
        query = {}
        if ano:
            query['ano'] = ano
        pacs = await db.pacs_geral_obras.find(query, {'_id': 0}).sort('created_at', -1).to_list(1000)
        return [PACGeralObras(**p) for p in pacs]

    @router.post("/pacs-geral-obras", response_model=PACGeralObras)
    async def create_pac_geral_obras(pac: PACGeralObrasCreate, request: Request):
        """Creates a new PAC Obras"""
        user = await get_current_user(request)
        pac_dict = pac.model_dump()
        pac_dict['pac_obras_id'] = f"paco_{uuid.uuid4().hex[:12]}"
        pac_dict['user_id'] = user.user_id
        pac_dict['created_at'] = datetime.now(timezone.utc)
        pac_dict['updated_at'] = datetime.now(timezone.utc)
        await db.pacs_geral_obras.insert_one(pac_dict)
        pac_dict.pop('_id', None)
        return PACGeralObras(**pac_dict)

    @router.get("/pacs-geral-obras/{pac_obras_id}", response_model=PACGeralObras)
    async def get_pac_geral_obras(pac_obras_id: str, request: Request):
        """Gets a specific PAC Obras"""
        user = await get_current_user(request)
        pac = await db.pacs_geral_obras.find_one({'pac_obras_id': pac_obras_id}, {'_id': 0})
        if not pac:
            raise HTTPException(status_code=404, detail="PAC Obras não encontrado")
        return PACGeralObras(**pac)

    @router.put("/pacs-geral-obras/{pac_obras_id}", response_model=PACGeralObras)
    async def update_pac_geral_obras(pac_obras_id: str, pac: PACGeralObrasUpdate, request: Request):
        """Updates a PAC Obras"""
        user = await get_current_user(request)
        existing = await db.pacs_geral_obras.find_one({'pac_obras_id': pac_obras_id})
        if not existing:
            raise HTTPException(status_code=404, detail="PAC Obras não encontrado")
        
        update_data = {k: v for k, v in pac.model_dump().items() if v is not None}
        update_data['updated_at'] = datetime.now(timezone.utc)
        
        await db.pacs_geral_obras.update_one({'pac_obras_id': pac_obras_id}, {'$set': update_data})
        updated = await db.pacs_geral_obras.find_one({'pac_obras_id': pac_obras_id}, {'_id': 0})
        return PACGeralObras(**updated)

    @router.delete("/pacs-geral-obras/{pac_obras_id}")
    async def delete_pac_geral_obras(pac_obras_id: str, request: Request):
        """Deletes a PAC Obras and its items"""
        user = await get_current_user(request)
        result = await db.pacs_geral_obras.delete_one({'pac_obras_id': pac_obras_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="PAC Obras não encontrado")
        await db.pac_obras_items.delete_many({'pac_obras_id': pac_obras_id})
        return {'message': 'PAC Obras excluído com sucesso'}

    # ===== ITEMS =====
    @router.get("/pacs-geral-obras/{pac_obras_id}/items", response_model=List[PACGeralObrasItem])
    async def get_pac_obras_items(pac_obras_id: str, request: Request):
        """Lists items of a PAC Obras"""
        user = await get_current_user(request)
        items = await db.pac_obras_items.find({'pac_obras_id': pac_obras_id}, {'_id': 0}).to_list(10000)
        return [PACGeralObrasItem(**item) for item in items]

    @router.post("/pacs-geral-obras/{pac_obras_id}/items", response_model=PACGeralObrasItem)
    async def create_pac_obras_item(pac_obras_id: str, item: PACGeralObrasItemCreate, request: Request):
        """Adds an item to a PAC Obras"""
        user = await get_current_user(request)
        pac = await db.pacs_geral_obras.find_one({'pac_obras_id': pac_obras_id})
        if not pac:
            raise HTTPException(status_code=404, detail="PAC Obras não encontrado")
        
        item_dict = item.model_dump()
        item_dict['item_id'] = f"itemo_{uuid.uuid4().hex[:12]}"
        item_dict['pac_obras_id'] = pac_obras_id
        
        # Calculate total quantity
        quantidade_total = (
            item_dict.get('qtd_ad', 0) + item_dict.get('qtd_fa', 0) +
            item_dict.get('qtd_sa', 0) + item_dict.get('qtd_se', 0) +
            item_dict.get('qtd_as', 0) + item_dict.get('qtd_ag', 0) +
            item_dict.get('qtd_ob', 0) + item_dict.get('qtd_tr', 0) +
            item_dict.get('qtd_cul', 0)
        )
        item_dict['quantidade_total'] = quantidade_total
        item_dict['valorTotal'] = round(quantidade_total * item_dict.get('valorUnitario', 0), 2)
        item_dict['created_at'] = datetime.now(timezone.utc)
        
        await db.pac_obras_items.insert_one(item_dict)
        item_dict.pop('_id', None)
        return PACGeralObrasItem(**item_dict)

    @router.put("/pacs-geral-obras/{pac_obras_id}/items/{item_id}", response_model=PACGeralObrasItem)
    async def update_pac_obras_item(pac_obras_id: str, item_id: str, item: PACGeralObrasItemUpdate, request: Request):
        """Updates a PAC Obras item"""
        user = await get_current_user(request)
        existing = await db.pac_obras_items.find_one({'item_id': item_id, 'pac_obras_id': pac_obras_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Item não encontrado")
        
        update_data = {k: v for k, v in item.model_dump().items() if v is not None}
        
        # Recalculate totals
        qtd_fields = ['qtd_ad', 'qtd_fa', 'qtd_sa', 'qtd_se', 'qtd_as', 'qtd_ag', 'qtd_ob', 'qtd_tr', 'qtd_cul']
        quantidade_total = sum(update_data.get(f, existing.get(f, 0)) for f in qtd_fields)
        update_data['quantidade_total'] = quantidade_total
        
        valor_unitario = update_data.get('valorUnitario', existing.get('valorUnitario', 0))
        update_data['valorTotal'] = round(quantidade_total * valor_unitario, 2)
        
        await db.pac_obras_items.update_one({'item_id': item_id}, {'$set': update_data})
        updated = await db.pac_obras_items.find_one({'item_id': item_id}, {'_id': 0})
        return PACGeralObrasItem(**updated)

    @router.delete("/pacs-geral-obras/{pac_obras_id}/items/{item_id}")
    async def delete_pac_obras_item(pac_obras_id: str, item_id: str, request: Request):
        """Deletes a PAC Obras item"""
        user = await get_current_user(request)
        result = await db.pac_obras_items.delete_one({'item_id': item_id, 'pac_obras_id': pac_obras_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Item não encontrado")
        return {'message': 'Item excluído com sucesso'}

    # ===== EXPORT PDF =====
    @router.get("/pacs-geral-obras/{pac_obras_id}/export/pdf")
    async def export_pac_obras_pdf(pac_obras_id: str, request: Request):
        """Exports PAC Obras to PDF"""
        user = await get_current_user(request)
        
        pac = await db.pacs_geral_obras.find_one({'pac_obras_id': pac_obras_id}, {'_id': 0})
        if not pac:
            raise HTTPException(status_code=404, detail="PAC Obras não encontrado")
        
        items = await db.pac_obras_items.find({'pac_obras_id': pac_obras_id}, {'_id': 0}).to_list(10000)
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=10*mm, rightMargin=10*mm, topMargin=15*mm, bottomMargin=10*mm)
        
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=12, textColor=colors.HexColor('#1F4E78'), alignment=TA_CENTER, spaceAfter=8)
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, spaceAfter=5)
        
        elements.append(Paragraph(f"PAC OBRAS E SERVIÇOS DE ENGENHARIA", title_style))
        elements.append(Paragraph(f"{pac.get('nome_secretaria', 'N/A')} - Ano: {pac.get('ano', '2026')} - Tipo: {pac.get('tipo_contratacao', 'OBRAS')}", subtitle_style))
        elements.append(Spacer(1, 5))
        
        # Table
        table_data = [['#', 'CATSER', 'Descrição', 'Classif.', 'AD', 'FA', 'SA', 'SE', 'AS', 'AG', 'OB', 'TR', 'CUL', 'Total', 'V.Total', 'Prazo']]
        
        total = 0
        for i, item in enumerate(items, 1):
            valor_total = item.get('valorTotal', 0)
            total += valor_total
            table_data.append([
                str(i),
                item.get('catmat', '')[:8],
                item.get('descricao', '')[:25],
                item.get('codigo_classificacao', '')[:6],
                str(int(item.get('qtd_ad', 0))),
                str(int(item.get('qtd_fa', 0))),
                str(int(item.get('qtd_sa', 0))),
                str(int(item.get('qtd_se', 0))),
                str(int(item.get('qtd_as', 0))),
                str(int(item.get('qtd_ag', 0))),
                str(int(item.get('qtd_ob', 0))),
                str(int(item.get('qtd_tr', 0))),
                str(int(item.get('qtd_cul', 0))),
                str(int(item.get('quantidade_total', 0))),
                f"R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                f"{item.get('prazo_execucao', 0)}m" if item.get('prazo_execucao') else '-'
            ])
        
        table_data.append(['', '', '', '', '', '', '', '', '', '', '', '', '', 'TOTAL:', f"R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), ''])
        
        table = Table(table_data, colWidths=[15, 35, 85, 35, 18, 18, 18, 18, 18, 18, 18, 18, 18, 28, 55, 25])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8E8E8')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(table)
        
        doc.build(elements)
        buffer.seek(0)
        
        filename = f"PAC_Obras_{pac.get('nome_secretaria', 'obras')}_{pac.get('ano', '2026')}.pdf"
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    return router
