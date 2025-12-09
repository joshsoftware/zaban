"use client";

import { motion } from "framer-motion";
import { withAuth, useAuth } from "../lib/withAuth";
import { useState } from "react";
import {
  LayoutDashboard,
  KeyRound,
  LogOut,
  Mic,
  Languages,
  Settings,
  Volume2,
} from "lucide-react";
import GenerateKeyModal from "../components/GenerateKeyModal";
import APIKeysTable from "../components/APIKeysTable";
import SpeechToText from "../components/SpeechToText";
import Translation from "../components/Translation";
import TextToSpeech from "../components/TextToSpeech";
import ApiKeySettings from "../components/ApiKeySettings";

type TabType =
  | "overview"
  | "api-keys"
  | "speech-to-text"
  | "translation"
  | "text-to-speech";

function DashboardPage() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>("overview");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const handleKeyGenerated = () => {
    // API key generation handled by GenerateKeyModal component
    // The APIKeysTable will refresh automatically after generation
  };

  const handleTranscriptionComplete = (text: string) => {
    console.log("Transcription:", text);
    // Handle transcription result (e.g., save to database, display notification)
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
              onClick={() => setActiveTab("overview")}
              className={`flex items-center w-full gap-3 px-4 py-2 text-gray-900 rounded-md hover:bg-orange-100 transition ${
                activeTab === "overview" ? "bg-orange-100 text-orange-600" : ""
              }`}
            >
              <LayoutDashboard className="h-5 w-5 text-orange-500" />
              Overview
            </button>

            <button
              onClick={() => setActiveTab("speech-to-text")}
              className={`flex items-center w-full gap-3 px-4 py-2 text-gray-900 rounded-md hover:bg-orange-100 transition ${
                activeTab === "speech-to-text"
                  ? "bg-orange-100 text-orange-600"
                  : ""
              }`}
            >
              <Mic className="h-5 w-5 text-orange-500" />
              Speech to Text
            </button>

            <button
              onClick={() => setActiveTab("translation")}
              className={`flex items-center w-full gap-3 px-4 py-2 text-gray-900 rounded-md hover:bg-orange-100 transition ${
                activeTab === "translation"
                  ? "bg-orange-100 text-orange-600"
                  : ""
              }`}
            >
              <Languages className="h-5 w-5 text-orange-500" />
              Translation
            </button>

            <button
              onClick={() => setActiveTab("text-to-speech")}
              className={`flex items-center w-full gap-3 px-4 py-2 text-gray-900 rounded-md hover:bg-orange-100 transition ${
                activeTab === "text-to-speech"
                  ? "bg-orange-100 text-orange-600"
                  : ""
              }`}
            >
              <Volume2 className="h-5 w-5 text-orange-500" />
              Text to Speech
            </button>

            <button
              onClick={() => setActiveTab("api-keys")}
              className={`flex items-center w-full gap-3 px-4 py-2 text-gray-900 rounded-md hover:bg-orange-100 transition ${
                activeTab === "api-keys" ? "bg-orange-100 text-orange-600" : ""
              }`}
            >
              <KeyRound className="h-5 w-5 text-orange-500" />
              API Keys
            </button>

            <button
              onClick={() => setIsModalOpen(true)}
              className="flex items-center w-full gap-3 px-4 py-2 text-gray-900 rounded-md hover:bg-orange-100 transition"
            >
              <KeyRound className="h-5 w-5 text-orange-500" />
              Generate Key
            </button>
          </nav>
        </div>

        <div className="p-4 border-t space-y-2">
          <button
            onClick={() => setIsSettingsOpen(true)}
            className="flex items-center w-full gap-3 px-4 py-2 text-gray-900 rounded-md hover:bg-orange-100 transition"
          >
            <Settings className="h-5 w-5 text-orange-500" />
            API Key Settings
          </button>
          <button
            onClick={logout}
            className="flex items-center w-full gap-3 px-4 py-2 text-gray-900 rounded-md hover:bg-orange-100 transition"
          >
            <LogOut className="h-5 w-5 text-orange-500" />
            Logout
          </button>
        </div>
      </motion.aside>

      {/* Main Content */}
      <div className="flex-1">
        <main className="px-6 py-8">
          {activeTab === "overview" && <OverviewTab user={user} />}
          {activeTab === "speech-to-text" && (
            <SpeechToTextTab
              onTranscriptionComplete={handleTranscriptionComplete}
            />
          )}
          {activeTab === "translation" && <TranslationTab />}
          {activeTab === "text-to-speech" && <TextToSpeechTab />}
          {activeTab === "api-keys" && <APIKeysTab />}
        </main>
      </div>

      <GenerateKeyModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onKeyGenerated={handleKeyGenerated}
      />
      <ApiKeySettings
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </div>
  );
}

export default withAuth(DashboardPage);

/* ========== SUB COMPONENTS ========== */

function OverviewTab({
  user,
}: {
  user: { email: string; name?: string } | null;
}) {
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
        <p className="text-gray-800">
          You have successfully logged in using Google SSO. This is a protected
          page that requires authentication.
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

function SpeechToTextTab({
  onTranscriptionComplete,
}: {
  onTranscriptionComplete: (text: string) => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <SpeechToText onTranscriptionComplete={onTranscriptionComplete} />
    </motion.div>
  );
}

function TranslationTab() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Translation />
    </motion.div>
  );
}

function TextToSpeechTab() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <TextToSpeech />
    </motion.div>
  );
}

function APIKeysTab() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">API Keys</h2>
      </div>
      <APIKeysTable />
    </motion.div>
  );
}
