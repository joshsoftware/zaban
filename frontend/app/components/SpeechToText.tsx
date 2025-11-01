'use client';

import { useState, useRef } from 'react';
import { Mic, Upload, X, Loader2, FileAudio } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface SpeechToTextProps {
  onTranscriptionComplete?: (text: string) => void;
}

export default function SpeechToText({ onTranscriptionComplete }: SpeechToTextProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [transcription, setTranscription] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  
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
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const audioFile = new File([audioBlob], 'recording.wav', { type: 'audio/wav' });
        setAudioFile(audioFile);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Unable to access microphone. Please grant permission.');
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
      if (!file.type.startsWith('audio/')) {
        alert('Please upload an audio file');
        return;
      }
      setAudioFile(file);
    }
  };

  // Process Audio (Send to API)
  const processAudio = async () => {
    if (!audioFile) return;

    setIsProcessing(true);
    
    try {
      // TODO: Replace with your actual API endpoint
      // const formData = new FormData();
      // formData.append('audio', audioFile);
      // const response = await fetch('/api/speech-to-text', {
      //   method: 'POST',
      //   body: formData,
      // });
      // const data = await response.json();
      // const text = data.transcription;

      // Mock transcription for demo
      await new Promise(resolve => setTimeout(resolve, 2000));
      const mockText = 'This is a sample transcription of your audio. Replace this with actual API call.';
      
      setTranscription(mockText);
      onTranscriptionComplete?.(mockText);
    } catch (error) {
      console.error('Error processing audio:', error);
      alert('Failed to process audio. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  // Clear Audio
  const clearAudio = () => {
    setAudioFile(null);
    setTranscription('');
    setRecordingTime(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Format time (seconds to MM:SS)
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-semibold text-gray-900">Speech to Text</h3>
          <p className="text-sm text-gray-600 mt-1">Record or upload audio to transcribe</p>
        </div>
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
                  ? 'border-red-500 bg-red-50'
                  : 'border-gray-300 hover:border-orange-500 hover:bg-orange-50'
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
                  <span className="text-sm font-medium text-red-600">Stop Recording</span>
                  <span className="text-xs text-red-500 mt-1">{formatTime(recordingTime)}</span>
                </>
              ) : (
                <>
                  <Mic className="w-12 h-12 text-orange-500 mb-3" />
                  <span className="text-sm font-medium text-gray-700">Record Audio</span>
                  <span className="text-xs text-gray-500 mt-1">Click to start</span>
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
              <span className="text-sm font-medium text-gray-700">Upload Audio</span>
              <span className="text-xs text-gray-500 mt-1">MP3, WAV, etc.</span>
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
                    <p className="text-sm font-medium text-gray-900">{audioFile.name}</p>
                    <p className="text-xs text-gray-600">
                      {(audioFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                <button
                  onClick={clearAudio}
                  className="p-2 hover:bg-orange-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-gray-600" />
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
                  'Transcribe Audio'
                )}
              </motion.button>
            </motion.div>
          </AnimatePresence>
        )}

        {/* Transcription Result */}
        {transcription && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="border border-gray-300 rounded-lg p-4 bg-gray-50"
          >
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-gray-900">Transcription</h4>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(transcription);
                  alert('Copied to clipboard!');
                }}
                className="text-xs text-orange-500 hover:text-orange-600 font-medium"
              >
                Copy
              </button>
            </div>
            <p className="text-sm text-gray-700 leading-relaxed">{transcription}</p>
          </motion.div>
        )}
      </div>

      {/* Info */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-xs text-blue-800">
          <strong>Note:</strong> Supported formats include MP3, WAV, M4A, and more. Maximum file size is 25MB.
        </p>
      </div>
    </div>
  );
}