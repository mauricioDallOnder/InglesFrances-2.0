

// Audio context initialization
let mediaRecorder, audioChunks, audioBlob, stream, audioRecorded;
const ctx = new AudioContext();
let currentAudioForPlaying;
let lettersOfWordAreCorrect = [];

// UI-related variables
const page_title = "AI Pronunciation Trainer";
const accuracy_colors = ["green", "orange", "red"];
let badScoreThreshold = 30;
let mediumScoreThreshold = 70;
let currentSample = 0;
let currentScore = 0.;
let sample_difficult = 0;
let scoreMultiplier = 1;
let playAnswerSounds = true;
let isNativeSelectedForPlayback = true;
let isRecording = false;
let serverIsInitialized = false;
let serverWorking = true;
let languageFound = true;
let currentSoundRecorded = false;
let currentText, currentIpa, real_transcripts_ipa, matched_transcripts_ipa;
let wordCategories;
let startTime, endTime;
let realWords, mappedWords; // <-- ADICIONE ESTA LINHA
// API related variables 
let AILanguage = "fr"; // Standard is German
var synth = window.speechSynthesis;
let utterance = null; 

let STScoreAPIKey = 'rll5QsTiv83nti99BW6uCmvs9BDVxSB39SVFceYb'; // Public Key. If, for some reason, you would like a private one, send-me a message and we can discuss some possibilities
let apiMainPathSample = '';// 'http://127.0.0.1:3001';// 'https://a3hj0l2j2m.execute-api.eu-central-1.amazonaws.com/Prod';
let apiMainPathSTS = '';// 'https://wrg7ayuv7i.execute-api.eu-central-1.amazonaws.com/Prod';


// Variables to playback accuracy sounds
let soundsPath = '../static';//'https://stscore-sounds-bucket.s3.eu-central-1.amazonaws.com';
let soundFileGood = null;
let soundFileOkay = null;
let soundFileBad = null;

// Speech generation
var synth = window.speechSynthesis;
let voice_idx = 0;
let voice_synth = null;

// Real-time IPA conversion variables
let ipaConversionTimeout = null;
let isConvertingIPA = false;
const IPA_DEBOUNCE_DELAY = 300; // milliseconds

// --- NOVAS VARIÁVEIS ---
let currentTooltip = null; // Controla o pop-up que está visível
let lastAnalysisData = null; // Armazena os dados da API para o pop-up
// --- FIM DAS NOVAS VARIÁVEIS ---

//############################ UI general control functions ###################
const unblockUI = () => {
    document.getElementById("recordAudio").classList.remove('disabled');
    document.getElementById("playSampleAudio").classList.remove('disabled');
    document.getElementById("buttonNext").onclick = () => getNextSample();
    document.getElementById("nextButtonDiv").classList.remove('disabled');
    document.getElementById("original_script").classList.remove('disabled');
    document.getElementById("buttonNext").style["background-color"] = '#58636d';

    if (currentSoundRecorded)
        document.getElementById("playRecordedAudio").classList.remove('disabled');


};

const blockUI = () => {

    document.getElementById("recordAudio").classList.add('disabled');
    document.getElementById("playSampleAudio").classList.add('disabled');
    document.getElementById("buttonNext").onclick = null;
    document.getElementById("original_script").classList.add('disabled');
    document.getElementById("playRecordedAudio").classList.add('disabled');

    document.getElementById("buttonNext").style["background-color"] = '#adadad';


};

const UIError = () => {
    blockUI();
    document.getElementById("buttonNext").onclick = () => getNextSample(); //If error, user can only try to get a new sample
    document.getElementById("buttonNext").style["background-color"] = '#58636d';

    document.getElementById("recorded_ipa_script").innerHTML = "";
    document.getElementById("single_word_ipa_pair").innerHTML = "Error";
    document.getElementById("ipa_script").innerHTML = "Error"

    document.getElementById("main_title").innerHTML = 'Server Error';
    document.getElementById("original_script").innerHTML = 'Server error. Either the daily quota of the server is over or there was some internal error. You can try to generate a new sample in a few seconds. If the error persist, try comming back tomorrow or download the local version from Github :)';
};

const UINotSupported = () => {
    unblockUI();

    document.getElementById("main_title").innerHTML = "Browser unsupported";

}

const UIRecordingError = () => {
    unblockUI();
    document.getElementById("main_title").innerHTML = "Recording error, please try again or restart page.";
    startMediaDevice();
}



//################### Application state functions #######################
function updateScore(currentPronunciationScore) {

    if (isNaN(currentPronunciationScore))
        return;
    currentScore += currentPronunciationScore * scoreMultiplier;
    currentScore = Math.round(currentScore);
}

