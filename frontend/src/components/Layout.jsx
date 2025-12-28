import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, List, Plus, LogOut, Building2, Users, Shield } from 'lucide-react';
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
          <nav className="flex items-center space-x-2 md:space-x-4">
            <Link
              to="/dashboard"
              data-testid="nav-dashboard-btn"
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
                isActive('/dashboard') ? 'bg-primary/80' : 'hover:bg-primary/80'
              }`}
            >
              <LayoutDashboard size={18} />
              <span className="hidden md:inline">Dashboard</span>
            </Link>
            <Link
              to="/pacs"
              data-testid="nav-pacs-btn"
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
                isActive('/pacs') ? 'bg-primary/80' : 'hover:bg-primary/80'
              }`}
            >
              <List size={18} />
              <span className="hidden md:inline">Meus PACs</span>
            </Link>
            <Link
              to="/pacs/new"
              data-testid="nav-new-pac-btn"
              className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-secondary/90 bg-secondary text-secondary-foreground shadow-sm transition-colors"
            >
              <Plus size={18} />
              <span className="hidden md:inline">Novo PAC</span>
            </Link>
            <Link
              to="/pacs-geral"
              data-testid="nav-pac-geral-btn"
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors border border-primary-foreground/20 ${
                isActive('/pacs-geral') ? 'bg-primary/80' : 'hover:bg-primary/80'
              }`}
            >
              <Building2 size={18} />
              <span className="hidden md:inline">PAC Geral</span>
            </Link>
            {user?.is_admin && (
              <>
                <div className="h-6 w-px bg-primary-foreground/20 mx-2"></div>
                <Link
                  to="/users"
                  data-testid="nav-users-btn"
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
                    isActive('/users') ? 'bg-primary/80' : 'hover:bg-primary/80'
                  }`}
                >
                  <Users size={18} />
                  <span className="hidden md:inline">Usuários</span>
                </Link>
              </>
            )}
            <div className="h-6 w-px bg-primary-foreground/20 mx-2"></div>
            {user && (
              <div className="hidden md:block text-sm">
                <div className="font-medium flex items-center gap-1">
                  {user.name}
                  {user.is_admin && (
                    <Shield size={14} className="text-amber-400" title="Administrador" />
                  )}
                </div>
                <div className="text-xs opacity-75">{user.email}</div>
              </div>
            )}
            <button
              onClick={handleLogout}
              data-testid="logout-btn"
              className="text-destructive-foreground hover:text-destructive transition-colors"
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
