# pronunciationTrainer.py - Versão Final e Completa

import torch
import numpy as np
import models as mo
import WordMetrics
import WordMatching as wm
import epitran
import ModelInterfaces as mi
import AIModels
import RuleBasedModels
from string import punctuation
import time
import re

# Importações para o processamento de áudio avançado
import torchaudio
import noisereduce as nr

# -----------------------------------------------------------------------------
# Funções de Apoio (Helpers)
# -----------------------------------------------------------------------------

def remove_noise_and_normalize(wf: torch.Tensor, sr: int) -> torch.Tensor:
    """
    Remove o ruído de fundo e normaliza o volume do áudio para um nível consistente.
    Esta função é chamada antes de o áudio ser processado pelo modelo de IA.
    """
    # Converte o tensor do PyTorch para um array NumPy para usar a biblioteca noisereduce
    arr = wf.squeeze().numpy()
    
    # Reduz o ruído do áudio. O parâmetro prop_decrease controla a agressividade da redução.
    cleaned = nr.reduce_noise(y=arr, sr=sr, prop_decrease=0.8)
    
    # Converte o array NumPy limpo de volta para um tensor do PyTorch
    wf2 = torch.tensor(cleaned, dtype=torch.float32).unsqueeze(0)
    
    # Normaliza o volume usando RMS (Root Mean Square) para garantir consistência
    rms = wf2.pow(2).mean().sqrt()
    
    # Retorna o tensor normalizado, com uma salvaguarda para evitar divisão por zero
    return wf2 / rms if rms > 1e-5 else wf2

def getTrainer(language: str):
    """
    Cria e retorna uma instância do PronunciationTrainer para o idioma especificado.
    """
    asr_model = mo.getASRModel(language, use_whisper=True)
    
    if language == 'de':
        phonem_converter = RuleBasedModels.EpitranPhonemConverter(
            epitran.Epitran('deu-Latn'))
    elif language == 'en':
        phonem_converter = RuleBasedModels.EngPhonemConverter()
    elif language == 'fr':
        phonem_converter = RuleBasedModels.EpitranPhonemConverter(
            epitran.Epitran('fra-Latn-p'))
    else:
        raise ValueError('Idioma não implementado')

    trainer = PronunciationTrainer(
        asr_model, phonem_converter)

    return trainer

def clean_text(text: str) -> list:
    """
    Limpa uma string de texto para garantir a sincronização entre o front-end e o back-end.
    - Converte para minúsculas.
    - Remove pontuação final de frases (.,;?!).
    - Mantém apóstrofos (') e hífens (-) que fazem parte de palavras.
    - Divide o texto em uma lista de palavras.
    """
    # 1. Converte para minúsculas
    text = text.lower()
    
    # 2. Usa uma expressão regular para remover apenas a pontuação que não faz parte de palavras
    cleaned_text = re.sub(r'[.,;?!]', '', text)
    
    # 3. Divide o texto limpo por espaços e retorna a lista de palavras
    words = cleaned_text.strip().split()
    
    return words

# -----------------------------------------------------------------------------
# Classe Principal do Treinador de Pronúncia
# -----------------------------------------------------------------------------

