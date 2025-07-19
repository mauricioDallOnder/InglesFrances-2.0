#!/usr/bin/env python3.11

import RuleBasedModels

def test_ipa_conversion():
    print("=== Teste de Conversão IPA ===")
    
    # Teste para francês
    print("\n1. Testando Francês:")
    fr_converter = RuleBasedModels.get_phonem_converter('fr')
    
    test_phrases_fr = [
        "Bonjour",
        "Comment allez-vous?",
        "Je suis étudiant",
        "Merci beaucoup",
        "Au revoir"
    ]
    
    for phrase in test_phrases_fr:
        ipa = fr_converter.convertToPhonem(phrase)
        print(f"  '{phrase}' -> /{ipa}/")
    
    # Teste para alemão
    print("\n2. Testando Alemão:")
    de_converter = RuleBasedModels.get_phonem_converter('de')
    
    test_phrases_de = [
        "Guten Tag",
        "Wie geht es Ihnen?",
        "Danke schön"
    ]
    
    for phrase in test_phrases_de:
        ipa = de_converter.convertToPhonem(phrase)
        print(f"  '{phrase}' -> /{ipa}/")
    
    # Teste para inglês
    print("\n3. Testando Inglês:")
    en_converter = RuleBasedModels.get_phonem_converter('en')
    
    test_phrases_en = [
        "Hello world",
        "How are you?",
        "Thank you"
    ]
    
    for phrase in test_phrases_en:
        ipa = en_converter.convertToPhonem(phrase)
        print(f"  '{phrase}' -> /{ipa}/")
    
    print("\n=== Teste Concluído ===")

if __name__ == "__main__":
    test_ipa_conversion()

