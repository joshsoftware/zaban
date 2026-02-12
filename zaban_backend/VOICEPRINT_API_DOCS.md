# Voiceprint API Documentation

The voiceprint service provides speaker enrollment and verification capabilities using ECAPA x-vectors and PLDA scoring with AS-Norm.

## 🛠 Setup & Configuration

### Prerequisites
- **Qdrant**: A vector database is required to store voice embeddings.
- **PLDA Model**: A trained PLDA model (`plda_model.pkl`) must be present in the `models/` directory.
- **Pretrained Models**: SpeechBrain ECAPA models will be downloaded automatically or loaded from `pretrained_models/`.

### Environment Variables
Add these to your `.env` file:

```env
# Voiceprint Core
VOICEPRINT_ENABLED=true
XOR_AUDIO_KEY=voiceprint_xor_key_v1

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Model Paths
PLDA_MODEL_PATH=./models/plda_model.pkl
ECAPA_SOURCE=speechbrain/spkrec-ecapa-voxceleb
ECAPA_SAVEDIR=./pretrained_models/spkrec-ecapa-voxceleb

# Verification Tuning
VERIFICATION_THRESHOLD=3.0
COHORT_TOP_K=30
MIN_ENROLLMENT_SAMPLES=3
```

## 🚀 Running the Service

### 1. Start Qdrant
If you have Docker installed:
```bash
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant
```

### 2. Install Dependencies
```bash
cd zaban_backend
uv pip install -e .
```

### 3. Run Backend
```bash
uv run uvicorn app.main:app --reload --port 8000
```

## 📡 API Endpoints

### 1. Enroll User
Enrolls a user by processing multiple voice samples and storing the averaged embedding in Qdrant.

- **URL**: `/api/v1/voiceprint/enroll/{user_id}`
- **Method**: `POST`
- **Body**: `multipart/form-data`
  - `files`: Multiple audio files (minimum 3)

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/v1/voiceprint/enroll/USER_UUID \
  -F "files=@voice1.wav" \
  -F "files=@voice2.wav" \
  -F "files=@voice3.wav"
```

### 2. Verify Speaker
Verifies a voice sample against a user's enrolled voiceprint.

- **URL**: `/api/v1/voiceprint/verify/{user_id}`
- **Method**: `POST`
- **Body**: `multipart/form-data`
  - `file`: Audio file to verify
  - `encrypted_audio`: (Optional) Base64 XOR-encrypted audio from frontend

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/v1/voiceprint/verify/USER_UUID \
  -F "file=@test_voice.wav"
```

**Response:**
```json
{
  "verified": true,
  "score": 4.52,
  "threshold": 3.0,
  "cohort_stats": { ... }
}
```

### 3. List Voiceprints
Lists all voiceprints (enrolled sessions) for a specific user.

- **URL**: `/api/v1/voiceprint/{user_id}/voiceprints`
- **Method**: `GET`

### 4. Management Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/voiceprint/{voiceprint_id}` | `PATCH` | Activate/Deactivate a specific voiceprint |
| `/api/v1/voiceprint/{voiceprint_id}` | `DELETE` | Delete a voiceprint record |
| `/api/v1/voiceprint/verify/{user_id}/history` | `GET` | Get verification attempt logs |
| `/api/v1/voiceprint/health` | `GET` | Check Qdrant connectivity |

## 🧪 Testing Tips
- Use `.wav` files with 16kHz sampling rate for best results.
- Ensure `VOICEPRINT_ENABLED=true` is set, otherwise you will receive a `501 Not Implemented` error.
- Check `/docs` for the interactive Swagger UI and detailed schema definitions.
