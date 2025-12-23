// lib/api-service.ts

import { clearAuthTokens } from "./auth";
import { config } from "./config";

const API_BASE_URL = `${config.api.baseUrl}/api/v1`;

const redirectToLogin = (reason: "expired" | "missing") => {
  clearAuthTokens();
  if (typeof window !== "undefined") {
    const search = reason ? `?reason=${reason}` : "";
    window.location.href = `/login${search}`;
  }
  throw new Error(
    reason === "expired"
      ? "Session expired. Redirecting to login."
      : "Not authenticated. Redirecting to login."
  );
};

export interface APIKey {
  id: string;
  name: string;
  is_active: boolean;
  created_at: string;
  revoked_at: string | null;
}

interface APIKeysResponse {
  api_keys: APIKey[];
  total: number;
}

export const getAccessToken = (): string | null => {
  if (typeof window !== "undefined") {
    return localStorage.getItem("access_token");
  }
  return null;
};

/**
 * Make authenticated API request
 */
const makeAuthenticatedRequest = async (
  endpoint: string,
  options: RequestInit = {}
) => {
  const token = getAccessToken();

  if (!token) {
    redirectToLogin("missing");
  }

  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      redirectToLogin("expired");
    }
    if (response.status === 404) {
      throw new Error("Resource not found.");
    }
    throw new Error(`Request failed: ${response.statusText}`);
  }

  return response;
};

/**
 * Fetch all API keys for the current user
 */
export const fetchAPIKeys = async (): Promise<APIKey[]> => {
  try {
    const response = await makeAuthenticatedRequest("/api-keys");
    const data: APIKeysResponse = await response.json();
    return data.api_keys || [];
  } catch (error) {
    console.error("Error fetching API keys:", error);
    throw error;
  }
};

/**
 * Delete an API key by ID
 * @param apiKeyId - The ID of the API key to delete
 */
export const deleteAPIKey = async (apiKeyId: string): Promise<void> => {
  try {
    await makeAuthenticatedRequest(`/api-keys/${apiKeyId}`, {
      method: "DELETE",
    });
  } catch (error) {
    console.error(`Error deleting API key ${apiKeyId}:`, error);
    throw error;
  }
};

/**
 * Get stored secret API key from localStorage
 */
export const getSecretApiKey = (): string | null => {
  if (typeof window !== "undefined") {
    return localStorage.getItem("secret_api_key");
  }
  return null;
};

/**
 * Set secret API key in localStorage
 */
export const setSecretApiKey = (key: string): void => {
  if (typeof window !== "undefined") {
    localStorage.setItem("secret_api_key", key);
  }
};

/**
 * Make API request with secret_api_key header
 */
