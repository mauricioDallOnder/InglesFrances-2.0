from flask import Flask, render_template, request
import webbrowser
import os
from flask_cors import CORS
import json
import RuleBasedModels
import PortugueseTranscription

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = '*'

rootPath = ''


@app.route(rootPath+'/')
def main():
    return render_template('main.html')


@app.route(rootPath+'/convertToIPA', methods=['POST'])
def convertToIPA():
    try:
        data = request.get_json(force=True)
        text = data.get('text', '')
        language = data.get('language', 'fr')
        
        if not text.strip():
            return json.dumps({'ipa': ''})
        
        # Get the phoneme converter for the specified language
        phonem_converter = RuleBasedModels.get_phonem_converter(language)
        
        # Convert text to IPA
        ipa_result = phonem_converter.convertToPhonem(text)
        
        return json.dumps({'ipa': ipa_result})
        
    except Exception as e:
        print('Error in convertToIPA: ', str(e))
        return json.dumps({'ipa': '', 'error': str(e)})


@app.route(rootPath+'/convertToPortuguese', methods=['POST'])
def convertToPortuguese():
    try:
        data = request.get_json(force=True)
        ipa_text = data.get('ipa', '')
        language = data.get('language', 'fr')
        
        if not ipa_text.strip():
            return json.dumps({'portuguese': ''})
        
        # Convert IPA to Portuguese approximation
        portuguese_result = PortugueseTranscription.convert_to_portuguese(ipa_text, language)
        
        return json.dumps({'portuguese': portuguese_result})
        
    except Exception as e:
        print('Error in convertToPortuguese: ', str(e))
        return json.dumps({'portuguese': '', 'error': str(e)})


if __name__ == "__main__":
    print("Servidor de teste iniciado em http://127.0.0.1:3002/")
    print("Testando funcionalidade de IPA e transcrição portuguesa")
    app.run(host="0.0.0.0", port=3002, debug=True)

