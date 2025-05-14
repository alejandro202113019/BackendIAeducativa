from typing import List, Set

# Lista de palabras prohibidas en contenido educativo
PROHIBITED_CONTENT: Set[str] = {
    "violencia", "discriminación", "odio", "obscenidad", "drogas", "suicidio",
    "abuso", "sexual", "terrorismo", "extremismo", "pornografía", "blasfemia"
}

def content_security_check(text: str) -> tuple[bool, str]:
    """
    Comprueba si el contenido es apropiado para entorno educativo
    
    Args:
        text: Texto a analizar
        
    Returns:
        (is_safe, reason): Tupla con booleano indicando si es seguro y razón si no lo es
    """
    text_lower = text.lower()
    
    # Búsqueda simple de palabras prohibidas
    for word in PROHIBITED_CONTENT:
        if word in text_lower:
            return False, f"El contenido contiene términos inapropiados: {word}"
    
    # Comprobación de longitud para evitar spam o textos vacíos
    if len(text) < 10:
        return False, "El contenido es demasiado corto"
    
    if len(text) > 100000:  # 100k caracteres
        return False, "El contenido es demasiado largo para procesar"
    
    return True, ""

def filter_educational_content(text: str) -> str:
    """
    Filtra contenido para asegurar que es apropiado para entorno educativo
    
    Args:
        text: Texto original
        
    Returns:
        Texto filtrado o mensaje de error si es inapropiado
    """
    is_safe, reason = content_security_check(text)
    
    if not is_safe:
        # Devolver mensaje genérico para evitar revelar detalles específicos
        return f"El contenido ha sido bloqueado por políticas de seguridad: {reason}"
    
    return text

def validate_file_type(filename: str) -> bool:
    """
    Valida que el tipo de archivo sea permitido
    
    Args:
        filename: Nombre del archivo
        
    Returns:
        True si es permitido, False en caso contrario
    """
    allowed_extensions = {'.pdf', '.txt', '.docx', '.md'}
    file_extension = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
    
    return file_extension in allowed_extensions

def sanitize_filename(filename: str) -> str:
    """
    Sanitiza el nombre de archivo para evitar path traversal
    
    Args:
        filename: Nombre original del archivo
        
    Returns:
        Nombre sanitizado
    """
    import re
    from pathlib import Path
    
    # Eliminar caracteres peligrosos y path traversal
    sanitized = re.sub(r'[^\w\-\.]', '_', filename)
    
    # Extraer solo el nombre base sin directorios
    sanitized = Path(sanitized).name
    
    return sanitized