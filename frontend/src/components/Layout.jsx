import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, List, LogOut, Building2, Users, Shield, ClipboardList, 
  Database, Globe, Newspaper, FileSignature, ChevronDown, Hammer, DollarSign,
  FileText, Settings, BarChart3, Bell, User
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
  
  // Verificar se usuário é externo (só acessa MROSC)
  const isExternalUser = user?.tipo_usuario === 'PESSOA_EXTERNA' || user?.permissions?.mrosc_only;
  const isAdmin = user?.is_admin;

  // Se usuário externo tentar acessar outras páginas, redirecionar
  useEffect(() => {
    if (isExternalUser && !location.pathname.startsWith('/prestacao-contas') && location.pathname !== '/') {
      navigate('/prestacao-contas');
      toast.info('Você tem acesso apenas ao módulo de Prestação de Contas');
    }
  }, [location.pathname, isExternalUser, navigate]);

  // Layout simplificado para usuário externo
  if (isExternalUser) {
    return (
      <div 
        className="min-h-screen flex flex-col bg-cover bg-center bg-fixed"
        style={{ backgroundImage: 'url(/bg-acaiaca.png)' }}
      >
        <div className="min-h-screen flex flex-col bg-background/85 backdrop-blur-[1px]">
          <header className="bg-purple-700 text-white shadow-lg no-print">
            <div className="container mx-auto px-4 py-3 flex justify-between items-center">
              <div className="flex items-center space-x-3">
                <div className="bg-white p-2 rounded">
                  <DollarSign className="text-purple-700 w-6 h-6" />
                </div>
                <div>
                  <h1 className="text-xl font-heading font-bold">Prestação de Contas</h1>
                  <div className="text-xs opacity-90">MROSC - Lei 13.019/2014</div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right hidden md:block">
                  <div className="text-sm font-medium">{user?.name}</div>
                  <div className="text-xs opacity-75">Pessoa Externa (OSC)</div>
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 px-3 py-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
                >
                  <LogOut size={16} />
                  <span className="hidden md:inline">Sair</span>
                </button>
              </div>
            </div>
          </header>
          <main className="flex-1 container mx-auto px-4 py-6">{children}</main>
          <footer className="bg-primary text-primary-foreground py-3 text-center text-xs no-print">
            <span>© 2026 Prefeitura Municipal de Acaiaca - CNPJ: 18.295.287/0001-90</span>
          </footer>
        </div>
      </div>
    );
  }

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

              <Link
                to="/dashboard-analitico"
                data-testid="nav-analitico-btn"
                className={`flex items-center space-x-1 px-2 py-2 rounded-lg transition-colors text-sm border border-blue-500/50 ${
                  isActive('/dashboard-analitico') ? 'bg-blue-600/80' : 'hover:bg-blue-600/80'
                }`}
              >
                <BarChart3 size={16} />
                <span className="hidden lg:inline">Analítico</span>
              </Link>

              <Link
                to="/analytics"
                data-testid="nav-analytics-realtime-btn"
                className={`flex items-center space-x-1 px-2 py-2 rounded-lg transition-colors text-sm border border-green-500/50 ${
                  isActive('/analytics') ? 'bg-green-600/80' : 'hover:bg-green-600/80'
                }`}
                title="Métricas em Tempo Real"
              >
                <Bell size={16} />
                <span className="hidden lg:inline">Tempo Real</span>
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

              {/* Menu Prestação de Contas */}
              <Link
                to="/prestacao-contas"
                data-testid="nav-prestacao-contas-btn"
                className={`flex items-center space-x-1 px-2 py-2 rounded-lg transition-colors text-sm border border-green-500/50 ${
                  isActive('/prestacao-contas') ? 'bg-green-600' : 'hover:bg-green-600/80'
                }`}
                title="Prestação de Contas MROSC"
              >
                <DollarSign size={16} />
                <span className="hidden xl:inline">MROSC</span>
              </Link>

              {/* Menu Configurações */}
              <DropdownMenu
                title="Configurações"
                icon={Settings}
                color="teal"
                isActive={isActive('/historico-assinaturas') || isActive('/usuarios') || isActive('/backup')}
                items={[
                  { path: '/historico-assinaturas', label: 'Assinaturas', icon: FileSignature },
                  ...(user?.is_admin ? [
                    { path: '/usuarios', label: 'Usuários', icon: Users },
                    { path: '/backup', label: 'Backup', icon: Database },
                  ] : []),
                ]}
              />

              <div className="h-6 w-px bg-primary-foreground/20 mx-1"></div>
              {user && (
                <div className="hidden xl:flex items-center gap-2 text-sm bg-primary/50 px-3 py-1.5 rounded-lg">
                  <User size={14} />
                  <span className="font-medium">{user.name?.split(' ')[0]}</span>
                  {user.is_admin && (
                    <Shield size={14} className="text-amber-400" title="Administrador" />
                  )}
                </div>
              )}
              <button
                onClick={handleLogout}
                data-testid="logout-btn"
                className="flex items-center gap-1 px-3 py-2 bg-red-500/80 hover:bg-red-600 rounded-lg transition-colors text-sm"
                title="Sair"
              >
                <LogOut size={16} />
                <span className="hidden md:inline">Sair</span>
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