const cacheSoundFiles = async () => {
    await fetch(soundsPath + '/ASR_good.wav').then(data => data.arrayBuffer()).
        then(arrayBuffer => ctx.decodeAudioData(arrayBuffer)).
        then(decodeAudioData => {
            soundFileGood = decodeAudioData;
        });

    await fetch(soundsPath + '/ASR_okay.wav').then(data => data.arrayBuffer()).
        then(arrayBuffer => ctx.decodeAudioData(arrayBuffer)).
        then(decodeAudioData => {
            soundFileOkay = decodeAudioData;
        });

    await fetch(soundsPath + '/ASR_bad.wav').then(data => data.arrayBuffer()).
        then(arrayBuffer => ctx.decodeAudioData(arrayBuffer)).
        then(decodeAudioData => {
            soundFileBad = decodeAudioData;
        });
}

const getNextSample = async () => {



    blockUI();

    if (!serverIsInitialized)
        await initializeServer();

    if (!serverWorking) {
        UIError();
        return;
    }

    if (soundFileBad == null)
        cacheSoundFiles();



    updateScore(parseFloat(document.getElementById("pronunciation_accuracy").innerHTML));

    document.getElementById("main_title").innerHTML = "Processing new sample...";


    if (document.getElementById('lengthCat1').checked) {
        sample_difficult = 0;
        scoreMultiplier = 1.3;
    }
    else if (document.getElementById('lengthCat2').checked) {
        sample_difficult = 1;
        scoreMultiplier = 1;
    }
    else if (document.getElementById('lengthCat3').checked) {
        sample_difficult = 2;
        scoreMultiplier = 1.3;
    }
    else if (document.getElementById('lengthCat4').checked) {
        sample_difficult = 3;
        scoreMultiplier = 1.6;
    }

    try {
        await fetch(apiMainPathSample + '/getSample', {
            method: "post",
            body: JSON.stringify({
                "category": sample_difficult.toString(), "language": AILanguage
            }),
            headers: { "X-Api-Key": STScoreAPIKey }
        }).then(res => res.json()).
            then(data => {



                let doc = document.getElementById("original_script");
                currentText = data.real_transcript;
                doc.innerHTML = currentText;

                currentIpa = data.ipa_transcript

                let doc_ipa = document.getElementById("ipa_script");
                doc_ipa.innerHTML = "/ " + currentIpa + " /";

                // Generate Portuguese transcription for generated sentences
                generatePortugueseForGeneratedSentence(currentIpa);

                document.getElementById("recorded_ipa_script").innerHTML = ""
                document.getElementById("pronunciation_accuracy").innerHTML = "";
                document.getElementById("single_word_ipa_pair").innerHTML = "Reference | Spoken"
                document.getElementById("section_accuracy").innerHTML = "| Score: " + currentScore.toString() + " - (" + currentSample.toString() + ")";
                currentSample += 1;

                document.getElementById("main_title").innerHTML = page_title;

                document.getElementById("translated_script").innerHTML = data.transcript_translation;

                currentSoundRecorded = false;
                unblockUI();
                document.getElementById("playRecordedAudio").classList.add('disabled');

            })
    }
    catch
    {
        UIError();
    }


};

const updateRecordingState = async () => {
    if (isRecording) {
        stopRecording();
        return
    }
    else {
        recordSample()
        return;
    }
}

const generateWordModal = (word_idx) => {
    const referenceWord = realWords[word_idx];
    const spokenWord = mappedWords[word_idx];
    document.getElementById("single_word_ipa_pair").innerHTML =
        wrapWordForPlayingLink(referenceWord, word_idx, false, "black") +
        ' | ' +
        wrapWordForPlayingLink(spokenWord, word_idx, true, accuracy_colors[parseInt(wordCategories[word_idx])]);
}

const recordSample = async () => {

    document.getElementById("main_title").innerHTML = "Recording... click again when done speaking";
    document.getElementById("recordIcon").innerHTML = 'pause_presentation';
    blockUI();
    document.getElementById("recordAudio").classList.remove('disabled');
    audioChunks = [];
    isRecording = true;
    mediaRecorder.start();

}

