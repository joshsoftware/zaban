// lib/api-service.ts

const API_BASE_URL = 'http://localhost:8000/api/v1';

export interface APIKey {
  id: string;
  name: string;
  is_active: boolean;
  created_at: string;
  revoked_at: string | null;
}

interface APIKeysResponse {
  api_keys: APIKey[];
  total: number;
}

/**
 * Get stored access token from localStorage
 */
export const getAccessToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('access_token');
  }
  return null;
};

/**
 * Make authenticated API request
 */
const makeAuthenticatedRequest = async (
  endpoint: string,
  options: RequestInit = {}
) => {
  const token = getAccessToken();

  if (!token) {
    throw new Error('No access token found. Please log in.');
  }

  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Unauthorized: Invalid or expired token. Please log in again.');
    }
    if (response.status === 404) {
      throw new Error('Resource not found.');
    }
    throw new Error(`Request failed: ${response.statusText}`);
  }

  return response;
};

/**
 * Fetch all API keys for the current user
 */
export const fetchAPIKeys = async (): Promise<APIKey[]> => {
  try {
    const response = await makeAuthenticatedRequest('/api-keys');
    const data: APIKeysResponse = await response.json();
    return data.api_keys || [];
  } catch (error) {
    console.error('Error fetching API keys:', error);
    throw error;
  }
};

/**
 * Delete an API key by ID
 * @param apiKeyId - The ID of the API key to delete
 */
export const deleteAPIKey = async (apiKeyId: string): Promise<void> => {
  try {
    await makeAuthenticatedRequest(`/api-keys/${apiKeyId}`, {
      method: 'DELETE',
    });
  } catch (error) {
    console.error(`Error deleting API key ${apiKeyId}:`, error);
    throw error;
  }
};