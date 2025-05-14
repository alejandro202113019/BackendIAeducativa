import uuid
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.dependencies import get_document_processor_service
from app.schemas.document import (
    DocumentResponse, 
    DocumentType,
    DocumentUploadResponse
)
from app.services.document_processor import DocumentProcessor

router = APIRouter()

@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subir un nuevo documento",
    description="Sube un documento (PDF, texto, etc.) para su procesamiento"
)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(None),
    document_type: DocumentType = Form(DocumentType.PDF),
    subject: str = Form(None),
    doc_processor: DocumentProcessor = Depends(get_document_processor_service)
):
    """
    Endpoint para subir documentos educativos.
    
    Args:
        file: Archivo a subir
        title: Título opcional del documento
        document_type: Tipo de documento
        subject: Materia o asignatura relacionada
        doc_processor: Servicio de procesamiento de documentos
        
    Returns:
        JSON con los detalles del documento subido
    """
    # Validar el tipo de archivo
    if document_type == DocumentType.PDF and not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser un PDF"
        )
    
    try:
        # Leer el contenido del archivo
        content = await file.read()
        
        # Generar un ID único para el documento
        document_id = str(uuid.uuid4())
        
        # Procesar el documento
        result = await doc_processor.process_document(
            content=content,
            filename=file.filename,
            document_id=document_id,
            document_type=document_type
        )
        
        # Crear respuesta
        response = DocumentUploadResponse(
            document_id=document_id,
            title=title or file.filename,
            file_name=file.filename,
            document_type=document_type,
            subject=subject,
            page_count=result.get("page_count", 1),
            text_length=result.get("text_length", 0),
            status="processed"
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el documento: {str(e)}"
        )

@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Obtener un documento",
    description="Recupera un documento procesado por su ID"
)
async def get_document(
    document_id: uuid.UUID,
    doc_processor: DocumentProcessor = Depends(get_document_processor_service)
):
    """
    Endpoint para recuperar detalles de un documento.
    
    Args:
        document_id: ID del documento
        doc_processor: Servicio de procesamiento de documentos
        
    Returns:
        JSON con los detalles del documento
    """
    try:
        document = await doc_processor.get_document(str(document_id))
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento no encontrado: {document_id}"
            )
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al recuperar el documento: {str(e)}"
        )

@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un documento",
    description="Elimina un documento por su ID"
)
async def delete_document(
    document_id: uuid.UUID,
    doc_processor: DocumentProcessor = Depends(get_document_processor_service)
):
    """
    Endpoint para eliminar un documento.
    
    Args:
        document_id: ID del documento
        doc_processor: Servicio de procesamiento de documentos
    """
    try:
        result = await doc_processor.delete_document(str(document_id))
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento no encontrado: {document_id}"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar el documento: {str(e)}"
        )

@router.get(
    "/",
    response_model=List[DocumentResponse],
    summary="Listar documentos",
    description="Obtiene una lista de todos los documentos disponibles"
)
async def list_documents(
    subject: str = None,
    doc_processor: DocumentProcessor = Depends(get_document_processor_service)
):
    """
    Endpoint para listar todos los documentos con filtros opcionales.
    
    Args:
        subject: Filtrar por materia/asignatura
        doc_processor: Servicio de procesamiento de documentos
        
    Returns:
        Lista de documentos
    """
    try:
        documents = await doc_processor.list_documents(subject=subject)
        return documents
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar los documentos: {str(e)}"
        )