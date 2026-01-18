"""
MROSC Routes - Prestação de Contas
Handles MROSC (Marco Regulatório das Organizações da Sociedade Civil) operations
"""
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
import uuid
import os
import shutil

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT

router = APIRouter(prefix="/api/mrosc", tags=["Prestação de Contas MROSC"])

# Expense natures according to Law 13.019/2014
NATUREZAS_DESPESA_MROSC = {
    "319011": {"nome": "Vencimentos e Vantagens Fixas - Pessoal Civil", "categoria": "RH"},
    "319013": {"nome": "Obrigações Patronais", "categoria": "RH"},
    "319094": {"nome": "Indenizações e Restituições Trabalhistas", "categoria": "RH"},
    "339030": {"nome": "Material de Consumo", "categoria": "MATERIAIS"},
    "339031": {"nome": "Premiações Culturais, Artísticas e Científicas", "categoria": "PREMIACOES"},
    "339035": {"nome": "Serviços de Consultoria", "categoria": "SERVICOS"},
    "339036": {"nome": "Outros Serviços de Terceiros - Pessoa Física", "categoria": "SERVICOS"},
    "339039": {"nome": "Outros Serviços de Terceiros - Pessoa Jurídica", "categoria": "SERVICOS"},
    "339046": {"nome": "Auxílio-Alimentação", "categoria": "BENEFICIOS"},
    "339049": {"nome": "Auxílio-Transporte", "categoria": "BENEFICIOS"},
    "339047": {"nome": "Obrigações Tributárias e Contributivas", "categoria": "TRIBUTOS"},
    "449051": {"nome": "Obras e Instalações", "categoria": "INVESTIMENTOS"},
    "449052": {"nome": "Equipamentos e Material Permanente", "categoria": "INVESTIMENTOS"}
}

UPLOAD_DIR = Path("/app/backend/uploads/mrosc")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def calcular_encargos_clt(salario_bruto: float, numero_meses: int) -> dict:
    """Calculates CLT labor charges according to MROSC"""
    provisao_ferias = salario_bruto / 12
    provisao_13_salario = salario_bruto / 12
    base_fgts = salario_bruto + provisao_ferias + provisao_13_salario
    fgts = base_fgts * 0.08
    inss_patronal = salario_bruto * 0.20
    custo_mensal = salario_bruto + provisao_ferias + provisao_13_salario + fgts + inss_patronal
    return {
        'provisao_ferias': round(provisao_ferias, 2),
        'provisao_13_salario': round(provisao_13_salario, 2),
        'fgts': round(fgts, 2),
        'inss_patronal': round(inss_patronal, 2),
        'custo_mensal_total': round(custo_mensal, 2),
        'custo_total_projeto': round(custo_mensal * numero_meses, 2)
    }


def calcular_media_orcamentos(orc1: float, orc2: float, orc3: float) -> float:
    """Calculates average of three quotes"""
    valores = [v for v in [orc1, orc2, orc3] if v and v > 0]
    return round(sum(valores) / len(valores), 2) if valores else 0.0


