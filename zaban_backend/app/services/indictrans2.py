import os
import torch
from typing import List, Optional
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from IndicTransToolkit import IndicProcessor


class IndicTrans2Service:
    """
    Service for IndicTrans2 translation model.
    Supports both En->Indic and Indic->En translations for 22 Indian languages.
    
    Language codes (BCP-47 format with script):
    - English: eng_Latn
    - Hindi: hin_Deva
    - Bengali: ben_Beng
    - Telugu: tel_Telu
    - Tamil: tam_Taml
    - Gujarati: guj_Gujr
    - Kannada: kan_Knda
    - Malayalam: mal_Mlym
    - Marathi: mar_Deva
    - Punjabi: pan_Guru
    - Oriya: ory_Orya
    - Assamese: asm_Beng
    ... (22 languages total)
    """
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.en_indic_model = None
        self.indic_en_model = None
        self.en_indic_tokenizer = None
        self.indic_en_tokenizer = None
        self.processor = None
        self.model_loaded = False
        
        # Check if auto-load is enabled
        if os.getenv("INDICTRANS2_AUTO_LOAD", "false").lower() == "true":
            self.load_models()
    
    def load_models(self):
        """Load IndicTrans2 models (lazy loading)"""
        if self.model_loaded:
            return
        
        print("Loading IndicTrans2 models... This may take a few minutes on first run.")
        
        # Load En->Indic model (200M distilled version for faster inference)
        en_indic_name = os.getenv("INDICTRANS2_EN_INDIC_MODEL", "ai4bharat/indictrans2-en-indic-dist-200M")
        self.en_indic_tokenizer = AutoTokenizer.from_pretrained(en_indic_name, trust_remote_code=True)
        self.en_indic_model = AutoModelForSeq2SeqLM.from_pretrained(
            en_indic_name, 
            trust_remote_code=True
        ).to(self.device)
        
        # Load Indic->En model
        indic_en_name = os.getenv("INDICTRANS2_INDIC_EN_MODEL", "ai4bharat/indictrans2-indic-en-dist-200M")
        self.indic_en_tokenizer = AutoTokenizer.from_pretrained(indic_en_name, trust_remote_code=True)
        self.indic_en_model = AutoModelForSeq2SeqLM.from_pretrained(
            indic_en_name,
            trust_remote_code=True
        ).to(self.device)
        
        # Initialize processor
        self.processor = IndicProcessor(inference=True)
        
        self.model_loaded = True
        print(f"IndicTrans2 models loaded successfully on {self.device}")
    
    async def translate(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str,
        batch_size: int = 4
    ) -> str:
        """
        Translate text from source language to target language.
        
        Args:
            text: Input text to translate
            source_lang: Source language code (e.g., 'eng_Latn', 'hin_Deva')
            target_lang: Target language code
            batch_size: Batch size for inference
            
        Returns:
            Translated text
        """
        if not self.model_loaded:
            self.load_models()
        
        # Determine which model to use
        is_en_to_indic = source_lang == "eng_Latn"
        
        model = self.en_indic_model if is_en_to_indic else self.indic_en_model
        tokenizer = self.en_indic_tokenizer if is_en_to_indic else self.indic_en_tokenizer
        
        # Preprocess
        sentences = [text]
        batch = self.processor.preprocess_batch(
            sentences, 
            src_lang=source_lang, 
            tgt_lang=target_lang,
            visualize=False
        )
        
        # Tokenize
        inputs = tokenizer(
            batch,
            truncation=True,
            padding="longest",
            max_length=256,
            return_tensors="pt"
        ).to(self.device)
        
        # Generate translation
        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                num_beams=5,
                num_return_sequences=1,
                max_length=256,
                use_cache=False  # Disable cache to avoid past_key_values issue
            )
        
        # Decode
        translations = tokenizer.batch_decode(
            outputs, 
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True
        )
        
        # Postprocess
        translations = self.processor.postprocess_batch(translations, lang=target_lang)
        
        return translations[0] if translations else ""
    
    async def translate_batch(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str,
        batch_size: int = 4
    ) -> List[str]:
        """
        Translate multiple texts in batch.
        
        Args:
            texts: List of input texts
            source_lang: Source language code
            target_lang: Target language code
            batch_size: Batch size for inference
            
        Returns:
            List of translated texts
        """
        if not self.model_loaded:
            self.load_models()
        
        is_en_to_indic = source_lang == "eng_Latn"
        model = self.en_indic_model if is_en_to_indic else self.indic_en_model
        tokenizer = self.en_indic_tokenizer if is_en_to_indic else self.indic_en_tokenizer
        
        # Preprocess
        batch = self.processor.preprocess_batch(
            texts,
            src_lang=source_lang,
            tgt_lang=target_lang,
            visualize=False
        )
        
        # Tokenize
        inputs = tokenizer(
            batch,
            truncation=True,
            padding="longest",
            max_length=256,
            return_tensors="pt"
        ).to(self.device)
        
        # Generate
        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                num_beams=5,
                num_return_sequences=1,
                max_length=256,
                use_cache=False  # Disable cache to avoid past_key_values issue
            )
        
        # Decode
        translations = tokenizer.batch_decode(
            outputs,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True
        )
        
        # Postprocess
        translations = self.processor.postprocess_batch(translations, lang=target_lang)
        
        return translations


# Singleton instance
_indictrans2_service = None


def get_indictrans2_service() -> IndicTrans2Service:
    """Get or create the singleton IndicTrans2 service instance"""
    global _indictrans2_service
    if _indictrans2_service is None:
        _indictrans2_service = IndicTrans2Service()
    return _indictrans2_service

