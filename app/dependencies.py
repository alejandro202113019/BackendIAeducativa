import spacy
from fastapi import Depends, HTTPException, status
from redis import Redis

from app.config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD, REDIS_ENABLED, SPACY_MODEL
from app.core.cache import get_redis_connection
from app.services.nlp_service import NLPService
from app.services.openai_service import OpenAIService
from app.services.document_processor import DocumentProcessor
from app.services.quiz_generator import QuizGenerator
from app.services.visualization import VisualizationService

# Inicializar modelo SpaCy
try:
    nlp_model = spacy.load(SPACY_MODEL)
except OSError:
    try:
        # Si el modelo no está instalado, lo descargamos
        import subprocess
        subprocess.run(["python", "-m", "spacy", "download", SPACY_MODEL], check=True)
        nlp_model = spacy.load(SPACY_MODEL)
    except Exception as e:
        # Fallback al modelo en inglés si falla la descarga
        print(f"Error cargando modelo SpaCy {SPACY_MODEL}: {e}")
        print("Cargando modelo en inglés como fallback...")
        try:
            nlp_model = spacy.load("en_core_web_sm")
        except:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
            nlp_model = spacy.load("en_core_web_sm")

# Dependencia para obtener conexión a Redis
def get_cache():
    if REDIS_ENABLED:
        try:
            redis_client = get_redis_connection()
            yield redis_client
        except Exception as e:
            print(f"Error conectando a Redis: {e}")
            yield None
    else:
        yield None

# Dependencia para NLP Service
def get_nlp_service():
    return NLPService(nlp_model)

# Dependencia para OpenAI Service
def get_openai_service():
    return OpenAIService()

# Dependencia para Document Processor
def get_document_processor(
    nlp_service: NLPService = Depends(get_nlp_service)
):
    return DocumentProcessor(nlp_service)

# Dependencia para Quiz Generator
def get_quiz_generator(
    nlp_service: NLPService = Depends(get_nlp_service),
    openai_service: OpenAIService = Depends(get_openai_service)
):
    return QuizGenerator(nlp_service, openai_service)

# Dependencia para Visualization Service
def get_visualization_service(
    nlp_service: NLPService = Depends(get_nlp_service)
):
    return VisualizationService(nlp_service)