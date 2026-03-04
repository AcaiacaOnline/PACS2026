import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import DashboardAnalitico from './pages/DashboardAnalitico';
import AnalyticsRealtime from './pages/AnalyticsRealtime';
import PACList from './pages/PACList';
import PACEditor from './pages/PACEditor';
import PACGeralList from './pages/PACGeralList';
import PACGeralEditor from './pages/PACGeralEditor';
import PACGeralObrasList from './pages/PACGeralObrasList';
import PACGeralObrasEditor from './pages/PACGeralObrasEditor';
import GestaoProcessual from './pages/GestaoProcessual';
import DashboardProcessual from './pages/DashboardProcessual';
import PrestacaoContasList from './pages/PrestacaoContasList';
import PrestacaoContasEditor from './pages/PrestacaoContasEditor';
import Users from './pages/Users';
import Backup from './pages/Backup';
import PortalPublico from './pages/PortalPublico';
import ValidarDocumento from './pages/ValidarDocumento';
import HistoricoAssinaturas from './pages/HistoricoAssinaturas';
import Configuracoes from './pages/Configuracoes';
import ProtectedRoute from './components/ProtectedRoute';
import { ThemeProvider } from './components/ThemeProvider';
import { Toaster } from './components/ui/sonner';
import api from './utils/api';
import { toast } from 'sonner';
import './App.css';

// Componente para processar OAuth callback
const OAuthCallback = () => {
  const navigate = useNavigate();
  const [processing, setProcessing] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const processSession = async () => {
      try {
        const hash = window.location.hash;
        const search = window.location.search;
        
        console.log('OAuthCallback - hash:', hash);
        console.log('OAuthCallback - search:', search);
        
        // Tentar pegar session_id do hash ou da query string
        const hashParams = new URLSearchParams(hash.substring(1));
        const searchParams = new URLSearchParams(search);
        
        const sessionId = hashParams.get('session_id') || searchParams.get('session_id');
        console.log('OAuthCallback - sessionId:', sessionId);

        if (!sessionId) {
          throw new Error('No session ID found in URL');
        }

        console.log('Calling /auth/oauth/session...');
        const response = await api.get('/auth/oauth/session', {
          headers: {
            'X-Session-ID': sessionId
          },
          withCredentials: true
        });
        
        console.log('OAuth response:', response.data);

        // Salvar dados do usuário e token
        localStorage.setItem('user', JSON.stringify(response.data));
        localStorage.setItem('auth_type', 'oauth');
        
        // Se houver token na resposta, salvar
        if (response.data.token) {
          localStorage.setItem('token', response.data.token);
          console.log('Token saved to localStorage');
        }
        
        // Marcar como recém autenticado
        sessionStorage.setItem('just_authenticated', 'true');
        
        // Limpar o hash da URL
        window.history.replaceState(null, '', '/dashboard');
        
        toast.success('Login realizado com sucesso!');
        navigate('/dashboard', { replace: true });
      } catch (error) {
        console.error('OAuth error:', error);
        console.error('OAuth error details:', error.response?.data);
        setError(error.response?.data?.detail || error.message || 'Erro desconhecido');
        toast.error('Erro ao autenticar com Google: ' + (error.response?.data?.detail || error.message));
        setTimeout(() => {
          navigate('/login', { replace: true });
        }, 3000);
      } finally {
        setProcessing(false);
      }
    };

    processSession();
  }, [navigate]);

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-center max-w-md p-6">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-foreground mb-2">Erro na autenticação</h2>
          <p className="text-muted-foreground mb-4">{error}</p>
          <p className="text-sm text-muted-foreground">Redirecionando para login...</p>
        </div>
      </div>
    );
  }

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

// Componente OAuth com sessionId como prop (para quando já temos o ID)
const OAuthCallbackWithId = ({ sessionId }) => {
  const [processing, setProcessing] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const processSession = async () => {
      try {
        console.log('OAuthCallbackWithId - sessionId:', sessionId);

        if (!sessionId) {
          throw new Error('No session ID provided');
        }

        console.log('Calling /auth/oauth/session with sessionId:', sessionId);
        const response = await api.get('/auth/oauth/session', {
          headers: {
            'X-Session-ID': sessionId
          },
          withCredentials: true
        });
        
        console.log('OAuth response:', response.data);

        // Salvar dados do usuário e token
        localStorage.setItem('user', JSON.stringify(response.data));
        localStorage.setItem('auth_type', 'oauth');
        
        if (response.data.token) {
          localStorage.setItem('token', response.data.token);
          console.log('Token saved to localStorage');
        }
        
        sessionStorage.setItem('just_authenticated', 'true');
        
        toast.success('Login realizado com sucesso!');
        
        // Usar window.location para forçar navegação completa
        window.location.href = '/dashboard';
      } catch (error) {
        console.error('OAuth error:', error);
        console.error('OAuth error details:', error.response?.data);
        setError(error.response?.data?.detail || error.message || 'Erro desconhecido');
        toast.error('Erro ao autenticar com Google: ' + (error.response?.data?.detail || error.message));
        setTimeout(() => {
          window.location.href = '/login';
        }, 3000);
      } finally {
        setProcessing(false);
      }
    };

    processSession();
  }, [sessionId]);

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-center max-w-md p-6">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-foreground mb-2">Erro na autenticação</h2>
          <p className="text-muted-foreground mb-4">{error}</p>
          <p className="text-sm text-muted-foreground">Redirecionando para login...</p>
          <p className="text-xs text-muted-foreground mt-4">URL: {window.location.href}</p>
        </div>
      </div>
    );
  }

  if (processing) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-foreground">Processando autenticação...</p>
          <p className="text-sm text-muted-foreground mt-2">Session ID: {sessionId?.substring(0, 20)}...</p>
        </div>
      </div>
    );
  }

  return null;
};

