"use client";

import { useState, useRef } from "react";
import {
  Mic,
  Upload,
  X,
  Loader2,
  FileAudio,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface SpeechToTextProps {
  onTranscriptionComplete?: (text: string) => void;
}

// Common language codes for STT
const LANGUAGE_OPTIONS = [
  { code: "hi", name: "Hindi" },
  { code: "en", name: "English" },
  { code: "mr", name: "Marathi" },
  { code: "ta", name: "Tamil" },
  { code: "te", name: "Telugu" },
  { code: "bn", name: "Bengali" },
  { code: "gu", name: "Gujarati" },
  { code: "kn", name: "Kannada" },
  { code: "ml", name: "Malayalam" },
  { code: "pa", name: "Punjabi" },
  { code: "or", name: "Oriya" },
  { code: "as", name: "Assamese" },
  { code: "ne", name: "Nepali" },
];

export default function SpeechToText({
  onTranscriptionComplete,
}: SpeechToTextProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [transcription, setTranscription] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [model, setModel] = useState<"whisper" | "ai4bharat">("whisper");
  const [language, setLanguage] = useState<string>("");

  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Start Recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: "audio/wav",
        });
        const audioFile = new File([audioBlob], "recording.wav", {
          type: "audio/wav",
        });
        setAudioFile(audioFile);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (error) {
      console.error("Error accessing microphone:", error);
      setError("Unable to access microphone. Please grant permission.");
    }
  };

  // Stop Recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);

      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  // Handle File Upload
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Check if file is audio
      if (!file.type.startsWith("audio/")) {
        setError("Please upload an audio file");
        return;
      }
      setAudioFile(file);
      setError(null);
    }
  };

  // Process Audio (Send to API)
  const processAudio = async () => {
    if (!audioFile) return;

    // Validate language for AI4Bharat model
    if (model === "ai4bharat" && !language) {
      setError("Please select a language for AI4Bharat model");
      return;
    }

    setIsProcessing(true);
    setTranscription("");
    setError(null);

    try {
      const { transcribeAudio } = await import("../lib/api-service");
      const result = await transcribeAudio(
        audioFile,
        language || undefined,
        model
      );

      setTranscription(result.text);
      onTranscriptionComplete?.(result.text);
    } catch (error) {
      console.error("Error processing audio:", error);
      const errorMessage =
        error instanceof Error
          ? error.message
          : "Failed to process audio. Please try again.";
      setError(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  };

  // Clear Audio
  const clearAudio = () => {
    setAudioFile(null);
    setTranscription("");
    setRecordingTime(0);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // Reset language when model changes
  const handleModelChange = (newModel: "whisper" | "ai4bharat") => {
    setModel(newModel);
    if (newModel === "whisper") {
      setLanguage(""); // Language is optional for Whisper
    }
    setError(null);
  };

  // Format time (seconds to MM:SS)
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs
      .toString()
      .padStart(2, "0")}`;
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-semibold text-gray-900">
            Speech to Text
          </h3>
          <p className="text-sm text-gray-800 mt-1">
            Record or upload audio to transcribe
          </p>
        </div>
      </div>

      {/* Model Selection */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <label className="block text-sm font-medium text-gray-900 mb-3">
          STT Model
        </label>
        <div className="space-y-3">
          <label className="flex items-start gap-3 p-3 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
            <input
              type="radio"
              name="stt-model"
              value="whisper"
              checked={model === "whisper"}
              onChange={() => handleModelChange("whisper")}
              className="w-4 h-4 text-orange-500 focus:ring-orange-500 mt-0.5"
            />
            <div className="flex-1">
              <span className="text-sm font-medium text-gray-900 block">
                Whisper
              </span>
              <span className="text-xs text-gray-700 mt-1 block">
                Auto-detects language, supports 100+ languages
              </span>
            </div>
          </label>
          <label className="flex items-start gap-3 p-3 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
            <input
              type="radio"
              name="stt-model"
              value="ai4bharat"
              checked={model === "ai4bharat"}
              onChange={() => handleModelChange("ai4bharat")}
              className="w-4 h-4 text-orange-500 focus:ring-orange-500 mt-0.5"
            />
            <div className="flex-1">
              <span className="text-sm font-medium text-gray-900 block">
                AI4Bharat
              </span>
              <span className="text-xs text-gray-700 mt-1 block">
                Best for Indian languages, requires language selection
              </span>
            </div>
          </label>
        </div>

        {/* Language Selection - shown when AI4Bharat is selected */}
        {model === "ai4bharat" && (
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Language <span className="text-red-500">*</span>
            </label>
            <select
              value={language}
              onChange={(e) => {
                setLanguage(e.target.value);
                setError(null);
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all bg-white"
              required
            >
              <option value="">Select language...</option>
              {LANGUAGE_OPTIONS.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.name}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-700 mt-2">
              AI4Bharat model works best for Indian languages: hi, mr, ta, te,
              bn, gu, kn, ml, pa, or, as, ne, en
            </p>
          </div>
        )}

        {/* Optional Language for Whisper */}
        {model === "whisper" && (
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Language (Optional - will auto-detect if not provided)
            </label>
            <select
              value={language}
              onChange={(e) => {
                setLanguage(e.target.value);
                setError(null);
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all bg-white"
            >
              <option value="">Auto-detect (recommended)</option>
              {LANGUAGE_OPTIONS.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.name}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-700 mt-2">
              Whisper can auto-detect the language. You can specify it manually
              for better accuracy.
            </p>
          </div>
        )}
      </div>

      {/* Recording/Upload Section */}
      <div className="space-y-4">
        {!audioFile ? (
          <div className="grid grid-cols-2 gap-4">
            {/* Record Audio */}
            <motion.button
              onClick={isRecording ? stopRecording : startRecording}
              className={`flex flex-col items-center justify-center p-6 border-2 border-dashed rounded-lg transition-all ${
                isRecording
                  ? "border-red-500 bg-red-50"
                  : "border-gray-300 hover:border-orange-500 hover:bg-orange-50"
              }`}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {isRecording ? (
                <>
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ repeat: Infinity, duration: 1.5 }}
                  >
                    <Mic className="w-12 h-12 text-red-500 mb-3" />
                  </motion.div>
                  <span className="text-sm font-medium text-red-600">
                    Stop Recording
                  </span>
                  <span className="text-xs text-red-500 mt-1">
                    {formatTime(recordingTime)}
                  </span>
                </>
              ) : (
                <>
                  <Mic className="w-12 h-12 text-orange-500 mb-3" />
                  <span className="text-sm font-medium text-gray-900">
                    Record Audio
                  </span>
                  <span className="text-xs text-gray-700 mt-1">
                    Click to start
                  </span>
                </>
              )}
            </motion.button>

            {/* Upload Audio */}
            <motion.button
              onClick={() => fileInputRef.current?.click()}
              className="flex flex-col items-center justify-center p-6 border-2 border-dashed border-gray-300 rounded-lg hover:border-orange-500 hover:bg-orange-50 transition-all"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Upload className="w-12 h-12 text-orange-500 mb-3" />
              <span className="text-sm font-medium text-gray-900">
                Upload Audio
              </span>
              <span className="text-xs text-gray-700 mt-1">MP3, WAV, etc.</span>
            </motion.button>

            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*"
              onChange={handleFileUpload}
              className="hidden"
            />
          </div>
        ) : (
          <AnimatePresence>
            {/* Audio File Preview */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="border-2 border-orange-200 bg-orange-50 rounded-lg p-4"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-orange-500 rounded-lg flex items-center justify-center">
                    <FileAudio className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {audioFile.name}
                    </p>
                    <p className="text-xs text-gray-800">
                      {(audioFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                <button
                  onClick={clearAudio}
                  className="p-2 hover:bg-orange-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-gray-800" />
                </button>
              </div>

              {/* Process Button */}
              <motion.button
                onClick={processAudio}
                disabled={isProcessing}
                className="w-full mt-4 bg-orange-500 text-white py-3 rounded-lg font-medium hover:bg-orange-600 transition-all disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                whileHover={{ scale: isProcessing ? 1 : 1.02 }}
                whileTap={{ scale: isProcessing ? 1 : 0.98 }}
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Processing...
                  </>
                ) : (
                  "Transcribe Audio"
                )}
              </motion.button>
            </motion.div>
          </AnimatePresence>
        )}

        {/* Error Display */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3"
            >
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-red-700">{error}</p>
              </div>
              <button
                onClick={() => setError(null)}
                className="p-1 hover:bg-red-100 rounded transition-colors"
              >
                <X className="w-4 h-4 text-red-500" />
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Success Message Display */}
        <AnimatePresence>
          {successMessage && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3"
            >
              <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-green-700">{successMessage}</p>
              </div>
              <button
                onClick={() => setSuccessMessage(null)}
                className="p-1 hover:bg-green-100 rounded transition-colors"
              >
                <X className="w-4 h-4 text-green-500" />
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Transcription Result */}
        {transcription && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="border border-gray-300 rounded-lg p-4 bg-gray-50"
          >
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-gray-900">
                Transcription
              </h4>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(transcription);
                  setSuccessMessage("Transcription copied to clipboard!");
                  setTimeout(() => setSuccessMessage(null), 3000);
                }}
                className="text-xs text-orange-500 hover:text-orange-600 font-medium"
              >
                Copy
              </button>
            </div>
            <p className="text-sm text-gray-900 leading-relaxed">
              {transcription}
            </p>
          </motion.div>
        )}
      </div>

      {/* Info */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-xs text-blue-800">
          <strong>Note:</strong> Supported formats include MP3, WAV, M4A, and
          more. Maximum file size is 25MB.
        </p>
      </div>
    </div>
  );
}
