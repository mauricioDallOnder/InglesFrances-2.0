# lambdaTTS.py - VERSÃO CORRIGIDA E OTIMIZADA
import models
import soundfile as sf
import json
import AIModels
import utilsFileIO
import os
import base64

# --- Carregamento dos Modelos (executado apenas uma vez, na inicialização da Lambda) ---
SAMPLING_RATE = 16000
print("Iniciando o carregamento dos modelos TTS...")

# Dicionário para armazenar os motores TTS para cada idioma
tts_engines = {
    'en': AIModels.NeuralTTS(
        models.getTTSModel(language='en', speaker='lj_16khz'),
        SAMPLING_RATE
    ),
    'fr': AIModels.NeuralTTS(
        models.getTTSModel(language='fr', speaker='gilles_16khz'),
        SAMPLING_RATE
    )
}
print("Modelos TTS carregados com sucesso!")
# ------------------------------------------------------------------------------------


def lambda_handler(event, context):

    try:
        body = json.loads(event['body'])
        text_string = body['value']
        # Adicione o campo 'lang' no seu JSON. Use 'en' como padrão se não for fornecido.
        lang = body.get('lang', 'en')
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps({"error": f"Erro ao processar o corpo da requisição: {str(e)}"})
        }

    # Seleciona o motor TTS pré-carregado com base no idioma
    model_TTS_lambda = tts_engines.get(lang)

    # Verifica se o idioma solicitado é suportado
    if not model_TTS_lambda:
        return {
            'statusCode': 400,
            'body': json.dumps({
                "error": f"Idioma '{lang}' não suportado. Idiomas disponíveis: {list(tts_engines.keys())}"
            })
        }

    # Geração do áudio com o modelo selecionado
    linear_factor = 0.2
    audio = model_TTS_lambda.getAudioFromSentence(
        text_string).detach().numpy() * linear_factor
    
    random_file_name = utilsFileIO.generateRandomString(20) + '.wav'
    temp_file_path = os.path.join('/tmp', random_file_name) # Use o diretório /tmp na Lambda

    sf.write(temp_file_path, audio, SAMPLING_RATE)

    with open(temp_file_path, "rb") as f:
        audio_byte_array = f.read()

    os.remove(temp_file_path)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(
            {
                "wavBase64": str(base64.b64encode(audio_byte_array))[2:-1],
            },
        )
    }