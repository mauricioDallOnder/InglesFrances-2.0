#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para transcrição aproximada de francês e inglês para português
Baseado no código fornecido pelo usuário
"""

import re
import logging
from typing import Dict, List, Optional

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mapeamento de fonemas franceses para português
FRENCH_TO_PORTUGUESE = {
    # VOGAIS ORAIS
    'i': 'i',
    'e': 'e', 
    'ɛ': 'é',
    'a': 'a',
    'ɑ': 'a',
    'ɔ': 'ó',
    'o': 'ô',
    'u': 'u',
    'y': 'u',
    'ø': 'eu',
    'œ': 'eu',
    'ə': 'e',

    # VOGAIS NASAIS
    'ɛ̃': 'ẽ',
    'ɑ̃': 'ã',
    'ɔ̃': 'õ',
    'œ̃': 'ũ',

    # SEMIVOGAIS
    'w': 'u',
    'ɥ': 'u',
    'j': 'i',

    # CONSOANTES
    'b': 'b',
    'd': 'd',
    'f': 'f',
    'g': 'g',
    'ʒ': 'j',
    'k': 'k',
    'l': 'l',
    'm': 'm',
    'n': 'n',
    'p': 'p',
    'ʁ': 'r',
    'r': 'r',
    's': 's',
    't': 't',
    'v': 'v',
    'z': 'z',
    'ʃ': 'ch',
    'ɲ': 'nh',
    'ŋ': 'ng',
    'ç': 's',
    'ʎ': 'lh',
    'ʔ': '',
    'θ': 't',
    'ɾ': 'r',
    'ʕ': 'r',
}

# Mapeamento de fonemas ingleses para português
ENGLISH_TO_PORTUGUESE = {
    # VOGAIS
    'i': 'i',
    'ɪ': 'i',
    'e': 'e',
    'ɛ': 'é',
    'æ': 'é',
    'a': 'a',
    'ɑ': 'a',
    'ɔ': 'ó',
    'o': 'ô',
    'ʊ': 'u',
    'u': 'u',
    'ʌ': 'a',
    'ə': 'e',
    'ɜ': 'er',
    'ɝ': 'er',

    # DITONGOS
    'eɪ': 'ei',
    'aɪ': 'ai',
    'ɔɪ': 'ói',
    'aʊ': 'au',
    'oʊ': 'ou',
    'ɪə': 'ia',
    'eə': 'ea',
    'ʊə': 'ua',

    # CONSOANTES
    'b': 'b',
    'd': 'd',
    'f': 'f',
    'g': 'g',
    'h': 'r',  # h aspirado inglês → r em português
    'j': 'i',
    'k': 'k',
    'l': 'l',
    'm': 'm',
    'n': 'n',
    'ŋ': 'ng',
    'p': 'p',
    'r': 'r',
    's': 's',
    't': 't',
    'v': 'v',
    'w': 'u',
    'z': 'z',
    'ʃ': 'ch',
    'ʒ': 'j',
    'θ': 't',  # th surdo → t
    'ð': 'd',  # th sonoro → d
    'tʃ': 'tch',
    'dʒ': 'dj',
}

# Casos especiais para francês
FRENCH_SPECIAL_CASES = {
    "c'est": "sé",
    "c'était": "seté", 
    "c'étaient": "setén",
    "j'aie": "je",
    "j'ai": "jé",
    "est-ce": "és",
    "est-ce que": "és k",
    "qu'est-ce": "kés",
    "qu'est-ce que": "kés k",
    "jusqu'au": "jusko",
    "jusqu'aux": "jusko",
    "bonjour": "bonjur",
    "bonsoir": "bonsuar",
    "merci": "mersi",
    "merci beaucoup": "mersi boku",
    "comment": "komã",
    "comment allez-vous": "komã tale vu",
    "au revoir": "o revuar",
    "s'il vous plaît": "sil vu plé",
    "excusez-moi": "eskuze mua",
    "pardon": "pardõ",
    "oui": "ui",
    "non": "nõ",
    "peut-être": "pö tetr",
    "d'accord": "dakor",
}

# Casos especiais para inglês
ENGLISH_SPECIAL_CASES = {
    "hello": "relou",
    "hi": "rai",
    "goodbye": "gudbai",
    "bye": "bai",
    "thank you": "thenk iu",
    "thanks": "thenks",
    "please": "plis",
    "excuse me": "ekskius mi",
    "sorry": "sóri",
    "yes": "iés",
    "no": "nou",
    "maybe": "meibi",
    "okay": "okei",
    "ok": "okei",
    "how are you": "rau ar iu",
    "what": "uót",
    "where": "uér",
    "when": "uén",
    "why": "uái",
    "who": "ru",
    "how": "rau",
    "the": "de",
    "and": "énd",
    "or": "ór",
    "but": "bát",
    "with": "uid",
    "without": "uidaut",
    "water": "uóter",
    "coffee": "kófi",
    "tea": "ti",
    "food": "fud",
    "good": "gud",
    "bad": "béd",
    "big": "big",
    "small": "smól",
    "hot": "rót",
    "cold": "kould",
}

def clean_ipa_text(ipa_text: str) -> str:
    """Remove caracteres não fonéticos do IPA"""
    # Remove barras, espaços extras e pontuação
    cleaned = re.sub(r'[/\[\]().,;:!?"\'-]', '', ipa_text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def convert_french_to_portuguese(ipa_text: str) -> str:
    """Converte IPA francês para transcrição aproximada em português"""
    try:
        # Limpar o texto IPA
        cleaned_ipa = clean_ipa_text(ipa_text)
        
        if not cleaned_ipa:
            return ""
        
        # Verificar casos especiais primeiro
        text_lower = cleaned_ipa.lower()
        for french_phrase, portuguese_approx in FRENCH_SPECIAL_CASES.items():
            if french_phrase in text_lower:
                return portuguese_approx
        
        # Conversão fonema por fonema
        result = ""
        i = 0
        while i < len(cleaned_ipa):
            found = False
            
            # Tentar sequências de 3, 2 e 1 caractere
            for length in [3, 2, 1]:
                if i + length <= len(cleaned_ipa):
                    phoneme = cleaned_ipa[i:i+length]
                    if phoneme in FRENCH_TO_PORTUGUESE:
                        result += FRENCH_TO_PORTUGUESE[phoneme]
                        i += length
                        found = True
                        break
            
            if not found:
                # Se não encontrou mapeamento, manter o caractere original
                result += cleaned_ipa[i]
                i += 1
        
        # Aplicar regras de pós-processamento
        result = apply_french_rules(result)
        
        return result.strip()
        
    except Exception as e:
        logger.error(f"Erro ao converter francês para português: {e}")
        return ipa_text

def convert_english_to_portuguese(ipa_text: str) -> str:
    """Converte IPA inglês para transcrição aproximada em português"""
    try:
        # Limpar o texto IPA
        cleaned_ipa = clean_ipa_text(ipa_text)
        
        if not cleaned_ipa:
            return ""
        
        # Verificar casos especiais primeiro
        text_lower = cleaned_ipa.lower()
        for english_phrase, portuguese_approx in ENGLISH_SPECIAL_CASES.items():
            if english_phrase in text_lower:
                return portuguese_approx
        
        # Conversão fonema por fonema
        result = ""
        i = 0
        while i < len(cleaned_ipa):
            found = False
            
            # Tentar sequências de 3, 2 e 1 caractere
            for length in [3, 2, 1]:
                if i + length <= len(cleaned_ipa):
                    phoneme = cleaned_ipa[i:i+length]
                    if phoneme in ENGLISH_TO_PORTUGUESE:
                        result += ENGLISH_TO_PORTUGUESE[phoneme]
                        i += length
                        found = True
                        break
            
            if not found:
                # Se não encontrou mapeamento, manter o caractere original
                result += cleaned_ipa[i]
                i += 1
        
        # Aplicar regras de pós-processamento
        result = apply_english_rules(result)
        
        return result.strip()
        
    except Exception as e:
        logger.error(f"Erro ao converter inglês para português: {e}")
        return ipa_text

def apply_french_rules(text: str) -> str:
    """Aplica regras específicas do francês"""
    # Remover duplicatas de consoantes
    text = re.sub(r'([bcdfghjklmnpqrstvwxyz])\1+', r'\1', text)
    
    # Simplificar grupos consonantais finais
    text = re.sub(r'rd$', 'r', text)
    text = re.sub(r'st$', 's', text)
    text = re.sub(r'nt$', 'n', text)
    
    # Ajustar nasalizações
    text = re.sub(r'an([bp])', r'ã\1', text)
    text = re.sub(r'en([bp])', r'ẽ\1', text)
    text = re.sub(r'on([bp])', r'õ\1', text)
    
    return text

def apply_english_rules(text: str) -> str:
    """Aplica regras específicas do inglês"""
    # Remover duplicatas de consoantes
    text = re.sub(r'([bcdfghjklmnpqrstvwxyz])\1+', r'\1', text)
    
    # Ajustar th sounds
    text = re.sub(r'th', 't', text)
    
    # Simplificar grupos consonantais
    text = re.sub(r'ks', 'x', text)
    text = re.sub(r'ng', 'ng', text)
    
    return text

def convert_to_portuguese(text: str, language: str) -> str:
    """Função principal para converter IPA para português aproximado"""
    if not text or not text.strip():
        return ""
    
    if language == 'fr':
        return convert_french_to_portuguese(text)
    elif language == 'en':
        return convert_english_to_portuguese(text)
    else:
        # Para outros idiomas, retornar vazio
        return ""

# Função de teste
def test_conversions():
    """Testa as conversões"""
    print("=== Teste de Conversões ===")
    
    # Testes francês
    print("\nFrancês:")
    test_cases_fr = [
        ("bɔ̃ʒur", "bonjur"),
        ("kɔmɑ̃ alevu", "komã alevu"),
        ("mɛrki boku", "mersi boku"),
        ("o rɛvwar", "o revuar"),
    ]
    
    for ipa, expected in test_cases_fr:
        result = convert_french_to_portuguese(ipa)
        print(f"  '{ipa}' -> '{result}' (esperado: '{expected}')")
    
    # Testes inglês
    print("\nInglês:")
    test_cases_en = [
        ("hɛˈloʊ", "relou"),
        ("haʊ ər ju", "rau er iu"),
        ("θæŋk ju", "tenk iu"),
        ("gud baɪ", "gud bai"),
    ]
    
    for ipa, expected in test_cases_en:
        result = convert_english_to_portuguese(ipa)
        print(f"  '{ipa}' -> '{result}' (esperado: '{expected}')")

if __name__ == "__main__":
    test_conversions()

