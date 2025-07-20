"""
Versão corrigida do lambdaSpeechToScore.py
Corrige o problema de sincronização de palavras com pontuação
"""

import torch
import json
import os
import WordMatching as wm
import utilsFileIO
import pronunciationTrainer
import base64
import time
import audioread
import numpy as np
from torchaudio.transforms import Resample
import io
import tempfile
import re
from typing import List, Tuple

# Configurações dos treinadores
trainer_SST_lambda = {}
trainer_SST_lambda['de'] = pronunciationTrainer.getTrainer("de")
trainer_SST_lambda['en'] = pronunciationTrainer.getTrainer("en")
trainer_SST_lambda['fr'] = pronunciationTrainer.getTrainer("fr")

# Função para limpar e dividir texto considerando pontuação
def clean_and_split_text(text: str, language: str = 'fr') -> List[str]:
    """
    Divide o texto em palavras tratando adequadamente a pontuação.
    
    Args:
        text: Texto a ser dividido
        language: Idioma ('fr' para francês, 'en' para inglês)
    
    Returns:
        Lista de palavras limpas sem pontuação
    """
    # Converter para minúsculas
    text = text.lower().strip()
    
    # Tratamento especial para contrações francesas
    if language == 'fr':
        # Tratar contrações comuns do francês
        contractions = {
            "l'": "le ",
            "d'": "de ",
            "n'": "ne ",
            "m'": "me ",
            "t'": "te ",
            "s'": "se ",
            "c'": "ce ",
            "j'": "je ",
            "qu'": "que "
        }
        
        for contraction, expansion in contractions.items():
            text = text.replace(contraction, expansion)
    
    # Remover pontuação mas manter hífens dentro de palavras
    # Substituir pontuação por espaços, exceto hífens no meio de palavras
    text = re.sub(r'[^\w\s\-]|(?<!\w)-|-(?!\w)', ' ', text)
    
    # Dividir por espaços e remover strings vazias
    words = [word.strip() for word in text.split() if word.strip()]
    
    return words

def map_words_to_times(original_text: str, transcribed_words: List[str], 
                      start_times: List[float], end_times: List[float],
                      language: str = 'fr') -> Tuple[List[str], List[float], List[float]]:
    """
    Mapeia palavras limpas com seus tempos correspondentes.
    """
    # Limpar e dividir texto original
    original_words = clean_and_split_text(original_text, language)
    
    # Se os arrays de tempo não correspondem ao texto transcrito, ajustar
    if len(transcribed_words) != len(start_times):
        print(f"Aviso: Desalinhamento detectado. Palavras: {len(transcribed_words)}, Tempos: {len(start_times)}")
        
        # Truncar ou estender arrays de tempo conforme necessário
        min_length = min(len(transcribed_words), len(start_times), len(end_times))
        transcribed_words = transcribed_words[:min_length]
        start_times = start_times[:min_length]
        end_times = end_times[:min_length]
    
    # Mapear palavras originais com palavras transcritas
    mapped_start_times = []
    mapped_end_times = []
    
    transcribed_idx = 0
    
    for original_word in original_words:
        if transcribed_idx < len(transcribed_words):
            # Verificar se a palavra original corresponde à transcrita
            if (original_word == transcribed_words[transcribed_idx] or 
                similar_words(original_word, transcribed_words[transcribed_idx])):
                
                mapped_start_times.append(start_times[transcribed_idx])
                mapped_end_times.append(end_times[transcribed_idx])
                transcribed_idx += 1
            else:
                # Se não corresponder, usar tempo estimado baseado na palavra anterior
                if mapped_start_times:
                    # Estimar tempo baseado na palavra anterior
                    estimated_duration = 0.3  # 300ms por palavra não encontrada
                    estimated_start = mapped_end_times[-1]
                    estimated_end = estimated_start + estimated_duration
                    
                    mapped_start_times.append(estimated_start)
                    mapped_end_times.append(estimated_end)
                else:
                    # Primeira palavra, usar tempo padrão
                    mapped_start_times.append(0.0)
                    mapped_end_times.append(0.3)
        else:
            # Não há mais palavras transcritas, estimar tempos
            if mapped_start_times:
                estimated_start = mapped_end_times[-1]
                estimated_end = estimated_start + 0.3
                mapped_start_times.append(estimated_start)
                mapped_end_times.append(estimated_end)
            else:
                mapped_start_times.append(0.0)
                mapped_end_times.append(0.3)
    
    return original_words, mapped_start_times, mapped_end_times