const makeApiRequestWithKey = async (
  endpoint: string,
  options: RequestInit = {}
) => {
  const secretKey = getSecretApiKey();

  if (!secretKey) {
    throw new Error("No API key found. Please set your API key in settings.");
  }

  const url = `${API_BASE_URL}${endpoint}`;

  // Remove Content-Type from headers if FormData is being sent
  const isFormData = options.body instanceof FormData;
  const headers: Record<string, string> = {
    secret_api_key: secretKey,
    "X-API-Key": secretKey, // Also send X-API-Key for backend compatibility
    ...(isFormData ? {} : { "Content-Type": "application/json" }),
    ...((options.headers as Record<string, string>) || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response
      .json()
      .catch(() => ({ detail: response.statusText }));
    const errorMessage =
      errorData.detail ||
      errorData.message ||
      `Request failed: ${response.statusText}`;

    if (response.status === 401 || response.status === 403) {
      throw new Error(
        "Invalid API key. Please check your API key in settings."
      );
    }
    if (response.status === 400) {
      throw new Error(errorMessage);
    }
    throw new Error(errorMessage);
  }

  return response;
};

/**
 * Speech-to-Text API
 * @param audioFile - Audio file to transcribe
 * @param lang - Language code (optional, will be auto-detected if not provided)
 * @param model - Model to use: 'whisper' (default) or 'ai4bharat'
 */
export interface STTResponse {
  text: string;
  language?: string;
  model?: string;
}

export const transcribeAudio = async (
  audioFile: File,
  lang?: string,
  model: string = "whisper"
): Promise<STTResponse> => {
  try {
    const formData = new FormData();
    formData.append("audio", audioFile);
    if (lang) {
      formData.append("lang", lang);
    }
    formData.append("model", model);

    const response = await makeApiRequestWithKey("/stt", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    // Handle different response formats
    if (data.text) {
      return { text: data.text, language: data.language, model: data.model };
    } else if (data.transcription) {
      return {
        text: data.transcription,
        language: data.language,
        model: data.model,
      };
    } else if (typeof data === "string") {
      return { text: data };
    }

    throw new Error("Unexpected response format from STT API");
  } catch (error) {
    console.error("Error transcribing audio:", error);
    throw error;
  }
};

/**
 * Translation API
 * @param text - Text to translate
 * @param sourceLang - Source language code (optional, will be auto-detected if not provided)
 * @param targetLang - Target language code (required)
 * @param autoDetect - Enable auto-detection of source language
 */
export interface TranslationResponse {
  translated_text: string;
  source_lang: string;
  target_lang: string;
  model?: string;
  auto_detected?: boolean;
}

export const translateText = async (
  text: string,
  targetLang: string,
  sourceLang?: string,
  autoDetect: boolean = false
): Promise<TranslationResponse> => {
  try {
    interface TranslateRequestBody {
      text: string;
      target_lang: string;
      source_lang?: string;
      auto_detect?: boolean;
    }

    const requestBody: TranslateRequestBody = {
      text,
      target_lang: targetLang,
    };

    if (sourceLang) {
      requestBody.source_lang = sourceLang;
    }

    if (autoDetect || !sourceLang) {
      requestBody.auto_detect = true;
    }

    const response = await makeApiRequestWithKey("/translate", {
      method: "POST",
      body: JSON.stringify(requestBody),
    });

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error translating text:", error);
    throw error;
  }
};

/**
 * Language Detection API
 * @param text - Text to detect language from
 */
export interface LanguageDetectionResponse {
  language: string;
  confidence: number;
  method: string;
}

export const detectLanguage = async (
  text: string
): Promise<LanguageDetectionResponse> => {
  try {
    const response = await makeApiRequestWithKey("/detect-language", {
      method: "POST",
      body: JSON.stringify({ text }),
    });

    const data = await response.json();

    // Normalize to 2-letter code if it's in BCP-47 format
    let langCode = data.detected_lang || data.language || "en";
    if (langCode.includes("_")) {
      langCode = langCode.split("_")[0]; // hin_Deva -> hin
    }
    langCode = langCode.substring(0, 2).toLowerCase(); // hin -> hi

    return {
      language: langCode,
      confidence: data.confidence || 1.0,
      method: data.method || "fasttext",
    };
  } catch (error) {
    console.error("Error detecting language:", error);
    // Return default instead of throwing
    return {
      language: "en",
      confidence: 0,
      method: "fallback",
    };
  }
};

/**
 * Text-to-Speech API
 * @param text - Text to convert to speech
 * @param language - Language code (optional, 2-letter ISO 639-1)
 * @param voiceDescription - Description of desired voice characteristics (optional)
 * @param speaker - Speaker name for consistent voice (optional)
 */
export const synthesizeSpeech = async (
  text: string,
  language?: string,
  voiceDescription?: string,
  speaker?: string
): Promise<Blob> => {
  try {
    interface TTSRequestBody {
      text: string;
      language?: string;
      voice_description?: string;
      speaker?: string;
    }

    const requestBody: TTSRequestBody = {
      text,
    };

    if (language) {
      requestBody.language = language;
    }

    if (voiceDescription) {
      requestBody.voice_description = voiceDescription;
    }

    if (speaker) {
      requestBody.speaker = speaker;
    }

    const response = await makeApiRequestWithKey("/tts", {
      method: "POST",
      body: JSON.stringify(requestBody),
    });

    // Return audio blob
    const audioBlob = await response.blob();
    return audioBlob;
  } catch (error) {
    console.error("Error synthesizing speech:", error);
    throw error;
  }
};