// Function to find the best voice for a specific language
const findBestVoice = (targetLang) => {
    const langPrefix = targetLang.substring(0, 2); // 'fr' or 'en'
    let voices = synth.getVoices().filter((voice) => voice.lang.startsWith(langPrefix));

    if (voices.length === 0) {
        console.warn(`No voice found for language: ${targetLang}`);
        return null;
    }

    // Search priority:
    // 1. Specific voice for the locale (e.g., en-GB) and high quality.
    // 2. Specific voice for the locale.
    // 3. First voice found for the language (e.g., any 'en' voice).

    const premiumKeywords = ["enhanced", "premium", "neural", "google", "microsoft", "apple", "natural"];
    
    let bestVoice = voices.find(voice => voice.lang === targetLang && premiumKeywords.some(kw => voice.name.toLowerCase().includes(kw)));
    if (bestVoice) return bestVoice;

    bestVoice = voices.find(voice => voice.lang === targetLang);
    if (bestVoice) return bestVoice;
    
    // If it's English, prioritize British voices if exact 'en-GB' not found
    if(langPrefix === 'en') {
        let ukVoice = voices.find(v => v.name.toLowerCase().includes('uk') || v.name.toLowerCase().includes('british'));
        if(ukVoice) return ukVoice;
    }

    // If it's French, prioritize French voices
    if(langPrefix === 'fr') {
        let frVoice = voices.find(v => v.name.toLowerCase().includes('french') || v.name.toLowerCase().includes('france'));
        if(frVoice) return frVoice;
    }

    console.log(`No specific voice for '${targetLang}' found. Using first available: ${voices[0].name}`);
    return voices[0]; 
};

const changeLanguage = (language, generateNewSample = false) => {
    voices = synth.getVoices();
    AILanguage = language;
    languageFound = false;
    let targetLang;
    
    switch (language) {
        case 'en':
            document.getElementById("languageBox").innerHTML = "English";
            targetLang = 'en-GB'; // Prioritize British English
            break;

        case 'fr':
            document.getElementById("languageBox").innerHTML = "French";
            targetLang = 'fr-FR'; // Prioritize French from France
            break;
            
        default:
            console.warn(`Unsupported language: ${language}`);
            return;
    }

    // Use the improved voice selection function
    voice_synth = findBestVoice(targetLang);
    
    if (voice_synth) {
        languageFound = true;
        console.log(`Selected voice: ${voice_synth.name} (Language: ${voice_synth.lang})`);
    } else {
        console.warn(`No voice found for language: ${language}`);
        languageFound = false;
    }
    
    if (generateNewSample)
        getNextSample();
}


//################### Speech-To-Score function ########################
const mediaStreamConstraints = {
    audio: {
        channelCount: 1,
        sampleRate: 48000
    }
}


const startMediaDevice = () => {
    navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, sampleRate: 48000 } }).then(_stream => {
        stream = _stream;
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            document.getElementById("recordIcon").innerHTML = 'mic';
            blockUI();

            audioBlob = new Blob(audioChunks, { type: 'audio/ogg;' });
            let audioUrl = URL.createObjectURL(audioBlob);
            audioRecorded = new Audio(audioUrl);
            let audioBase64 = await convertBlobToBase64(audioBlob);

            if (audioBase64.length < 6) {
                setTimeout(UIRecordingError, 50);
                return;
            }

           // CÓDIGO CORRIGIDO E MAIS SEGURO
            try {
                let text = document.getElementById("original_script").innerText;
                currentText = [text];

                const response = await fetch(apiMainPathSTS + '/GetAccuracyFromRecordedAudio', {
                    method: "post",
                    body: JSON.stringify({ "title": currentText[0], "base64Audio": audioBase64, "language": AILanguage }),
                    headers: { "X-Api-Key": STScoreAPIKey }
                });

                // 1. VERIFICA SE A RESPOSTA DA REDE FOI BEM-SUCEDIDA (ex: status 200)
                if (!response.ok) {
                    throw new Error(`Erro na API: status ${response.status}`);
                }

                const responseData = await response.json();

                // 2. VERIFICA SE O 'body' DENTRO DO JSON EXISTE E É VÁLIDO
                if (!responseData || typeof responseData.body !== 'string' || responseData.body.length === 0) {
                    throw new Error("A resposta da API não continha um corpo ('body') válido.");
                }

                // 3. AGORA, COM SEGURANÇA, FAZ O PARSE DO JSON INTERNO
                const data = JSON.parse(responseData.body);
                lastAnalysisData = data; // Armazena os dados para o pop-up

                // A partir daqui, seu código original continua
                if (playAnswerSounds) playSoundForAnswerAccuracy(parseFloat(data.pronunciation_accuracy));

                document.getElementById("recorded_ipa_script").innerHTML = "/ " + data.ipa_transcript + " /";
                document.getElementById("main_title").innerHTML = page_title;
                document.getElementById("pronunciation_accuracy").innerHTML = data.pronunciation_accuracy + "%";
                document.getElementById("ipa_script").innerHTML = data.real_transcripts_ipa;

                startTime = data.start_time;
                endTime = data.end_time;
                real_transcripts_ipa = data.real_transcripts_ipa.split(" ");
                matched_transcripts_ipa = data.matched_transcripts_ipa.split(" ");
                realWords = data.real_words.split(" ");
                mappedWords = data.mapped_words.split(" ");
                wordCategories = data.pair_accuracy_category.split(" ");
                let currentTextWords = cleanAndSplitText(currentText[0]);

                let coloredWords = "";
                const correctness_string = data.is_letter_correct_all_words;
                let correctness_idx = 0;

                for (let word_idx = 0; word_idx < currentTextWords.length; word_idx++) {
                    let wordTemp = '';
                    const currentWord = currentTextWords[word_idx];
                    const wordCategory = parseInt(wordCategories[word_idx]);
                    const overallWordColor = accuracy_colors[wordCategory];

                    for (let letter_idx = 0; letter_idx < currentWord.length; letter_idx++) {
                        let final_letter_color = '';
                        if (wordCategory === 1 || wordCategory === 2) {
                            final_letter_color = overallWordColor;
                        } else {
                            const letter_is_correct = correctness_string[correctness_idx] === '1';
                            final_letter_color = letter_is_correct ? 'green' : 'red';
                        }
                        wordTemp += '<font color=' + final_letter_color + '>' + currentWord[letter_idx] + "</font>";
                        if (correctness_idx < correctness_string.length) correctness_idx++;
                    }
                    coloredWords += " " + wrapWordForIndividualPlayback(wordTemp, word_idx);
                }

                document.getElementById("original_script").innerHTML = coloredWords.trim();
                currentSoundRecorded = true;
                unblockUI();
                
            } catch (error) {
                // O erro capturado aqui será muito mais informativo
                console.error("Erro ao processar áudio:", error);
                UIError();
            }
        };
    });
};

