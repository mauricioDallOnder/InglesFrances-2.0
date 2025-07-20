#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para transcrição aproximada de IPA para português.
Delega a transcrição de francês para o módulo FrenchTranscription
e mantém a lógica para inglês.
"""

import re
import logging
from typing import Dict, List

# --- NOVA SEÇÃO: Importa as funções dos seus novos ficheiros ---
# Isto permite que este ficheiro chame a lógica de transcrição francesa.
from FrenchTranscription import transliterate_and_convert_sentence

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# LÓGICA ANTIGA MANTIDA APENAS PARA A TRANSCRIÇÃO DE INGLÊS
# -----------------------------------------------------------------------------

# Mapeamento de fonemas ingleses para português
ENGLISH_TO_PORTUGUESE = {
    # VOGAIS
    'i': 'i', 'ɪ': 'i', 'e': 'e', 'ɛ': 'é', 'æ': 'é', 'a': 'a', 'ɑ': 'a',
    'ɔ': 'ó', 'o': 'ô', 'ʊ': 'u', 'u': 'u', 'ʌ': 'a', 'ə': 'e', 'ɜ': 'er',
    'ɝ': 'er',
    # DITONGOS
    'eɪ': 'ei', 'aɪ': 'ai', 'ɔɪ': 'ói', 'aʊ': 'au', 'oʊ': 'ou', 'ɪə': 'ia',
    'eə': 'ea', 'ʊə': 'ua',
    # CONSOANTES
    'b': 'b', 'd': 'd', 'f': 'f', 'g': 'g', 'h': 'r', 'j': 'i', 'k': 'k',
    'l': 'l', 'm': 'm', 'n': 'n', 'ŋ': 'ng', 'p': 'p', 'r': 'r', 's': 's',
    't': 't', 'v': 'v', 'w': 'u', 'z': 'z', 'ʃ': 'ch', 'ʒ': 'j', 'θ': 't',
    'ð': 'd', 'tʃ': 'tch', 'dʒ': 'dj',
}

def clean_ipa_text(ipa_text: str) -> str:
    """Remove caracteres não fonéticos do IPA."""
    cleaned = re.sub(r'[/\[\]().,;:!?"\'-]', '', ipa_text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def apply_english_rules(text: str) -> str:
    """Aplica regras de pós-processamento específicas para o inglês."""
    text = re.sub(r'([bcdfghjklmnpqrstvwxyz])\1+', r'\1', text) # Remove consoantes duplicadas
    text = re.sub(r'ks', 'x', text)
    return text

def convert_english_to_portuguese(ipa_text: str) -> str:
    """Converte IPA inglês para transcrição aproximada em português."""
    try:
        cleaned_ipa = clean_ipa_text(ipa_text)
        if not cleaned_ipa:
            return ""
        
        result = ""
        i = 0
        while i < len(cleaned_ipa):
            found = False
            # Tenta encontrar o fonema mais longo primeiro (3, depois 2, depois 1)
            for length in [3, 2, 1]:
                if i + length <= len(cleaned_ipa):
                    phoneme = cleaned_ipa[i:i+length]
                    if phoneme in ENGLISH_TO_PORTUGUESE:
                        result += ENGLISH_TO_PORTUGUESE[phoneme]
                        i += length
                        found = True
                        break
            if not found:
                result += cleaned_ipa[i]
                i += 1
        
        return apply_english_rules(result).strip()
        
    except Exception as e:
        logger.error(f"Erro ao converter inglês para português: {e}")
        return ipa_text

# -----------------------------------------------------------------------------
# FUNÇÃO PRINCIPAL (GESTORA)
# -----------------------------------------------------------------------------

def convert_to_portuguese(text: str, language: str) -> str:
    """
    Função principal que delega a conversão para o módulo correto
    baseado no idioma.
    """
    if not text or not text.strip():
        return ""
    
    if language == 'fr':
        # --- MUDANÇA PRINCIPAL ---
        # Chama a função importada do seu novo ficheiro FrenchTranscription.py
        # Nota: A sua nova função espera a frase original, não o IPA.
        # Se precisar passar o IPA, terá que ajustar a função em FrenchTranscription.py
        return transliterate_and_convert_sentence(text)
    
    elif language == 'en':
        # Mantém a lógica antiga para o inglês
        return convert_english_to_portuguese(text)
    
    else:
        # Para outros idiomas, retorna vazio
        logger.warning(f"Idioma '{language}' não suportado para transcrição.")
        return ""

# -----------------------------------------------------------------------------
# Função de teste (opcional, para verificar se tudo funciona)
# -----------------------------------------------------------------------------
def test_conversions():
    """Testa as conversões para ambos os idiomas."""
    print("=== Teste de Conversões ===")
    
    # Teste para Francês (agora chama a nova função)
    print("\nFrancês:")
    french_sentence = "Bonjour, comment allez-vous?"
    result_fr = convert_to_portuguese(french_sentence, 'fr')
    print(f"  '{french_sentence}' -> '{result_fr}'")

    # Teste para Inglês (usa a lógica antiga)
    print("\nInglês:")
    english_ipa = "hɛˈloʊ haʊ ɑr ju"
    result_en = convert_to_portuguese(english_ipa, 'en')
    print(f"  '{english_ipa}' -> '{result_en}'")

if __name__ == "__main__":
    # Para executar este ficheiro diretamente e testar
    test_conversions()
