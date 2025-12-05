export const config = {
  google: {
    clientId: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "",
    clientSecret: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_SECRET || "",
    redirectUri:
      process.env.NEXT_PUBLIC_GOOGLE_REDIRECT_URI ||
      "http://localhost:3000/auth/callback",
    allowedDomains: process.env.NEXT_PUBLIC_ALLOWED_SSO_DOMAINS?.split(",") || [
      "joshsoftware.com",
    ],
  },
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
  },
};
