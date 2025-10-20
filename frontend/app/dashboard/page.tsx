'use client';

import { motion } from 'framer-motion';
import { withAuth, useAuth } from '../lib/withAuth';
import { useState } from 'react';
import { LayoutDashboard, KeyRound, LogOut } from 'lucide-react';
import GenerateKeyModal from '../componenets/GenerateKeyModal';
import APIKeysTable, { APIKey } from '../componenets/APIKeysTable';

type TabType = 'overview' | 'api-keys';

function DashboardPage() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);

  const handleKeyGenerated = (name: string, key: string) => {
    const maskedKey = `${key.substring(0, 12)}${'•'.repeat(20)}`;
    const newApiKey: APIKey = {
      id: Date.now().toString(),
      name,
      key,
      maskedKey,
      createdAt: new Date(),
    };
    setApiKeys((prev) => [...prev, newApiKey]);
  };

  return (
    <div className="min-h-screen flex bg-gray-50">
      {/* Sidebar */}
      <motion.aside
        className="w-64 bg-white shadow-md flex flex-col justify-between"
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
      >
        <div>
          <div className="p-6 border-b">
            <h1 className="text-xl font-bold text-orange-500">Zabaan</h1>
          </div>

          <nav className="p-4 space-y-2">
            <button
              onClick={() => setActiveTab('overview')}
              className={`flex items-center w-full gap-3 px-4 py-2 text-gray-700 rounded-md hover:bg-orange-100 transition ${
                activeTab === 'overview' ? 'bg-orange-100 text-orange-600' : ''
              }`}
            >
              <LayoutDashboard className="h-5 w-5 text-orange-500" />
              Overview
            </button>

            <button
              onClick={() => setActiveTab('api-keys')}
              className={`flex items-center w-full gap-3 px-4 py-2 text-gray-700 rounded-md hover:bg-orange-100 transition ${
                activeTab === 'api-keys' ? 'bg-orange-100 text-orange-600' : ''
              }`}
            >
              <KeyRound className="h-5 w-5 text-orange-500" />
              API Keys
            </button>

            <button
              onClick={() => setIsModalOpen(true)}
              className="flex items-center w-full gap-3 px-4 py-2 text-gray-700 rounded-md hover:bg-orange-100 transition"
            >
              <KeyRound className="h-5 w-5 text-orange-500" />
              Generate Key
            </button>
          </nav>
        </div>

        <div className="p-4 border-t">
          <button
            onClick={logout}
            className="flex items-center w-full gap-3 px-4 py-2 text-gray-700 rounded-md hover:bg-orange-100 transition"
          >
            <LogOut className="h-5 w-5 text-orange-500" />
            Logout
          </button>
        </div>
      </motion.aside>

      {/* Main Content */}
      <div className="flex-1">
        <main className="px-6 py-8">
          {activeTab === 'overview' ? (
            <OverviewTab user={user} />
          ) : (
            <APIKeysTab apiKeys={apiKeys} />
          )}
        </main>
      </div>

      <GenerateKeyModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onKeyGenerated={handleKeyGenerated}
      />
    </div>
  );
}

export default withAuth(DashboardPage);

/* ========== SUB COMPONENTS ========== */

function OverviewTab({ user }: { user: any }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">
          Welcome to Your Dashboard
        </h2>
        <p className="text-gray-600">
          You have successfully logged in using Google SSO. This is a protected page that
          requires authentication.
        </p>
      </div>

      {user && (
        <motion.div
          className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg shadow-md p-6 text-white"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
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
  );
}

function APIKeysTab({ apiKeys }: { apiKeys: APIKey[] }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">API Keys</h2>
      </div>
      <APIKeysTable apiKeys={apiKeys} />
    </motion.div>
  );
}
