import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, List, LogOut, Building2, Users, Shield, ClipboardList, 
  Database, Globe, FileSignature, ChevronDown, Hammer, DollarSign,
  FileText, Settings, BarChart3, Bell, User, Menu, X
} from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';
import NotificationCenter from './NotificationCenter';

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
        <span className="hidden xl:inline">{title}</span>
        <ChevronDown size={14} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      {isOpen && (
        <div className="absolute top-full left-0 mt-1 bg-card border border-border rounded-lg shadow-xl py-1 min-w-[180px] z-50 max-h-[70vh] overflow-y-auto">
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

// Menu Mobile Accordion
const MobileMenuSection = ({ title, icon: Icon, items, isOpen, onToggle }) => {
  return (
    <div className="border-b border-primary-foreground/10 last:border-b-0">
      <button
        onClick={onToggle}
        className="flex items-center justify-between w-full p-3 text-left hover:bg-primary/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Icon size={18} />
          <span className="font-medium">{title}</span>
        </div>
        <ChevronDown size={16} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      {isOpen && (
        <div className="bg-primary/30 px-2 pb-2">
          {items.map((item, index) => (
            <Link
              key={index}
              to={item.path}
              className="flex items-center gap-2 px-3 py-2 text-sm rounded-lg hover:bg-primary/50 transition-colors"
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
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [openMobileSection, setOpenMobileSection] = useState(null);

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

  // Fechar menu mobile ao mudar de rota
  useEffect(() => {
    setIsMobileMenuOpen(false);
    setOpenMobileSection(null);
  }, [location.pathname]);

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
          <div className="container mx-auto px-2 lg:px-4 py-3">
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-2 lg:space-x-3 flex-shrink-0">
                <div className="bg-primary-foreground p-1.5 lg:p-2 rounded">
                  <Building2 className="text-primary w-5 h-5 lg:w-6 lg:h-6" />
                </div>
                <div className="hidden sm:block">
                  <h1 className="text-lg lg:text-xl font-heading font-bold">Planejamento Acaiaca</h1>
                  <div className="text-xs opacity-90">Planejamento e Contratações</div>
                </div>
              </div>
              
              {/* Menu Desktop */}
              <nav className="hidden lg:flex items-center space-x-1 xl:space-x-2 flex-wrap justify-end">
                <Link
                  to="/"
                  data-testid="nav-portal-btn"
                  className="flex items-center space-x-1 px-2 py-2 rounded-lg transition-colors hover:bg-primary/80 border border-primary-foreground/20"
                  title="Portal Público"
                >
                  <Globe size={16} />
                  <span className="hidden xl:inline">Portal</span>
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
                  <span className="hidden xl:inline">Dashboard</span>
                </Link>

                <Link
                  to="/dashboard-analitico"
                  data-testid="nav-analitico-btn"
                  className={`flex items-center space-x-1 px-2 py-2 rounded-lg transition-colors text-sm border border-blue-500/50 ${
                    isActive('/dashboard-analitico') ? 'bg-blue-600/80' : 'hover:bg-blue-600/80'
                  }`}
                >
                  <BarChart3 size={16} />
                  <span className="hidden xl:inline">Analítico</span>
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
                </Link>

                {/* Menu Configurações */}
                <DropdownMenu
                  title="Config"
                  icon={Settings}
                  color="teal"
                  isActive={isActive('/historico-assinaturas') || isActive('/usuarios') || isActive('/backup') || isActive('/configuracoes')}
                  items={[
                    { path: '/historico-assinaturas', label: 'Assinaturas', icon: FileSignature },
                    { path: '/configuracoes', label: 'Aparência', icon: Settings },
                    ...(user?.is_admin ? [
                      { path: '/usuarios', label: 'Usuários', icon: Users },
                      { path: '/backup', label: 'Backup', icon: Database },
                    ] : []),
                  ]}
                />

                <div className="h-6 w-px bg-primary-foreground/20 mx-1"></div>
                {user && (
                  <div className="hidden 2xl:flex items-center gap-2 text-sm bg-primary/50 px-2 py-1.5 rounded-lg">
                    <User size={14} />
                    <span className="font-medium max-w-[80px] truncate">{user.name?.split(' ')[0]}</span>
                    {user.is_admin && (
                      <Shield size={14} className="text-amber-400" title="Administrador" />
                    )}
                  </div>
                )}
                
                {/* Centro de Notificações */}
                {user && <NotificationCenter userId={user.user_id} />}
                
                <button
                  onClick={handleLogout}
                  data-testid="logout-btn"
                  className="flex items-center gap-1 px-2 py-2 bg-red-500/80 hover:bg-red-600 rounded-lg transition-colors text-sm"
                  title="Sair"
                >
                  <LogOut size={16} />
                </button>
              </nav>
              
              {/* Menu Mobile Button */}
              <div className="flex lg:hidden items-center gap-2">
                {user && <NotificationCenter userId={user.user_id} />}
                <button
                  onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                  className="p-2 rounded-lg hover:bg-primary/80 transition-colors"
                  aria-label="Menu"
                  data-testid="mobile-menu-toggle"
                >
                  {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
                </button>
                <button
                  onClick={handleLogout}
                  className="p-2 bg-red-500/80 hover:bg-red-600 rounded-lg transition-colors"
                  title="Sair"
                  data-testid="logout-btn-mobile"
                >
                  <LogOut size={18} />
                </button>
              </div>
            </div>
            
            {/* Menu Mobile Expandido - Melhorado */}
            {isMobileMenuOpen && (
              <nav className="lg:hidden mt-3 pt-3 border-t border-primary-foreground/20 space-y-1 max-h-[70vh] overflow-y-auto">
                {/* Links Rápidos */}
                <div className="grid grid-cols-4 gap-2 pb-3 border-b border-primary-foreground/10">
                  <Link to="/" onClick={() => setIsMobileMenuOpen(false)} className="flex flex-col items-center gap-1 p-2 rounded-lg hover:bg-primary/80 text-xs">
                    <Globe size={20} /><span>Portal</span>
                  </Link>
                  <Link to="/dashboard" onClick={() => setIsMobileMenuOpen(false)} className="flex flex-col items-center gap-1 p-2 rounded-lg hover:bg-primary/80 text-xs">
                    <LayoutDashboard size={20} /><span>Dashboard</span>
                  </Link>
                  <Link to="/dashboard-analitico" onClick={() => setIsMobileMenuOpen(false)} className="flex flex-col items-center gap-1 p-2 rounded-lg hover:bg-primary/80 text-xs">
                    <BarChart3 size={20} /><span>Analítico</span>
                  </Link>
                  <Link to="/analytics" onClick={() => setIsMobileMenuOpen(false)} className="flex flex-col items-center gap-1 p-2 rounded-lg hover:bg-primary/80 text-xs">
                    <Bell size={20} /><span>Alertas</span>
                  </Link>
                </div>
                
                {/* PACs Section */}
                <MobileMenuSection
                  title="PACs"
                  icon={FileText}
                  isOpen={openMobileSection === 'pacs'}
                  onToggle={() => setOpenMobileSection(openMobileSection === 'pacs' ? null : 'pacs')}
                  items={[
                    { path: '/pacs', label: 'PAC Individual', icon: List },
                    { path: '/pacs-geral', label: 'PAC Geral', icon: Building2 },
                    { path: '/pacs-geral-obras', label: 'PAC Geral Obras', icon: Hammer },
                  ]}
                />
                
                {/* Processos Section */}
                <MobileMenuSection
                  title="Processos"
                  icon={ClipboardList}
                  isOpen={openMobileSection === 'processos'}
                  onToggle={() => setOpenMobileSection(openMobileSection === 'processos' ? null : 'processos')}
                  items={[
                    { path: '/gestao-processual', label: 'Gestão Processual', icon: ClipboardList },
                    { path: '/processos/dashboard', label: 'Dashboard', icon: LayoutDashboard },
                  ]}
                />
                
                {/* MROSC */}
                <Link 
                  to="/prestacao-contas" 
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center gap-2 p-3 hover:bg-primary/50 transition-colors rounded-lg"
                >
                  <DollarSign size={18} />
                  <span className="font-medium">Prestação de Contas (MROSC)</span>
                </Link>
                
                {/* Config Section */}
                <MobileMenuSection
                  title="Configurações"
                  icon={Settings}
                  isOpen={openMobileSection === 'config'}
                  onToggle={() => setOpenMobileSection(openMobileSection === 'config' ? null : 'config')}
                  items={[
                    { path: '/historico-assinaturas', label: 'Assinaturas', icon: FileSignature },
                    { path: '/configuracoes', label: 'Aparência', icon: Settings },
                    ...(user?.is_admin ? [
                      { path: '/usuarios', label: 'Usuários', icon: Users },
                      { path: '/backup', label: 'Backup', icon: Database },
                    ] : []),
                  ]}
                />
                
                {/* User Info Mobile */}
                {user && (
                  <div className="pt-3 border-t border-primary-foreground/10 flex items-center justify-between p-3">
                    <div className="flex items-center gap-2">
                      <User size={18} />
                      <div>
                        <div className="font-medium text-sm">{user.name}</div>
                        <div className="text-xs opacity-75">{user.email}</div>
                      </div>
                      {user.is_admin && <Shield size={14} className="text-amber-400" />}
                    </div>
                  </div>
                )}
              </nav>
            )}
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
