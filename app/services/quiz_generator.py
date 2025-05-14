import json
from typing import Dict, List, Optional, Any

from app.schemas.quiz import (
    CreateQuizRequest,
    QuestionType, 
    QuizQuestion, 
    QuizResponse
)
from app.services.openai_service import OpenAIService


class QuizGenerator:
    """Servicio para generación de cuestionarios basados en texto"""
    
    def __init__(self, openai_service: OpenAIService):
        self.openai_service = openai_service
    
    async def generate_quiz(
        self,
        text: str,
        num_questions: int = 5,
        question_type: QuestionType = QuestionType.MULTIPLE_CHOICE,
        difficulty: str = "medium",
        topics: Optional[List[str]] = None
    ) -> QuizResponse:
        """
        Genera un cuestionario basado en el texto proporcionado.
        
        Args:
            text: Texto del que se extraerán las preguntas
            num_questions: Número de preguntas a generar
            question_type: Tipo de preguntas (opción múltiple, verdadero/falso, etc.)
            difficulty: Dificultad del cuestionario (easy, medium, hard)
            topics: Lista opcional de temas específicos a cubrir
            
        Returns:
            Un objeto QuizResponse con las preguntas generadas
        """
        # Limitar la longitud del texto si es necesario
        if len(text) > 10000:
            text = text[:10000]
        
        # Construir el prompt para especificar temas si los hay
        topic_instruction = ""
        if topics and len(topics) > 0:
            topic_instruction = f"Enfócate en los siguientes temas: {', '.join(topics)}. "
        
        # Instrucción de dificultad
        difficulty_map = {
            "easy": "nivel básico, conceptos fundamentales",
            "medium": "nivel intermedio, que requiera comprensión moderada",
            "hard": "nivel avanzado, que requiera comprensión profunda y análisis crítico"
        }
        difficulty_instruction = difficulty_map.get(difficulty, difficulty_map["medium"])
        
        # Generar las preguntas usando OpenAI
        raw_questions = await self.openai_service.generate_quiz(
            text, 
            num_questions=num_questions,
            question_type=question_type.value
        )
        
        # Convertir las preguntas generadas al formato requerido
        questions = []
        for q in raw_questions:
            question = QuizQuestion(
                question=q["question"],
                options=q.get("options", []),
                correct_answer=q["correct_answer"],
                explanation=q.get("explanation", "")
            )
            questions.append(question)
        
        # Crear la respuesta
        return QuizResponse(
            questions=questions,
            document_id=None,  # Se debe establecer después
            type=question_type,
            difficulty=difficulty
        )