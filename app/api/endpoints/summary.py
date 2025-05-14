import uuid
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_nlp_service, get_document_processor_service, get_openai_service, get_visualization_service
from app.schemas.summary import (
    CreateSummaryRequest,
    SummaryResponse,
    VisualizationResponse,
    VisualizationType
)
from app.services.document_processor import DocumentProcessor
from app.services.nlp_service import NLPService
from app.services.openai_service import OpenAIService
from app.services.visualization import VisualizationService

router = APIRouter()

@router.post(
    "/",
    response_model=SummaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generar un resumen",
    description="Genera un resumen de un documento o texto proporcionado"
)
async def create_summary(
    request: CreateSummaryRequest,
    doc_processor: DocumentProcessor = Depends(get_document_processor_service),
    nlp_service: NLPService = Depends(get_nlp_service),
    openai_service: OpenAIService = Depends(get_openai_service)
):
    """
    Endpoint para generar un resumen de un documento.
    
    Args:
        request: Datos para generar el resumen
        doc_processor: Servicio de procesamiento de documentos
        nlp_service: Servicio de NLP
        openai_service: Servicio de OpenAI
        
    Returns:
        Resumen generado
    """
    try:
        # Obtener el texto del documento si se proporciona un ID
        document_text = None
        if request.document_id:
            document = await doc_processor.get_document(str(request.document_id))
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Documento no encontrado: {request.document_id}"
                )
            document_text = document.text
        else:
            # Usar el texto proporcionado directamente
            document_text = request.text
            
        if not document_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se debe proporcionar texto o document_id"
            )
        
        # Preprocesar texto con NLP si es necesario
        if request.preprocess:
            document_text = await nlp_service.preprocess_text(document_text)
        
        # Generar resumen
        summary_text = await openai_service.generate_summary(document_text, request.length)
        
        # Extraer keywords si se solicita
        keywords = []
        if request.include_keywords:
            keywords = await nlp_service.extract_keywords(document_text, top_n=10)
        
        # Crear respuesta
        summary_id = str(uuid.uuid4())
        response = SummaryResponse(
            summary_id=summary_id,
            document_id=request.document_id,
            text=summary_text,
            length=request.length,
            keywords=keywords,
            created_at="2023-11-01T12:00:00Z"  # En producción usar datetime.now().isoformat()
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar el resumen: {str(e)}"
        )

@router.get(
    "/{summary_id}",
    response_model=SummaryResponse,
    summary="Obtener un resumen",
    description="Recupera un resumen generado previamente por su ID"
)
async def get_summary(summary_id: uuid.UUID):
    """
    Endpoint para recuperar un resumen por su ID.
    
    Args:
        summary_id: ID del resumen
        
    Returns:
        Resumen recuperado
    """
    # En un sistema real, esto consultaría una base de datos
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Esta funcionalidad aún no está implementada"
    )

@router.post(
    "/visualization",
    response_model=VisualizationResponse,
    summary="Generar una visualización",
    description="Genera una visualización basada en un documento o texto"
)
async def create_visualization(
    document_id: Optional[uuid.UUID] = Query(None),
    text: Optional[str] = Query(None),
    viz_type: VisualizationType = Query(VisualizationType.WORDCLOUD),
    doc_processor: DocumentProcessor = Depends(get_document_processor_service),
    viz_service: VisualizationService = Depends(get_visualization_service)
):
    """
    Endpoint para generar visualizaciones a partir de texto.
    
    Args:
        document_id: ID opcional del documento
        text: Texto opcional
        viz_type: Tipo de visualización
        doc_processor: Servicio de procesamiento de documentos
        viz_service: Servicio de visualización
        
    Returns:
        Datos de la visualización generada
    """
    try:
        # Obtener texto de una de las fuentes
        source_text = None
        if document_id:
            document = await doc_processor.get_document(str(document_id))
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Documento no encontrado: {document_id}"
                )
            source_text = document.text
        elif text:
            source_text = text
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se debe proporcionar texto o document_id"
            )
            
        # Generar visualización
        viz_data = await viz_service.generate_visualization(
            text=source_text,
            viz_type=viz_type
        )
        
        # Crear respuesta
        response = VisualizationResponse(
            visualization_id=str(uuid.uuid4()),
            document_id=document_id,
            type=viz_type,
            data=viz_data
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar la visualización: {str(e)}"
        )