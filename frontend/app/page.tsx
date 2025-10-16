import Image from "next/image";
import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen flex">
      {/* Left Section - Orange Gradient Background */}
      <div className="w-3/5 bg-gradient-to-b from-orange-600 to-orange-400 flex items-center justify-center relative">
        {/* Josh Logo */}
        <div className="w-56 h-24 bg-white rounded-lg flex items-center justify-center shadow-lg p-4">
          <Image
            src="/assets/josh_logo.png"
            alt="Josh Logo"
            width={96}
            height={96}
            className="object-contain"
          />
        </div>
      </div>

      {/* Right Section - Main Content */}
      <div className="w-3/5 bg-gray-50 flex flex-col justify-between p-12">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <h1 className="text-3xl font-bold text-gray-800">Josh</h1>
          <div className="w-px h-8 bg-gray-300"></div>
          <span className="text-gray-500">API Dashboard</span>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col justify-center">
          <div className="mb-12">
            <h2 className="text-4xl font-light text-gray-600 mb-4">
              Unlock the power of AI
            </h2>
            <h3 className="text-4xl font-bold text-gray-800">
              with Josh
            </h3>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4 mb-8">
          <Link 
              href="/login"
              className="bg-orange-500 text-white px-8 py-3 rounded-lg hover:bg-orange-600 transition-colors font-medium"
            >
              Login
            </Link>
            <Link 
              href="/signup"
              className="border border-orange-500 text-orange-500 px-8 py-3 rounded-lg hover:bg-orange-50 transition-colors font-medium"
            >
              Sign Up
            </Link>

          </div>
         
          </div>

          {/* Login and Signup Buttons */}
          <div className="flex gap-4">
         
          </div>

        {/* Footer */}
        <div className="text-sm text-gray-400">
          By signing in, you agree to our{" "}
          <a href="#" className="underline hover:text-gray-600">
            privacy policy
          </a>
          .
        </div>
      </div>
    </div>
  );
}
