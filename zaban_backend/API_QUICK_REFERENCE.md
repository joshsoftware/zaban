# API Quick Reference

## 🔐 Authentication Flow

1. **Get Google OAuth Code**
   ```
   https://accounts.google.com/o/oauth2/v2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8000/auth/callback&response_type=code&scope=openid%20email%20profile&prompt=consent&login_hint=your.email@joshsoftware.com
   ```

2. **Exchange for JWT Token**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/google/login \
     -H "Content-Type: application/json" \
     -d '{"code":"YOUR_CODE","redirect_uri":"http://localhost:8000/auth/callback"}'
   ```

3. **Create API Key**
   ```bash
   curl -X POST http://localhost:8000/api/v1/api-keys \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name": "My Key"}'
   ```

## 🔑 API Key Management

| Endpoint | Method | Headers | Description |
|----------|--------|---------|-------------|
| `/api/v1/api-keys` | POST | `Authorization: Bearer JWT` | Create API key |
| `/api/v1/api-keys` | GET | `Authorization: Bearer JWT` | List user's API keys |
| `/api/v1/api-keys/{id}` | GET | `Authorization: Bearer JWT` | Get specific API key |
| `/api/v1/api-keys/{id}` | DELETE | `Authorization: Bearer JWT` | Delete API key |

## 🤖 AI4Bharat Services (All require X-API-Key header)

| Service | Endpoint | Method | Headers |
|---------|----------|--------|---------|
| Translation | `/api/v1/translate` | POST | `X-API-Key: sk-...` |
| TTS | `/api/v1/tts` | POST | `X-API-Key: sk-...` |
| STT | `/api/v1/stt` | POST | `X-API-Key: sk-...` |
| Transliteration | `/api/v1/transliterate` | POST | `X-API-Key: sk-...` |

## 📝 Example Requests

### Translation
```bash
curl -X POST http://localhost:8000/api/v1/translate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-your-secret-key" \
  -d '{"text":"Hello","source_lang":"eng_Latn","target_lang":"hin_Deva"}'
```

### Translation with audio (include_audio: true)
Response is JSON with `audio_base64` (base64-encoded WAV).

**Play the audio from Postman:** In the request’s **Tests** tab, add:
```javascript
const j = pm.response.json();

pm.test("Status is success", function () {
  pm.response.to.have.status(200);
});
pm.test("Response has translation or audio", function () {
  pm.expect(j.translated_text || j.audio_base64).to.be.ok;
});

if (j.audio_base64) {
  const dataUrl = "data:audio/wav;base64," + j.audio_base64;
  pm.visualizer.set(`
    <p><strong>Translation:</strong> ${j.translated_text || ''}</p>
    <audio controls src="${dataUrl}"></audio>
    <p><a href="${dataUrl}" target="_blank" rel="noopener">Open / play in browser</a></p>
  `);
  pm.environment.set("audio_play_url", dataUrl);
}
```
Then **Send** the request.

- **Option A – Visualize tab:** In the **response** section (bottom half), open the **Body** tab. Above the response body you should see view options: **Pretty** | **Raw** | **Preview** | **Visualize**. Click **Visualize** to see the player and the “Open / play in browser” link.
- **Option B – Play in browser (no Visualize needed):** After sending, go to **Environments** → select your environment → find **audio_play_url**. Copy its value (the long `data:audio/wav;base64,...` string), paste it into your **browser’s address bar**, and press Enter. The browser will play the audio.
- **Option C – Decode online:** Copy the `audio_base64` value from the **Body** (Pretty view), go to [base64.guru/convert/decode/audio](https://base64.guru/convert/decode/audio), paste, decode, then download the WAV and play it.

### TTS
```bash
curl -X POST http://localhost:8000/api/v1/tts \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-your-secret-key" \
  -d '{"text":"नमस्ते","lang":"hi","speaker":"female"}'
```

### STT
```bash
curl -X POST http://localhost:8000/api/v1/stt \
  -H "X-API-Key: sk-your-secret-key" \
  -F "audio=@audio.wav" -F "lang=hi"
```

### Transliteration
```bash
curl -X POST http://localhost:8000/api/v1/transliterate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-your-secret-key" \
  -d '{"text":"namaste","source_script":"latn","target_script":"deva","lang":"hi"}'
```

## 🔒 Security Features

- **API Key Format**: All keys start with `sk-` prefix
- **User Isolation**: Users can only see their own API keys
- **One-time Display**: Raw keys shown only during creation
- **Secure Storage**: Keys are hashed in database
- **Deactivation**: Deleted keys are permanently unusable

## 🚨 Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `401 X-API-Key header missing` | No API key provided | Add `X-API-Key: sk-...` header |
| `401 Invalid or inactive API key` | Wrong/deleted key | Create new API key |
| `401 Unauthorized` | Missing JWT token | Get JWT from Google OAuth |

## 🌐 Language Codes (BCP-47)

| Language | Code | Script |
|----------|------|--------|
| English | `eng_Latn` | Latin |
| Hindi | `hin_Deva` | Devanagari |
| Bengali | `ben_Beng` | Bengali |
| Tamil | `tam_Taml` | Tamil |
| Telugu | `tel_Telu` | Telugu |
| Gujarati | `guj_Gujr` | Gujarati |
| Kannada | `kan_Knda` | Kannada |
| Malayalam | `mal_Mlym` | Malayalam |
| Marathi | `mar_Deva` | Devanagari |
| Punjabi | `pan_Guru` | Gurmukhi |

## 📊 Response Formats

### Create API Key Response
```json
{
  "id": "uuid-here",
  "name": "My API Key",
  "secret_key": "sk-ewVR1t_HMn57DRmVu..."
}
```

### List API Keys Response
```json
{
  "api_keys": [
    {
      "id": "uuid-here",
      "name": "My API Key",
      "is_active": true,
      "created_at": "2025-10-23T06:59:12",
      "revoked_at": null
    }
  ],
  "total": 1
}
```

### Translation Response
```json
{
  "translated_text": "आप कैसे हैं?",
  "source_lang": "eng_Latn",
  "target_lang": "hin_Deva",
  "model": "indictrans2-local"
}
```
