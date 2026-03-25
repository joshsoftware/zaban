# app/services/diarization/pipeline.py

import torch
import librosa
from speechbrain.inference import EncoderClassifier
from speechbrain.inference.VAD import VAD


class DiarizationPipeline:
    def __init__(self):
        # Speaker embedding model (ECAPA)
        self.embedding_model = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            run_opts={"device": "cpu"}
        )

        # Voice Activity Detection
        self.vad = VAD.from_hparams(
            source="speechbrain/vad-crdnn-libriparty",
            run_opts={"device": "cpu"}
        )

    def load_audio(self, path):
        waveform, sr = librosa.load(path, sr=16000)
        return torch.tensor(waveform).unsqueeze(0), sr

    def get_speech_segments(self, audio_path):
        """
        Returns speech segments [(start, end)]
        """
        boundaries = self.vad.get_speech_segments(audio_path)
        segments = []

        for seg in boundaries:
            start = float(seg[0])
            end = float(seg[1])
            segments.append((start, end))
        print("VAD output:", boundaries)

        return segments

    def get_embedding(self, waveform):
        """
        Extract speaker embedding
        """
        with torch.no_grad():
            emb = self.embedding_model.encode_batch(waveform)
        return emb.squeeze().numpy()

    def extract_embeddings(self, audio_path, segments):
        waveform, sr = self.load_audio(audio_path)

        embeddings = []

        CHUNK_DURATION = 1.5  # seconds
        STRIDE = 0.75         # overlap

        chunk_size = int(CHUNK_DURATION * sr)
        stride_size = int(STRIDE * sr)

        for start, end in segments:
            duration = end - start
            start_sample = int(start * sr)
            end_sample = int(end * sr)
            segment_wave = waveform[:, start_sample:end_sample]

            if segment_wave.shape[1] == 0:
                continue

            # If segment is shorter than chunk_size, take the whole segment
            if duration < CHUNK_DURATION:
                emb = self.get_embedding(segment_wave)
                embeddings.append({
                    "start": start,
                    "end": end,
                    "embedding": emb
                })
                continue

            # For longer segments, use sliding window
            for i in range(0, segment_wave.shape[1] - chunk_size + 1, stride_size):
                chunk = segment_wave[:, i:i + chunk_size]
                
                emb = self.get_embedding(chunk)
                embeddings.append({
                    "start": start + (i / sr),
                    "end": start + (min(i + chunk_size, segment_wave.shape[1]) / sr),
                    "embedding": emb
                })

        return embeddings