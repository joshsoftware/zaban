# Voice Print Backend

**Speaker Verification API using ECAPA-TDNN + PLDA + AS-Norm**

A production-ready FastAPI-based speaker verification system that uses:
- **ECAPA-TDNN** (SpeechBrain) for speaker embedding extraction
- **PLDA** (Probabilistic Linear Discriminant Analysis) for scoring
- **AS-Norm** (Adaptive Score Normalization) for robust verification
- **Qdrant** for vector storage and similarity search

## Features

- 🎙️ **Speaker Enrollment** - Enroll users with 3-10 audio samples
- ✅ **Speaker Verification** - Verify audio against enrolled users
- 📊 **PLDA Scoring** - Robust scoring with AS-Norm normalization
- 🔍 **Cohort-based Normalization** - Uses Indian speaker cohort for score normalization
- 🚀 **FastAPI** - Modern, high-performance API

## Project Structure

```
voice-print-backend-plda/
├── app/                          # FastAPI Application
│   ├── main.py                   # Application entry point
│   ├── config.py                 # Configuration management
│   ├── api/routes/               # API endpoints
│   │   ├── enrollment.py         # POST /api/v1/enroll
│   │   ├── verification.py       # POST /api/v1/verify
│   │   └── health.py             # GET /health
│   ├── core/                     # Business logic
│   │   ├── voice_verifier.py     # VoiceVerifierECAPA
│   │   ├── plda.py               # PLDA scoring
│   │   └── cohort.py             # Cohort management
│   ├── utils/                    # Utilities
│   │   ├── audio.py              # Audio processing
│   │   └── embeddings.py         # ECAPA embeddings
│   └── schemas/                  # Pydantic models
├── data/                         # Data files
│   ├── embeddings_plda.npz       # Pre-extracted embeddings
│   └── *.parquet                 # Training datasets
├── models/                       # Model files
│   └── plda_model.pkl            # Trained PLDA model
├── scripts/                      # CLI tools
│   ├── train_plda.py             # Train PLDA model
│   ├── extract_embeddings_from_parquet.py
│   ├── populate_cohort.py        # Populate Qdrant cohort
│   ├── vectorize_from_parquet.py
│   └── record_audio.py           # Audio recording utility
├── audio/                        # Test audio samples
├── pretrained_models/            # SpeechBrain model cache
├── docker-compose.yml            # Qdrant service
└── requirements.txt
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Qdrant (Vector Database)

```bash
docker-compose up -d
```

### 3. Run the API Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access the API

- **Swagger UI**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Enrollment

**POST /api/v1/enroll**

Enroll a user with multiple audio samples (3-10 required).

```bash
curl -X POST http://localhost:8000/api/v1/enroll \
  -F "user_id=john_doe" \
  -F "audio_files=@audio/sample1.wav" \
  -F "audio_files=@audio/sample2.wav" \
  -F "audio_files=@audio/sample3.wav"
```

### Verification

**POST /api/v1/verify**

Verify if an audio sample belongs to an enrolled user.

```bash
curl -X POST http://localhost:8000/api/v1/verify \
  -F "user_id=john_doe" \
  -F "audio_file=@audio/test.wav"
```

Response:
```json
{
  "verified": true,
  "score": 4.52,
  "raw_score": 12.34,
  "threshold": 3.0,
  "cohort_stats": {
    "enrollment_cohort_mean": 2.1,
    "enrollment_cohort_std": 1.5,
    "test_cohort_mean": 2.3,
    "test_cohort_std": 1.4,
    "cohort_size": 30
  }
}
```

### List Enrolled Users

**GET /api/v1/enroll/users**

```bash
curl http://localhost:8000/api/v1/enroll/users
```

## Configuration

Environment variables (can be set in `.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_HOST` | localhost | Qdrant server host |
| `QDRANT_PORT` | 6333 | Qdrant server port |
| `VERIFICATION_THRESHOLD` | 3.0 | AS-Norm threshold for verification |
| `COHORT_TOP_K` | 30 | Top-K cohort vectors for AS-Norm |
| `PLDA_MODEL_PATH` | models/plda_model.pkl | Path to PLDA model |

## Scripts

### Train PLDA Model

```bash
python scripts/train_plda.py data/embeddings_plda.npz -o models/plda_model.pkl
```

### Extract Embeddings from Parquet

```bash
python scripts/extract_embeddings_from_parquet.py data/*.parquet -o data/embeddings_plda.npz
```

### Populate Cohort

```bash
python scripts/populate_cohort.py data/*.parquet --max-per-file 500
```

## Technology Stack

- **Embedding Model**: ECAPA-TDNN (SpeechBrain)
- **Scoring**: PLDA with AS-Norm normalization
- **Vector Database**: Qdrant
- **API Framework**: FastAPI
- **Audio Processing**: torchaudio, soundfile, librosa

## License

MIT
