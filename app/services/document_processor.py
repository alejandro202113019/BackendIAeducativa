import os
import uuid
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import PyPDF2
from PIL import Image
import pytesseract
from fastapi import HTTPException, UploadFile, status

from app.config import TESSERACT_CMD, TESSERACT_LANG, CHUNK_SIZE
from app.core.security import content_security_check, filter_educational_content
from app.core.utils import chunk_text, generate_file_id
from app.schemas.document import (
    DocumentChunk, DocumentMetadata, DocumentType, ProcessedDocument
)
from app.services.nlp_service import NLPService


class DocumentProcessor:
    """Servicio para procesar documentos y extraer texto"""
    
    def __init__(self, nlp_service: NLPService):
        """
        Inicializa el procesador de documentos
        
        Args:
            nlp_service: Servicio de procesamiento de lenguaje natural
        """
        self.nlp_service = nlp_service
        # Configurar Tesseract
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    
    async def process_upload(
        self, file: UploadFile, perform_ocr: bool = True
    ) -> ProcessedDocument:
        """
        Procesa un archivo subido para extraer su texto
        
        Args:
            file: Archivo subido
            perform_ocr: Si debe realizar OCR en imágenes detectadas
            
        Returns:
            Documento procesado con texto extraído
        """
        # Leer contenido del archivo
        content = await file.read()
        
        # Determinar tipo de documento
        file_ext = os.path.splitext(file.filename)[1].lower()
        doc_type = self._get_document_type(file_ext)
        
        # Procesar según tipo
        if doc_type == DocumentType.PDF:
            extracted_text, metadata = self._process_pdf(content, perform_ocr)
        elif doc_type == DocumentType.TEXT:
            extracted_text = content.decode('utf-8')
            metadata = self._create_basic_metadata(file.filename, len(content), file.content_type)
        else:
            # Para otros tipos, por ahora tratamos como texto plano
            try:
                extracted_text = content.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="Formato de archivo no soportado o corrupto"
                )
            metadata = self._create_basic_metadata(file.filename, len(content), file.content_type)
        
        # Verificar contenido apropiado
        is_safe, reason = content_security_check(extracted_text)
        if not is_safe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contenido inapropiado: {reason}"
            )
        
        # Generar ID único para el documento
        document_id = generate_file_id()
        
        # Dividir texto en chunks
        text_chunks = chunk_text(extracted_text, CHUNK_SIZE)
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{document_id}_{i}",
                    text=chunk_text,
                    position=i,
                    page_number=None  # Se podría mejorar para PDFs
                )
            )
        
        # Extraer entidades y palabras clave con spaCy
        entities, keywords = self.nlp_service.extract_entities_and_keywords(extracted_text)
        
        # Detectar idioma
        language = self.nlp_service.detect_language(extracted_text)
        metadata.language = language
        
        # Crear objeto de documento procesado
        processed_doc = ProcessedDocument(
            document_id=document_id,
            metadata=metadata,
            text=extracted_text,
            chunks=chunks,
            entities=entities,
            keywords=keywords
        )
        
        return processed_doc
    
    def _get_document_type(self, file_extension: str) -> DocumentType:
        """Determina el tipo de documento basado en la extensión"""
        extension_map = {
            '.pdf': DocumentType.PDF,
            '.txt': DocumentType.TEXT,
            '.docx': DocumentType.DOCX,
            '.md': DocumentType.MARKDOWN
        }
        return extension_map.get(file_extension, DocumentType.TEXT)
    
    def _create_basic_metadata(
        self, filename: str, file_size: int, content_type: str
    ) -> DocumentMetadata:
        """Crea metadatos básicos para un documento"""
        return DocumentMetadata(
            filename=filename,
            file_size=file_size,
            content_type=content_type,
            has_images=False
        )
    
    def _process_pdf(
        self, content: bytes, perform_ocr: bool = True
    ) -> Tuple[str, DocumentMetadata]:
        """
        Procesa un archivo PDF para extraer texto
        
        Args:
            content: Contenido del PDF en bytes
            perform_ocr: Si debe realizar OCR en imágenes
            
        Returns:
            Tuple[texto extraído, metadatos]
        """
        pdf_stream = BytesIO(content)
        
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            num_pages = len(pdf_reader.pages)
            
            # Crear metadatos
            metadata = DocumentMetadata(
                filename="document.pdf",  # Placeholder, se actualizará
                file_size=len(content),
                content_type="application/pdf",
                page_count=num_pages,
                has_images=False  # Se actualizará si se detectan imágenes
            )
            
            # Extraer texto de cada página
            full_text = ""
            has_images = False
            
            for i, page in enumerate(pdf_reader.pages):
                # Extraer texto directamente del PDF
                page_text = page.extract_text() or ""
                
                # Si hay poco o ningún texto y OCR está habilitado, podría ser una imagen
                if perform_ocr and (len(page_text) < 100):
                    # Intentar extraer y procesar imágenes con OCR
                    if '/XObject' in page['/Resources']:
                        x_objects = page['/Resources']['/XObject']
                        if isinstance(x_objects, dict):
                            has_images = True
                            # Aquí se podría implementar extracción de imágenes y OCR
                            # Para este ejemplo, omitimos esa implementación compleja
                
                full_text += page_text + "\n\n"
            
            # Actualizar flag de imágenes
            metadata.has_images = has_images
            
            return full_text.strip(), metadata
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error procesando PDF: {str(e)}"
            )
    
    async def text_to_document(self, text: str, title: Optional[str] = None) -> ProcessedDocument:
        """
        Convierte texto plano en un documento procesado
        
        Args:
            text: Texto a procesar
            title: Título opcional del documento
            
        Returns:
            Documento procesado
        """
        # Verificar contenido
        is_safe, reason = content_security_check(text)
        if not is_safe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contenido inapropiado: {reason}"
            )
        
        # Generar ID y metadatos
        document_id = generate_file_id()
        filename = f"{title or 'document'}.txt"
        
        metadata = DocumentMetadata(
            filename=filename,
            file_size=len(text.encode('utf-8')),
            content_type="text/plain",
            has_images=False
        )
        
        # Dividir en chunks
        text_chunks = chunk_text(text, CHUNK_SIZE)
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{document_id}_{i}",
                    text=chunk_text,
                    position=i,
                    page_number=None
                )
            )
        
        # Extraer entidades y palabras clave
        entities, keywords = self.nlp_service.extract_entities_and_keywords(text)
        
        # Detectar idioma
        language = self.nlp_service.detect_language(text)
        metadata.language = language
        
        # Crear documento procesado
        return ProcessedDocument(
            document_id=document_id,
            metadata=metadata,
            text=text,
            chunks=chunks,
            entities=entities,
            keywords=keywords
        )