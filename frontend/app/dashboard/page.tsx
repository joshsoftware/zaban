'use client';

import { motion } from 'framer-motion';
import { withAuth, useAuth } from '../lib/withAuth';

/**
 * Example protected page using the withAuth HOC
 * This page is only accessible to authenticated users
 */
function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <motion.header
        className="bg-white shadow-sm"
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
          <div className="flex items-center gap-4">
            {user && (
              <div className="text-sm text-gray-600">
                Welcome, <span className="font-medium">{user.email}</span>
              </div>
            )}
            <button
              onClick={logout}
              className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Welcome to Your Dashboard
            </h2>
            <p className="text-gray-600">
              You have successfully logged in using Google SSO. This is a protected page
              that requires authentication.
            </p>
          </div>

          {/* User Info Card */}
          {user && (
            <motion.div
              className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg shadow-md p-6 text-white"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.4, duration: 0.5 }}
            >
              <h3 className="text-lg font-semibold mb-2">Your Account</h3>
              <div className="space-y-2">
                <p>
                  <span className="font-medium">Email:</span> {user.email}
                </p>
                {user.name && (
                  <p>
                    <span className="font-medium">Name:</span> {user.name}
                  </p>
                )}
              </div>
            </motion.div>
          )}
        </motion.div>
      </main>
    </div>
  );
}

// Wrap the component with the authentication HOC
export default withAuth(DashboardPage);



