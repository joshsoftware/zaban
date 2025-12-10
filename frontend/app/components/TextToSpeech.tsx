"use client";

import { useState, useRef, useEffect } from "react";
import {
  Volume2,
  Play,
  Pause,
  Download,
  Loader2,
  AlertCircle,
} from "lucide-react";

interface TextToSpeechProps {
  onSynthesisComplete?: (audioUrl: string) => void;
}

export default function TextToSpeech({
  onSynthesisComplete,
}: TextToSpeechProps) {
  const [text, setText] = useState("");
  const [language, setLanguage] = useState("hi");
  const [autoDetect, setAutoDetect] = useState(false);
  const [detectedLanguage, setDetectedLanguage] = useState<string | null>(null);
  const [voiceType, setVoiceType] = useState("default");
  const [customDescription, setCustomDescription] = useState("");
  const [speaker, setSpeaker] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Update audio element whenever we receive a new audio URL
  useEffect(() => {
    if (!audioUrl || !audioRef.current) return;

    const audioEl = audioRef.current;
    audioEl.src = audioUrl;
    setIsPlaying(false);

    audioEl.onerror = (e) => {
      console.error("Audio playback error:", e);
      setError("Audio file cannot be played. The format may be unsupported.");
    };

    audioEl.onloadedmetadata = () => {
      console.log("Audio loaded successfully:", {
        duration: audioEl.duration,
        readyState: audioEl.readyState,
      });
    };

    // Attempt autoplay
    audioEl
      .play()
      .then(() => setIsPlaying(true))
      .catch((err) => {
        console.error("Playback failed:", err);
        setError("Failed to play audio. Click the play button to try again.");
        setIsPlaying(false);
      });
  }, [audioUrl]);

  // Supported languages for IndicParler TTS
  const languages = [
    { code: "hi", name: "Hindi (हिन्दी)" },
    { code: "bn", name: "Bengali (বাংলা)" },
    { code: "ta", name: "Tamil (தமிழ்)" },
    { code: "te", name: "Telugu (తెలుగు)" },
    { code: "mr", name: "Marathi (मराठी)" },
    { code: "gu", name: "Gujarati (ગુજરાતી)" },
    { code: "kn", name: "Kannada (ಕನ್ನಡ)" },
    { code: "ml", name: "Malayalam (മലയാളം)" },
    { code: "pa", name: "Punjabi (ਪੰਜਾਬੀ)" },
    { code: "or", name: "Odia (ଓଡ଼ିଆ)" },
    { code: "as", name: "Assamese (অসমীয়া)" },
    { code: "ur", name: "Urdu (اردو)" },
    { code: "ne", name: "Nepali (नेपाली)" },
    { code: "sa", name: "Sanskrit (संस्कृतम्)" },
    { code: "en", name: "English" },
    { code: "brx", name: "Bodo (बड़ो)" },
    { code: "ks", name: "Kashmiri (कॉशुर)" },
    { code: "mni", name: "Manipuri (মৈতৈলোন্)" },
    { code: "sd", name: "Sindhi (سنڌي)" },
    { code: "doi", name: "Dogri (डोगरी)" },
    { code: "kok", name: "Konkani (कोंकणी)" },
  ];

  const voiceTypes = [
    {
      value: "default",
      label: "Default",
      description: "A clear and natural voice with moderate speed and pitch.",
    },
    {
      value: "female_expressive",
      label: "Female Expressive",
      description:
        "A female speaker delivers a slightly expressive and animated speech with a moderate speed and pitch. The recording is of very high quality, with the speaker's voice sounding clear and very close up.",
    },
    {
      value: "male_calm",
      label: "Male Calm",
      description:
        "A male speaker delivers a calm and steady speech with a moderate speed and pitch. The recording is of very high quality.",
    },
    {
      value: "female_fast",
      label: "Female Fast",
      description:
        "A female speaker delivers speech with a fast pace and moderate pitch. The recording is clear and very close up.",
    },
    {
      value: "male_slow",
      label: "Male Slow",
      description:
        "A male speaker delivers speech with a slow pace and deep pitch. The recording is of high quality.",
    },
    {
      value: "custom",
      label: "Custom",
      description: "Provide your own voice description",
    },
  ];

  // Example texts for different languages
  const exampleTexts: Record<string, string> = {
    hi: "नमस्ते, आप कैसे हैं?",
    bn: "নমস্কার, আপনি কেমন আছেন?",
    ta: "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
    te: "నమస్కారం, మీరు ఎలా ఉన్నారు?",
    mr: "नमस्कार, तुम्ही कसे आहात?",
    gu: "નમસ્તે, તમે કેવા છો?",
    kn: "ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ?",
    ml: "നമസ്കാരം, നിങ്ങൾ എങ്ങനെയുണ്ട്?",
    pa: "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ, ਤੁਸੀਂ ਕਿਵੇਂ ਹੋ?",
    or: "ନମସ୍କାର, ଆପଣ କେମିତି ଅଛନ୍ତି?",
    en: "Hello, how are you?",
  };

  const handleLanguageChange = (newLang: string) => {
    if (newLang === "auto") {
      setAutoDetect(true);
      setLanguage("hi"); // Default fallback
    } else {
      setAutoDetect(false);
      setLanguage(newLang);
      // Auto-fill example text if current text is empty or is an example from another language
      if (!text || Object.values(exampleTexts).includes(text)) {
        setText(exampleTexts[newLang] || "");
      }
    }
    setDetectedLanguage(null);
  };

  const detectLanguage = async (text: string): Promise<string> => {
    try {
      const { detectLanguage: detectLangApi } = await import(
        "../lib/api-service"
      );
      const result = await detectLangApi(text);
      return result.language;
    } catch (error) {
      console.error("Language detection failed:", error);
      return "hi"; // Default to Hindi
    }
  };

  const synthesizeSpeech = async () => {
    if (!text.trim()) {
      setError("Please enter some text to convert to speech");
      return;
    }

    setIsProcessing(true);
    setError(null);
    setAudioUrl(null);
    setDetectedLanguage(null);

    try {
      const { synthesizeSpeech: synthesizeApi } = await import(
        "../lib/api-service"
      );

      // Auto-detect language if enabled
      let targetLanguage = language;
      if (autoDetect) {
        console.log("🔍 Auto-detecting language...");
        targetLanguage = await detectLanguage(text);
        setDetectedLanguage(targetLanguage);
        console.log(`✅ Detected language: ${targetLanguage}`);
      }

      // Determine voice description
      let voiceDescription: string | undefined;
      if (voiceType === "custom") {
        voiceDescription = customDescription || undefined;
      } else if (voiceType !== "default") {
        const selectedVoice = voiceTypes.find((v) => v.value === voiceType);
        voiceDescription = selectedVoice?.description;
      }

      // Show loading message for Indian languages (can take longer)
      const nonEnglishLangs = [
        "hi",
        "bn",
        "ta",
        "te",
        "mr",
        "gu",
        "kn",
        "ml",
        "pa",
        "or",
        "as",
        "ur",
        "ne",
        "sa",
        "brx",
        "ks",
        "mni",
        "sd",
        "doi",
        "kok",
      ];
      if (nonEnglishLangs.includes(targetLanguage)) {
        console.log(
          "⏳ Note: First request may take 30-60 seconds to load the model..."
        );
      }

      const audioBlob = await synthesizeApi(
        text,
        targetLanguage,
        voiceDescription,
        speaker || undefined
      );

      // Verify blob type and size
      console.log("Audio blob received:", {
        type: audioBlob.type,
        size: audioBlob.size,
        sizeKB: (audioBlob.size / 1024).toFixed(2) + " KB",
      });

      // Create a proper WAV blob with correct MIME type
      const wavBlob = new Blob([audioBlob], { type: "audio/wav" });
      const url = URL.createObjectURL(wavBlob);

      console.log("Created audio URL:", url);
      setAudioUrl(url);
      onSynthesisComplete?.(url);

      // Auto-play the audio
      if (audioRef.current) {
        audioRef.current.src = url;

        // Add error handler
        audioRef.current.onerror = (e) => {
          console.error("Audio playback error:", e);
          setError(
            "Audio file cannot be played. The format may be unsupported."
          );
        };

        // Add loaded metadata handler
        audioRef.current.onloadedmetadata = () => {
          console.log("Audio loaded successfully:", {
            duration: audioRef.current?.duration,
            readyState: audioRef.current?.readyState,
          });
        };

        audioRef.current.play().catch((err) => {
          console.error("Playback failed:", err);
          setError("Failed to play audio. Click the play button to try again.");
          setIsPlaying(false);
        });

        setIsPlaying(true);
      }
    } catch (error) {
      console.error("Error synthesizing speech:", error);
      const errorMessage =
        error instanceof Error
          ? error.message
          : "Failed to synthesize speech. Please try again.";
      setError(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  };

  const togglePlayPause = () => {
    if (!audioRef.current || !audioUrl) return;

    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const downloadAudio = () => {
    if (!audioUrl) return;

    const a = document.createElement("a");
    a.href = audioUrl;
    a.download = `speech_${language}_${Date.now()}.wav`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl">
          <Volume2 className="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Text to Speech</h2>
          <p className="text-sm text-gray-600">
            Convert text to natural-sounding speech in 21 Indian languages
          </p>
        </div>
      </div>

      {/* Input Section */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Language Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-800 mb-2">
              Language
            </label>
            <select
              value={autoDetect ? "auto" : language}
              onChange={(e) => handleLanguageChange(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-gray-900"
            >
              <option value="auto">🔍 Auto-Detect Language</option>
              <option disabled>───────────────</option>
              {languages.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.name}
                </option>
              ))}
            </select>
            {autoDetect && detectedLanguage && (
              <p className="text-xs text-green-600 mt-1">
                ✅ Detected:{" "}
                {languages.find((l) => l.code === detectedLanguage)?.name ||
                  detectedLanguage}
              </p>
            )}
          </div>

          {/* Voice Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-800 mb-2">
              Voice Type
            </label>
            <select
              value={voiceType}
              onChange={(e) => setVoiceType(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-gray-900"
            >
              {voiceTypes.map((voice) => (
                <option key={voice.value} value={voice.value}>
                  {voice.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Custom Voice Description (if custom voice type selected) */}
        {voiceType === "custom" && (
          <div>
            <label className="block text-sm font-medium text-gray-800 mb-2">
              Voice Description
            </label>
            <textarea
              value={customDescription}
              onChange={(e) => setCustomDescription(e.target.value)}
              placeholder="Describe the voice characteristics (e.g., 'A female speaker with a soft, calm voice and moderate speed')"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none text-gray-900"
              rows={2}
            />
          </div>
        )}

        {/* Advanced Options Toggle */}
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-sm text-purple-600 hover:text-purple-700 font-medium"
        >
          {showAdvanced ? "− Hide" : "+ Show"} Advanced Options
        </button>

        {/* Advanced Options */}
        {showAdvanced && (
          <div>
            <label className="block text-sm font-medium text-gray-800 mb-2">
              Speaker Name (Optional)
            </label>
            <input
              type="text"
              value={speaker}
              onChange={(e) => setSpeaker(e.target.value)}
              placeholder="e.g., Divya, Rajesh (for consistent voice across requests)"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-gray-900"
            />
            <p className="text-xs text-gray-500 mt-1">
              Specify a speaker name for consistent voice characteristics across
              multiple requests
            </p>
          </div>
        )}

        {/* Text Input */}
        <div>
          <label className="block text-sm font-medium text-gray-800 mb-2">
            Text to Convert
          </label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Enter text to convert to speech..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none text-gray-900"
            rows={4}
          />
          <div className="flex justify-between items-center mt-2">
            <p className="text-xs text-gray-500">{text.length} characters</p>
            {exampleTexts[language] && (
              <button
                onClick={() => setText(exampleTexts[language])}
                className="text-xs text-purple-600 hover:text-purple-700 font-medium"
              >
                Use Example Text
              </button>
            )}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="flex items-start gap-2 p-4 bg-red-50 border border-red-200 rounded-lg">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-900">Error</p>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Synthesize Button */}
        <button
          onClick={synthesizeSpeech}
          disabled={isProcessing || !text.trim()}
          className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white py-3 px-6 rounded-lg font-medium hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
        >
          {isProcessing ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Generating Speech...{" "}
              {language !== "en" && "(may take 30-60s on first request)"}
            </>
          ) : (
            <>
              <Volume2 className="w-5 h-5" />
              Generate Speech
            </>
          )}
        </button>

        {isProcessing && language !== "en" && (
          <div className="text-sm text-gray-600 text-center mt-2">
            ⏳ First request for{" "}
            {languages.find((l) => l.code === language)?.name} may take 30-60
            seconds. Please wait...
          </div>
        )}
      </div>

      {/* Audio Player */}
      {audioUrl && (
        <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl shadow-sm border border-purple-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Generated Speech
          </h3>

          <div className="flex items-center gap-4">
            <button
              onClick={togglePlayPause}
              className="p-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-full hover:from-purple-700 hover:to-pink-700 transition-all"
            >
              {isPlaying ? (
                <Pause className="w-6 h-6" />
              ) : (
                <Play className="w-6 h-6 ml-0.5" />
              )}
            </button>

            <div className="flex-1">
              <audio
                ref={audioRef}
                onEnded={() => setIsPlaying(false)}
                onPause={() => setIsPlaying(false)}
                onPlay={() => setIsPlaying(true)}
                className="w-full"
                controls
              />
            </div>

            <button
              onClick={downloadAudio}
              className="p-3 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              title="Download Audio"
            >
              <Download className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}

      {/* Info Section */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-blue-900 mb-2">
          ℹ️ About IndicParler TTS
        </h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Supports 21 Indian languages with 69 unique voices</li>
          <li>• Controllable voice characteristics through descriptions</li>
          <li>• High-quality, natural-sounding speech synthesis</li>
          <li>• Powered by AI4Bharat’s IndicParler model</li>
        </ul>
      </div>
    </div>
  );
}