startMediaDevice();

// ################### Audio playback ##################
const playSoundForAnswerAccuracy = async (accuracy) => {

    currentAudioForPlaying = soundFileGood;
    if (accuracy < mediumScoreThreshold) {
        if (accuracy < badScoreThreshold) {
            currentAudioForPlaying = soundFileBad;
        }
        else {
            currentAudioForPlaying = soundFileOkay;
        }
    }
    playback();

}

const playAudio = async () => {

    document.getElementById("main_title").innerHTML = "Generating sound...";
    const currentUserText = getCurrentText();
    if (currentUserText && currentUserText.length > 0) {
        playWithMozillaApi(currentUserText);
    } else {
        // Fallback to original text if no user text
        playWithMozillaApi(currentText[0]);
    }
    document.getElementById("main_title").innerHTML = "Current Sound was played";

};

function playback() {
    const playSound = ctx.createBufferSource();
    playSound.buffer = currentAudioForPlaying;
    playSound.connect(ctx.destination);
    playSound.start(ctx.currentTime)
}


const playRecording = async (start = null, end = null) => {
    blockUI();

    try {
        if (start == null || end == null) {
            endTimeInMs = Math.round(audioRecorded.duration * 1000)
            audioRecorded.addEventListener("ended", function () {
                audioRecorded.currentTime = 0;
                unblockUI();
                document.getElementById("main_title").innerHTML = "Recorded Sound was played";
            });
            await audioRecorded.play();

        }
        else {
            audioRecorded.currentTime = start;
            audioRecorded.play();
            durationInSeconds = end - start;
            endTimeInMs = Math.round(durationInSeconds * 1000);
            setTimeout(function () {
                unblockUI();
                audioRecorded.pause();
                audioRecorded.currentTime = 0;
                document.getElementById("main_title").innerHTML = "Recorded Sound was played";
            }, endTimeInMs);

        }
    }
    catch {
        UINotSupported();
    }
};

const playNativeAndRecordedWord = async (word_idx) => {

    if (isNativeSelectedForPlayback)
        playCurrentWord(word_idx)
    else
        playRecordedWord(word_idx);

    isNativeSelectedForPlayback = !isNativeSelectedForPlayback;
}

const stopRecording = () => {
    isRecording = false
    mediaRecorder.stop()
    document.getElementById("main_title").innerHTML = "Processing audio...";
}


