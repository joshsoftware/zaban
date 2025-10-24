'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated } from './auth';

/**
 * Higher-order component to protect routes that require authentication
 * Usage:
 * 
 * export default withAuth(YourProtectedPage);
 */
export function withAuth<P extends object>(
  WrappedComponent: React.ComponentType<P>
) {
  return function ProtectedRoute(props: P) {
    const router = useRouter();
    const [isAuthorized, setIsAuthorized] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
      const checkAuth = () => {
        if (!isAuthenticated()) {
          router.push('/login');
        } else {
          setIsAuthorized(true);
        }
        setIsLoading(false);
      };

      checkAuth();
    }, [router]);

    if (isLoading) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="w-12 h-12 border-4 border-orange-500 border-t-transparent rounded-full animate-spin" />
        </div>
      );
    }

    if (!isAuthorized) {
      return null;
    }

    return <WrappedComponent {...props} />;
  };
}


export function useAuth() {
  const [user, setUser] = useState<{ email: string; name?: string } | null>(null);
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      if (!isAuthenticated()) {
        setUser(null);
        return;
      }

      // Get user info from token
      const { getAccessToken, getUserFromToken } = await import('./auth');
      const token = getAccessToken();
      if (token) {
        const userData = getUserFromToken(token);
        setUser(userData);
      }
    };

    checkAuth();
  }, []);

  const logout = () => {
    const { logout: logoutFn } = require('./auth');
    logoutFn();
  };

  return { user, isAuthenticated: !!user, logout };
}

