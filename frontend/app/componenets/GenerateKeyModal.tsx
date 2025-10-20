'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';

interface GenerateKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onKeyGenerated: (name: string, key: string) => void;
}

export default function GenerateKeyModal({ 
  isOpen, 
  onClose, 
  onKeyGenerated 
}: GenerateKeyModalProps) {
  const [keyName, setKeyName] = useState('');
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);
  const [isCopied, setIsCopied] = useState(false);

  const generateAPIKey = (): string => {
    const randomString = () => Math.random().toString(36).substring(2, 15);
    return `josh_${randomString()}${randomString()}`;
  };

  const handleCreateKey = () => {
    if (!keyName.trim()) return;

    const newKey = generateAPIKey();
    setGeneratedKey(newKey);
    onKeyGenerated(keyName, newKey);
  };

  const handleCopyToClipboard = async () => {
    if (!generatedKey) return;

    try {
      await navigator.clipboard.writeText(generatedKey);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  const handleClose = () => {
    setKeyName('');
    setGeneratedKey(null);
    setIsCopied(false);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {/* Backdrop */}
      <motion.div
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={handleClose}
      />

      {/* Modal */}
      <motion.div
        className="fixed inset-0 flex items-center justify-center z-50 p-4"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        transition={{ duration: 0.2 }}
      >
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          {!generatedKey ? (
            <CreateKeyForm
              keyName={keyName}
              onKeyNameChange={setKeyName}
              onCreate={handleCreateKey}
              onCancel={handleClose}
            />
          ) : (
            <KeyGeneratedSuccess
              generatedKey={generatedKey}
              isCopied={isCopied}
              onCopy={handleCopyToClipboard}
              onDone={handleClose}
            />
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

// Sub-component: Create Key Form
interface CreateKeyFormProps {
  keyName: string;
  onKeyNameChange: (value: string) => void;
  onCreate: () => void;
  onCancel: () => void;
}

function CreateKeyForm({ 
  keyName, 
  onKeyNameChange, 
  onCreate, 
  onCancel 
}: CreateKeyFormProps) {
  return (
    <>
      <h3 className="text-xl font-bold text-gray-900 mb-4">
        Create API Key
      </h3>
      
      <div className="mb-6">
        <label 
          htmlFor="keyName" 
          className="block text-sm font-medium text-gray-900 mb-2"
        >
          Name this key
        </label>
        <input
          type="text"
          id="keyName"
          value={keyName}
          onChange={(e) => onKeyNameChange(e.target.value)}
          placeholder="e.g., Production API Key"
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all text-gray-900 placeholder:text-gray-500"
          autoFocus
        />
      </div>

      <div className="flex gap-3">
        <button
          onClick={onCancel}
          className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={onCreate}
          disabled={!keyName.trim()}
          className="flex-1 px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          Create
        </button>
      </div>
    </>
  );
}

// Sub-component: Key Generated Success
interface KeyGeneratedSuccessProps {
  generatedKey: string;
  isCopied: boolean;
  onCopy: () => void;
  onDone: () => void;
}

function KeyGeneratedSuccess({ 
  generatedKey, 
  isCopied, 
  onCopy, 
  onDone 
}: KeyGeneratedSuccessProps) {
  return (
    <>
      <div className="text-center mb-6">
        <SuccessIcon />
        <h3 className="text-xl font-bold text-gray-900 mb-2">
          API Key Generated!
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          Copy your API key now. You won&apos;t be able to see it again.
        </p>
      </div>

      <div className="bg-gray-50 rounded-lg p-4 mb-6">
        <div className="flex items-center justify-between gap-3">
          <code className="text-sm text-gray-900 font-mono break-all flex-1">
            {generatedKey}
          </code>
          <button
            onClick={onCopy}
            className="p-2 text-orange-500 hover:bg-orange-50 rounded-lg transition-colors flex-shrink-0"
            title={isCopied ? 'Copied!' : 'Copy to clipboard'}
          >
            {isCopied ? <CheckIcon /> : <CopyIcon />}
          </button>
        </div>
      </div>

      <button
        onClick={onDone}
        className="w-full px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
      >
        Done
      </button>
    </>
  );
}

// Icon Components
function SuccessIcon() {
  return (
    <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
      <svg 
        className="w-6 h-6 text-green-500" 
        fill="none" 
        stroke="currentColor" 
        viewBox="0 0 24 24"
      >
        <path 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          strokeWidth={2} 
          d="M5 13l4 4L19 7" 
        />
      </svg>
    </div>
  );
}

function CopyIcon() {
  return (
    <svg 
      className="w-5 h-5" 
      fill="none" 
      stroke="currentColor" 
      viewBox="0 0 24 24"
    >
      <path 
        strokeLinecap="round" 
        strokeLinejoin="round" 
        strokeWidth={2} 
        d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" 
      />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg 
      className="w-5 h-5" 
      fill="none" 
      stroke="currentColor" 
      viewBox="0 0 24 24"
    >
      <path 
        strokeLinecap="round" 
        strokeLinejoin="round" 
        strokeWidth={2} 
        d="M5 13l4 4L19 7" 
      />
    </svg>
  );
}