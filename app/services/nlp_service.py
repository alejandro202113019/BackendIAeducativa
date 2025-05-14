import re
from collections import Counter
from typing import Dict, List, Optional, Set, Tuple, Any

import spacy
from spacy.language import Language
from spacy.tokens import Doc

from app.core.utils import chunk_text


class NLPService:
    """Servicio para análisis de lenguaje natural"""
    
    def __init__(self, nlp_model: Language):
        """
        Inicializa el servicio NLP
        
        Args:
            nlp_model: Modelo spaCy cargado
        """
        self.nlp = nlp_model
        
        # Idiomas compatibles con el modelo actual
        self.supported_languages = {
            "es": "español",
            "en": "inglés",
            "fr": "francés",
            "pt": "portugués",
            "it": "italiano",
            "ca": "catalán",
            "de": "alemán"
        }
    
    def process_text(self, text: str) -> Doc:
        """
        Procesa texto con spaCy, dividiendo en chunks si es necesario
        
        Args:
            text: Texto a procesar
            
        Returns:
            Documento spaCy procesado
        """
        # Para textos grandes, limitar para evitar problemas de memoria
        if len(text) > 100000:
            # Dividir y procesar por chunks
            chunks = chunk_text(text, 100000)
            combined_doc = None
            
            for i, chunk in enumerate(chunks):
                doc = self.nlp(chunk)
                
                if i == 0:
                    combined_doc = doc
                else:
                    # Concatenar resultados (esto es una simplificación)
                    # En una implementación completa, habría que manejar
                    # correctamente la fusión de documentos spaCy
                    pass
            
            return combined_doc or self.nlp("")
        
        return self.nlp(text)
    
    def extract_entities_and_keywords(self, text: str) -> Tuple[Dict[str, List[str]], List[str]]:
        """
        Extrae entidades nombradas y palabras clave de un texto
        
        Args:
            text: Texto a analizar
            
        Returns:
            Tuple[entidades por tipo, palabras clave]
        """
        doc = self.process_text(text)
        
        # Extraer entidades
        entities = {}
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            
            # Evitar duplicados
            if ent.text not in entities[ent.label_]:
                entities[ent.label_].append(ent.text)
        
        # Extraer keywords (sustantivos, verbos, adjetivos más frecuentes)
        keywords = self._extract_keywords(doc)
        
        return entities, keywords
    
    def _extract_keywords(self, doc: Doc, top_n: int = 20) -> List[str]:
        """
        Extrae palabras clave de un documento spaCy
        
        Args:
            doc: Documento spaCy procesado
            top_n: Número máximo de palabras clave a devolver
            
        Returns:
            Lista de palabras clave
        """
        # Filtrar por categorías gramaticales relevantes
        pos_filter = {'NOUN', 'PROPN', 'ADJ', 'VERB'}
        
        # Stopwords y tokens a ignorar
        stopwords = self.nlp.Defaults.stop_words
        min_token_length = 3
        
        # Extraer lemmas de tokens relevantes
        candidates = []
        for token in doc:
            if (token.pos_ in pos_filter and 
                token.lemma_.lower() not in stopwords and
                len(token.lemma_) >= min_token_length and
                not token.is_punct and not token.is_space and
                not token.is_digit):
                
                candidates.append(token.lemma_.lower())
        
        # Contar frecuencias
        counter = Counter(candidates)
        
        # Devolver las más frecuentes
        keywords = [item[0] for item in counter.most_common(top_n)]
        
        return keywords
    
    def detect_language(self, text: str) -> Optional[str]:
        """
        Detecta el idioma del texto utilizando heurísticas básicas
        
        Args:
            text: Texto a analizar
            
        Returns:
            Código de idioma o None si no se puede determinar
        """
        # Esta es una detección simple y limitada
        # En una implementación real, usaríamos una librería como langdetect
        
        # Tomar un fragmento para el análisis
        sample = text[:1000] if len(text) > 1000 else text
        
        # Analizar con spaCy
        doc = self.nlp(sample)
        
        # Heurística simple: usar idioma del modelo si está disponible
        if hasattr(doc, "lang_"):
            lang_code = doc.lang_
            return self.supported_languages.get(lang_code, lang_code)
        
        # Fallback: análisis simple de caracteres y palabras frecuentes
        # (esto es muy básico y debería reemplazarse por una librería especializada)
        spanish_markers = ["de", "la", "el", "en", "que", "con", "para", "por", "los", "las"]
        english_markers = ["the", "of", "and", "to", "in", "is", "that", "for", "with", "as"]
        
        words = re.findall(r'\b\w+\b', text.lower())
        sp_count = sum(1 for word in words if word in spanish_markers)
        en_count = sum(1 for word in words if word in english_markers)
        
        if sp_count > en_count:
            return "español"
        elif en_count > sp_count:
            return "inglés"
        
        return None
    
    def extract_main_topics(self, text: str, num_topics: int = 5) -> List[str]:
        """
        Extrae los temas principales del texto
        
        Args:
            text: Texto a analizar
            num_topics: Número de temas a extraer
            
        Returns:
            Lista de temas principales
        """
        doc = self.process_text(text)
        
        # Extraer sustantivos más frecuentes como temas
        noun_phrases = []
        
        # Extraer frases nominales si están disponibles
        if hasattr(doc, "noun_chunks"):
            for chunk in doc.noun_chunks:
                clean_chunk = chunk.text.lower().strip()
                if len(clean_chunk) > 3:  # Filtrar chunks muy cortos
                    noun_phrases.append(clean_chunk)
        
        # Si no hay suficientes frases nominales, usar sustantivos
        if len(noun_phrases) < num_topics:
            for token in doc:
                if token.pos_ in ["NOUN", "PROPN"] and len(token.text) > 3:
                    noun_phrases.append(token.lemma_.lower())
        
        # Contar y obtener los más frecuentes
        counter = Counter(noun_phrases)
        topics = [item[0] for item in counter.most_common(num_topics)]
        
        return topics
    
    def extract_educational_concepts(self, text: str) -> List[Dict[str, Any]]:
        """
        Extrae conceptos educativos del texto
        
        Args:
            text: Texto a analizar
            
        Returns:
            Lista de conceptos con su definición contextual
        """
        doc = self.process_text(text)
        
        # Extraer entidades y sustantivos/nombres propios importantes
        candidates = []
        
        # Primero obtener entidades nombradas
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PERSON", "EVENT", "WORK_OF_ART", "LAW", "DATE"]:
                candidates.append((ent.text, "entity", ent.start, ent.end))
        
        # Extraer sustantivos y frases nominales relevantes
        for chunk in doc.noun_chunks:
            if chunk.root.pos_ in ["NOUN", "PROPN"] and len(chunk.text) > 3:
                # Evitar duplicados con entidades
                if not any(chunk.start >= c[2] and chunk.end <= c[3] for c in candidates if c[1] == "entity"):
                    candidates.append((chunk.text, "noun_phrase", chunk.start, chunk.end))
        
        # Extraer contexto para cada concepto
        concepts = []
        for concept, concept_type, start, end in candidates:
            # Obtener contexto (oración donde aparece)
            context_sentence = None
            for sent in doc.sents:
                if start >= sent.start and end <= sent.end:
                    context_sentence = sent.text
                    break
            
            if context_sentence:
                concepts.append({
                    "term": concept,
                    "type": concept_type,
                    "context": context_sentence
                })
        
        # Eliminar duplicados y limitar a conceptos únicos
        unique_concepts = []
        seen_terms = set()
        
        for concept in concepts:
            # Normalizar para comparación
            term_norm = concept["term"].lower()
            if term_norm not in seen_terms:
                seen_terms.add(term_norm)
                unique_concepts.append(concept)
        
        return unique_concepts