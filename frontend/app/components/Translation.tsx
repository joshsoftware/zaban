'use client';

import { useState } from 'react';
import { Languages, Loader2, Copy, Check, ArrowRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { translateText, type TranslationResponse } from '../lib/api-service';

// Common language codes for Indian languages
const LANGUAGE_OPTIONS = [
  { code: 'eng_Latn', name: 'English' },
  { code: 'hin_Deva', name: 'Hindi' },
  { code: 'ben_Beng', name: 'Bengali' },
  { code: 'tel_Telu', name: 'Telugu' },
  { code: 'tam_Taml', name: 'Tamil' },
  { code: 'guj_Gujr', name: 'Gujarati' },
  { code: 'kan_Knda', name: 'Kannada' },
  { code: 'mal_Mlym', name: 'Malayalam' },
  { code: 'mar_Deva', name: 'Marathi' },
  { code: 'pan_Guru', name: 'Punjabi' },
  { code: 'ory_Orya', name: 'Oriya' },
  { code: 'asm_Beng', name: 'Assamese' },
  { code: 'urd_Arab', name: 'Urdu' },
  { code: 'npi_Deva', name: 'Nepali' },
  { code: 'san_Deva', name: 'Sanskrit' },
];

export default function Translation() {
  const [inputText, setInputText] = useState('');
  const [sourceLang, setSourceLang] = useState<string>('');
  const [targetLang, setTargetLang] = useState<string>('hin_Deva');
  const [autoDetect, setAutoDetect] = useState(true);
  const [translation, setTranslation] = useState<TranslationResponse | null>(null);
  const [isTranslating, setIsTranslating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleTranslate = async () => {
    if (!inputText.trim()) {
      setError('Please enter text to translate');
      return;
    }

    if (!targetLang) {
      setError('Please select target language');
      return;
    }

    setIsTranslating(true);
    setError(null);
    setTranslation(null);

    try {
      const result = await translateText(
        inputText,
        targetLang,
        autoDetect ? undefined : sourceLang,
        autoDetect
      );
      setTranslation(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Translation failed. Please try again.';
      setError(errorMessage);
      console.error('Translation error:', err);
    } finally {
      setIsTranslating(false);
    }
  };

  const handleCopy = async () => {
    if (!translation?.translated_text) return;

    try {
      await navigator.clipboard.writeText(translation.translated_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  const swapLanguages = () => {
    if (translation) {
      setInputText(translation.translated_text);
      setSourceLang(targetLang);
      setTargetLang(translation.source_lang);
      setTranslation(null);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-semibold text-gray-900">Translation</h3>
          <p className="text-sm text-gray-800 mt-1">Translate text between multiple languages</p>
        </div>
      </div>

      <div className="space-y-6">
        {/* Language Selection */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Source Language {autoDetect && <span className="text-orange-500">(Auto-detect)</span>}
            </label>
            <select
              value={sourceLang}
              onChange={(e) => setSourceLang(e.target.value)}
              disabled={autoDetect}
              className={`w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all ${
                autoDetect ? 'bg-gray-100 text-gray-500 cursor-not-allowed' : 'bg-white'
              }`}
            >
              <option value="">Auto-detect</option>
              {LANGUAGE_OPTIONS.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.name}
                </option>
              ))}
            </select>
            <label className="flex items-center gap-2 mt-2 text-sm text-gray-800">
              <input
                type="checkbox"
                checked={autoDetect}
                onChange={(e) => setAutoDetect(e.target.checked)}
                className="rounded border-gray-300 text-orange-500 focus:ring-orange-500"
              />
              Auto-detect source language
            </label>
          </div>

          <div className="flex items-end justify-center">
            <button
              onClick={swapLanguages}
              disabled={!translation}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Swap languages"
            >
              <ArrowRight className="w-5 h-5 text-gray-600" />
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Target Language <span className="text-red-500">*</span>
            </label>
            <select
              value={targetLang}
              onChange={(e) => setTargetLang(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all bg-white"
            >
              {LANGUAGE_OPTIONS.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Input Section */}
        <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Text to Translate <span className="text-red-500">*</span>
            </label>
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Enter text to translate..."
            rows={6}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all resize-none"
          />
          <div className="flex justify-between items-center mt-2">
            <p className="text-xs text-gray-700">
              {inputText.length} characters
            </p>
            <button
              onClick={() => setInputText('')}
              className="text-xs text-gray-500 hover:text-gray-700"
            >
              Clear
            </button>
          </div>
        </div>

        {/* Translate Button */}
        <motion.button
          onClick={handleTranslate}
          disabled={!inputText.trim() || !targetLang || isTranslating}
          className="w-full bg-orange-500 text-white py-3 rounded-lg font-medium hover:bg-orange-600 transition-all disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          whileHover={{ scale: isTranslating ? 1 : 1.02 }}
          whileTap={{ scale: isTranslating ? 1 : 0.98 }}
        >
          {isTranslating ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Translating...
            </>
          ) : (
            <>
              <Languages className="w-5 h-5" />
              Translate
            </>
          )}
        </motion.button>

        {/* Error Display */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="p-4 bg-red-50 border border-red-200 rounded-lg"
            >
              <p className="text-sm text-red-700">{error}</p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Translation Result */}
        <AnimatePresence>
          {translation && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="border border-gray-300 rounded-lg p-4 bg-gray-50"
            >
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h4 className="text-sm font-semibold text-gray-900">Translation</h4>
                  {translation.auto_detected && (
              <p className="text-xs text-gray-800 mt-1">
                Detected source: {LANGUAGE_OPTIONS.find(l => l.code === translation.source_lang)?.name || translation.source_lang}
              </p>
                  )}
                </div>
                <button
                  onClick={handleCopy}
                  className="inline-flex items-center gap-2 px-3 py-1 text-sm text-orange-500 hover:bg-orange-50 rounded-lg transition-colors"
                >
                  {copied ? (
                    <>
                      <Check className="w-4 h-4" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4" />
                      Copy
                    </>
                  )}
                </button>
              </div>
              <p className="text-sm text-gray-900 leading-relaxed whitespace-pre-wrap">
                {translation.translated_text}
              </p>
              {translation.model && (
                <p className="text-xs text-gray-700 mt-3">
                  Model: {translation.model}
                </p>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Sample Format Info */}
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-xs text-blue-800">
            <strong>Note:</strong> Language codes follow BCP-47 format with script (e.g., eng_Latn, hin_Deva). 
            Auto-detection is enabled by default. You can disable it to manually select the source language.
          </p>
        </div>
      </div>
    </div>
  );
}

