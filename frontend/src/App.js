import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import PACList from './pages/PACList';
import PACEditor from './pages/PACEditor';
import PACGeralList from './pages/PACGeralList';
import PACGeralEditor from './pages/PACGeralEditor';
import GestaoProcessual from './pages/GestaoProcessual';
import DashboardProcessual from './pages/DashboardProcessual';
import Users from './pages/Users';
import Backup from './pages/Backup';
import PortalPublico from './pages/PortalPublico';
import DOEM from './pages/DOEM';
import DOEMPublico from './pages/DOEMPublico';
import ProtectedRoute from './components/ProtectedRoute';
import { Toaster } from './components/ui/sonner';
import api from './utils/api';
import { toast } from 'sonner';
import './App.css';

// Componente para processar OAuth callback
const OAuthCallback = () => {
  const navigate = useNavigate();
  const [processing, setProcessing] = useState(true);

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
          },
          withCredentials: true
        });

        // Salvar dados do usuário e token
        localStorage.setItem('user', JSON.stringify(response.data));
        localStorage.setItem('auth_type', 'oauth');
        
        // Se houver token na resposta, salvar
        if (response.data.token) {
          localStorage.setItem('token', response.data.token);
        }
        
        // Limpar o hash da URL
        window.history.replaceState(null, '', window.location.pathname);
        
        toast.success('Login realizado com sucesso!');
        navigate('/dashboard', { replace: true });
      } catch (error) {
        console.error('OAuth error:', error);
        toast.error('Erro ao autenticar com Google');
        navigate('/login', { replace: true });
      } finally {
        setProcessing(false);
      }
    };

    processSession();
  }, [navigate]);

  if (processing) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-foreground">Processando autenticação...</p>
        </div>
      </div>
    );
  }

  return null;
};

// Wrapper para detectar OAuth callback
const AppRoutes = () => {
  // Verificar se é um callback OAuth
  const isOAuthCallback = window.location.hash && window.location.hash.includes('session_id=');

  if (isOAuthCallback) {
    return <OAuthCallback />;
  }

  return (
    <Routes>
      {/* Rota Pública - Portal de Transparência (PÁGINA INICIAL) */}
      <Route path="/" element={<PortalPublico />} />
      <Route path="/transparencia" element={<PortalPublico />} />
      
      {/* Rotas Protegidas */}
      <Route path="/login" element={<Login />} />
      <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/pacs" element={<ProtectedRoute><PACList /></ProtectedRoute>} />
      <Route path="/pacs/:id/edit" element={<ProtectedRoute><PACEditor /></ProtectedRoute>} />
      <Route path="/pacs/new" element={<ProtectedRoute><PACEditor /></ProtectedRoute>} />
      <Route path="/pacs-geral" element={<ProtectedRoute><PACGeralList /></ProtectedRoute>} />
      <Route path="/pacs-geral/:id/edit" element={<ProtectedRoute><PACGeralEditor /></ProtectedRoute>} />
      <Route path="/pacs-geral/new" element={<ProtectedRoute><PACGeralEditor /></ProtectedRoute>} />
      <Route path="/gestao-processual" element={<ProtectedRoute><GestaoProcessual /></ProtectedRoute>} />
      <Route path="/gestao-processual/dashboard" element={<ProtectedRoute><DashboardProcessual /></ProtectedRoute>} />
      <Route path="/users" element={<ProtectedRoute><Users /></ProtectedRoute>} />
      <Route path="/backup" element={<ProtectedRoute><Backup /></ProtectedRoute>} />
    </Routes>
  );
};

function App() {
  return (
    <div className="App">
      <Toaster position="top-right" />
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </div>
  );
}

export default App;
