'use client';

import { motion } from 'framer-motion';
import Image from 'next/image';
import Link from 'next/link';
import { useState } from 'react';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement password reset email logic
    setIsSubmitted(true);
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Section - Orange Gradient Background */}
      <motion.div 
        className="w-3/5 bg-gradient-to-b from-orange-600 to-orange-400 flex items-center justify-center relative"
        initial={{ opacity: 0, x: -50 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      >
        {/* Josh Logo */}
        <motion.div 
          className="flex items-center justify-center"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.6, ease: "easeOut" }}
        >
          <Image
            src="/assets/josh_logo.png"
            alt="Josh Logo"
            width={200}
            height={80}
            className="object-contain"
          />
        </motion.div>
      </motion.div>

      {/* Right Section - Forgot Password Form */}
      <motion.div 
        className="w-3/5 bg-gray-50 flex flex-col justify-center p-12"
        initial={{ opacity: 0, x: 50 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      >
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.6 }}
        >
          <div className="max-w-md mx-auto">
            {!isSubmitted ? (
              <>
                {/* Header */}
                <div className="text-center mb-8">
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Forgot Password?</h1>
                  <p className="text-gray-700">No worries, we&apos;ll send you reset instructions</p>
                </div>

                {/* Forgot Password Form */}
                <motion.form 
                  onSubmit={handleSubmit}
                  className="space-y-6"
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.6, duration: 0.6 }}
                >
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-900 mb-2">
                      Email Address
                    </label>
                    <motion.input
                      type="email"
                      id="email"
                      name="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all duration-200 text-gray-900 placeholder:text-gray-500"
                      placeholder="Enter your email"
                      whileFocus={{ scale: 1.02 }}
                      required
                    />
                  </div>

                  <motion.button
                    type="submit"
                    className="w-full bg-orange-500 text-white py-3 rounded-lg font-medium hover:bg-orange-600 transition-all duration-200"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    Reset Password
                  </motion.button>
                </motion.form>
              </>
            ) : (
              <>
                {/* Success Message */}
                <motion.div
                  className="text-center"
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.5 }}
                >
                  <div className="mb-6 flex justify-center">
                    <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                      <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  </div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Check Your Email</h1>
                  <p className="text-gray-700 mb-6">
                    We&apos;ve sent password reset instructions to <span className="font-medium text-gray-900">{email}</span>
                  </p>
                  <p className="text-sm text-gray-600 mb-8">
                    Didn&apos;t receive the email? Check your spam folder or{' '}
                    <button 
                      onClick={() => setIsSubmitted(false)} 
                      className="text-orange-500 hover:text-orange-600 font-medium transition-colors"
                    >
                      try another email address
                    </button>
                  </p>
                </motion.div>
              </>
            )}

            {/* Back to Login Link */}
            <motion.div 
              className="text-center mt-8"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8, duration: 0.6 }}
            >
              <Link 
                href="/login" 
                className="inline-flex items-center text-gray-700 hover:text-orange-500 font-medium transition-colors"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Login
              </Link>
            </motion.div>
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
}