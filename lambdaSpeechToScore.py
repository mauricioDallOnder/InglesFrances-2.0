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
                      start_times: List[float], end_times: List[float], language: str = 'fr'):
    original_words = clean_and_split_text(original_text, language)
    
    # Se os arrays de tempo não correspondem ao texto transcrito, ajustar
    if len(transcribed_words) != len(start_times):
        print(f"Aviso: Desalinhamento detectado. Palavras: {len(transcribed_words)}, Tempos: {len(start_times)}")
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

# NO ARQUIVO: lambdaSpeechToScore.py
# SUBSTITUA TODA A FUNÇÃO lambda_handler

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

        # 1. O trainer agora faz o trabalho pesado de processamento e alinhamento
        result = trainer_SST_lambda[language].processAudioForGivenText(
            signal, real_text)
        
        # --- INÍCIO DA CORREÇÃO ---
        # 2. Em vez de reprocessar o texto, usamos as listas de palavras já corrigidas
        #    diretamente do resultado do trainer. Isso garante consistência.
        words_real_clean = [word[0] for word in result['real_and_transcribed_words']]
        mapped_words_clean = [word[1] for word in result['real_and_transcribed_words']]

        print("Words real clean (from trainer):", words_real_clean)
        print("Mapped words clean (from trainer):", mapped_words_clean)

        # A lógica de IPA e precisão já usa o resultado direto, o que é bom
        real_transcripts_ipa = ' '.join(
            [word[0] for word in result['real_and_transcribed_words_ipa']])
        matched_transcripts_ipa = ' '.join(
            [word[1] for word in result['real_and_transcribed_words_ipa']])
        
        pair_accuracy_category = ' '.join(
            [str(category) for category in result['pronunciation_categories']])

        # 3. Verificamos se os tempos existem e garantimos que o número de palavras
        #    e tempos bate ANTES de continuar.
        if 'start_time' in result and 'end_time' in result and len(result['start_time']) == len(words_real_clean):
            start_time_str = ' '.join(map(str, result['start_time']))
            end_time_str = ' '.join(map(str, result['end_time']))
        else:
            # Fallback caso haja desalinhamento (como segurança)
            print(f"Aviso de segurança: Desalinhamento detectado no Lambda. Palavras: {len(words_real_clean)}, Tempos: {len(result.get('start_time', []))}")
            start_time_str = ' '.join(['0.0'] * len(words_real_clean))
            end_time_str = ' '.join(['0.5'] * len(words_real_clean))

        # A lógica para 'is_letter_correct_all_words' precisa usar as palavras já processadas
        is_letter_correct_all_words = ''
        for idx, word_real in enumerate(words_real_clean):
            if idx < len(mapped_words_clean):
                mapped_letters, mapped_letters_indices = wm.get_best_mapped_words(
                    mapped_words_clean[idx], word_real)

                is_letter_correct = wm.getWhichLettersWereTranscribedCorrectly(
                    word_real, mapped_letters)
                is_letter_correct_all_words += ''.join([str(int(is_correct)) for is_correct in is_letter_correct])

        # --- FIM DA CORREÇÃO ---

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
                'start_time': start_time_str,  # Usar tempos já formatados
                'end_time': end_time_str,      # Usar tempos já formatados
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

