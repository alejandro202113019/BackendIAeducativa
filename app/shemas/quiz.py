from enum import Enum
from typing import Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field, validator


class QuestionType(str, Enum):
    """Tipos de preguntas disponibles"""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_IN_BLANK = "fill_in_blank"
    SHORT_ANSWER = "short_answer"
    MATCHING = "matching"


class QuestionDifficulty(str, Enum):
    """Niveles de dificultad para preguntas"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuizOption(BaseModel):
    """Opción para preguntas de selección múltiple"""
    text: str
    is_correct: bool
    explanation: Optional[str] = None


class QuizQuestion(BaseModel):
    """Pregunta generada para un quiz"""
    question_id: str
    text: str
    type: QuestionType
    difficulty: QuestionDifficulty
    options: Optional[List[QuizOption]] = None
    correct_answer: Optional[Union[str, int, List[int]]] = None
    explanation: str
    related_concepts: List[str] = Field(default_factory=list)
    
    @validator('options')
    def validate_options(cls, v, values):
        """Validar que hay opciones para preguntas de selección múltiple"""
        if values.get('type') == QuestionType.MULTIPLE_CHOICE and (not v or len(v) < 2):
            raise ValueError("Las preguntas de selección múltiple deben tener al menos 2 opciones")
        return v
    
    @validator('correct_answer')
    def validate_correct_answer(cls, v, values):
        """Validar que hay una respuesta correcta apropiada según el tipo de pregunta"""
        q_type = values.get('type')
        
        if q_type == QuestionType.MULTIPLE_CHOICE:
            # Para selección múltiple, debe ser un índice válido
            if not isinstance(v, int) and not (isinstance(v, list) and all(isinstance(i, int) for i in v)):
                raise ValueError("La respuesta correcta debe ser un índice o lista de índices")
                
        elif q_type == QuestionType.TRUE_FALSE:
            # Para verdadero/falso, debe ser un booleano o string "true"/"false"
            if not (v in [0, 1] or v in ["true", "false", True, False]):
                raise ValueError("La respuesta correcta debe ser true o false")
                
        return v


class QuizRequest(BaseModel):
    """Solicitud para generar un quiz"""
    document_id: str
    num_questions: int = Field(5, ge=1, le=20, description="Número de preguntas a generar")
    question_types: Optional[List[QuestionType]] = None
    difficulty: Optional[QuestionDifficulty] = None
    focus_concepts: Optional[List[str]] = None
    educational_level: Optional[str] = Field(
        "universitario", description="Nivel educativo (primaria, secundaria, universitario)"
    )


class QuizResponse(BaseModel):
    """Respuesta con el quiz generado"""
    document_id: str
    quiz_id: str
    title: str
    description: str
    questions: List[QuizQuestion]
    covered_concepts: List[str] = Field(default_factory=list)
    estimated_time: int = Field(..., description="Tiempo estimado para completar el quiz en minutos")


class QuizSubmission(BaseModel):
    """Envío de respuestas a un quiz"""
    quiz_id: str
    user_id: Optional[str] = None
    answers: Dict[str, Union[int, str, List[int]]] = Field(..., description="Respuestas del usuario (question_id: respuesta)")


class QuizFeedback(BaseModel):
    """Retroalimentación para un quiz completado"""
    quiz_id: str
    user_id: Optional[str] = None
    score: float = Field(..., ge=0, le=100, description="Puntuación del 0 al 100")
    correct_count: int
    total_questions: int
    time_taken: Optional[float] = None
    question_feedback: Dict[str, Dict[str, Union[bool, str]]] = Field(
        ..., description="Retroalimentación por pregunta"
    )
    weakness_areas: List[str] = Field(default_factory=list)
    strength_areas: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)