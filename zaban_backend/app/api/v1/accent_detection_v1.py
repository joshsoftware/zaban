"""
Accent Detection API using wav2vec2-large-xlsr-53 (HuggingFace)

This version replaces MFCC-based scikit-learn models with:
 - Pretrained wav2vec2 XLSR-53 for speech embeddings
 - A small PyTorch classifier head for accent prediction

API Endpoints:
  POST /predict — Upload audio file, returns accent probabilities
  GET /health — Health check

Dependencies:
  pip install fastapi uvicorn python-multipart torch torchaudio transformers librosa soundfile numpy

Model files created during training:
  models/xlsr_embedding_head.pt        (PyTorch classifier)
  models/xlsr_label_list.json          (Accent labels)

Run Server:
  uvicorn accent_detection_api:app --host 0.0.0.0 --port 8000
"""

import io
import os
import json
import torch
import librosa
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from transformers import Wav2Vec2Processor, Wav2Vec2Model

# ------------------------------
# CONFIG
# ------------------------------
MODEL_NAME = "facebook/wav2vec2-large-xlsr-53"
MODEL_DIR = "models"
EMBEDDING_HEAD_PATH = f"{MODEL_DIR}/xlsr_embedding_head.pt"
LABEL_LIST_PATH = f"{MODEL_DIR}/xlsr_label_list.json"
SAMPLE_RATE = 16000
MAX_AUDIO_SEC = 10.0

app = FastAPI(title="Indian Accent Detection API — wav2vec2 XLSR-53")

# ------------------------------
# RESPONSE MODEL
# ------------------------------
class PredictionResponse(BaseModel):
    label: str
    scores: dict

# ------------------------------
# LOAD wav2vec2 BASE MODEL
# ------------------------------
print("Loading wav2vec2 XLSR model...")
processor = Wav2Vec2Processor.from_pretrained(MODEL_NAME)
base_model = Wav2Vec2Model.from_pretrained(MODEL_NAME)
base_model.eval()

# ------------------------------
# CLASSIFIER HEAD
# ------------------------------
class AccentClassifier(torch.nn.Module):
    def __init__(self, embedding_dim: int, num_labels: int):
        super().__init__()
        self.classifier = torch.nn.Sequential(
            torch.nn.Linear(embedding_dim, 256),
            torch.nn.ReLU(),
            torch.nn.Linear(256, num_labels)
        )

    def forward(self, x):
        return self.classifier(x)

# load labels
if os.path.exists(LABEL_LIST_PATH):
    with open(LABEL_LIST_PATH, "r") as f:
        LABELS = json.load(f)
else:
    LABELS = []

# load classifier head
if os.path.exists(EMBEDDING_HEAD_PATH) and LABELS:
    EMB_DIM = base_model.config.hidden_size
    classifier_head = AccentClassifier(EMB_DIM, len(LABELS))
    classifier_head.load_state_dict(torch.load(EMBEDDING_HEAD_PATH, map_location="cpu"))
    classifier_head.eval()
    MODEL_READY = True
else:
    classifier_head = None
    MODEL_READY = False

# ------------------------------
# AUDIO LOADING
# ------------------------------
async def load_audio(file: UploadFile) -> np.ndarray:
    data = await file.read()
    if len(data) == 0:
        raise HTTPException(400, "Empty audio file")

    try:
        audio, _ = librosa.load(io.BytesIO(data), sr=SAMPLE_RATE, mono=True)
    except Exception:
        import soundfile as sf
        audio, sr = sf.read(io.BytesIO(data))
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        audio = librosa.resample(audio, orig_sr=sr, target_sr=SAMPLE_RATE)

    max_len = SAMPLE_RATE * MAX_AUDIO_SEC
    if len(audio) > max_len:
        audio = audio[:int(max_len)]

    return audio.astype(np.float32)

# ------------------------------
# EMBEDDING EXTRACTION
# ------------------------------
@torch.inference_mode()
def extract_wav2vec2_embedding(audio: np.ndarray) -> torch.Tensor:
    inputs = processor(audio, sampling_rate=SAMPLE_RATE, return_tensors="pt", padding=True)
    outputs = base_model(**inputs)
    # Take mean over time dimension
    embedding = outputs.last_hidden_state.mean(dim=1)
    return embedding

# ------------------------------
# API ROUTES
# ------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "model_ready": MODEL_READY, "labels": LABELS}

@app.post("/predict", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...)):
    if classifier_head is None or not LABELS:
        raise HTTPException(500, "Model not trained or missing classifier head.")

    audio = await load_audio(file)

    emb = extract_wav2vec2_embedding(audio)
    logits = classifier_head(emb)
    probs = torch.softmax(logits, dim=1)[0].tolist()

    scores = {label: float(prob) for label, prob in zip(LABELS, probs)}
    best_label = max(scores.items(), key=lambda x: x[1])[0]

    return PredictionResponse(label=best_label, scores=scores)

# ------------------------------
# TRAINING SCRIPT (MANUAL RUN)
# ------------------------------
"""
To train your model:

1. Prepare a CSV:
   filename,label
   audio1.wav,hindi
   audio2.wav,tamil
   ...

2. Place audio files in a folder, e.g., dataset/

3. Run:
   python accent_detection_api.py --train --csv labels.csv --audio_dir dataset/

This will:
 - Extract wav2vec2 embeddings for each audio file
 - Train classifier head
 - Save classifier + label list to `models/`
"""

if __name__ == "__main__":
    import argparse
    import csv

    parser = argparse.ArgumentParser()
    parser.add_argument("--train", action="store_true")
    parser.add_argument("--csv", type=str, required=False)
    parser.add_argument("--audio_dir", type=str, required=False)
    args = parser.parse_args()

    if args.train:
        if not args.csv or not args.audio_dir:
            print("Provide --csv and --audio_dir")
            exit(1)

        print("Loading training dataset...")
        X = []
        Y = []

        with open(args.csv) as f:
            reader = csv.DictReader(f)
            for row in reader:
                filepath = os.path.join(args.audio_dir, row["filename"])
                label = row["label"].strip().lower()
                if label not in LABELS:
                    LABELS.append(label)

        LABELS = sorted(list(set(LABELS)))
        print("Labels:", LABELS)

        with open(args.csv) as f:
            reader = csv.DictReader(f)
            for row in reader:
                filepath = os.path.join(args.audio_dir, row["filename"])
                label = row["label"].strip().lower()
                if label not in LABELS:
                    continue
                audio, _ = librosa.load(filepath, sr=SAMPLE_RATE)
                emb = extract_wav2vec2_embedding(audio).squeeze(0).numpy()

                X.append(emb)
                Y.append(LABELS.index(label))

        X = torch.tensor(np.stack(X))
        Y = torch.tensor(Y)

        print("Training classifier head...")
        model = AccentClassifier(base_model.config.hidden_size, len(LABELS))
        optim = torch.optim.Adam(model.parameters(), lr=1e-3)
        loss_fn = torch.nn.CrossEntropyLoss()

        for epoch in range(10):
            optim.zero_grad()
            logits = model(X)
            loss = loss_fn(logits, Y)
            loss.backward()
            optim.step()
            print(f"Epoch {epoch+1} Loss: {loss.item():.4f}")

        os.makedirs(MODEL_DIR, exist_ok=True)
        torch.save(model.state_dict(), EMBEDDING_HEAD_PATH)

        with open(LABEL_LIST_PATH, "w") as f:
            json.dump(LABELS, f, indent=2)

        print("Training complete. Files saved in models/")
    else:
        print("Run server with: uvicorn accent_detection_api:app --reload")
