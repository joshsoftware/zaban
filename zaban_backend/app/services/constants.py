"""
Constants for STT services.
"""

# Mapping from Whisper language codes to BCP-47 format.
# Whisper often confuses Hindi (hi) and Marathi (mr); pass lang when known.
WHISPER_TO_BCP47 = {
    'en': 'eng_Latn',
    'hi': 'hin_Deva',
    'bn': 'ben_Beng',
    'ta': 'tam_Taml',
    'te': 'tel_Telu',
    'gu': 'guj_Gujr',
    'kn': 'kan_Knda',
    'ml': 'mal_Mlym',
    'mr': 'mar_Deva',
    'pa': 'pan_Guru',
    'or': 'ory_Orya',
    'as': 'asm_Beng',
    'ur': 'urd_Arab',
    'ne': 'nep_Deva',
    'si': 'sin_Sinh',
}

# Default prompt for Whisper translation task to bias toward translation (not transliteration).
# IMPORTANT: Whisper uses prompts for style/vocabulary biasing, NOT instructions.
# The prompt must be example transcriptions showing the desired style, not instruction text.
# Whisper will follow the STYLE of the prompt text. Max ~224 tokens.
# Proper nouns may still be transliterated - this is a Whisper limitation.
DEFAULT_TRANSLATE_PROMPT = (
    "Only Indian langues,like, hindi, marthi,tamil,gujarti,telegu,bengali,panjabi,bengali,malayalam,kannada or Indian english voice. "
    "Do not translitarate, translate to English words, do not mix other language words"
)

# Whisper translation quality parameters (beam search)
WHISPER_BEAM_SIZE = 5
WHISPER_BEST_OF = 5

# Audio format detection configuration
# Format: (extension, magic_bytes_at_start, optional_check_bytes, check_offset)
AUDIO_FORMAT_CONFIG = {
    "wav": {
        "extension": ".wav",
        "magic": b"RIFF",
        "check": b"WAVE",
        "check_offset": 8,
    },
    "flac": {
        "extension": ".flac",
        "magic": b"fLaC",
        "check": None,
        "check_offset": None,
    },
    "mp3": {
        "extension": ".mp3",
        "magic": b"ID3",  # ID3 tag
        "alt_magic": b"\xff\xfb",  # MPEG header (alternative)
        "check": None,
        "check_offset": None,
    },
    "webm": {
        "extension": ".webm",
        "magic": b"\x1a\x45\xdf\xa3",  # EBML header
        "check": None,
        "check_offset": None,
    },
}

# Default audio suffix
DEFAULT_AUDIO_SUFFIX = ".wav"

# Audio format names (keys for AUDIO_FORMAT_CONFIG)
WAV_FORMAT_NAME = "wav"
FLAC_FORMAT_NAME = "flac"
MP3_FORMAT_NAME = "mp3"
WEBM_FORMAT_NAME = "webm"