
import torch
import numpy as np
import models as mo
import WordMetrics
import WordMatching as wm
import epitran
import ModelInterfaces as mi
import string
import RuleBasedModels
from string import punctuation
import time
import re

def clean_text(text: str) -> list:
    """
    Limpa o texto removendo pontuação final de frases/cláusulas,
    mas mantendo apóstrofos e hífens internos para sincronia com o front-end.
    """
    # 1. Converte para minúsculas
    text = text.lower()
    
    # 2. Remove apenas a pontuação que não faz parte de palavras (.,;?!)
    # Esta expressão regular substitui os caracteres .,;?! por uma string vazia
    cleaned_text = re.sub(r'[.,;?!]', '', text)
    
    # 3. Divide o texto limpo por espaços e remove quaisquer elementos vazios
    words = cleaned_text.strip().split()
    
    return words


def getTrainer(language: str):

    asr_model = mo.getASRModel(language,use_whisper=True)
    
    if language == 'de':
        phonem_converter = RuleBasedModels.EpitranPhonemConverter(
            epitran.Epitran('deu-Latn'))
    elif language == 'en':
        phonem_converter = RuleBasedModels.EngPhonemConverter()
    elif language == 'fr':
        phonem_converter = RuleBasedModels.EpitranPhonemConverter(
            epitran.Epitran('fra-Latn-p'))
    else:
        raise ValueError('Language not implemented')

    trainer = PronunciationTrainer(
        asr_model, phonem_converter)

    return trainer


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

        fade_duration_in_samples = 0.05*self.sampling_rate
        word_locations_in_samples = [(int(np.maximum(0, word['start_ts']-fade_duration_in_samples)), int(np.minimum(
            audio_length_in_samples-1, word['end_ts']+fade_duration_in_samples))) for word in word_locations_in_samples]
        
        return audio_transcript, word_locations_in_samples

    def getWordsRelativeIntonation(self, Audio: torch.tensor, word_locations: list):
        intonations = torch.zeros((len(word_locations), 1))
        intonation_fade_samples = 0.3*self.sampling_rate
        print(intonations.shape)
        for word in range(len(word_locations)):
            intonation_start = int(np.maximum(
                0, word_locations[word][0]-intonation_fade_samples))
            intonation_end = int(np.minimum(
                Audio.shape[1]-1, word_locations[word][1]+intonation_fade_samples))
            intonations[word] = torch.sqrt(torch.mean(
                Audio[0][intonation_start:intonation_end]**2))

        intonations = intonations/torch.mean(intonations)
        return intonations

    ##################### ASR Functions ###########################

    def processAudioForGivenText(self, recordedAudio: torch.Tensor = None, real_text=None):

        start = time.time()
        recording_transcript, recording_ipa, word_locations = self.getAudioTranscript(
            recordedAudio)
        print('Time for NN to transcript audio: ', str(time.time()-start))
        print("Word locations:", word_locations)
        start = time.time()
        real_and_transcribed_words, real_and_transcribed_words_ipa, mapped_words_indices = self.matchSampleAndRecordedWords(
            real_text, recording_transcript)
        print('Time for matching transcripts: ', str(time.time()-start))

        start_time, end_time = self.getWordLocationsFromRecordInSeconds(word_locations, mapped_words_indices)

        pronunciation_accuracy, current_words_pronunciation_accuracy = self.getPronunciationAccuracy(
            real_and_transcribed_words)  # _ipa

        pronunciation_categories = self.getWordsPronunciationCategory(
            current_words_pronunciation_accuracy)

        result = {
                'start_time': start_time,
                 'end_time': end_time,
            'recording_transcript': recording_transcript,
                  'real_and_transcribed_words': real_and_transcribed_words,
                  'recording_ipa': recording_ipa, 'start_time': start_time, 'end_time': end_time,
                  'real_and_transcribed_words_ipa': real_and_transcribed_words_ipa, 'pronunciation_accuracy': pronunciation_accuracy,
                  'pronunciation_categories': pronunciation_categories,
                  'ipa_transcript': recording_ipa} # Chave 'ipa_transcript' adicionada
        print("Result start_time:", result['start_time'])
        print("Result end_time:", result['end_time'])

        return result

    # SUBSTITUA A FUNÇÃO ORIGINAL POR ESTA
    def getAudioTranscript(self, recordedAudio: torch.Tensor = None):
        current_recorded_audio = recordedAudio

        current_recorded_audio = self.preprocessAudio(
            current_recorded_audio)

        self.asr_model.processAudio(current_recorded_audio)

        current_recorded_transcript, current_recorded_word_locations = self.getTranscriptAndWordsLocations(
            current_recorded_audio.shape[1])
        
        # --- INÍCIO DA CORREÇÃO 1 ---
        # Garante que a quantidade de palavras e de localizações seja a mesma.
        # O ideal seria corrigir o modelo ASR, mas isso previne o erro.
        transcribed_words = current_recorded_transcript.split()
        min_length = min(len(transcribed_words), len(current_recorded_word_locations))

        # Trunca as listas para terem o mesmo tamanho
        transcribed_words = transcribed_words[:min_length]
        current_recorded_word_locations = current_recorded_word_locations[:min_length]

        # Remonta a string de transcrição para consistência
        current_recorded_transcript = " ".join(transcribed_words)
        # --- FIM DA CORREÇÃO 1 ---

        current_recorded_ipa = self.ipa_converter.convertToPhonem(
            current_recorded_transcript)

        return current_recorded_transcript, current_recorded_ipa, current_recorded_word_locations
    
    def getWordLocationsFromRecordInSeconds(self, word_locations, mapped_words_indices):
        start_time = []
        end_time = []
        # Only include timings for valid indices
        for idx in mapped_words_indices:
            if idx >= 0 and idx < len(word_locations):  # Check bounds
                start_time.append(float(word_locations[idx][0]) / self.sampling_rate)
                end_time.append(float(word_locations[idx][1]) / self.sampling_rate)
            else:
                # Fallback for unmatched words
                start_time.append(0.0)
                end_time.append(0.0)
        return start_time, end_time  # Return lists, not strings

    ##################### END ASR Functions ###########################

    ##################### Evaluation Functions ###########################
    # SUBSTITUA A FUNÇÃO ORIGINAL POR ESTA
    def matchSampleAndRecordedWords(self, real_text, recorded_transcript):
        
        # --- INÍCIO DA CORREÇÃO 2 ---
        # Usa a nova função clean_text para processar os textos de forma consistente
        words_estimated = clean_text(recorded_transcript)
        
        if real_text is None:
            words_real = clean_text(self.current_transcript[0])
        else:
            words_real = clean_text(real_text)
        # --- FIM DA CORREÇÃO 2 ---

        mapped_words, mapped_words_indices = wm.get_best_mapped_words(
            words_estimated, words_real)

        real_and_transcribed_words = []
        real_and_transcribed_words_ipa = []
        for word_idx in range(len(words_real)):
            # Adiciona verificação para evitar 'index out of range'
            if word_idx < len(mapped_words):
                mapped_word = mapped_words[word_idx]
            else:
                mapped_word = '-' # Token para palavra não encontrada

            real_and_transcribed_words.append(
                (words_real[word_idx], mapped_word))
            real_and_transcribed_words_ipa.append((self.ipa_converter.convertToPhonem(words_real[word_idx]),
                                                self.ipa_converter.convertToPhonem(mapped_word)))
        
        # Os prints de depuração que você tinha no seu log original
        print("Transcribed words (cleaned):", words_estimated)
        print("Expected words (cleaned):", words_real)
        print("Mapped indices:", mapped_words_indices)
                
        return real_and_transcribed_words, real_and_transcribed_words_ipa, mapped_words_indices

    def getPronunciationAccuracy(self, real_and_transcribed_words_ipa) -> float:
        total_mismatches = 0.
        number_of_phonemes = 0.
        current_words_pronunciation_accuracy = []
        for pair in real_and_transcribed_words_ipa:

            real_without_punctuation = self.removePunctuation(pair[0]).lower()
            number_of_word_mismatches = WordMetrics.edit_distance_python(
                real_without_punctuation, self.removePunctuation(pair[1]).lower())
            total_mismatches += number_of_word_mismatches
            number_of_phonemes_in_word = len(real_without_punctuation)
            number_of_phonemes += number_of_phonemes_in_word

            current_words_pronunciation_accuracy.append(float(
                number_of_phonemes_in_word-number_of_word_mismatches)/number_of_phonemes_in_word*100)

        percentage_of_correct_pronunciations = (
            number_of_phonemes-total_mismatches)/number_of_phonemes*100

        return np.round(percentage_of_correct_pronunciations), current_words_pronunciation_accuracy

    def removePunctuation(self, word: str) -> str:
        return ''.join([char for char in word if char not in punctuation])

    def getWordsPronunciationCategory(self, accuracies) -> list:
        categories = []

        for accuracy in accuracies:
            categories.append(
                self.getPronunciationCategoryFromAccuracy(accuracy))

        return categories

    def getPronunciationCategoryFromAccuracy(self, accuracy) -> int:
        return np.argmin(abs(self.categories_thresholds-accuracy))

    def preprocessAudio(self, audio: torch.tensor) -> torch.tensor:
        audio = audio-torch.mean(audio)
        audio = audio/torch.max(torch.abs(audio))
        return audio
