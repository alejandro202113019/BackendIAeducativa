import io
import base64
from typing import Dict, List, Optional, Union, Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np

from app.schemas.summary import VisualizationType


class VisualizationService:
    """Servicio para generación de visualizaciones basadas en texto"""
    
    async def generate_visualization(
        self,
        text: str,
        viz_type: VisualizationType,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Genera una visualización basada en el texto proporcionado.
        
        Args:
            text: Texto a visualizar
            viz_type: Tipo de visualización a generar
            config: Configuración opcional para la visualización
            
        Returns:
            Diccionario con los datos de la visualización
        """
        if config is None:
            config = {}
            
        if viz_type == VisualizationType.WORDCLOUD:
            return await self._generate_wordcloud(text, config)
        elif viz_type == VisualizationType.FLOW_DIAGRAM:
            return await self._generate_flow_diagram(text, config)
        else:
            raise ValueError(f"Tipo de visualización no soportado: {viz_type}")
    
    async def _generate_wordcloud(
        self, 
        text: str, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Genera un wordcloud a partir del texto.
        
        Args:
            text: Texto para generar el wordcloud
            config: Opciones de configuración como colores, tamaño, etc.
            
        Returns:
            Diccionario con la imagen en base64 y metadatos
        """
        # Configuración predeterminada
        width = config.get("width", 800)
        height = config.get("height", 400)
        background_color = config.get("background_color", "white")
        max_words = config.get("max_words", 200)
        
        # Generar wordcloud
        wordcloud = WordCloud(
            width=width,
            height=height,
            background_color=background_color,
            max_words=max_words
        ).generate(text)
        
        # Convertir a imagen
        img_buffer = io.BytesIO()
        plt.figure(figsize=(width/100, height/100), dpi=100)
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        plt.tight_layout(pad=0)
        plt.savefig(img_buffer, format='png')
        plt.close()
        
        # Convertir a base64 para enviar en JSON
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
        
        return {
            "image": f"data:image/png;base64,{img_base64}",
            "type": "wordcloud",
            "width": width,
            "height": height
        }
    
    async def _generate_flow_diagram(
        self, 
        text: str, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Genera un diagrama de flujo a partir del texto analizado.
        Este método es un poco más complejo y requeriría procesamiento NLP
        para extraer relaciones y conceptos.
        
        Args:
            text: Texto a analizar
            config: Opciones de configuración
            
        Returns:
            Diccionario con los datos del diagrama en formato JSON
        """
        # Simplificación - en un caso real esto sería mucho más complejo
        # y probablemente usaría servicios de NLP para extraer conceptos y relaciones
        
        # Extraer algunos conceptos simples (solo para demostración)
        words = text.lower().split()
        concepts = set([w for w in words if len(w) > 5])
        top_concepts = list(concepts)[:min(10, len(concepts))]
        
        # Crear algunas relaciones aleatorias (solo para demostración)
        import random
        nodes = []
        edges = []
        
        for i, concept in enumerate(top_concepts):
            nodes.append({
                "id": i,
                "label": concept,
                "value": len(concept)
            })
        
        # Crear algunas conexiones
        for i in range(len(top_concepts)):
            for _ in range(2):  # Cada nodo tiene aproximadamente 2 conexiones
                target = random.randint(0, len(top_concepts) - 1)
                if target != i:
                    edges.append({
                        "from": i,
                        "to": target,
                        "value": 1
                    })
        
        return {
            "type": "flow_diagram",
            "nodes": nodes,
            "edges": edges
        }