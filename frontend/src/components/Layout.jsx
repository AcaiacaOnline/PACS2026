import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, List, LogOut, Building2, Users, Shield, ClipboardList, 
  Database, Globe, Newspaper, FileSignature, ChevronDown, Hammer, DollarSign,
  FileText, Settings
} from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';

const DropdownMenu = ({ title, icon: Icon, items, isActive, color = 'primary' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const colorClasses = {
    primary: 'hover:bg-primary/80',
    amber: 'hover:bg-amber-600/80 border-amber-500/50',
    purple: 'hover:bg-purple-600/80 border-purple-500/50',
    green: 'hover:bg-green-600/80 border-green-500/50',
    teal: 'hover:bg-teal-600/80 border-teal-500/50',
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center space-x-1 px-2 py-2 rounded-lg transition-colors text-sm border border-primary-foreground/20 ${
          isActive ? 'bg-primary/80' : colorClasses[color]
        }`}
      >
        <Icon size={16} />
        <span className="hidden lg:inline">{title}</span>
        <ChevronDown size={14} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      {isOpen && (
        <div className="absolute top-full left-0 mt-1 bg-card border border-border rounded-lg shadow-xl py-1 min-w-[180px] z-50">
          {items.map((item, index) => (
            <Link
              key={index}
              to={item.path}
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-muted transition-colors"
            >
              {item.icon && <item.icon size={14} />}
              {item.label}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

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
    <div 
      className="min-h-screen flex flex-col bg-cover bg-center bg-fixed"
      style={{ backgroundImage: 'url(/bg-acaiaca.png)' }}
    >
      {/* Overlay */}
      <div className="min-h-screen flex flex-col bg-background/85 backdrop-blur-[1px]">
        <header className="bg-primary text-primary-foreground shadow-lg no-print">
          <div className="container mx-auto px-4 py-3 flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <div className="bg-primary-foreground p-2 rounded">
                <Building2 className="text-primary w-6 h-6" />
              </div>
              <div>
                <h1 className="text-xl font-heading font-bold">Planejamento Acaiaca</h1>
                <div className="text-xs opacity-90">Planejamento e Contratações</div>
              </div>
            </div>
            <nav className="flex items-center space-x-1 md:space-x-2">
              <Link
                to="/"
                data-testid="nav-portal-btn"
                className="flex items-center space-x-1 px-2 py-2 rounded-lg transition-colors hover:bg-primary/80 border border-primary-foreground/20"
                title="Portal Público"
              >
                <Globe size={16} />
                <span className="hidden lg:inline">Portal</span>
              </Link>
              <div className="h-6 w-px bg-primary-foreground/20 mx-1"></div>
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
              
              {/* Menu PACS */}
              <DropdownMenu
                title="PACs"
                icon={FileText}
                isActive={isActive('/pacs') || isActive('/pacs-geral')}
                items={[
                  { path: '/pacs', label: 'PAC Individual', icon: List },
                  { path: '/pacs-geral', label: 'PAC Geral', icon: Building2 },
                  { path: '/pacs-geral-obras', label: 'PAC Geral Obras', icon: Hammer },
                ]}
              />

              {/* Menu Processos */}
              <DropdownMenu
                title="Processos"
                icon={ClipboardList}
                color="amber"
                isActive={isActive('/gestao-processual') || isActive('/processos')}
                items={[
                  { path: '/gestao-processual', label: 'Gestão Processual', icon: ClipboardList },
                  { path: '/processos/dashboard', label: 'Dashboard', icon: LayoutDashboard },
                ]}
              />

              {/* Menu Diário Oficial */}
              <DropdownMenu
                title="DOEM"
                icon={Newspaper}
                color="purple"
                isActive={isActive('/doem')}
                items={[
                  { path: '/doem', label: 'Edições', icon: Newspaper },
                  { path: '/doem/publicacoes', label: 'Publicações', icon: FileText },
                ]}
              />

              <Link
                to="/historico-assinaturas"
                data-testid="nav-historico-assinaturas-btn"
                className={`flex items-center space-x-1 px-2 py-2 rounded-lg transition-colors text-sm border border-teal-500/50 ${
                  isActive('/historico-assinaturas') ? 'bg-teal-600' : 'hover:bg-teal-600/80'
                }`}
                title="Histórico de Assinaturas"
              >
                <FileSignature size={16} />
                <span className="hidden xl:inline">Assinaturas</span>
              </Link>
              {user?.is_admin && (
                <>
                  <div className="h-6 w-px bg-primary-foreground/20 mx-1"></div>
                  <Link
                    to="/usuarios"
                    data-testid="nav-users-btn"
                    className={`flex items-center space-x-1 px-2 py-2 rounded-lg transition-colors text-sm ${
                      isActive('/usuarios') ? 'bg-primary/80' : 'hover:bg-primary/80'
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
          <p className="text-xs mt-1">Planejamento Acaiaca &copy; {new Date().getFullYear()}</p>
        </footer>
      </div>
    </div>
  );
};

export default Layout;
