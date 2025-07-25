import epitran
import unicodedata
from FrenchSpecialRoules import *
import logging
# Inicializar Epitran para Francês
epi = epitran.Epitran('fra-Latn-p')
import json


# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Carregar o dic.json
with open('dic.json', 'r', encoding='utf-8') as f:
    ipa_dictionary = json.load(f)

# Mapeamento de fonemas francês para português com regras contextuais aprimoradas
# Cada entrada deve ser um dicionário com, no mínimo, a chave 'default'.
# Se houver contextos adicionais (ex.: 'before_front_vowel', 'word_initial', etc.),
# mantenha também o 'default' para evitar KeyError.

french_to_portuguese_phonemes = {
    # VOGAIS ORAIS
    'i': { 'default': 'i' },
    'e': { 'default': 'e' },
    'ɛ': { 'default': 'é' },
    'a': { 'default': 'a' },
    'ɑ': { 'default': 'a' },    # se não quiser “á” aberto
    'ɔ': { 'default': 'ó' },
    'o': { 'default': 'ô' },
    'u': { 'default': 'u' },
    'y': { 'default': 'u' },
    'ø': { 'default': 'eu' },   # ou 'ô', se preferir "vou" ~ "vô"
    'œ': { 'default': 'eu' },   # ou 'é'
    'ə': { 'default': 'e'  },   # TROCA IMPORTANTE: schwa -> “e”

    # VOGAIS NASAIS
    'ɛ̃': { 'default': 'ẽ' },
    'ɑ̃': { 'default': 'ã' },
    'ɔ̃': { 'default': 'õ' },
    'œ̃': { 'default': 'ũ' },
    'ð':  { 'default': 'd'  },

    # SEMIVOGAIS
    'w': { 'default': 'u' },
    'ɥ': { 'default': 'u', 'after_vowel': 'w' },

    # CONSOANTES
    'b':  { 'default': 'b' },
    'd':  { 'default': 'd', 'before_i': 'dj' },
    'f':  { 'default': 'f' },
    'g':  { 'default': 'g', 'before_front_vowel': 'j' },
    'ʒ':  { 'default': 'j' },
    'k':  { 'default': 'k', 'before_front_vowel': 'qu' },
    'l':  { 'default': 'l' },
    'm':  { 'default': 'm' },
    'n':  { 'default': 'n' },
    'p':  { 'default': 'p' },
    # REMOVE o "rr" e "h" aqui:
    'ʁ':  { 'default': 'r' }, 
    's':  { 
        'default': 's',
        'between_vowels': 'z',
        'word_final': 's'
    },
    't':  { 'default': 't', 'before_i': 'tch' },
    'v':  { 'default': 'v' },
    'z':  { 'default': 'z' },
    'ʃ':  { 'default': 'ch' },
    'dʒ': { 'default': 'dj' },
    'tʃ': { 'default': 'tch' },
    'ɲ':  { 'default': 'nh' },
    'ŋ':  { 'default': 'ng' },
    'ç':  { 'default': 's' },
    'ʎ':  { 'default': 'lh' },
    'ʔ':  { 'default': '' },
    'θ':  { 'default': 't' },
    'ɾ':  { 'default': 'r' },
    'ʕ':  { 'default': 'r' },

    # FONEMAS COMPOSTOS
    'sj': { 'default': 'si' },  
    'ks': { 'default': 'x' },
    'gz': { 'default': 'gz' },
    'x':  { 'default': 'x' },
    'ʃj': { 'default': 'chi' },
    'ʒʁ':{ 'default': 'jr' },

    # H aspirado ou mudo
    'h':  {
        'default': '',
        'aspirated': 'h',
        'mute': ''
    },

    # Consoantes duplas
    'kk': { 'default': 'c' },
    'tt': { 'default': 't' },
    'pp': { 'default': 'p' },
    'bb': { 'default': 'b' },
    'gg': { 'default': 'g' },

    # Finais
    'k$': { 'default': 'c' },
    'g$': { 'default': 'g' },
    'p$': { 'default': 'p' },
    't$': { 'default': 't' },

    # Outros
    'ɡə': { 'default': 'gue' },
    'ɡi': { 'default': 'gi' },
    'ʧ': { 'default': 'tch' },
    'ʤ': { 'default': 'dj' },
    'ty': { 'default': 'tu' },
}

# Características fonéticas

