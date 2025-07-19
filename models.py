import torch
import torch.nn as nn
import pickle
from ModelInterfaces import IASRModel
from AIModels import NeuralASR 
# Você precisará da biblioteca 'transformers' e 'sentencepiece'
# pip install transformers sentencepiece
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

def getASRModel(language: str,use_whisper:bool=True) -> IASRModel:

    if use_whisper:
        from whisper_wrapper import WhisperASRModel
        return WhisperASRModel()
    
    if language == 'de':

        model, decoder, utils = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                               model='silero_stt',
                                               language='de',
                                               device=torch.device('cpu'))
        model.eval()
        return NeuralASR(model, decoder)

    elif language == 'en':
        model, decoder, utils = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                               model='silero_stt',
                                               language='en',
                                               device=torch.device('cpu'))
        model.eval()
        return NeuralASR(model, decoder)
    elif language == 'fr':
        model, decoder, utils = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                               model='silero_stt',
                                               language='fr',
                                               device=torch.device('cpu'))
        model.eval()
        return NeuralASR(model, decoder)
    else:
        raise ValueError('Language not implemented')


def getTTSModel(language: str) -> nn.Module:

    if language == 'de':

        speaker = 'thorsten_v2'  # 16 kHz
        model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                  model='silero_tts',
                                  language=language,
                                  speaker=speaker)

    elif language == 'en':
        speaker = 'lj_16khz'  # 16 kHz
        model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models',
                               model='silero_tts',
                               language=language,
                               speaker=speaker)
                               
    # <<< ADICIONADO O BLOCO PARA FRANCÊS >>>
    elif language == 'fr':
        # 'gilles_16khz' é uma das vozes disponíveis para o francês
        speaker = 'gilles_16khz'
        model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                  model='silero_tts',
                                  language=language,
                                  speaker=speaker)
    # <<< FIM DA ADIÇÃO >>>
    
    else:
        raise ValueError('Language not implemented')

    return model


def getTranslationModel(language: str): # Retorna uma tupla (model, tokenizer)
    
    if language == 'de':
        model_name = "Helsinki-NLP/opus-mt-de-en"
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Cache models to avoid Hugging face processing
        with open('translation_model_de.pickle', 'wb') as handle:
            pickle.dump(model, handle)
        with open('translation_tokenizer_de.pickle', 'wb') as handle:
            pickle.dump(tokenizer, handle)

    # <<< ADICIONADO O BLOCO PARA FRANCÊS >>>
    elif language == 'fr':
        # Modelo para tradução de Francês para Inglês
        model_name = "Helsinki-NLP/opus-mt-fr-en"
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Cache para os modelos de francês para evitar o download a cada execução
        with open('translation_model_fr.pickle', 'wb') as handle:
            pickle.dump(model, handle)
        with open('translation_tokenizer_fr.pickle', 'wb') as handle:
            pickle.dump(tokenizer, handle)
    # <<< FIM DA ADIÇÃO >>>
            
    else:
        raise ValueError('Language not implemented')

    return model, tokenizer