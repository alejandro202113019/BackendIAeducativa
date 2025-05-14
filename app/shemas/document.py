from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, HttpUrl, validator


class DocumentType(str, Enum):
    """Tipos de documentos soportados"""
    PDF = "pdf"
    TEXT = "text"
    DOCX = "docx"
    MARKDOWN = "markdown"


class DocumentMetadata(BaseModel):
    """Metadatos del documento"""
    filename: str
    file_size: int = Field(..., description="Tamaño del archivo en bytes")
    content_type: str = Field(..., description="MIME type del archivo")
    page_count: Optional[int] = Field(None, description="Número de páginas (para PDFs)")
    has_images: bool = Field(False, description="Indica si contiene imágenes")
    created_at: Optional[str] = Field(None, description="Fecha de creación del documento (si está disponible)")
    language: Optional[str] = Field(None, description="Idioma detectado")


class DocumentChunk(BaseModel):
    """Chunk de texto extraído de un documento"""
    chunk_id: str = Field(..., description="ID único del chunk")
    text: str = Field(..., description="Texto extraído")
    page_number: Optional[int] = Field(None, description="Número de página (para PDFs)")
    position: int = Field(..., description="Posición del chunk en el documento")


class ProcessedDocument(BaseModel):
    """Documento procesado con texto extraído"""
    document_id: str = Field(..., description="ID único del documento")
    metadata: DocumentMetadata
    text: str = Field(..., description="Texto completo extraído")
    chunks: List[DocumentChunk] = Field(default_factory=list, description="Texto dividido en chunks")
    entities: Optional[Dict[str, List[str]]] = Field(None, description="Entidades extraídas por tipo")
    keywords: Optional[List[str]] = Field(None, description="Palabras clave extraídas")


class UploadResponse(BaseModel):
    """Respuesta a la subida de un documento"""
    document_id: str
    metadata: DocumentMetadata
    text_preview: str = Field(..., description="Vista previa del texto extraído (primeros 200 caracteres)")
    page_count: Optional[int] = None
    status: str = "success"
    word_count: int
    estimated_reading_time: float = Field(
        ..., description="Tiempo estimado de lectura en minutos (asumiendo 200 palabras por minuto)"
    )


class DocumentContent(BaseModel):
    """Contenido de texto para procesar directamente"""
    text: str = Field(..., min_length=10, description="Texto a procesar")
    title: Optional[str] = Field(None, description="Título del contenido")
    source: Optional[str] = Field(None, description="Fuente del contenido")
    
    @validator('text')
    def validate_text_length(cls, v):
        if len(v) < 10:
            raise ValueError('El texto debe tener al menos 10 caracteres')
        return v


class DocumentReference(BaseModel):
    """Referencia a un documento ya procesado"""
    document_id: str = Field(..., description="ID del documento previamente subido")


class DocumentRequest(BaseModel):
    """Request para operaciones que requieren un documento"""
    document_id: Optional[str] = Field(None, description="ID del documento previamente procesado")
    content: Optional[DocumentContent] = Field(None, description="Contenido directo a procesar")
    
    @validator('document_id', 'content')
    def validate_document_source(cls, v, values):
        # Asegurar que se proporciona exactamente una fuente de documento
        if 'document_id' in values and values['document_id'] and 'content' in values and values['content']:
            raise ValueError('Proporcione solo document_id o content, no ambos')
        if ('document_id' not in values or not values['document_id']) and ('content' not in values or not values['content']):
            raise ValueError('Debe proporcionar document_id o content')
        return v