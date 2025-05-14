import json
from typing import Any, Dict, List, Optional, Union

import openai
from tenacity import retry, stop_after_attempt, wait_random_exponential

from app.config import (
    OPENAI_API_KEY, 
    GPT_MODEL, 
    MAX_TOKENS, 
    TEMPERATURE
)


class OpenAIService:
    """Servicio para interacción con la API de OpenAI"""
    
    def __init__(self):
        openai.api_key = OPENAI_API_KEY
    
    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    async def generate_completion(
        self, 
        prompt: str, 
        max_tokens: int = MAX_TOKENS,
        temperature: float = TEMPERATURE,
        model: str = GPT_MODEL
    ) -> str:
        """
        Genera una respuesta utilizando GPT.
        
        Args:
            prompt: El texto de entrada para la generación
            max_tokens: Número máximo de tokens a generar
            temperature: Controla la aleatoriedad (0.0-1.0)
            model: El modelo de OpenAI a utilizar
            
        Returns:
            La respuesta generada como texto
        """
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Eres un asistente educativo especializado en generar contenido didáctico."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"Error al generar completado con OpenAI: {str(e)}")
    
    async def generate_summary(self, text: str, length: str = "medium") -> str:
        """
        Genera un resumen de un texto utilizando GPT.
        
        Args:
            text: El texto a resumir
            length: Longitud del resumen ('short', 'medium', 'long')
            
        Returns:
            El resumen generado
        """
        length_instructions = {
            "short": "Genera un resumen conciso de aproximadamente 3-5 oraciones.",
            "medium": "Genera un resumen detallado de aproximadamente 1-2 párrafos.",
            "long": "Genera un resumen extenso y completo de aproximadamente 3-5 párrafos."
        }
        
        instruction = length_instructions.get(length, length_instructions["medium"])
        prompt = f"{instruction}\n\nTexto a resumir:\n{text}"
        
        return await self.generate_completion(prompt, max_tokens=1000)
    
    async def generate_quiz(
        self, text: str, num_questions: int = 5, question_type: str = "multiple_choice"
    ) -> List[Dict[str, Any]]:
        """
        Genera un cuestionario basado en un texto utilizando GPT.
        
        Args:
            text: El texto del que se generarán preguntas
            num_questions: Número de preguntas a generar
            question_type: Tipo de preguntas ('multiple_choice', 'true_false', etc.)
            
        Returns:
            Lista de preguntas con sus respuestas
        """
        type_instructions = {
            "multiple_choice": "preguntas de opción múltiple con 4 opciones cada una",
            "true_false": "preguntas de verdadero o falso",
            "open_ended": "preguntas abiertas"
        }
        
        instruction = type_instructions.get(question_type, type_instructions["multiple_choice"])
        prompt = f"""
        Basándote en el siguiente texto, genera {num_questions} {instruction}.
        Incluye las respuestas correctas. Devuelve el resultado en formato JSON con la siguiente estructura:
        
        [
            {{
                "question": "Texto de la pregunta",
                "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
                "correct_answer": "Opción correcta o índice",
                "explanation": "Explicación de la respuesta correcta"
            }}
        ]
        
        Texto de referencia:
        {text}
        """
        
        response = await self.generate_completion(prompt, max_tokens=2000)
        
        try:
            # Extraer el JSON de la respuesta (puede estar rodeado de texto explicativo)
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                response = json_match.group(0)
            
            quiz_data = json.loads(response)
            return quiz_data
        except Exception as e:
            raise Exception(f"Error al parsear el cuestionario generado: {str(e)}")