const playCurrentWord = async (word_idx) => {

    document.getElementById("main_title").innerHTML = "Generating word...";
    const currentUserText = getCurrentText();
    if (currentUserText && currentUserText.length > 0) {
        const words = currentUserText.split(' ');
        if (word_idx < words.length) {
            playWithMozillaApi(words[word_idx]);
        } else {
            // Fallback if word index is out of bounds
            playWithMozillaApi(currentText[0].split(' ')[word_idx]);
        }
    } else {
        // Fallback to original text if no user text
        playWithMozillaApi(currentText[0].split(' ')[word_idx]);
    }
    document.getElementById("main_title").innerHTML = "Word was played";
}

// TODO: Check if fallback is correct
const playWithMozillaApi = (text) => {

    if (languageFound) {
        blockUI();
        if (voice_synth == null)
            changeLanguage(AILanguage);

        var utterThis = new SpeechSynthesisUtterance(text);
        utterThis.voice = voice_synth;
        utterThis.rate = 0.7;
        utterThis.onend = function (event) {
            unblockUI();
        }
        synth.speak(utterThis);
    }
    else {
        UINotSupported();
    }
}
// Versão corrigida das funções de reprodução de palavras gravadas
// Corrige problemas de sincronização com pontuação

// Função melhorada para reproduzir palavra gravada
const playRecordedWord = (word_idx) => {
    // Garante que os tempos são arrays de números válidos
    const startTimes = (startTime || '').split(' ')
        .map(t => parseFloat(t))
        .filter(t => !isNaN(t) && t >= 0);
    
    const endTimes = (endTime || '').split(' ')
        .map(t => parseFloat(t))
        .filter(t => !isNaN(t) && t >= 0);

    // Validação de índice
    if (word_idx < 0 || word_idx >= startTimes.length || word_idx >= endTimes.length) {
        console.error(`Índice de palavra (${word_idx}) fora do intervalo válido. Disponível: 0-${Math.min(startTimes.length, endTimes.length) - 1}`);
        return;
    }

    let adjustedStartTime = startTimes[word_idx];
    let adjustedEndTime = endTimes[word_idx];

    // Aplicar correções específicas por idioma
    if (AILanguage === 'fr') {
        const correctedTimes = correctFrenchWordTiming(word_idx, startTimes, endTimes);
        adjustedStartTime = correctedTimes.start;
        adjustedEndTime = correctedTimes.end;
    } else if (AILanguage === 'en') {
        const correctedTimes = correctEnglishWordTiming(word_idx, startTimes, endTimes);
        adjustedStartTime = correctedTimes.start;
        adjustedEndTime = correctedTimes.end;
    }

    // Validação final para garantir tempos válidos
    if (adjustedEndTime <= adjustedStartTime) {
        // Se a duração for inválida, criar uma duração mínima segura
        const minDuration = 0.2; // 200ms mínimo
        adjustedEndTime = adjustedStartTime + minDuration;
    }

    // Garantir que os tempos não sejam negativos
    adjustedStartTime = Math.max(0, adjustedStartTime);
    adjustedEndTime = Math.max(adjustedStartTime + 0.1, adjustedEndTime);

    console.log(`Reproduzindo palavra ${word_idx}: ${adjustedStartTime.toFixed(3)}s - ${adjustedEndTime.toFixed(3)}s (duração: ${(adjustedEndTime - adjustedStartTime).toFixed(3)}s)`);
    
    playRecording(adjustedStartTime, adjustedEndTime);
};

// Função melhorada para correção de timing em francês
const correctFrenchWordTiming = (word_idx, startTimes, endTimes) => {
    let correctedStart = startTimes[word_idx];
    let correctedEnd = endTimes[word_idx];

    // Margem de segurança para evitar sobreposições
    const safetyMargin = 0.02; // 20ms

    // Estratégia 1: Corrigir sobreposição com a palavra anterior
    if (word_idx > 0) {
        const previousEndTime = endTimes[word_idx - 1];
        if (correctedStart < previousEndTime + safetyMargin) {
            correctedStart = previousEndTime + safetyMargin;
            console.log(`Correção FR - Palavra ${word_idx}: Início ajustado para ${correctedStart.toFixed(3)}s (evitar sobreposição)`);
        }
    }

    // Estratégia 2: Garantir que a palavra não invada a próxima
    if (word_idx < startTimes.length - 1) {
        const nextStartTime = startTimes[word_idx + 1];
        if (correctedEnd > nextStartTime - safetyMargin) {
            correctedEnd = nextStartTime - safetyMargin;
            console.log(`Correção FR - Palavra ${word_idx}: Fim ajustado para ${correctedEnd.toFixed(3)}s (evitar invasão)`);
        }
    }

    // Estratégia 3: Garantir duração mínima
    const minDuration = 0.15; // 150ms mínimo para francês
    if (correctedEnd - correctedStart < minDuration) {
        correctedEnd = correctedStart + minDuration;
        console.log(`Correção FR - Palavra ${word_idx}: Duração ajustada para ${minDuration}s`);
    }

    // Estratégia 4: Tratamento especial para palavras muito curtas (artigos, preposições)
    const currentText = getCurrentText();
    if (currentText) {
        const words = cleanAndSplitText(currentText);
        if (word_idx < words.length) {
            const currentWord = words[word_idx];
            const shortWords = ['le', 'la', 'les', 'un', 'une', 'de', 'du', 'des', 'à', 'au', 'aux', 'et', 'ou', 'ne', 'se', 'me', 'te', 'ce'];
            
            if (shortWords.includes(currentWord.toLowerCase())) {
                // Palavras curtas podem ter duração reduzida mas não muito
                const shortWordDuration = Math.max(0.1, correctedEnd - correctedStart);
                correctedEnd = correctedStart + shortWordDuration;
            }
        }
    }

    return {
        start: correctedStart,
        end: correctedEnd
    };
};

