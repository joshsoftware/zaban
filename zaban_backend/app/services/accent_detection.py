import torch
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor
import torchaudio
from typing import Dict


class AccentDetectionService:
    def __init__(self):
        # Using a public model for demonstration. This model is for language ID, not accent, but is public and works for demo/testing.
        self.model_name = "facebook/wav2vec2-large-xlsr-53"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.processor = None
        self.label_map = None

    async def detect_accent(self, audio_file) -> Dict:
        # Lazy-load model and processor
        if self.model is None or self.processor is None or self.label_map is None:
            self.model = Wav2Vec2ForSequenceClassification.from_pretrained(self.model_name).to(self.device)
            self.processor = Wav2Vec2FeatureExtractor.from_pretrained(self.model_name)
            self.label_map = self.model.config.id2label

        # Read audio file
        waveform, sample_rate = await self._read_audio(audio_file)
        # Preprocess
        inputs = self.processor(waveform, sampling_rate=sample_rate, return_tensors="pt", padding=True)
        input_values = inputs.input_values.to(self.device)
        # Inference
        with torch.no_grad():
            logits = self.model(input_values).logits
            probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]
        pred_id = int(probs.argmax())
        accent = self.label_map[pred_id]
        confidence = float(probs[pred_id])
        return {
            "accent": accent,
            "confidence": confidence,
            "details": {"probs": {self.label_map[i]: float(p) for i, p in enumerate(probs)}}
        }

    async def _read_audio(self, audio_file):
        # Read file bytes
        contents = await audio_file.read()
        import io
        waveform, sample_rate = torchaudio.load(io.BytesIO(contents))
        # Convert to mono if needed
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        return waveform.squeeze().numpy(), sample_rate