def setup_mrosc_routes(db, get_current_user, ProjetoMROSC, ProjetoMROSCCreate, ProjetoMROSCUpdate, RecursoHumanoMROSC, RecursoHumanoMROSCCreate, DespesaMROSC, DespesaMROSCCreate, DocumentoMROSC):
    """Configure MROSC routes with injected dependencies"""

    @router.get("/naturezas-despesa")
    async def get_naturezas_despesa():
        """Returns expense natures according to MROSC"""
        return NATUREZAS_DESPESA_MROSC

    # ===== PROJECTS =====
    @router.get("/projetos", response_model=List[ProjetoMROSC])
    async def get_projetos_mrosc(request: Request):
        """Lists all MROSC projects"""
        user = await get_current_user(request)
        query = {} if user.is_admin else {'user_id': user.user_id}
        projetos = await db.mrosc_projetos.find(query, {'_id': 0}).to_list(100)
        return [ProjetoMROSC(**p) for p in projetos]

    @router.post("/projetos", response_model=ProjetoMROSC)
    async def create_projeto_mrosc(projeto_data: ProjetoMROSCCreate, request: Request):
        """Creates a new MROSC project"""
        user = await get_current_user(request)
        projeto_id = f"mrosc_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        projeto_doc = {
            'projeto_id': projeto_id,
            'user_id': user.user_id,
            **projeto_data.model_dump(),
            'created_at': now,
            'updated_at': now
        }
        await db.mrosc_projetos.insert_one(projeto_doc)
        projeto_doc.pop('_id', None)
        return ProjetoMROSC(**projeto_doc)

    @router.get("/projetos/{projeto_id}", response_model=ProjetoMROSC)
    async def get_projeto_mrosc(projeto_id: str, request: Request):
        """Gets a specific MROSC project"""
        user = await get_current_user(request)
        projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
        if not projeto:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        return ProjetoMROSC(**projeto)

    @router.put("/projetos/{projeto_id}", response_model=ProjetoMROSC)
    async def update_projeto_mrosc(projeto_id: str, projeto_data: ProjetoMROSCUpdate, request: Request):
        """Updates a MROSC project"""
        user = await get_current_user(request)
        projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
        if not projeto:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        update_data = {k: v for k, v in projeto_data.model_dump().items() if v is not None}
        update_data['updated_at'] = datetime.now(timezone.utc)
        await db.mrosc_projetos.update_one({'projeto_id': projeto_id}, {'$set': update_data})
        updated = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
        return ProjetoMROSC(**updated)

    @router.delete("/projetos/{projeto_id}")
    async def delete_projeto_mrosc(projeto_id: str, request: Request):
        """Deletes a MROSC project and all related data"""
        user = await get_current_user(request)
        projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
        if not projeto:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        await db.mrosc_rh.delete_many({'projeto_id': projeto_id})
        await db.mrosc_despesas.delete_many({'projeto_id': projeto_id})
        await db.mrosc_documentos.delete_many({'projeto_id': projeto_id})
        await db.mrosc_projetos.delete_one({'projeto_id': projeto_id})
        return {'message': 'Projeto excluído com sucesso'}

    # ===== HUMAN RESOURCES =====
    @router.get("/projetos/{projeto_id}/rh", response_model=List[RecursoHumanoMROSC])
    async def get_rh_mrosc(projeto_id: str, request: Request):
        """Lists human resources of a project"""
        user = await get_current_user(request)
        rhs = await db.mrosc_rh.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(100)
        return [RecursoHumanoMROSC(**rh) for rh in rhs]

    @router.post("/projetos/{projeto_id}/rh", response_model=RecursoHumanoMROSC)
    async def create_rh_mrosc(projeto_id: str, rh_data: RecursoHumanoMROSCCreate, request: Request):
        """Adds a human resource to the project"""
        user = await get_current_user(request)
        projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
        if not projeto:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        
        rh_id = f"rh_{uuid.uuid4().hex[:12]}"
        rh_dict = rh_data.model_dump()
        
        # Calculate charges
        encargos = calcular_encargos_clt(rh_dict['salario_bruto'], rh_dict['numero_meses'])
        rh_dict.update(encargos)
        
        # Add benefits
        rh_dict['custo_mensal_total'] += rh_dict.get('vale_transporte', 0) + rh_dict.get('vale_alimentacao', 0)
        rh_dict['custo_total_projeto'] = rh_dict['custo_mensal_total'] * rh_dict['numero_meses']
        
        # Calculate average quotes
        rh_dict['media_orcamentos'] = calcular_media_orcamentos(
            rh_dict.get('orcamento_1', 0),
            rh_dict.get('orcamento_2', 0),
            rh_dict.get('orcamento_3', 0)
        )
        
        rh_dict['rh_id'] = rh_id
        rh_dict['projeto_id'] = projeto_id
        rh_dict['created_at'] = datetime.now(timezone.utc)
        
        await db.mrosc_rh.insert_one(rh_dict)
        rh_dict.pop('_id', None)
        return RecursoHumanoMROSC(**rh_dict)

    @router.delete("/projetos/{projeto_id}/rh/{rh_id}")
    async def delete_rh_mrosc(projeto_id: str, rh_id: str, request: Request):
        """Deletes a human resource"""
        user = await get_current_user(request)
        result = await db.mrosc_rh.delete_one({'rh_id': rh_id, 'projeto_id': projeto_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Recurso humano não encontrado")
        return {'message': 'Recurso humano excluído com sucesso'}

    # ===== EXPENSES =====
    @router.get("/projetos/{projeto_id}/despesas", response_model=List[DespesaMROSC])
    async def get_despesas_mrosc(projeto_id: str, request: Request):
        """Lists expenses of a project"""
        user = await get_current_user(request)
        despesas = await db.mrosc_despesas.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(100)
        return [DespesaMROSC(**d) for d in despesas]

    @router.post("/projetos/{projeto_id}/despesas", response_model=DespesaMROSC)
    async def create_despesa_mrosc(projeto_id: str, despesa_data: DespesaMROSCCreate, request: Request):
        """Adds an expense to the project"""
        user = await get_current_user(request)
        projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
        if not projeto:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        
        despesa_id = f"desp_{uuid.uuid4().hex[:12]}"
        despesa_dict = despesa_data.model_dump()
        
        # Calculate average and total
        despesa_dict['media_orcamentos'] = calcular_media_orcamentos(
            despesa_dict['orcamento_1'],
            despesa_dict['orcamento_2'],
            despesa_dict['orcamento_3']
        )
        despesa_dict['valor_total'] = round(despesa_dict['quantidade'] * despesa_dict['valor_unitario'], 2)
        
        despesa_dict['despesa_id'] = despesa_id
        despesa_dict['projeto_id'] = projeto_id
        despesa_dict['created_at'] = datetime.now(timezone.utc)
        
        await db.mrosc_despesas.insert_one(despesa_dict)
        despesa_dict.pop('_id', None)
        return DespesaMROSC(**despesa_dict)

    @router.delete("/projetos/{projeto_id}/despesas/{despesa_id}")
    async def delete_despesa_mrosc(projeto_id: str, despesa_id: str, request: Request):
        """Deletes an expense"""
        user = await get_current_user(request)
        result = await db.mrosc_despesas.delete_one({'despesa_id': despesa_id, 'projeto_id': projeto_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Despesa não encontrada")
        return {'message': 'Despesa excluída com sucesso'}

    # ===== SUMMARY =====
    @router.get("/projetos/{projeto_id}/resumo")
    async def get_resumo_mrosc(projeto_id: str, request: Request):
        """Gets financial summary of a project"""
        user = await get_current_user(request)
        projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
        if not projeto:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        
        rhs = await db.mrosc_rh.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(100)
        despesas = await db.mrosc_despesas.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(100)
        documentos = await db.mrosc_documentos.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(100)
        
        total_rh = sum(rh.get('custo_total_projeto', 0) for rh in rhs)
        total_despesas = sum(d.get('valor_total', 0) for d in despesas)
        docs_validados = sum(1 for d in documentos if d.get('validado'))
        
        return {
            'projeto': projeto,
            'resumo_rh': {
                'quantidade': len(rhs),
                'total': total_rh
            },
            'resumo_despesas': {
                'quantidade': len(despesas),
                'total': total_despesas
            },
            'resumo_documentos': {
                'total': len(documentos),
                'validados': docs_validados
            },
            'total_geral': total_rh + total_despesas
        }

    # ===== DOCUMENTS =====
    @router.get("/projetos/{projeto_id}/documentos")
    async def get_documentos_mrosc(projeto_id: str, request: Request):
        """Lists documents of a project"""
        user = await get_current_user(request)
        documentos = await db.mrosc_documentos.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(100)
        return documentos

    @router.post("/projetos/{projeto_id}/documentos/upload")
    async def upload_documento_mrosc(
        projeto_id: str,
        request: Request,
        file: UploadFile = File(...),
        tipo_documento: str = "COMPROVANTE",
        numero_documento: str = "",
        data_documento: str = "",
        valor: float = 0,
        despesa_id: str = None
    ):
        """Uploads a document to the project"""
        user = await get_current_user(request)
        projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
        if not projeto:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        
        # Validate file type (PDF and images)
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg']
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Tipo de arquivo não permitido. Use PDF, JPG ou PNG.")
        
        # Save file
        documento_id = f"doc_{uuid.uuid4().hex[:12]}"
        ext = file.filename.split('.')[-1] if '.' in file.filename else 'pdf'
        filename = f"{documento_id}.{ext}"
        filepath = UPLOAD_DIR / projeto_id
        filepath.mkdir(parents=True, exist_ok=True)
        
        with open(filepath / filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parse date
        try:
            data_doc = datetime.fromisoformat(data_documento) if data_documento else datetime.now(timezone.utc)
        except:
            data_doc = datetime.now(timezone.utc)
        
        documento_doc = {
            'documento_id': documento_id,
            'projeto_id': projeto_id,
            'despesa_id': despesa_id,
            'tipo_documento': tipo_documento,
            'numero_documento': numero_documento,
            'data_documento': data_doc,
            'valor': valor,
            'arquivo_url': f"/api/mrosc/documentos/{documento_id}/download",
            'arquivo_nome': file.filename,
            'arquivo_tamanho': file.size or 0,
            'validado': False,
            'created_at': datetime.now(timezone.utc)
        }
        
        await db.mrosc_documentos.insert_one(documento_doc)
        documento_doc.pop('_id', None)
        return documento_doc

    @router.get("/documentos/{documento_id}/download")
    async def download_documento_mrosc(documento_id: str, request: Request):
        """Downloads a document"""
        user = await get_current_user(request)
        documento = await db.mrosc_documentos.find_one({'documento_id': documento_id}, {'_id': 0})
        if not documento:
            raise HTTPException(status_code=404, detail="Documento não encontrado")
        
        projeto_id = documento['projeto_id']
        ext = documento['arquivo_nome'].split('.')[-1] if '.' in documento['arquivo_nome'] else 'pdf'
        filepath = UPLOAD_DIR / projeto_id / f"{documento_id}.{ext}"
        
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        
        content_type = 'application/pdf' if ext.lower() == 'pdf' else f'image/{ext.lower()}'
        
        return StreamingResponse(
            open(filepath, 'rb'),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={documento['arquivo_nome']}"}
        )

    @router.delete("/projetos/{projeto_id}/documentos/{documento_id}")
    async def delete_documento_mrosc(projeto_id: str, documento_id: str, request: Request):
        """Deletes a document"""
        user = await get_current_user(request)
        documento = await db.mrosc_documentos.find_one({'documento_id': documento_id}, {'_id': 0})
        if not documento:
            raise HTTPException(status_code=404, detail="Documento não encontrado")
        
        # Delete file
        ext = documento['arquivo_nome'].split('.')[-1] if '.' in documento['arquivo_nome'] else 'pdf'
        filepath = UPLOAD_DIR / projeto_id / f"{documento_id}.{ext}"
        if filepath.exists():
            filepath.unlink()
        
        await db.mrosc_documentos.delete_one({'documento_id': documento_id})
        return {'message': 'Documento excluído com sucesso'}

    @router.put("/projetos/{projeto_id}/documentos/{documento_id}/validar")
    async def validar_documento_mrosc(projeto_id: str, documento_id: str, request: Request, validado: bool = True, observacoes: str = None):
        """Validates or invalidates a document"""
        user = await get_current_user(request)
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="Apenas administradores podem validar documentos")
        
        documento = await db.mrosc_documentos.find_one({'documento_id': documento_id}, {'_id': 0})
        if not documento:
            raise HTTPException(status_code=404, detail="Documento não encontrado")
        
        await db.mrosc_documentos.update_one(
            {'documento_id': documento_id},
            {'$set': {
                'validado': validado,
                'validado_por': user.user_id,
                'data_validacao': datetime.now(timezone.utc),
                'observacoes_validacao': observacoes
            }}
        )
        
        return {'message': 'Documento validado com sucesso' if validado else 'Documento invalidado'}

    # ===== WORKFLOW =====
    @router.post("/projetos/{projeto_id}/submeter")
    async def submeter_projeto_mrosc(projeto_id: str, request: Request):
        """Submits project for review"""
        user = await get_current_user(request)
        projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
        if not projeto:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        
        if projeto.get('status') not in ['ELABORACAO', 'CORRECAO']:
            raise HTTPException(status_code=400, detail="Projeto não pode ser submetido no status atual")
        
        await db.mrosc_projetos.update_one(
            {'projeto_id': projeto_id},
            {'$set': {
                'status': 'SUBMETIDO',
                'data_submissao': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }}
        )
        
        # Log action
        await db.mrosc_historico.insert_one({
            'historico_id': f"hist_{uuid.uuid4().hex[:12]}",
            'projeto_id': projeto_id,
            'acao': 'SUBMISSAO',
            'usuario_id': user.user_id,
            'usuario_nome': user.name,
            'data': datetime.now(timezone.utc),
            'observacao': 'Projeto submetido para análise'
        })
        
        return {'message': 'Projeto submetido com sucesso'}

    @router.post("/projetos/{projeto_id}/receber")
    async def receber_projeto_mrosc(projeto_id: str, request: Request):
        """Receives submitted project"""
        user = await get_current_user(request)
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="Apenas administradores podem receber projetos")
        
        projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
        if not projeto:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        
        await db.mrosc_projetos.update_one(
            {'projeto_id': projeto_id},
            {'$set': {
                'status': 'ANALISE',
                'data_recebimento': datetime.now(timezone.utc),
                'recebido_por': user.user_id,
                'updated_at': datetime.now(timezone.utc)
            }}
        )
        
        await db.mrosc_historico.insert_one({
            'historico_id': f"hist_{uuid.uuid4().hex[:12]}",
            'projeto_id': projeto_id,
            'acao': 'RECEBIMENTO',
            'usuario_id': user.user_id,
            'usuario_nome': user.name,
            'data': datetime.now(timezone.utc),
            'observacao': 'Projeto recebido para análise'
        })
        
        return {'message': 'Projeto recebido com sucesso'}

    @router.post("/projetos/{projeto_id}/solicitar-correcao")
    async def solicitar_correcao_mrosc(projeto_id: str, request: Request, observacao: str = ""):
        """Requests correction for project"""
        user = await get_current_user(request)
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="Apenas administradores podem solicitar correções")
        
        projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
        if not projeto:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        
        await db.mrosc_projetos.update_one(
            {'projeto_id': projeto_id},
            {'$set': {
                'status': 'CORRECAO',
                'observacao_correcao': observacao,
                'data_solicitacao_correcao': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }}
        )
        
        await db.mrosc_historico.insert_one({
            'historico_id': f"hist_{uuid.uuid4().hex[:12]}",
            'projeto_id': projeto_id,
            'acao': 'SOLICITACAO_CORRECAO',
            'usuario_id': user.user_id,
            'usuario_nome': user.name,
            'data': datetime.now(timezone.utc),
            'observacao': observacao or 'Correções solicitadas'
        })
        
        return {'message': 'Solicitação de correção enviada'}

    @router.post("/projetos/{projeto_id}/aprovar")
    async def aprovar_projeto_mrosc(projeto_id: str, request: Request, observacao: str = ""):
        """Approves project"""
        user = await get_current_user(request)
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="Apenas administradores podem aprovar projetos")
        
        projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
        if not projeto:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        
        await db.mrosc_projetos.update_one(
            {'projeto_id': projeto_id},
            {'$set': {
                'status': 'APROVADO',
                'data_aprovacao': datetime.now(timezone.utc),
                'aprovado_por': user.user_id,
                'observacao_aprovacao': observacao,
                'updated_at': datetime.now(timezone.utc)
            }}
        )
        
        await db.mrosc_historico.insert_one({
            'historico_id': f"hist_{uuid.uuid4().hex[:12]}",
            'projeto_id': projeto_id,
            'acao': 'APROVACAO',
            'usuario_id': user.user_id,
            'usuario_nome': user.name,
            'data': datetime.now(timezone.utc),
            'observacao': observacao or 'Projeto aprovado'
        })
        
        return {'message': 'Projeto aprovado com sucesso'}

    @router.get("/projetos/{projeto_id}/historico")
    async def get_historico_mrosc(projeto_id: str, request: Request):
        """Gets project history"""
        user = await get_current_user(request)
        historico = await db.mrosc_historico.find(
            {'projeto_id': projeto_id},
            {'_id': 0}
        ).sort('data', -1).to_list(100)
        return historico

    # ===== PDF REPORT =====
    @router.get("/projetos/{projeto_id}/relatorio/pdf")
    async def gerar_relatorio_mrosc_pdf(projeto_id: str, request: Request):
        """Generates PDF report of the project"""
        user = await get_current_user(request)
        
        projeto = await db.mrosc_projetos.find_one({'projeto_id': projeto_id}, {'_id': 0})
        if not projeto:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        
        rhs = await db.mrosc_rh.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(100)
        despesas = await db.mrosc_despesas.find({'projeto_id': projeto_id}, {'_id': 0}).to_list(100)
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
        
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=14, textColor=colors.HexColor('#1F4E78'), alignment=TA_CENTER, spaceAfter=10)
        section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=11, textColor=colors.HexColor('#2E7D32'), spaceBefore=10, spaceAfter=5)
        
        # Header
        elements.append(Paragraph("PRESTAÇÃO DE CONTAS - MROSC", title_style))
        elements.append(Paragraph(f"Lei 13.019/2014 - Marco Regulatório das OSCs", ParagraphStyle('Sub', fontSize=9, alignment=TA_CENTER)))
        elements.append(Spacer(1, 10))
        
        # Project info
        elements.append(Paragraph("1. DADOS DO PROJETO", section_style))
        info_data = [
            ['Nome do Projeto:', projeto.get('nome_projeto', 'N/A')],
            ['Organização:', projeto.get('organizacao_parceira', 'N/A')],
            ['CNPJ:', projeto.get('cnpj_parceira', 'N/A')],
            ['Responsável:', projeto.get('responsavel_osc', 'N/A')],
            ['Valor Total:', f"R$ {projeto.get('valor_total', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')],
            ['Status:', projeto.get('status', 'ELABORACAO')]
        ]
        
        info_table = Table(info_data, colWidths=[80, 300])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(info_table)
        
        # Human Resources
        if rhs:
            elements.append(Paragraph("2. RECURSOS HUMANOS", section_style))
            rh_data = [['Função', 'Regime', 'Salário', 'Custo Total']]
            total_rh = 0
            for rh in rhs:
                custo = rh.get('custo_total_projeto', 0)
                total_rh += custo
                rh_data.append([
                    rh.get('nome_funcao', '')[:30],
                    rh.get('regime_contratacao', ''),
                    f"R$ {rh.get('salario_bruto', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                    f"R$ {custo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                ])
            rh_data.append(['', '', 'TOTAL:', f"R$ {total_rh:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')])
            
            rh_table = Table(rh_data, colWidths=[120, 60, 80, 80])
            rh_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8E8E8')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            elements.append(rh_table)
        
        # Expenses
        if despesas:
            elements.append(Paragraph("3. DESPESAS", section_style))
            desp_data = [['Item', 'Natureza', 'Qtd', 'V.Unit', 'V.Total']]
            total_desp = 0
            for d in despesas:
                vtotal = d.get('valor_total', 0)
                total_desp += vtotal
                desp_data.append([
                    d.get('item_despesa', '')[:25],
                    d.get('natureza_despesa', '')[:6],
                    str(d.get('quantidade', 0)),
                    f"R$ {d.get('valor_unitario', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                    f"R$ {vtotal:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                ])
            desp_data.append(['', '', '', 'TOTAL:', f"R$ {total_desp:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')])
            
            desp_table = Table(desp_data, colWidths=[100, 50, 35, 70, 70])
            desp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8E8E8')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            elements.append(desp_table)
        
        # Footer
        elements.append(Spacer(1, 15))
        elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", ParagraphStyle('Footer', fontSize=8, alignment=TA_CENTER, textColor=colors.gray)))
        
        doc.build(elements)
        buffer.seek(0)
        
        filename = f"MROSC_{projeto.get('nome_projeto', 'projeto')[:20]}_{datetime.now().strftime('%Y%m%d')}.pdf"
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    return router
