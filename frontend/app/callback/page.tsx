'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { exchangeGoogleCode } from '../lib/auth';
import { motion } from 'framer-motion';

export default function CallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(true);

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code');
      const errorParam = searchParams.get('error');

      if (errorParam) {
        setError('Authentication failed. Please try again.');
        setIsProcessing(false);
        setTimeout(() => router.push('/login'), 3000);
        return;
      }

      if (!code) {
        setError('No authorization code received.');
        setIsProcessing(false);
        setTimeout(() => router.push('/login'), 3000);
        return;
      }

      try {
        await exchangeGoogleCode(code);
        // Successfully authenticated, redirect to dashboard
        router.push('/dashboard');
      } catch {
        setError('Failed to complete authentication. Please try again.');
        setIsProcessing(false);
        setTimeout(() => router.push('/login'), 3000);
      }
    };

    handleCallback();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-orange-600 to-orange-400">
      <motion.div
        className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full text-center"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        {isProcessing && !error ? (
          <>
            <motion.div
              className="w-16 h-16 border-4 border-orange-500 border-t-transparent rounded-full mx-auto mb-4"
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            />
            <h2 className="text-2xl font-bold text-gray-800 mb-2">
              Authenticating...
            </h2>
            <p className="text-gray-600">
              Please wait while we complete your sign-in
            </p>
          </>
        ) : error ? (
          <>
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-red-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">
              Authentication Failed
            </h2>
            <p className="text-gray-600 mb-4">{error}</p>
            <p className="text-sm text-gray-500">
              Redirecting to login page...
            </p>
          </>
        ) : null}
      </motion.div>
    </div>
  );
}