// Função para correção de timing em inglês
const correctEnglishWordTiming = (word_idx, startTimes, endTimes) => {
    let correctedStart = startTimes[word_idx];
    let correctedEnd = endTimes[word_idx];

    const safetyMargin = 0.015; // 15ms para inglês

    // Aplicar correções similares ao francês mas com parâmetros ajustados
    if (word_idx > 0) {
        const previousEndTime = endTimes[word_idx - 1];
        if (correctedStart < previousEndTime + safetyMargin) {
            correctedStart = previousEndTime + safetyMargin;
        }
    }

    if (word_idx < startTimes.length - 1) {
        const nextStartTime = startTimes[word_idx + 1];
        if (correctedEnd > nextStartTime - safetyMargin) {
            correctedEnd = nextStartTime - safetyMargin;
        }
    }

    const minDuration = 0.12; // 120ms mínimo para inglês
    if (correctedEnd - correctedStart < minDuration) {
        correctedEnd = correctedStart + minDuration;
    }

    return {
        start: correctedStart,
        end: correctedEnd
    };
};

// --- FUNÇÃO DE LIMPEZA UNIFICADA ---
const cleanAndSplitText = (text) => {
    if (!text) return [];
    let lowerText = text.toLowerCase();
    // Remove pontuação final mas mantém apóstrofos e hífens
    let cleanedText = lowerText.replace(/[.,;?!]/g, '');
    // Divide por espaços e remove itens vazios
    return cleanedText.trim().split(/\s+/).filter(Boolean);
};

// Função melhorada para obter texto atual limpo
const getCurrentTextCleaned = () => {
    const textElement = document.getElementById("original_script");
    if (!textElement) return '';
    
    let text = textElement.innerHTML;
    
    // Remove HTML tags
    text = text.replace(/<[^>]*>/g, '');
    text = text.trim();
    text = text.replace(/\s+/g, ' ');
    
    return text;
};

// Função de debug para verificar sincronização
const debugWordTiming = () => {
    const currentText = getCurrentTextCleaned();
    const words = cleanAndSplitText(currentText, AILanguage);
    
    const startTimes = (startTime || '').split(' ').map(t => parseFloat(t)).filter(t => !isNaN(t));
    const endTimes = (endTime || '').split(' ').map(t => parseFloat(t)).filter(t => !isNaN(t));
    
    console.log('=== DEBUG WORD TIMING ===');
    console.log('Texto atual:', currentText);
    console.log('Palavras limpas:', words);
    console.log('Número de palavras:', words.length);
    console.log('Número de tempos início:', startTimes.length);
    console.log('Número de tempos fim:', endTimes.length);
    
    for (let i = 0; i < Math.max(words.length, startTimes.length); i++) {
        const word = words[i] || '(sem palavra)';
        const start = startTimes[i] || 'N/A';
        const end = endTimes[i] || 'N/A';
        const duration = (startTimes[i] && endTimes[i]) ? (endTimes[i] - startTimes[i]).toFixed(3) : 'N/A';
        
        console.log(`${i}: "${word}" | ${start}s - ${end}s (${duration}s)`);
    }
    console.log('========================');
};

// Adicionar função de debug ao objeto global para fácil acesso
window.debugWordTiming = debugWordTiming;



// ############# Utils #####################
const convertBlobToBase64 = async (blob) => {
    return await blobToBase64(blob);
}

const blobToBase64 = blob => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(blob);
    reader.onload = () => resolve(reader.result);
    reader.onerror = error => reject(error);
});

