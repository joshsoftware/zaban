import { config } from './config';

export interface AuthTokens {
  access_token: string;
  token_type: string;
  expires_in: number | null;
}

export interface User {
  email: string;
  name?: string;
}

// Store tokens in localStorage
export const setAuthTokens = (tokens: AuthTokens): void => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('access_token', tokens.access_token);
    localStorage.setItem('token_type', tokens.token_type);
    if (tokens.expires_in) {
      const expiresAt = Date.now() + tokens.expires_in * 1000;
      localStorage.setItem('expires_at', expiresAt.toString());
    }
  }
};

// Get stored access token
export const getAccessToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('access_token');
  }
  return null;
};

// Check if user is authenticated
export const isAuthenticated = (): boolean => {
  const token = getAccessToken();
  if (!token) return false;
  
  const expiresAt = localStorage.getItem('expires_at');
  if (expiresAt && Date.now() > parseInt(expiresAt)) {
    clearAuthTokens();
    return false;
  }
  
  return true;
};

// Clear authentication tokens
export const clearAuthTokens = (): void => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('access_token');
    localStorage.removeItem('token_type');
    localStorage.removeItem('expires_at');
  }
};

// Initiate Google OAuth flow
export const initiateGoogleLogin = (): void => {
  // Validate that client_id is configured
  if (!config.google.clientId) {
    alert('Google Sign-In is not configured properly. Please check your environment variables.');
    return;
  }
  
  const googleAuthUrl = 'https://accounts.google.com/o/oauth2/v2/auth';
  const params = new URLSearchParams({
    client_id: config.google.clientId,
    redirect_uri: config.google.redirectUri,
    response_type: 'code',
    scope: 'openid email profile',
    access_type: 'offline',
    prompt: 'consent',
  });

  const authUrl = `${googleAuthUrl}?${params.toString()}`;
  window.location.href = authUrl;
};

// Exchange auth code for access token
export const exchangeGoogleCode = async (code: string): Promise<AuthTokens> => {
  const response = await fetch(`${config.api.baseUrl}/api/v1/auth/google/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      code: code,
      redirect_uri: config.google.redirectUri,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to authenticate with Google');
  }

  const tokens: AuthTokens = await response.json();
  setAuthTokens(tokens);
  return tokens;
};

// Decode JWT token to get user info (simple implementation)
export const getUserFromToken = (token: string): User | null => {
  try {
    const payload = token.split('.')[1];
    const decoded = JSON.parse(atob(payload));
    return {
      email: decoded.sub || '',
      name: decoded.name || '',
    };
  } catch {
    return null;
  }
};

// Logout user
export const logout = (): void => {
  clearAuthTokens();
  window.location.href = '/login';
};

