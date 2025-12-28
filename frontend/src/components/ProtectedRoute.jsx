import React, { useState, useEffect, useRef } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import api from '../utils/api';

const ProtectedRoute = ({ children }) => {
  const location = useLocation();
  const [isAuthenticated, setIsAuthenticated] = useState(
    location.state?.user ? true : null
  );
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    
    const checkAuth = async () => {
      if (location.state?.user) {
        return;
      }

      const token = localStorage.getItem('token');
      const authType = localStorage.getItem('auth_type');
      const hasUser = localStorage.getItem('user');
      
      // Se não tem token E não tem OAuth E não tem usuário, não está autenticado
      if (!token && authType !== 'oauth' && !hasUser) {
        if (isMounted.current) {
          setIsAuthenticated(false);
        }
        return;
      }

      const justAuth = sessionStorage.getItem('just_authenticated');
      if (!justAuth) {
        await new Promise(r => setTimeout(r, 150));
      } else {
        sessionStorage.removeItem('just_authenticated');
      }

      try {
        // Verificar autenticação no backend
        // O backend aceitará tanto token Bearer quanto cookie session_token
        await api.get('/auth/me');
        if (isMounted.current) {
          setIsAuthenticated(true);
        }
      } catch (error) {
        if (isMounted.current) {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          localStorage.removeItem('auth_type');
          setIsAuthenticated(false);
        }
      }
    };

    checkAuth();

    return () => {
      isMounted.current = false;
    };
  }, [location.state]);

  if (isAuthenticated === null) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-gray-600">Verificando autenticação...</p>
        </div>
      </div>
    );
  }

  if (isAuthenticated === false) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default ProtectedRoute;