const wrapWordForPlayingLink = (word, word_idx, isFromRecording, word_accuracy_color) => {
    if (isFromRecording)
        return '<a style = " white-space:nowrap; color:' + word_accuracy_color + '; " href="javascript:playRecordedWord(' + word_idx.toString() + ')"  >' + word + '</a> '
    else
        return '<a style = " white-space:nowrap; color:' + word_accuracy_color + '; " href="javascript:playCurrentWord(' + word_idx.toString() + ')" >' + word + '</a> '
}

const wrapWordForIndividualPlayback = (word, word_idx) => {
    // Adicionamos uma classe 'word-link' para identificar as palavras clicáveis
    return `<a class="word-link" style="white-space:nowrap;" href="javascript:void(0)" onclick="showWordPopup(${word_idx}, this)">${word}</a> `;
}

// ########## Function to initialize server ###############
// This is to try to avoid aws lambda cold start 
try {
    fetch(apiMainPathSTS + '/GetAccuracyFromRecordedAudio', {
        method: "post",
        body: JSON.stringify({ "title": '', "base64Audio": '', "language": AILanguage }),
        headers: { "X-Api-Key": STScoreAPIKey }

    });
}
catch { }

const initializeServer = async () => {

    valid_response = false;
    document.getElementById("main_title").innerHTML = 'Initializing server, this may take up to 2 minutes...';
    let number_of_tries = 0;
    let maximum_number_of_tries = 4;

    while (!valid_response) {
        if (number_of_tries > maximum_number_of_tries) {
            serverWorking = false;
            break;
        }

        try {
            await fetch(apiMainPathSTS + '/GetAccuracyFromRecordedAudio', {
                method: "post",
                body: JSON.stringify({ "title": '', "base64Audio": '', "language": AILanguage }),
                headers: { "X-Api-Key": STScoreAPIKey }

            }).then(
                valid_response = true);
            serverIsInitialized = true;
        }
        catch
        {
            number_of_tries += 1;
        }
    }
}

// ########## Utility function to get current text ###############

const getCurrentText = () => {
    // Get current text from the editable element
    const textElement = document.getElementById("original_script");
    let text = textElement.innerHTML;
    
    // Remove HTML tags and clean up text
    text = text.replace(/<[^>]*>?/gm, '');
    text = text.trim();
    text = text.replace(/\s\s+/g, ' ');
    
    return text;
};

// ########## Real-time IPA conversion functions ###############

const convertTextToIPA = async (text, language) => {
    try {
        const response = await fetch('/convertToIPA', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: text,
                language: language
            })
        });
        
        const data = await response.json();
        return data.ipa || '';
    } catch (error) {
        console.error('Error converting text to IPA:', error);
        return '';
    }
};

const convertIPAToPortuguese = async (ipa, language) => {
    try {
        const response = await fetch('/convertToPortuguese', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ipa: ipa,
                language: language
            })
        });
        
        const data = await response.json();
        return data.portuguese || '';
    } catch (error) {
        console.error('Error converting IPA to Portuguese:', error);
        return '';
    }
};

const generatePortugueseForGeneratedSentence = async (ipa) => {
    try {
        // Only generate for French and English
        if (AILanguage === 'fr' || AILanguage === 'en') {
            const portuguese = await convertIPAToPortuguese(ipa, AILanguage);
            const portugueseElement = document.getElementById("portuguese_script");
            
            if (portuguese) {
                portugueseElement.innerHTML = "🇧🇷 " + portuguese;
            } else {
                portugueseElement.innerHTML = "";
            }
        } else {
            // Clear for other languages
            document.getElementById("portuguese_script").innerHTML = "";
        }
    } catch (error) {
        console.error('Error generating Portuguese for generated sentence:', error);
        document.getElementById("portuguese_script").innerHTML = "";
    }
};

const updateIPADisplay = async (text) => {
    if (isConvertingIPA) return;
    
    isConvertingIPA = true;
    
    try {
        const ipa = await convertTextToIPA(text, AILanguage);
        const ipaElement = document.getElementById("ipa_script");
        const portugueseElement = document.getElementById("portuguese_script");
        
        if (ipa) {
            ipaElement.innerHTML = "/ " + ipa + " /";
            
            // Convert IPA to Portuguese approximation (only for French and English)
            if (AILanguage === 'fr' || AILanguage === 'en') {
                const portuguese = await convertIPAToPortuguese(ipa, AILanguage);
                if (portuguese) {
                    portugueseElement.innerHTML = "🇧🇷 " + portuguese;
                } else {
                    portugueseElement.innerHTML = "";
                }
            } else {
                portugueseElement.innerHTML = "";
            }
        } else {
            ipaElement.innerHTML = "";
            portugueseElement.innerHTML = "";
        }
    } catch (error) {
        console.error('Error updating IPA display:', error);
    } finally {
        isConvertingIPA = false;
    }
};