# Lista de palavras com 'h' aspirado
h_aspirate_words = [
    "hache", "hagard", "haie", "haillon", "haine", "haïr", "hall", "halo", "halte", "hamac",
    "hamburger", "hameau", "hamster", "hanche", "handicap", "hangar", "hanter", "happer",
    "harceler", "hardi", "harem", "hareng", "harfang", "hargne", "haricot", "harnais", "harpe",
    "hasard", "hâte", "hausse", "haut", "havre", "hennir", "hérisser", "hernie", "héron",
    "héros", "hêtre", "heurter", "hibou", "hic", "hideur", "hiérarchie", "hiéroglyphe", "hippie",
    "hisser", "hocher", "hockey", "hollande", "homard", "honte", "hoquet", "horde", "hors",
    "hotte", "houblon", "houle", "housse", "huard", "hublot", "huche", "huer", "huit", "humer",
    "hurler", "huron", "husky", "hutte", "hyène"
]

#--------------------------------------------------------------------------------------------------

# Funções de pronúncia e transcrição --------------------------------------------------------------------------------------------------
# 
def get_pronunciation(word):
    word_normalized = word.lower()
    # Tratar casos especiais para artigos definidos e pronomes tonicos
    if word_normalized == 'le':
        return 'luh'
    elif word_normalized == 'la':
        return 'lá'
    elif word_normalized == 'les':
        return 'lê'
    elif word_normalized== 'moi':
        return 'mwa'
    elif word_normalized== 'toi':
        return 'twa'
    elif word_normalized== 'lui':
        return 'lui'
    elif word_normalized== 'elle':
        return 'él'
    elif word_normalized== 'nous':
        return 'nu'
    elif word_normalized== 'vous':
        return 'vu'
    elif word_normalized== 'eux':
        return 'ø'
    elif word_normalized== 'elles':
        return 'él'
    elif word_normalized=='une':
        return  'úne'
    elif word_normalized=='un':
        return  'ãn'
    elif word_normalized=="Il est":
        return 'il ét'
    elif word_normalized=="c'est":
        return 'se'
    else:
        try:
            # Tentar obter a pronúncia do dic.json
            pronunciation = ipa_dictionary.get(word_normalized)
            if pronunciation:
                return pronunciation
            else:
                # Se não encontrado, usar Epitran como fallback
                pronunciation = epi.transliterate(word)
                return pronunciation
        except Exception as e:
            logger.error(f"Erro ao obter pronúncia para '{word}': {e}")
            return word  # Retorna a palavra original como fallback


def remove_silent_endings(pronunciation, word):
    # Verificar se a palavra termina com 'ent' e a pronúncia termina com 't'
    if word.endswith('ent') and pronunciation.endswith('t'):
        pronunciation = pronunciation[:-1]
    # Adicionar outras regras conforme necessário
    return pronunciation


# Ajustar listas conforme sua necessidade
vogais_orais = ['a', 'e', 'i', 'o', 'u', 'é', 'ê', 'í', 'ó', 'ô', 'ú', 'ø', 'œ', 'ə']
vogais_nasais = ['ã', 'ẽ', 'ĩ', 'õ', 'ũ']
semivogais = ['j', 'w', 'ɥ']
grupos_consonantais_especiais = ['tch', 'dj', 'sj', 'dʒ', 'ks']
consoantes_base = [
    'b','d','f','g','k','l','m','n','p','ʁ','r','s','t','v','z','ʃ','ʒ','ɲ','ŋ','ç'
]

excecoes_semivogais = {
    # Exemplos de exceções: padrão -> substituição
    # Caso queira ajustar manualmente certos clusters após a primeira passagem.
    # Por exemplo, se "sós.jó" sempre deveria ficar "sósjó"
    ("sós","jó"): ["sósjó"],
    ("próm","uv"): ["pró","muv"],  # exemplo hipotético
}

def e_vogal(c):
    return (c in vogais_orais) or (c in vogais_nasais)

def e_vogal_nasal(c):
    return c in vogais_nasais

def e_semivogal(c):
    return c in semivogais

def e_consoante(c):
    return c in consoantes_base

def e_grupo_consonantal(seq):
    return seq in grupos_consonantais_especiais

