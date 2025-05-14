from enum import Enum
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field, validator


class VisualizationType(str, Enum):
    """Tipos de visualizaciones disponibles"""
    WORDCLOUD = "wordcloud"
    FLOW_DIAGRAM = "flow_diagram"
    TIMELINE = "timeline"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    NETWORK_GRAPH = "network_graph"
    CONCEPT_MAP = "concept_map"


class Visualization(BaseModel):
    """Datos de una visualización generada"""
    type: VisualizationType
    title: str
    description: str
    data: Dict[str, Any] = Field(..., description="Datos para renderizar la visualización (formato Plotly)")


class KeyConcept(BaseModel):
    """Concepto clave extraído del texto"""
    term: str
    relevance: float = Field(..., ge=0, le=1, description="Relevancia del concepto (0-1)")
    definition: str
    related_terms: List[str] = Field(default_factory=list)
    examples: Optional[List[str]] = Field(default_factory=list)


class SummaryRequest(BaseModel):
    """Solicitud para generar un resumen"""
    document_id: str
    max_length: Optional[int] = Field(None, description="Longitud máxima del resumen")
    focus_topics: Optional[List[str]] = Field(
        None, description="Temas en los que concentrar el resumen"
    )
    include_visualizations: bool = Field(True, description="Incluir visualizaciones")
    visualization_types: Optional[List[VisualizationType]] = Field(
        None, description="Tipos específicos de visualizaciones a generar"
    )
    educational_level: Optional[str] = Field(
        "universitario", description="Nivel educativo (primaria, secundaria, universitario)"
    )


class SummaryResponse(BaseModel):
    """Respuesta con el resumen generado"""
    document_id: str
    summary: str = Field(..., description="Resumen generado")
    key_concepts: List[KeyConcept] = Field(..., description="Conceptos clave identificados")
    visualizations: List[Visualization] = Field(
        default_factory=list, description="Visualizaciones generadas"
    )
    estimated_reading_time: float = Field(
        ..., description="Tiempo estimado de lectura del resumen en minutos"
    )
    original_text_length: int = Field(..., description="Longitud del texto original en caracteres")
    compression_ratio: float = Field(
        ..., description="Ratio de compresión (resumen/original)", ge=0, le=1
    )

    @validator('compression_ratio')
    def validate_compression_ratio(cls, v, values):
        if 'summary' in values and 'original_text_length' in values:
            # Recalcular para asegurar consistencia
            summary_length = len(values['summary'])
            original_length = values['original_text_length']
            if original_length > 0:
                return round(summary_length / original_length, 2)
        return v