import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, List, Plus, LogOut, Building2, Users, Shield, ClipboardList, Database } from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';

const Layout = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(null);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await api.get('/auth/me');
        setUser(response.data);
      } catch (error) {
        console.error('Error fetching user:', error);
      }
    };
    fetchUser();
  }, []);

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      localStorage.removeItem('auth_type');
      toast.success('Logout realizado com sucesso');
      navigate('/login');
    } catch (error) {
      toast.error('Erro ao fazer logout');
    }
  };

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path);

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="bg-primary text-primary-foreground shadow-lg no-print">
        <div className="container mx-auto px-4 py-3 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="bg-primary-foreground p-2 rounded">
              <Building2 className="text-primary w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-heading font-bold">PAC Acaiaca 2026</h1>
              <div className="text-xs opacity-90">Planejamento e Contratações</div>
            </div>
          </div>
          <nav className="flex items-center space-x-1 md:space-x-2">
            <Link
              to="/dashboard"
              data-testid="nav-dashboard-btn"
              className={`flex items-center space-x-1 px-2 py-2 rounded-lg transition-colors text-sm ${
                isActive('/dashboard') ? 'bg-primary/80' : 'hover:bg-primary/80'
              }`}
            >
              <LayoutDashboard size={16} />
              <span className="hidden lg:inline">Dashboard</span>
            </Link>
            <Link
              to="/pacs"
              data-testid="nav-pacs-btn"
              className={`flex items-center space-x-1 px-2 py-2 rounded-lg transition-colors text-sm ${
                isActive('/pacs') && !isActive('/pacs-geral') ? 'bg-primary/80' : 'hover:bg-primary/80'
              }`}
            >
              <List size={16} />
              <span className="hidden lg:inline">Meus PACs</span>
            </Link>
            <Link
              to="/pacs-geral"
              data-testid="nav-pac-geral-btn"
              className={`flex items-center space-x-1 px-2 py-2 rounded-lg transition-colors text-sm border border-primary-foreground/20 ${
                isActive('/pacs-geral') ? 'bg-primary/80' : 'hover:bg-primary/80'
              }`}
            >
              <Building2 size={16} />
              <span className="hidden lg:inline">PAC Geral</span>
            </Link>
            <Link
              to="/gestao-processual"
              data-testid="nav-gestao-processual-btn"
              className={`flex items-center space-x-1 px-2 py-2 rounded-lg transition-colors text-sm border border-amber-500/50 ${
                isActive('/gestao-processual') ? 'bg-amber-600' : 'hover:bg-amber-600/80'
              }`}
            >
              <ClipboardList size={16} />
              <span className="hidden lg:inline">Gestão Processual</span>
            </Link>
            {user?.is_admin && (
              <>
                <div className="h-6 w-px bg-primary-foreground/20 mx-1"></div>
                <Link
                  to="/users"
                  data-testid="nav-users-btn"
                  className={`flex items-center space-x-1 px-2 py-2 rounded-lg transition-colors text-sm ${
                    isActive('/users') ? 'bg-primary/80' : 'hover:bg-primary/80'
                  }`}
                >
                  <Users size={16} />
                  <span className="hidden lg:inline">Usuários</span>
                </Link>
                <Link
                  to="/backup"
                  data-testid="nav-backup-btn"
                  className={`flex items-center space-x-1 px-2 py-2 rounded-lg transition-colors text-sm border border-green-500/50 ${
                    isActive('/backup') ? 'bg-green-600' : 'hover:bg-green-600/80'
                  }`}
                  title="Backup e Restauração"
                >
                  <Database size={16} />
                  <span className="hidden lg:inline">Backup</span>
                </Link>
              </>
            )}
            <div className="h-6 w-px bg-primary-foreground/20 mx-1"></div>
            {user && (
              <div className="hidden xl:block text-sm">
                <div className="font-medium flex items-center gap-1">
                  {user.name?.split(' ')[0]}
                  {user.is_admin && (
                    <Shield size={14} className="text-amber-400" title="Administrador" />
                  )}
                </div>
              </div>
            )}
            <button
              onClick={handleLogout}
              data-testid="logout-btn"
              className="text-destructive-foreground hover:text-destructive transition-colors p-2"
              title="Sair"
            >
              <LogOut size={18} />
            </button>
          </nav>
        </div>
      </header>
      <main className="flex-grow container mx-auto px-4 py-6">
        {children}
      </main>
      <footer className="bg-muted py-4 text-center text-sm text-muted-foreground no-print">
        <p>Desenvolvido por Cristiano Abdo de Souza - Assessor de Planejamento, Compras e Logística</p>
        <p className="text-xs mt-1">PAC Acaiaca 2026 &copy; {new Date().getFullYear()}</p>
      </footer>
    </div>
  );
};

export default Layout;
