import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env
load_dotenv()

# Configuración básica
API_V1_STR = "/api/v1"
PROJECT_NAME = "Educative AI Generator API"
PROJECT_DESCRIPTION = "API para procesar documentos y generar contenido educativo"
VERSION = "0.1.0"

# Directorio raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent

# Directorio temporal para archivos subidos
UPLOAD_DIR = ROOT_DIR / "tmp" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Configuración de seguridad
SECRET_KEY = os.getenv("SECRET_KEY", "insecure-secret-key-for-dev")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 8))  # 8 días

# Configuración de OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-3.5-turbo")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1000))
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))

# Configuración de Redis para caché
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "False").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", 60 * 60 * 24))  # 24 horas en segundos

# Configuración de procesamiento
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", 30))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 3000))  # Caracteres por chunk

# Configuración SpaCy
SPACY_MODEL = os.getenv("SPACY_MODEL", "es_core_news_md")

# Configuración BERT para generación de quizzes
BERT_MODEL = os.getenv("BERT_MODEL", "dccuchile/bert-base-spanish-wwm-uncased")

# Configuración Tesseract OCR
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "tesseract")
TESSERACT_LANG = os.getenv("TESSERACT_LANG", "spa")