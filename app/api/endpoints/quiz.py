import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_document_processor_service, get_quiz_generator_service
from app.schemas.quiz import (
    CreateQuizRequest,
    QuizQuestion,
    QuizResponse,
    QuestionType
)
from app.services.document_processor import DocumentProcessor
from app.services.quiz_generator import QuizGenerator

router = APIRouter()

@router.post(
    "/",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generar un cuestionario",
    description="Genera un cuestionario basado en un documento o texto proporcionado"
)
async def create_quiz(
    request: CreateQuizRequest,
    doc_processor: DocumentProcessor = Depends(get_document_processor_service),
    quiz_generator: QuizGenerator = Depends(get_quiz_generator_service)
):
    """
    Endpoint para generar un cuestionario educativo.
    
    Args:
        request: Datos para generar el cuestionario
        doc_processor: Servicio de procesamiento de documentos
        quiz_generator: Servicio de generación de cuestionarios
        
    Returns:
        Cuestionario generado
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
        
        # Generar cuestionario
        quiz = await quiz_generator.generate_quiz(
            text=document_text,
            num_questions=request.num_questions,
            question_type=request.question_type,
            difficulty=request.difficulty,
            topics=request.topics
        )
        
        # Actualizar document_id en la respuesta
        quiz.document_id = request.document_id
        quiz.quiz_id = str(uuid.uuid4())
        
        return quiz
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar el cuestionario: {str(e)}"
        )

@router.get(
    "/{quiz_id}",
    response_model=QuizResponse,
    summary="Obtener un cuestionario",
    description="Recupera un cuestionario generado previamente por su ID"
)
async def get_quiz(quiz_id: uuid.UUID):
    """
    Endpoint para recuperar un cuestionario por su ID.
    
    Args:
        quiz_id: ID del cuestionario
        
    Returns:
        Cuestionario recuperado
    """
    # En un sistema real, esto consultaría una base de datos
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Esta funcionalidad aún no está implementada"
    )

@router.get(
    "/",
    response_model=List[QuizResponse],
    summary="Listar cuestionarios",
    description="Obtiene una lista de cuestionarios generados"
)
async def list_quizzes(
    document_id: Optional[uuid.UUID] = Query(None),
    question_type: Optional[QuestionType] = Query(None),
    difficulty: Optional[str] = Query(None)
):
    """
    Endpoint para listar cuestionarios con filtros opcionales.
    
    Args:
        document_id: Filtrar por ID de documento
        question_type: Filtrar por tipo de pregunta
        difficulty: Filtrar por dificultad
        
    Returns:
        Lista de cuestionarios
    """
    # En un sistema real, esto consultaría una base de datos
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Esta funcionalidad aún no está implementada"
    )