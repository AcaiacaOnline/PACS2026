"""
Document Validation Routes - Refactored Module
Handles digital signature validation for documents
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import logging

router = APIRouter(prefix="/api/validar", tags=["Validação de Documentos"])

class DocumentValidationRequest(BaseModel):
    validation_code: str

class DocumentValidationResponse(BaseModel):
    is_valid: bool
    message: str
    document_info: Optional[dict] = None

def mask_cpf(cpf: str) -> str:
    """Mask CPF for privacy"""
    if not cpf or len(cpf) < 6:
        return '***'
    return f"***{cpf[3:6]}***"

def setup_validation_routes(db):
    """Setup validation routes with database dependency"""

    @router.get("/")
    async def validation_info():
        """Returns information about document validation service"""
        return {
            "titulo": "Validação de Documentos Assinados Digitalmente",
            "descricao": "Use este serviço para verificar a autenticidade de documentos emitidos pela Prefeitura Municipal de Acaiaca.",
            "instrucoes": [
                "Digite o código de validação presente no selo de assinatura do documento",
                "O código possui o formato: DOC-XXXXXXXX-YYYYMMDD",
                "Você também pode escanear o QR Code presente no documento"
            ]
        }

    @router.get("/{validation_code}")
    async def validate_document_get(validation_code: str):
        """Validates a document by code (via QR Code or direct link)"""
        return await validate_document_internal(validation_code)

    @router.post("/verificar")
    async def validate_document_post(request: DocumentValidationRequest):
        """Validates a document by code (via form)"""
        return await validate_document_internal(request.validation_code)

    async def validate_document_internal(validation_code: str) -> DocumentValidationResponse:
        """Internal function for document validation"""
        try:
            signature = await db.document_signatures.find_one(
                {'validation_code': validation_code.strip().upper()},
                {'_id': 0}
            )
            
            if not signature:
                return DocumentValidationResponse(
                    is_valid=False,
                    message="Código de validação não encontrado. Verifique se o código foi digitado corretamente.",
                    document_info=None
                )
            
            if not signature.get('is_valid', True):
                return DocumentValidationResponse(
                    is_valid=False,
                    message="Este documento foi revogado ou invalidado.",
                    document_info=None
                )
            
            signers_info = []
            for signer in signature.get('signers', []):
                signers_info.append({
                    'nome': signer.get('nome', 'N/A'),
                    'cargo': signer.get('cargo', ''),
                    'cpf_masked': mask_cpf(signer.get('cpf', '')),
                    'email': signer.get('email', '')[:3] + '***@***' if signer.get('email') else ''
                })
            
            return DocumentValidationResponse(
                is_valid=True,
                message="Documento válido! A assinatura digital foi verificada com sucesso.",
                document_info={
                    'tipo_documento': signature.get('document_type', 'Documento'),
                    'data_assinatura': signature.get('created_at').isoformat() if signature.get('created_at') else None,
                    'assinantes': signers_info,
                    'hash_parcial': signature.get('hash_document', '')[:16] + '...'
                }
            )
        except Exception as e:
            logging.error(f"Erro ao validar documento: {e}")
            return DocumentValidationResponse(
                is_valid=False,
                message="Erro ao processar a validação. Tente novamente.",
                document_info=None
            )

    return router