def tokenizar_palavra(palavra):
    i = 0
    tokens = []
    while i < len(palavra):
        matched = False
        for gc in grupos_consonantais_especiais:
            length = len(gc)
            if palavra[i:i+length] == gc:
                tokens.append(gc)
                i += length
                matched = True
                break
        if not matched:
            tokens.append(palavra[i])
            i += 1
    return tokens

def ajustar_semivogais(silabas):
    # Primeiro, mover semivogais do final da sílaba se a próxima inicia com vogal
    novas_silabas = []
    i = 0
    while i < len(silabas):
        s = silabas[i]
        if i < len(silabas)-1:
            ultima_letra = s[-1]
            proxima_silaba = silabas[i+1]
            if ultima_letra in semivogais and e_vogal(proxima_silaba[0]):
                # Move a semivogal para a próxima sílaba
                s = s[:-1]
                proxima_silaba = ultima_letra + proxima_silaba
                novas_silabas.append(s)
                silabas[i+1] = proxima_silaba
            else:
                novas_silabas.append(s)
        else:
            # Última sílaba, apenas adiciona
            novas_silabas.append(s)
        i += 1

    silabas = novas_silabas

    # Agora, tentar mesclar semivogais do início de uma sílaba anterior se a anterior terminou em vogal
    # Exemplo: se anterior terminar em vogal e a atual começar com semivogal + vogal, podemos unir.
    # Cuidado para não bagunçar a lógica já aplicada. Faça testes com frases reais.
    novas_silabas = []
    i = 0
    while i < len(silabas):
        if i > 0:
            # Verifica se a sílaba atual começa com semivogal e a anterior termina em vogal
            si = silabas[i]
            anterior = novas_silabas[-1]
            if si and e_semivogal(si[0]) and e_vogal(anterior[-1]):
                # Une a semivogal com a sílaba anterior
                novas_silabas[-1] = novas_silabas[-1] + si
            else:
                novas_silabas.append(si)
        else:
            novas_silabas.append(silabas[i])
        i += 1

    silabas = novas_silabas

    # Aplicar exceções específicas de semivogais:
    # Procurar padrões em pares de sílabas e substituir caso encontre
    i = 0
    refinadas = []
    while i < len(silabas):
        if i < len(silabas)-1:
            par = (silabas[i], silabas[i+1])
            if par in excecoes_semivogais:
                # Substituir pelo padrão definido
                refinadas.extend(excecoes_semivogais[par])
                i += 2
                continue
        refinadas.append(silabas[i])
        i += 1

    return refinadas

def silabificar_refinado(palavra):
    tokens = tokenizar_palavra(palavra)
    silabas = []
    silaba_atual = []
    encontrou_vogal = False

    for t in tokens:
        if e_vogal(t):
            if encontrou_vogal and silaba_atual:
                silabas.append(''.join(silaba_atual))
                silaba_atual = [t]
            else:
                silaba_atual.append(t)
                encontrou_vogal = True
        else:
            silaba_atual.append(t)

    if silaba_atual:
        silabas.append(''.join(silaba_atual))

    # Ajustar semivogais após a primeira criação de sílabas
    silabas = ajustar_semivogais(silabas)

    return silabas

def unir_silabas_com_pontos(silabas):
    return '.'.join(silabas)

def aplicar_regras_de_liaison(texto):
    # Adicione aqui quaisquer substituições adicionais finais.
    # Se quiser remover esta função, pode, mas ela pode ser útil
    # caso queira ajustar casos específicos de liaison.
    # Exemplo:
    texto = texto.replace("nu a", "nu.z a")
    return texto

def gerar_versao_usuario(frase_com_pontos):
    # Remove os pontos para o usuário final e reagrupa as palavras
    # Supondo que as palavras já estão separadas por espaços, basta remover os pontos
    palavras = frase_com_pontos.split()
    palavras_sem_pontos = [p.replace('.', '') for p in palavras]
    return ' '.join(palavras_sem_pontos)