// Wrapper para rotas normais
const AppRoutes = () => {
  return (
    <Routes>
      {/* Rota Pública - Portal de Transparência (PÁGINA INICIAL) */}
      <Route path="/" element={<PortalPublico />} />
      <Route path="/transparencia" element={<PortalPublico />} />
      <Route path="/portal-publico" element={<PortalPublico />} />
      <Route path="/validar" element={<ValidarDocumento />} />
      
      {/* Rotas Protegidas */}
      <Route path="/login" element={<Login />} />
      <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/dashboard-analitico" element={<ProtectedRoute><DashboardAnalitico /></ProtectedRoute>} />
      <Route path="/analytics" element={<ProtectedRoute><AnalyticsRealtime /></ProtectedRoute>} />
      <Route path="/pacs" element={<ProtectedRoute><PACList /></ProtectedRoute>} />
      <Route path="/pacs/:id/edit" element={<ProtectedRoute><PACEditor /></ProtectedRoute>} />
      <Route path="/pacs/new" element={<ProtectedRoute><PACEditor /></ProtectedRoute>} />
      <Route path="/pacs-geral" element={<ProtectedRoute><PACGeralList /></ProtectedRoute>} />
      <Route path="/pacs-geral/:id/edit" element={<ProtectedRoute><PACGeralEditor /></ProtectedRoute>} />
      <Route path="/pacs-geral/new" element={<ProtectedRoute><PACGeralEditor /></ProtectedRoute>} />
      <Route path="/pacs-geral-obras" element={<ProtectedRoute><PACGeralObrasList /></ProtectedRoute>} />
      <Route path="/pacs-geral-obras/:id" element={<ProtectedRoute><PACGeralObrasEditor /></ProtectedRoute>} />
      <Route path="/gestao-processual" element={<ProtectedRoute><GestaoProcessual /></ProtectedRoute>} />
      <Route path="/processos/dashboard" element={<ProtectedRoute><DashboardProcessual /></ProtectedRoute>} />
      <Route path="/prestacao-contas" element={<ProtectedRoute><PrestacaoContasList /></ProtectedRoute>} />
      <Route path="/prestacao-contas/:id" element={<ProtectedRoute><PrestacaoContasEditor /></ProtectedRoute>} />
      <Route path="/usuarios" element={<ProtectedRoute><Users /></ProtectedRoute>} />
      <Route path="/users" element={<Navigate to="/usuarios" replace />} />
      <Route path="/backup" element={<ProtectedRoute><Backup /></ProtectedRoute>} />
      <Route path="/historico-assinaturas" element={<ProtectedRoute><HistoricoAssinaturas /></ProtectedRoute>} />
      <Route path="/configuracoes" element={<ProtectedRoute><Configuracoes /></ProtectedRoute>} />
    </Routes>
  );
};

function App() {
  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  // Detect session_id synchronously during render (NOT in useEffect)
  // Check URL fragment (hash) for session_id - user lands at {redirect_url}#session_id={session_id}
  const currentHash = window.location.hash;
  const currentSearch = window.location.search;
  
  // Parse both hash and search params
  const hashParams = new URLSearchParams(currentHash.substring(1));
  const searchParams = new URLSearchParams(currentSearch);
  
  const sessionId = hashParams.get('session_id') || searchParams.get('session_id');
  const isOAuthCallback = !!sessionId;
  
  if (isOAuthCallback) {
    return (
      <ThemeProvider>
        <div className="App">
          <Toaster position="top-right" />
          <BrowserRouter>
            <OAuthCallbackWithId sessionId={sessionId} />
          </BrowserRouter>
        </div>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider>
      <div className="App">
        <Toaster position="top-right" />
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </div>
    </ThemeProvider>
  );
}

export default App;