const handleTextChange = () => {
    // Clear existing timeout
    if (ipaConversionTimeout) {
        clearTimeout(ipaConversionTimeout);
    }
    
    // Get current text from the editable element
    const textElement = document.getElementById("original_script");
    let text = textElement.innerHTML;
    
    // Remove HTML tags and clean up text
    text = text.replace(/<[^>]*>?/gm, '');
    text = text.trim();
    text = text.replace(/\s\s+/g, ' ');
    
    // Set new timeout for debounced IPA conversion
    ipaConversionTimeout = setTimeout(() => {
        if (text.length > 0) {
            updateIPADisplay(text);
        } else {
            document.getElementById("ipa_script").innerHTML = "";
            document.getElementById("portuguese_script").innerHTML = "";
        }
    }, IPA_DEBOUNCE_DELAY);
};

const initializeRealTimeIPA = () => {
    const textElement = document.getElementById("original_script");
    
    if (textElement) {
        // Add event listeners for real-time text changes
        textElement.addEventListener('input', handleTextChange);
        textElement.addEventListener('paste', () => {
            // Small delay to allow paste content to be processed
            setTimeout(handleTextChange, 10);
        });
        textElement.addEventListener('keyup', handleTextChange);
    }
};

// Initialize real-time IPA when page loads
document.addEventListener('DOMContentLoaded', initializeRealTimeIPA);

// Also initialize when the page is ready (fallback)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeRealTimeIPA);
} else {
    initializeRealTimeIPA();
}

/**
 * Fecha o pop-up ativo se o usuário clicar fora dele.
 */
document.addEventListener('click', function (event) {
    // Verifica se o pop-up existe e se o clique foi fora dele e não em uma palavra
    if (currentTooltip && !currentTooltip.contains(event.target) && !event.target.classList.contains('word-link')) {
        currentTooltip.remove();
        currentTooltip = null;
    }
}, true);


/**
 * Cria e exibe um pop-up flutuante E ATUALIZA O PAINEL FIXO.
 * @param {number} word_idx - O índice da palavra clicada.
 * @param {HTMLElement} element - O elemento <a> da palavra que foi clicado.
 */
const showWordPopup = (word_idx, element) => {
    generateWordModal(word_idx); // <-- ADICIONE ESTA LINHA AQUI

    event.stopPropagation(); // Impede que o clique feche o pop-up imediatamente

    // Fecha qualquer pop-up que já esteja aberto
    if (currentTooltip) {
        currentTooltip.remove();
    }
    
    // Verifica se temos os dados da análise para trabalhar
    if (!lastAnalysisData) {
        console.error("Dados da análise não encontrados.");
        return;
    }

    // O resto da função continua exatamente como está...
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';

    // Pega os dados específicos da palavra usando o índice
    const ref_word = (lastAnalysisData.real_words || '').split(' ')[word_idx];
    const user_word = (lastAnalysisData.mapped_words || '').split(' ')[word_idx];
    const ref_ipa = (lastAnalysisData.real_transcripts_ipa || '').split(' ')[word_idx];
    const user_ipa = (lastAnalysisData.matched_transcripts_ipa || '').split(' ')[word_idx];

    // Monta o conteúdo do pop-up
    tooltip.innerHTML = `
        <div class="tooltip-section">
            <span style="font-weight: bold;">Referência:</span>
            <span>${ref_word} [${ref_ipa}]</span>
            <a href="javascript:playCurrentWord(${word_idx})" class="tooltip-play-button">▶️ Ouvir</a>
        </div>
        <hr>
        <div class="tooltip-section">
            <span style="font-weight: bold;">Sua Pronúncia:</span>
            <span>${user_word} [${user_ipa}]</span>
            <a href="javascript:playRecordedWord(${word_idx})" class="tooltip-play-button">▶️ Ouvir</a>
        </div>
    `;

    document.body.appendChild(tooltip);

    // Posiciona o pop-up acima da palavra
    const spanRect = element.getBoundingClientRect();
    tooltip.style.left = `${spanRect.left + window.scrollX}px`;
    tooltip.style.top = `${spanRect.top + window.scrollY - tooltip.offsetHeight - 10}px`; // 10px de espaço

    // Armazena a referência do pop-up atual
    currentTooltip = tooltip;
}