def transliterate_and_convert_sentence(sentence):
    words = sentence.split()
    words = handle_apostrophes(words)

    # 1) TRATAMENTO DE "est-ce que"
    words = handle_est_ce_que(words)

    # 2) TRATAMENTO ESPECIAL PARA "plus"
    for i, w in enumerate(words):
        if w.lower() == "plus":
            special_plus = handle_plus_pronunciation(i, words)
            words[i] = special_plus
    
    # 3) TRATAMENTO ESPECIAL PARA "est" (verbo x direção), se quiser
    for i, w in enumerate(words):
        if w.lower() == "est":
            special_est = handle_est_pronunciation(i, words)
            words[i] = special_est

    # 4) Converter cada palavra em pronúncia (Epitran + dicionário)
    pronunciations = [get_pronunciation(word) for word in words]

    # 5) Liaisons, removendo finais mudos, etc.
    pronunciations = apply_liaisons(words, pronunciations)
    pronunciations = [remove_silent_endings(pron, word)
                      for pron, word in zip(pronunciations, words)]

    # 6) Converte fonemas para "pt-BR"
    palavras_convertidas = [
        convert_pronunciation_to_portuguese(pron, idx, pronunciations)
        for idx, pron in enumerate(pronunciations)
    ]

    # 7) Silabifica e une com pontos
    palavras_silabificadas = []
    for p in palavras_convertidas:
        silabas = silabificar_refinado(p)
        palavras_silabificadas.append(unir_silabas_com_pontos(silabas))

    frase_com_pontos = ' '.join(palavras_silabificadas)
    frase_com_pontos = aplicar_regras_de_liaison(frase_com_pontos)

    # 8) Gerar versão amigável para usuário (remover pontos)
    frase_usuario = gerar_versao_usuario(frase_com_pontos)

    return frase_usuario




  

def split_into_phonemes(pronunciation):
    phonemes = []
    idx = 0
    while idx < len(pronunciation):
        matched = False
        # Lista de fonemas ordenada para priorizar fonemas individuais
        phoneme_list = [
            # Fonemas individuais
            'a', 'e', 'i', 'o', 'u', 'y', 'ɛ', 'ɔ', 'ɑ', 'ø', 'œ', 'ə',
            'ɛ̃', 'ɑ̃', 'ɔ̃', 'œ̃',
            'j', 'w', 'ɥ',
            'b', 'd', 'f', 'g', 'k', 'l', 'm', 'n', 'p', 'ʁ', 's', 't',
            'v', 'z', 'ʃ', 'ʒ', 'ɲ', 'ŋ', 'ç',
            # Fonemas compostos (depois)
            'dʒ', 'tʃ', 'ks', 'sj', 'ʎ', 'ʔ', 'θ', 'ð', 'ɾ', 'ʕ'
        ]
        for phoneme in phoneme_list:
            length = len(phoneme)
            if pronunciation[idx:idx+length] == phoneme:
                phonemes.append(phoneme)
                idx += length
                matched = True
                break
        if not matched:
            phonemes.append(pronunciation[idx])
            logger.warning(f"Fonema não mapeado: '{pronunciation[idx]}' na pronúncia '{pronunciation}'")
            idx += 1
    return phonemes


def convert_pronunciation_to_portuguese(pronunciation, word_idx, all_pronunciations):
    phonemes = split_into_phonemes(pronunciation)
    result = []
    idx = 0
    length = len(phonemes)
    word_start = idx == 0
    while idx < length:
        phoneme = phonemes[idx]
        mapping = french_to_portuguese_phonemes.get(phoneme, {'default': phoneme})
        context = 'default'

        next_phoneme = phonemes[idx + 1] if idx + 1 < length else ''
        prev_phoneme = phonemes[idx - 1] if idx > 0 else ''

        # Definir listas de vogais
        vowels = ['a', 'e', 'i', 'o', 'u', 'ɛ', 'ɔ', 'ɑ', 'ø', 'œ', 'ə']
        front_vowels = ['i', 'e', 'ɛ', 'ɛ̃', 'œ', 'ø', 'y']

        next_is_i = next_phoneme == 'i'
        prev_is_vowel = prev_phoneme in vowels
        next_is_vowel = next_phoneme in vowels
        next_is_front_vowel = next_phoneme in front_vowels

        # Definir o contexto
        if phoneme == 'd' and next_is_i:
            context = 'before_i'
        elif phoneme == 't' and next_is_i:
            context = 'before_i'
        elif phoneme == 'k' and next_is_front_vowel:
            context = 'before_front_vowel'
        elif phoneme == 'ʁ':
            if word_start:
                context = 'word_initial'
            elif prev_is_vowel:
                context = 'after_vowel'
            else:
                context = 'after_consonant'
        elif phoneme == 's' and prev_is_vowel and next_is_vowel:
            context = 'between_vowels'
        elif phoneme == 'ʒ' and phonemes[idx - 1] in ['ɛ̃', 'ɑ̃', 'ɔ̃', 'œ̃']:
            context = 'after_nasal'

        # Obter o mapeamento
        mapped_phoneme = mapping.get(context, mapping['default'])
        result.append(mapped_phoneme)
        idx += 1
        word_start = False  # Apenas a primeira iteração é o início da palavra

    return ''.join(result)

