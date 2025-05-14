import asyncio
import hashlib
import json
import os
import uuid
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from fastapi import HTTPException, status

from app.config import CHUNK_SIZE, TIMEOUT_SECONDS, UPLOAD_DIR


def generate_file_id() -> str:
    """Genera un ID único para un archivo"""
    return str(uuid.uuid4())


def save_upload_file(file_content: bytes, filename: str) -> Path:
    """
    Guarda un archivo subido en el directorio temporal
    
    Args:
        file_content: Contenido del archivo en bytes
        filename: Nombre del archivo
        
    Returns:
        Path al archivo guardado
    """
    # Crear directorio si no existe
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generar hash del contenido para evitar duplicados
    file_hash = hashlib.md5(file_content).hexdigest()
    
    # Guardar con nombre único basado en hash + nombre original
    file_path = UPLOAD_DIR / f"{file_hash}_{filename}"
    
    with open(file_path, 'wb') as f:
        f.write(file_content)
    
    return file_path


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    """
    Divide un texto largo en chunks más pequeños para procesar
    
    Args:
        text: Texto a dividir
        chunk_size: Tamaño máximo de cada chunk en caracteres
        
    Returns:
        Lista de chunks de texto
    """
    # Si el texto es más corto que el tamaño de chunk, devolverlo directamente
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    current_pos = 0
    
    while current_pos < len(text):
        # Buscar un punto de separación natural (final de frase o párrafo)
        end_pos = min(current_pos + chunk_size, len(text))
        
        # Si no estamos al final del texto, buscar un buen punto de corte
        if end_pos < len(text):
            # Intentar cortar por párrafo primero
            paragraph_end = text.rfind('\n\n', current_pos, end_pos)
            if paragraph_end > current_pos:
                end_pos = paragraph_end + 2  # Incluir los saltos de línea
            else:
                # Si no hay párrafo, intentar cortar por frase
                sentence_end = text.rfind('. ', current_pos, end_pos)
                if sentence_end > current_pos:
                    end_pos = sentence_end + 2  # Incluir el punto y espacio
                else:
                    # Si no hay frases, intentar cortar por espacio
                    space_end = text.rfind(' ', current_pos, end_pos)
                    if space_end > current_pos:
                        end_pos = space_end + 1  # Incluir el espacio
        
        # Agregar el chunk a la lista
        chunks.append(text[current_pos:end_pos])
        current_pos = end_pos
    
    return chunks


def merge_chunks(chunk_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Combina los resultados de procesar múltiples chunks
    
    Args:
        chunk_results: Lista de resultados de chunks
        
    Returns:
        Resultados combinados
    """
    if not chunk_results:
        return {}
    
    # Inicializar con el primer resultado
    merged = {key: [] if isinstance(value, list) else "" 
              for key, value in chunk_results[0].items()}
    
    # Combinar los resultados
    for result in chunk_results:
        for key, value in result.items():
            if isinstance(value, list):
                merged[key].extend(value)
            elif isinstance(value, str):
                merged[key] += value + " "
    
    # Limpiar espacios extra en strings
    for key, value in merged.items():
        if isinstance(value, str):
            merged[key] = value.strip()
    
    return merged


def with_timeout(seconds: int = TIMEOUT_SECONDS):
    """
    Decorador para limitar el tiempo de ejecución de una función asíncrona
    
    Args:
        seconds: Tiempo máximo de ejecución en segundos
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail=f"La operación excedió el tiempo límite de {seconds} segundos"
                )
        return wrapper
    return decorator


def clean_temporary_files(max_age_hours: int = 24):
    """
    Limpia archivos temporales antiguos
    
    Args:
        max_age_hours: Edad máxima de los archivos en horas
    """
    from datetime import datetime, timedelta
    
    # Calcular la fecha límite
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    
    # Recorrer archivos en el directorio de uploads
    for file_path in UPLOAD_DIR.glob('*'):
        if file_path.is_file():
            # Comprobar la fecha de modificación
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if mod_time < cutoff_time:
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error eliminando archivo temporal {file_path}: {e}")