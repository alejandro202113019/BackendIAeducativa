from fastapi import APIRouter

from app.api.endpoints import upload, summary, quiz

# Crear el router principal
api_router = APIRouter()

# Incluir los routers de los endpoints
api_router.include_router(upload.router, prefix="/documents", tags=["Documentos"])
api_router.include_router(summary.router, prefix="/summaries", tags=["Resúmenes"])
api_router.include_router(quiz.router, prefix="/quizzes", tags=["Cuestionarios"])