def handle_apostrophes(words_list):
    new_words = []
    for word in words_list:
        if "'" in word:
            prefix, sep, suffix = word.partition("'")
            # Contrações comuns
            if prefix.lower() in ["l", "d", "j", "qu", "n", "m", "c"]:
                combined_word = prefix + suffix
                new_words.append(combined_word)
            else:
                new_words.append(word)
        else:
            new_words.append(word)
    return new_words

def apply_liaisons(words_list, pronunciations):
    nasal_words = {'un','mon','ton','son','en'}
    new_pronunciations = []
    for i in range(len(words_list) - 1):
        current_word = words_list[i]
        next_word = words_list[i + 1]
        current_pron = pronunciations[i]

        # Verificar se a próxima palavra começa com "h" aspirado
        next_word_clean = re.sub(r"[^a-zA-Z']", '', next_word).lower()
        h_aspirate = next_word_clean in h_aspirate_words

        # Verificar se a próxima palavra começa com vogal ou 'h' mudo
        if re.match(r"^[aeiouyâêîôûéèëïüÿæœ]", next_word, re.IGNORECASE) and not h_aspirate:
            # --- REGRAS DE LIAISON EXISTENTES ---
            if current_word.lower() == "les":
                current_pron = current_pron.rstrip('e') + 'z'
            elif current_word[-1] in ['s', 'x', 'z']:
                current_pron = current_pron + 'z'
            elif current_word[-1] == 'd':
                current_pron = current_pron + 't'
            elif current_word[-1] == 'g':
                current_pron = current_pron + 'k'
            elif current_word[-1] == 't':
                current_pron = current_pron + 't'
            elif current_word[-1] == 'n':
                current_pron = current_pron + 'n'
            elif current_word[-1] == 'p':
                current_pron = current_pron + 'p'
            elif current_word[-1] == 'r':
                current_pron = current_pron + 'r'
            elif current_word.lower() == "d'" and re.match(r"^[aeiouyâêîôûéèëïüÿæœ]", next_word, re.IGNORECASE):
                current_pron = current_pron.rstrip('e') + 'z'
            
            # --- REGRAS ESPECIAIS PARA "un" ---
            # Se a palavra for "un" E a próxima inicia por vogal (ou h mudo),
            # a nasal final ("ã" ou "ẽ") volta a ter som de "n" => "ãn" / "ẽn"
            if current_word.lower() == 'un':
                # Supondo que 'un' foi transliterado como "ẽ" ou "œ̃":
                # Exemplo: se get_pronunciation("un") => "œ̃", que mapeia p/ "ãn" ou "ẽ"
                # Precisamos reintroduzir o /n/.
                # Só se o final for 'ã'/'ẽ' (ou algo nasal). Ajuste se o seu mapeamento for diferente!
                if current_pron.endswith('ã'):
                    # vira "ãn"
                    current_pron = current_pron[:-1] + 'ãn'
                elif current_pron.endswith('ẽ'):
                    # vira "ẽn"
                    current_pron = current_pron[:-1] + 'ẽn'
                elif current_pron.endswith('õ'):
                    # "õn"? raríssimo pra "un", mas se você quiser cobrir "on"...
                    current_pron = current_pron[:-1] + 'õn'
                if current_word.lower() in nasal_words:
                    # reintroduz 'n'
                    if current_pron.endswith('ã'):
                        current_pron = current_pron[:-1] + 'ãn'
    
        new_pronunciations.append(current_pron)
    # Adicionar a última pronúncia (não esqueça)
    new_pronunciations.append(pronunciations[-1])
    return new_pronunciations


def remove_accents(text):
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

def normalize_text(text):
    text = text.lower()
    text = text.replace("’", "'")
    text = remove_accents(text)
    text = re.sub(r"[^\w\s']", '', text)
    text = re.sub(r"\s+'", "'", text)
    text = re.sub(r"'\s+", "'", text)
    return text.strip()


def remove_punctuation_end(sentence):
      return sentence.rstrip('.')