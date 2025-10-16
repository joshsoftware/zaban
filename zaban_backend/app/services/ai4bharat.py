import os
import httpx
from typing import Optional, Dict, Any


class Ai4BharatClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("AI4B_API_KEY")
        self.tts_url = os.getenv("AI4B_TTS_URL")
        self.stt_url = os.getenv("AI4B_STT_URL")
        self.open_speech_url = os.getenv("AI4B_OPEN_SPEECH_URL")
        self.translate_url = os.getenv("AI4B_TRANSLATE_URL")
        self.transliterate_url = os.getenv("AI4B_TRANSLITERATE_URL")

    def _headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if extra:
            headers.update(extra)
        return headers

    async def tts(self, text: str, lang: str, speaker: Optional[str] = None, sample_rate: Optional[int] = None, fmt: Optional[str] = "wav") -> Any:
        if not self.tts_url:
            raise ValueError("AI4B_TTS_URL not configured")
        payload = {"text": text, "lang": lang, "format": fmt}
        if speaker:
            payload["speaker"] = speaker
        if sample_rate:
            payload["sample_rate"] = sample_rate
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(self.tts_url, json=payload, headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    async def stt_file(self, audio, lang: str, fmt: Optional[str] = None) -> Any:
        if not self.stt_url:
            raise ValueError("AI4B_STT_URL not configured")
        form = {"lang": (None, lang)}
        if fmt:
            form["format"] = (None, fmt)
        file_bytes = await audio.read()
        form["audio"] = (audio.filename, file_bytes, audio.content_type or "application/octet-stream")
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(self.stt_url, files=form, headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    async def stt_url(self, audio_url: str, lang: str, fmt: Optional[str] = None) -> Any:
        url = self.open_speech_url or self.stt_url
        if not url:
            raise ValueError("AI4B_OPEN_SPEECH_URL/AI4B_STT_URL not configured")
        payload = {"audio_url": audio_url, "lang": lang}
        if fmt:
            payload["format"] = fmt
        headers = {}
        open_speech_key = os.getenv("AI4B_OPEN_SPEECH_API_KEY")
        if open_speech_key:
            headers["x-api-key"] = open_speech_key
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, json=payload, headers=self._headers(headers))
            resp.raise_for_status()
            return resp.json()

    async def translate(self, text: str, source_lang: str, target_lang: str, domain: Optional[str] = None) -> Any:
        if not self.translate_url:
            raise ValueError("AI4B_TRANSLATE_URL not configured")
        payload = {"text": text, "source_lang": source_lang, "target_lang": target_lang}
        if domain:
            payload["domain"] = domain
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(self.translate_url, json=payload, headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    async def transliterate(self, text: str, source_script: str, target_script: str, lang: str, topk: int = 1) -> Any:
        if not self.transliterate_url:
            raise ValueError("AI4B_TRANSLITERATE_URL not configured")
        payload = {
            "text": text,
            "source_script": source_script,
            "target_script": target_script,
            "lang": lang,
            "topk": topk,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(self.transliterate_url, json=payload, headers=self._headers())
            resp.raise_for_status()
            return resp.json()


