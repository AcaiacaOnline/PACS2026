import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import { toast } from 'sonner';

const AuthCallback = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const processSession = async () => {
      try {
        const hash = window.location.hash;
        const params = new URLSearchParams(hash.substring(1));
        const sessionId = params.get('session_id');

        if (!sessionId) {
          throw new Error('No session ID found');
        }

        const response = await api.get('/auth/oauth/session', {
          headers: {
            'X-Session-ID': sessionId
          }
        });

        localStorage.setItem('user', JSON.stringify(response.data));
        
        sessionStorage.setItem('just_authenticated', 'true');
        
        toast.success('Login realizado com sucesso!');
        navigate('/dashboard', { replace: true, state: { user: response.data } });
      } catch (error) {
        console.error('OAuth error:', error);
        toast.error('Erro ao autenticar com Google');
        navigate('/login', { replace: true });
      }
    };

    processSession();
  }, [navigate]);

  return (
    <div className="flex h-screen items-center justify-center bg-background">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
        <p className="mt-4 text-foreground">Processando autenticação...</p>
      </div>
    </div>
  );
};

export default AuthCallback;