class PronunciationTrainer:
    current_transcript: str
    current_ipa: str
    current_recorded_audio: torch.Tensor
    current_recorded_transcript: str
    current_recorded_word_locations: list
    current_recorded_intonations: torch.tensor
    current_words_pronunciation_accuracy = []
    categories_thresholds = np.array([80, 60, 59])

    sampling_rate = 16000

    def __init__(self, asr_model: mi.IASRModel, word_to_ipa_coverter: mi.ITextToPhonemModel) -> None:
        self.asr_model = asr_model
        self.ipa_converter = word_to_ipa_coverter

    def getTranscriptAndWordsLocations(self, audio_length_in_samples: int):
        audio_transcript = self.asr_model.getTranscript()
        word_locations_in_samples = self.asr_model.getWordLocations()

        fade_duration_in_samples = 0.05 * self.sampling_rate
        word_locations_in_samples = [(int(np.maximum(0, word['start_ts'] - fade_duration_in_samples)), int(np.minimum(
            audio_length_in_samples - 1, word['end_ts'] + fade_duration_in_samples))) for word in word_locations_in_samples]
        
        return audio_transcript, word_locations_in_samples

    def getWordsRelativeIntonation(self, Audio: torch.tensor, word_locations: list):
        intonations = torch.zeros((len(word_locations), 1))
        intonation_fade_samples = 0.3 * self.sampling_rate
        print(intonations.shape)
        for word in range(len(word_locations)):
            intonation_start = int(np.maximum(
                0, word_locations[word][0] - intonation_fade_samples))
            intonation_end = int(np.minimum(
                Audio.shape[1] - 1, word_locations[word][1] + intonation_fade_samples))
            intonations[word] = torch.sqrt(torch.mean(
                Audio[0][intonation_start:intonation_end]**2))

        intonations = intonations / torch.mean(intonations)
        return intonations

    def processAudioForGivenText(self, recordedAudio: torch.Tensor = None, real_text=None):
        start_time_proc = time.time()
        recording_transcript, recording_ipa, word_locations = self.getAudioTranscript(
            recordedAudio)
        print('Time for NN to transcript audio: ', str(time.time() - start_time_proc))
        
        start_time_match = time.time()
        real_and_transcribed_words, real_and_transcribed_words_ipa, mapped_words_indices = self.matchSampleAndRecordedWords(
            real_text, recording_transcript)
        print('Time for matching transcripts: ', str(time.time() - start_time_match))

        start_time, end_time = self.getWordLocationsFromRecordInSeconds(word_locations, mapped_words_indices)

        pronunciation_accuracy, current_words_pronunciation_accuracy = self.getPronunciationAccuracy(
            real_and_transcribed_words)

        pronunciation_categories = self.getWordsPronunciationCategory(
            current_words_pronunciation_accuracy)

        result = {
            'real_and_transcribed_words': real_and_transcribed_words,
            'recording_ipa': recording_ipa, 
            'start_time': start_time, 
            'end_time': end_time,
            'real_and_transcribed_words_ipa': real_and_transcribed_words_ipa, 
            'pronunciation_accuracy': pronunciation_accuracy,
            'pronunciation_categories': pronunciation_categories,
            'ipa_transcript': recording_ipa
        }
        
        print("Result start_time:", result['start_time'])
        print("Result end_time:", result['end_time'])

        return result

    def getAudioTranscript(self, recordedAudio: torch.Tensor = None):
        current_recorded_audio = recordedAudio
        current_recorded_audio = self.preprocessAudio(current_recorded_audio)
        self.asr_model.processAudio(current_recorded_audio)
        current_recorded_transcript, current_recorded_word_locations = self.getTranscriptAndWordsLocations(
            current_recorded_audio.shape[1])
        current_recorded_ipa = self.ipa_converter.convertToPhonem(current_recorded_transcript)
        return current_recorded_transcript, current_recorded_ipa, current_recorded_word_locations

    def getWordLocationsFromRecordInSeconds(self, word_locations, mapped_words_indices):
        start_time = []
        end_time = []
        for idx in mapped_words_indices:
            if idx >= 0 and idx < len(word_locations):
                start_time.append(float(word_locations[idx][0]) / self.sampling_rate)
                end_time.append(float(word_locations[idx][1]) / self.sampling_rate)
            else:
                start_time.append(0.0)
                end_time.append(0.0)
        return start_time, end_time

    def matchSampleAndRecordedWords(self, real_text, recorded_transcript):
        words_estimated = clean_text(recorded_transcript)
        words_real = clean_text(real_text) if real_text is not None else clean_text(self.current_transcript[0])

        mapped_words, mapped_words_indices = wm.get_best_mapped_words(words_estimated, words_real)

        real_and_transcribed_words = []
        real_and_transcribed_words_ipa = []
        for word_idx in range(len(words_real)):
            # Garante que mapped_words tenha um item para cada palavra real
            mapped_word = mapped_words[word_idx] if word_idx < len(mapped_words) else '-'
            
            real_and_transcribed_words.append((words_real[word_idx], mapped_word))
            real_and_transcribed_words_ipa.append((self.ipa_converter.convertToPhonem(words_real[word_idx]),
                                                   self.ipa_converter.convertToPhonem(mapped_word)))
        
        print("Transcribed words (cleaned):", words_estimated)
        print("Expected words (cleaned):", words_real)
        print("Mapped indices:", mapped_words_indices)
        
        return real_and_transcribed_words, real_and_transcribed_words_ipa, mapped_words_indices

    def getPronunciationAccuracy(self, real_and_transcribed_words_ipa) -> float:
        total_mismatches = 0.0
        number_of_phonemes = 0.0
        current_words_pronunciation_accuracy = []
        for pair in real_and_transcribed_words_ipa:
            real_without_punctuation = self.removePunctuation(pair[0]).lower()
            number_of_word_mismatches = WordMetrics.edit_distance_python(
                real_without_punctuation, self.removePunctuation(pair[1]).lower())
            total_mismatches += number_of_word_mismatches
            number_of_phonemes_in_word = len(real_without_punctuation)
            number_of_phonemes += number_of_phonemes_in_word
            
            # Evita divisão por zero
            if number_of_phonemes_in_word > 0:
                accuracy = float(number_of_phonemes_in_word - number_of_word_mismatches) / number_of_phonemes_in_word * 100
            else:
                accuracy = 0.0
            current_words_pronunciation_accuracy.append(accuracy)

        # Evita divisão por zero
        if number_of_phonemes > 0:
            percentage_of_correct_pronunciations = (number_of_phonemes - total_mismatches) / number_of_phonemes * 100
        else:
            percentage_of_correct_pronunciations = 0.0

        return np.round(percentage_of_correct_pronunciations), current_words_pronunciation_accuracy

    def removePunctuation(self, word: str) -> str:
        return ''.join([char for char in word if char not in punctuation])

    def getWordsPronunciationCategory(self, accuracies) -> list:
        categories = []
        for accuracy in accuracies:
            categories.append(self.getPronunciationCategoryFromAccuracy(accuracy))
        return categories

    def getPronunciationCategoryFromAccuracy(self, accuracy) -> int:
        return np.argmin(abs(self.categories_thresholds - accuracy))

    def preprocessAudio(self, audio: torch.tensor) -> torch.tensor:
        """
        Função de pré-processamento de áudio que usa a nova lógica de 
        redução de ruído e normalização de volume.
        """
        processed_audio = remove_noise_and_normalize(audio, self.sampling_rate)
        return processed_audio