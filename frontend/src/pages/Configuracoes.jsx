import React, { useState } from 'react';
import { Settings, Palette, Shield, Bell, Database, User, Check, Moon, Sun } from 'lucide-react';
import { useTheme, ThemeSelector, THEMES } from '../components/ThemeProvider';
import { toast } from 'sonner';

const Configuracoes = () => {
  const { currentTheme, theme, changeTheme } = useTheme();
  const [activeTab, setActiveTab] = useState('aparencia');

  const tabs = [
    { id: 'aparencia', label: 'Aparência', icon: Palette },
    { id: 'notificacoes', label: 'Notificações', icon: Bell },
    { id: 'seguranca', label: 'Segurança', icon: Shield },
    { id: 'sistema', label: 'Sistema', icon: Database },
  ];

  const handleThemeChange = (themeId) => {
    changeTheme(themeId);
    toast.success(`Tema alterado para ${THEMES[themeId].name}`);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div 
              className="p-3 rounded-xl"
              style={{ backgroundColor: theme?.colors.primaryLight }}
            >
              <Settings 
                size={24} 
                style={{ color: theme?.colors.primary }}
              />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Configurações</h1>
              <p className="text-gray-500">Personalize sua experiência no sistema</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar de navegação */}
          <div className="lg:col-span-1">
            <nav className="bg-white rounded-xl shadow-sm p-2 sticky top-6">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`
                      w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-all
                      ${isActive 
                        ? 'text-white font-medium' 
                        : 'text-gray-600 hover:bg-gray-50'}
                    `}
                    style={{
                      backgroundColor: isActive ? theme?.colors.primary : undefined,
                    }}
                  >
                    <Icon size={18} />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Conteúdo Principal */}
          <div className="lg:col-span-3 space-y-6">
            {/* Aba Aparência */}
            {activeTab === 'aparencia' && (
              <>
                {/* Seleção de Tema */}
                <div className="bg-white rounded-xl shadow-sm p-6">
                  <div className="flex items-center gap-3 mb-6">
                    <Palette size={20} style={{ color: theme?.colors.primary }} />
                    <div>
                      <h2 className="text-lg font-semibold">Tema do Sistema</h2>
                      <p className="text-sm text-gray-500">Escolha as cores que combinam com você</p>
                    </div>
                  </div>

                  <ThemeSelector />

                  <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Check size={16} className="text-green-500" />
                      <span>Tema atual: <strong>{theme?.name}</strong></span>
                    </div>
                  </div>
                </div>

                {/* Preview do Tema */}
                <div className="bg-white rounded-xl shadow-sm p-6">
                  <h3 className="text-lg font-semibold mb-4">Preview do Tema</h3>
                  
                  {/* Mini preview */}
                  <div className="border rounded-xl overflow-hidden">
                    {/* Header do preview */}
                    <div 
                      className="h-12 flex items-center px-4"
                      style={{ background: theme?.colors.headerBg }}
                    >
                      <span className="text-white font-semibold">Header do Sistema</span>
                    </div>
                    
                    <div className="flex">
                      {/* Sidebar do preview */}
                      <div 
                        className="w-48 p-3"
                        style={{ backgroundColor: theme?.colors.sidebarBg }}
                      >
                        <div className="space-y-2">
                          {['Dashboard', 'PAC', 'Processos'].map((item, i) => (
                            <div 
                              key={i}
                              className={`px-3 py-2 rounded-lg text-sm ${i === 0 ? 'bg-white/20' : ''}`}
                              style={{ color: 'white' }}
                            >
                              {item}
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      {/* Conteúdo do preview */}
                      <div 
                        className="flex-1 p-4"
                        style={{ backgroundColor: theme?.colors.background }}
                      >
                        <div 
                          className="p-4 rounded-lg"
                          style={{ backgroundColor: theme?.colors.surface }}
                        >
                          <h4 
                            className="font-semibold mb-2"
                            style={{ color: theme?.colors.text }}
                          >
                            Conteúdo Principal
                          </h4>
                          <p 
                            className="text-sm mb-3"
                            style={{ color: theme?.colors.textMuted }}
                          >
                            Este é um preview de como o conteúdo aparecerá.
                          </p>
                          <div className="flex gap-2">
                            <button 
                              className="px-3 py-1.5 rounded-lg text-white text-sm"
                              style={{ backgroundColor: theme?.colors.primary }}
                            >
                              Botão Primário
                            </button>
                            <button 
                              className="px-3 py-1.5 rounded-lg text-sm"
                              style={{ 
                                backgroundColor: theme?.colors.primaryLight,
                                color: theme?.colors.primary 
                              }}
                            >
                              Botão Secundário
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Paleta de Cores */}
                <div className="bg-white rounded-xl shadow-sm p-6">
                  <h3 className="text-lg font-semibold mb-4">Paleta de Cores</h3>
                  
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    {[
                      { name: 'Primária', key: 'primary' },
                      { name: 'Acento', key: 'accent' },
                      { name: 'Sucesso', key: 'success' },
                      { name: 'Alerta', key: 'warning' },
                      { name: 'Perigo', key: 'danger' },
                      { name: 'Texto', key: 'text' },
                      { name: 'Fundo', key: 'background' },
                      { name: 'Borda', key: 'border' },
                    ].map((color) => (
                      <div key={color.key} className="text-center">
                        <div 
                          className="w-full h-12 rounded-lg mb-2 border"
                          style={{ backgroundColor: theme?.colors[color.key] }}
                        />
                        <span className="text-xs text-gray-600">{color.name}</span>
                        <div className="text-xs text-gray-400 font-mono">
                          {theme?.colors[color.key]}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Aba Notificações */}
            {activeTab === 'notificacoes' && (
              <div className="bg-white rounded-xl shadow-sm p-6">
                <div className="flex items-center gap-3 mb-6">
                  <Bell size={20} style={{ color: theme?.colors.primary }} />
                  <div>
                    <h2 className="text-lg font-semibold">Notificações</h2>
                    <p className="text-sm text-gray-500">Gerencie suas preferências de notificação</p>
                  </div>
                </div>

                <div className="space-y-4">
                  {[
                    { label: 'Notificações por email', desc: 'Receber alertas por email' },
                    { label: 'Notificações no sistema', desc: 'Mostrar notificações em tempo real' },
                    { label: 'Som de notificação', desc: 'Reproduzir som ao receber notificações' },
                    { label: 'Alertas de prazo', desc: 'Notificar sobre prazos próximos' },
                  ].map((item, i) => (
                    <div key={i} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div>
                        <div className="font-medium text-gray-900">{item.label}</div>
                        <div className="text-sm text-gray-500">{item.desc}</div>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" defaultChecked={i < 2} className="sr-only peer" />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Aba Segurança */}
            {activeTab === 'seguranca' && (
              <div className="bg-white rounded-xl shadow-sm p-6">
                <div className="flex items-center gap-3 mb-6">
                  <Shield size={20} style={{ color: theme?.colors.primary }} />
                  <div>
                    <h2 className="text-lg font-semibold">Segurança</h2>
                    <p className="text-sm text-gray-500">Configurações de segurança da conta</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <button className="w-full flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                    <div className="text-left">
                      <div className="font-medium text-gray-900">Alterar Senha</div>
                      <div className="text-sm text-gray-500">Atualize sua senha de acesso</div>
                    </div>
                    <span className="text-gray-400">→</span>
                  </button>

                  <button className="w-full flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                    <div className="text-left">
                      <div className="font-medium text-gray-900">Sessões Ativas</div>
                      <div className="text-sm text-gray-500">Gerencie dispositivos conectados</div>
                    </div>
                    <span className="text-gray-400">→</span>
                  </button>

                  <button className="w-full flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                    <div className="text-left">
                      <div className="font-medium text-gray-900">Dados para Assinatura Digital</div>
                      <div className="text-sm text-gray-500">Configure CPF e cargo para assinar documentos</div>
                    </div>
                    <span className="text-gray-400">→</span>
                  </button>
                </div>
              </div>
            )}

            {/* Aba Sistema */}
            {activeTab === 'sistema' && (
              <div className="bg-white rounded-xl shadow-sm p-6">
                <div className="flex items-center gap-3 mb-6">
                  <Database size={20} style={{ color: theme?.colors.primary }} />
                  <div>
                    <h2 className="text-lg font-semibold">Sistema</h2>
                    <p className="text-sm text-gray-500">Informações e configurações do sistema</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-sm text-gray-500 mb-1">Versão do Sistema</div>
                    <div className="font-medium">Planejamento Acaiaca v2.0.0</div>
                  </div>

                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-sm text-gray-500 mb-1">Última Atualização</div>
                    <div className="font-medium">{new Date().toLocaleDateString('pt-BR')}</div>
                  </div>

                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-sm text-gray-500 mb-1">Ambiente</div>
                    <div className="font-medium">Produção</div>
                  </div>

                  <button 
                    onClick={() => {
                      localStorage.clear();
                      toast.success('Cache limpo com sucesso!');
                    }}
                    className="w-full p-4 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition-colors font-medium"
                  >
                    Limpar Cache Local
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Configuracoes;
