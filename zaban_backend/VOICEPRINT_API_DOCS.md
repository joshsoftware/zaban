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
  - `device_id`: (Optional) Unique identifier for the device

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/v1/voiceprint/enroll/USER_UUID \
  -F "files=@voice1.wav" \
  -F "files=@voice2.wav" \
  -F "files=@voice3.wav" \
  -F "device_id=my-device-123"
```

**Response:**
```json
{
  "status": "success",
  "user_id": "USER_UUID",
  "device_id": "my-device-123",
  "message": "Voiceprint enrolled successfully",
  "num_samples": 3
}
```

### 2. Verify Speaker
Verifies a voice sample against a user's enrolled voiceprint.

- **URL**: `/api/v1/voiceprint/verify/{user_id}`
- **Method**: `POST`
- **Body**: `multipart/form-data`
  - `file`: (Optional) Audio file to verify
  - `encrypted_audio`: (Optional) Base64 XOR-encrypted audio from frontend

**Example Request (File):**
```bash
curl -X POST http://localhost:8000/api/v1/voiceprint/verify/USER_UUID \
  -F "file=@test_voice.wav"
```

**Example Request (Encrypted):**
```bash
curl -X POST http://localhost:8000/api/v1/voiceprint/verify/USER_UUID \
  -F "encrypted_audio=BASE64_XOR_DATA"
```

**Response:**
```json
{
  "verified": true,
  "score": 4.52,
  "raw_score": 1.25,
  "threshold": 3.0,
  "cohort_stats": {
    "enrollment_cohort_mean": 0.12,
    "enrollment_cohort_std": 0.05,
    "test_cohort_mean": 0.11,
    "test_cohort_std": 0.04,
    "cohort_size": 30
  }
}
```

### 3. List Voiceprints
Lists all voiceprints (enrolled sessions) for a specific user.

- **URL**: `/api/v1/voiceprint/{user_id}/voiceprints`
- **Method**: `GET`

**Response:**
```json
[
  {
    "id": "VP_UUID",
    "user_id": "USER_UUID",
    "qdrant_vector_id": "VECTOR_UUID",
    "model_name": "speechbrain/spkrec-ecapa-voxceleb",
    "is_active": true,
    "created_at": "2023-10-27T10:00:00"
  }
]
```

### 4. Management Endpoints

| Endpoint | Method | Body | Description |
|----------|--------|------|-------------|
| `/api/v1/voiceprint/{voiceprint_id}` | `PATCH` | `{"is_active": bool}` | Activate/Deactivate a specific voiceprint |
| `/api/v1/voiceprint/{voiceprint_id}` | `DELETE` | - | Delete a voiceprint record |
| `/api/v1/voiceprint/verify/{user_id}/history` | `GET` | - | Get verification attempt logs |
| `/api/v1/voiceprint/health` | `GET` | - | Check Qdrant connectivity |

**Health Check Response:**
```json
{
  "status": "healthy",
  "qdrant_connected": true,
  "collections": ["voice_embeddings"]
}
```

## 🧪 Testing Tips
- Use `.wav` files with 16kHz sampling rate for best results.
- Ensure `VOICEPRINT_ENABLED=true` is set, otherwise you will receive a `501 Not Implemented` error.
- Check `/docs` for the interactive Swagger UI and detailed schema definitions.