def similar_words(word1: str, word2: str, threshold: float = 0.8) -> bool:
    """
    Verifica se duas palavras são similares (para lidar com erros de ASR).
    """
    if not word1 or not word2:
        return False
    
    # Calcular similaridade simples baseada em caracteres comuns
    common_chars = set(word1.lower()) & set(word2.lower())
    max_len = max(len(word1), len(word2))
    
    if max_len == 0:
        return True
    
    similarity = len(common_chars) / max_len
    return similarity >= threshold

# Função principal do lambda (modificada)
def lambda_handler(event, context):
    data = json.loads(event['body'])
    
    real_text = data['title']
    file_bytes = base64.b64decode(
        data['base64Audio'][22:].encode('utf-8'))
    language = data['language']
    
    if len(real_text) == 0:
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Credentials': "true",
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': ''
        }

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=True) as tmp:
        tmp.write(file_bytes)
        tmp.flush()
        tmp_name = tmp.name
        signal, fs = audioread_load(tmp_name)
        signal = transform(torch.Tensor(signal)).unsqueeze(0)

        # Processar o áudio com o modelo de pronunciação
        start = time.time()
        result = trainer_SST_lambda[language].processAudioForGivenText(
            signal, real_text)
        
        real_transcripts_ipa = ' '.join(
            [word[0] for word in result['real_and_transcribed_words_ipa']])
        matched_transcripts_ipa = ' '.join(
            [word[1] for word in result['real_and_transcribed_words_ipa']])

        real_transcripts = ' '.join(
            [word[0] for word in result['real_and_transcribed_words']])
        matched_transcripts = ' '.join(
            [word[1] for word in result['real_and_transcribed_words']])

        # CORREÇÃO APLICADA AQUI - Em vez de split simples, usar função corrigida
        words_real_original = real_transcripts.lower().split()  # Manter original para compatibilidade
        mapped_words_original = matched_transcripts.split()     # Manter original para compatibilidade
        
        # Usar função corrigida para palavras limpas
        words_real_clean = clean_and_split_text(real_transcripts, language)
        mapped_words_clean = clean_and_split_text(matched_transcripts, language)

        is_letter_correct_all_words = ''
        for idx, word_real in enumerate(words_real_original):
            if idx < len(mapped_words_original):
                mapped_letters, mapped_letters_indices = wm.get_best_mapped_words(
                    mapped_words_original[idx], word_real)

                is_letter_correct = wm.getWhichLettersWereTranscribedCorrectly(
                    word_real, mapped_letters)  # , mapped_letters_indices)
                is_letter_correct_all_words += ''.join([str(is_correct)
                                                       for is_correct in is_letter_correct])
                for is_correct in is_letter_correct:
                    is_letter_correct_all_words += str(is_correct)

        pair_accuracy_category = ' '.join(
            [str(result['pronunciation_categories'][i]) for i in range(len(result['pronunciation_categories']))])

        # CORREÇÃO APLICADA - Mapear tempos corretamente com palavras limpas
        if 'start_time' in result and 'end_time' in result:
            original_start_times = result['start_time']
            original_end_times = result['end_time']
            
            # Aplicar correção de mapeamento
            corrected_words, corrected_start_times, corrected_end_times = map_words_to_times(
                real_text, mapped_words_clean, original_start_times, original_end_times, language
            )
            
            start_time_corrected = ' '.join(map(str, corrected_start_times))
            end_time_corrected = ' '.join(map(str, corrected_end_times))
        else:
            # Fallback se não houver tempos
            start_time_corrected = ' '.join(['0.0'] * len(words_real_clean))
            end_time_corrected = ' '.join(['0.5'] * len(words_real_clean))

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Credentials': "true",
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps({
                'pronunciation_accuracy': result['pronunciation_accuracy'],
                'real_transcripts_ipa': real_transcripts_ipa,
                'matched_transcripts_ipa': matched_transcripts_ipa,
                'pair_accuracy_category': pair_accuracy_category,
                'is_letter_correct_all_words': is_letter_correct_all_words,
                'start_time': start_time_corrected,  # Usar tempos corrigidos
                'end_time': end_time_corrected,      # Usar tempos corrigidos
                'ipa_transcript': result['ipa_transcript']
            })
        }

# Função auxiliar para carregar áudio (mantida do original)
def audioread_load(path):
    """Load an audio file using audioread."""
    with audioread.audio_open(path) as input_file:
        sr_native = input_file.samplerate
        n_channels = input_file.channels
        
        # Read all frames
        frames = []
        for frame in input_file:
            frames.append(frame)
        
        # Convert to numpy array
        audio_data = b''.join(frames)
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        # Convert to float and normalize
        audio_array = audio_array.astype(np.float32) / 32768.0
        
        # Handle stereo by taking first channel
        if n_channels > 1:
            audio_array = audio_array[::n_channels]
            
        return audio_array, sr_native

# Transform para resample (mantido do original)
transform = Resample(orig_freq=48000, new_freq=16000)

