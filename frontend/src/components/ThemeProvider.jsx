import React, { createContext, useContext, useState, useEffect } from 'react';

// Definição dos temas disponíveis
export const THEMES = {
  default: {
    id: 'default',
    name: 'Padrão (Azul)',
    description: 'Tema padrão do sistema com tons de azul',
    colors: {
      primary: '#1e40af',        // blue-800
      primaryHover: '#1e3a8a',   // blue-900
      primaryLight: '#dbeafe',   // blue-100
      secondary: '#64748b',      // slate-500
      accent: '#3b82f6',         // blue-500
      success: '#22c55e',        // green-500
      warning: '#f59e0b',        // amber-500
      danger: '#ef4444',         // red-500
      background: '#f8fafc',     // slate-50
      surface: '#ffffff',
      text: '#1e293b',           // slate-800
      textMuted: '#64748b',      // slate-500
      border: '#e2e8f0',         // slate-200
      headerBg: 'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)',
      sidebarBg: '#1e293b',      // slate-800
    },
    cssVars: {
      '--theme-primary': '#1e40af',
      '--theme-primary-hover': '#1e3a8a',
      '--theme-accent': '#3b82f6',
      '--theme-header-from': '#1e40af',
      '--theme-header-to': '#3b82f6',
    }
  },
  
  governo: {
    id: 'governo',
    name: 'Governo (Verde/Amarelo)',
    description: 'Cores institucionais do Brasil',
    colors: {
      primary: '#166534',        // green-800
      primaryHover: '#14532d',   // green-900
      primaryLight: '#dcfce7',   // green-100
      secondary: '#ca8a04',      // yellow-600
      accent: '#22c55e',         // green-500
      success: '#22c55e',
      warning: '#eab308',        // yellow-500
      danger: '#ef4444',
      background: '#f0fdf4',     // green-50
      surface: '#ffffff',
      text: '#14532d',           // green-900
      textMuted: '#166534',
      border: '#bbf7d0',         // green-200
      headerBg: 'linear-gradient(135deg, #166534 0%, #22c55e 100%)',
      sidebarBg: '#14532d',
    },
    cssVars: {
      '--theme-primary': '#166534',
      '--theme-primary-hover': '#14532d',
      '--theme-accent': '#22c55e',
      '--theme-header-from': '#166534',
      '--theme-header-to': '#22c55e',
    }
  },
  
  minasGerais: {
    id: 'minasGerais',
    name: 'Minas Gerais (Vermelho)',
    description: 'Inspirado no Diário Oficial de MG',
    colors: {
      primary: '#8B0000',        // darkred
      primaryHover: '#6B0000',
      primaryLight: '#fee2e2',   // red-100
      secondary: '#1a365d',      // navy
      accent: '#DC2626',         // red-600
      success: '#059669',        // emerald-600
      warning: '#d97706',        // amber-600
      danger: '#dc2626',
      background: '#fef2f2',     // red-50
      surface: '#ffffff',
      text: '#1f2937',           // gray-800
      textMuted: '#6b7280',
      border: '#fecaca',         // red-200
      headerBg: 'linear-gradient(135deg, #8B0000 0%, #DC2626 100%)',
      sidebarBg: '#1a365d',
    },
    cssVars: {
      '--theme-primary': '#8B0000',
      '--theme-primary-hover': '#6B0000',
      '--theme-accent': '#DC2626',
      '--theme-header-from': '#8B0000',
      '--theme-header-to': '#DC2626',
    }
  },
  
  modern: {
    id: 'modern',
    name: 'Moderno (Roxo)',
    description: 'Design contemporâneo com tons de roxo',
    colors: {
      primary: '#7c3aed',        // violet-600
      primaryHover: '#6d28d9',   // violet-700
      primaryLight: '#ede9fe',   // violet-100
      secondary: '#8b5cf6',      // violet-500
      accent: '#a78bfa',         // violet-400
      success: '#10b981',        // emerald-500
      warning: '#f59e0b',
      danger: '#ef4444',
      background: '#faf5ff',     // purple-50
      surface: '#ffffff',
      text: '#1f2937',
      textMuted: '#6b7280',
      border: '#e9d5ff',         // purple-200
      headerBg: 'linear-gradient(135deg, #7c3aed 0%, #a78bfa 100%)',
      sidebarBg: '#4c1d95',      // violet-900
    },
    cssVars: {
      '--theme-primary': '#7c3aed',
      '--theme-primary-hover': '#6d28d9',
      '--theme-accent': '#a78bfa',
      '--theme-header-from': '#7c3aed',
      '--theme-header-to': '#a78bfa',
    }
  },
  
  dark: {
    id: 'dark',
    name: 'Escuro',
    description: 'Tema escuro para uso noturno',
    colors: {
      primary: '#3b82f6',        // blue-500
      primaryHover: '#2563eb',   // blue-600
      primaryLight: '#1e3a5f',
      secondary: '#94a3b8',      // slate-400
      accent: '#60a5fa',         // blue-400
      success: '#22c55e',
      warning: '#f59e0b',
      danger: '#ef4444',
      background: '#0f172a',     // slate-900
      surface: '#1e293b',        // slate-800
      text: '#f1f5f9',           // slate-100
      textMuted: '#94a3b8',      // slate-400
      border: '#334155',         // slate-700
      headerBg: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
      sidebarBg: '#0f172a',
    },
    cssVars: {
      '--theme-primary': '#3b82f6',
      '--theme-primary-hover': '#2563eb',
      '--theme-accent': '#60a5fa',
      '--theme-header-from': '#1e293b',
      '--theme-header-to': '#334155',
    }
  },
  
  earth: {
    id: 'earth',
    name: 'Terra (Marrom)',
    description: 'Tons terrosos e naturais',
    colors: {
      primary: '#92400e',        // amber-800
      primaryHover: '#78350f',   // amber-900
      primaryLight: '#fef3c7',   // amber-100
      secondary: '#78716c',      // stone-500
      accent: '#d97706',         // amber-600
      success: '#16a34a',
      warning: '#eab308',
      danger: '#dc2626',
      background: '#fefce8',     // yellow-50
      surface: '#ffffff',
      text: '#422006',           // amber-950
      textMuted: '#78716c',
      border: '#fde68a',         // amber-200
      headerBg: 'linear-gradient(135deg, #92400e 0%, #d97706 100%)',
      sidebarBg: '#44403c',      // stone-700
    },
    cssVars: {
      '--theme-primary': '#92400e',
      '--theme-primary-hover': '#78350f',
      '--theme-accent': '#d97706',
      '--theme-header-from': '#92400e',
      '--theme-header-to': '#d97706',
    }
  },
  
  ocean: {
    id: 'ocean',
    name: 'Oceano (Azul-Verde)',
    description: 'Tons calmantes de água',
    colors: {
      primary: '#0891b2',        // cyan-600
      primaryHover: '#0e7490',   // cyan-700
      primaryLight: '#cffafe',   // cyan-100
      secondary: '#14b8a6',      // teal-500
      accent: '#06b6d4',         // cyan-500
      success: '#10b981',
      warning: '#f59e0b',
      danger: '#ef4444',
      background: '#ecfeff',     // cyan-50
      surface: '#ffffff',
      text: '#164e63',           // cyan-900
      textMuted: '#0e7490',
      border: '#a5f3fc',         // cyan-200
      headerBg: 'linear-gradient(135deg, #0891b2 0%, #14b8a6 100%)',
      sidebarBg: '#134e4a',      // teal-900
    },
    cssVars: {
      '--theme-primary': '#0891b2',
      '--theme-primary-hover': '#0e7490',
      '--theme-accent': '#06b6d4',
      '--theme-header-from': '#0891b2',
      '--theme-header-to': '#14b8a6',
    }
  },
};

// Contexto do Tema
const ThemeContext = createContext(null);

// Hook personalizado para usar o tema
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

// Provider do Tema
export const ThemeProvider = ({ children }) => {
  const [currentTheme, setCurrentTheme] = useState('default');
  const [isLoaded, setIsLoaded] = useState(false);

  // Carregar tema salvo do localStorage
  useEffect(() => {
    const savedTheme = localStorage.getItem('app-theme');
    if (savedTheme && THEMES[savedTheme]) {
      setCurrentTheme(savedTheme);
    }
    setIsLoaded(true);
  }, []);

  // Aplicar variáveis CSS quando o tema mudar
  useEffect(() => {
    const theme = THEMES[currentTheme];
    if (theme) {
      const root = document.documentElement;
      
      // Aplicar variáveis CSS
      Object.entries(theme.cssVars).forEach(([key, value]) => {
        root.style.setProperty(key, value);
      });

      // Aplicar cores como variáveis CSS
      Object.entries(theme.colors).forEach(([key, value]) => {
        root.style.setProperty(`--color-${key}`, value);
      });

      // Salvar no localStorage
      localStorage.setItem('app-theme', currentTheme);

      // Classe no body para estilos específicos
      document.body.className = `theme-${currentTheme}`;
    }
  }, [currentTheme]);

  const changeTheme = (themeId) => {
    if (THEMES[themeId]) {
      setCurrentTheme(themeId);
    }
  };

  const theme = THEMES[currentTheme];

  const value = {
    currentTheme,
    theme,
    themes: THEMES,
    changeTheme,
    isLoaded,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

// Componente Seletor de Tema
export const ThemeSelector = ({ className = '' }) => {
  const { currentTheme, themes, changeTheme } = useTheme();

  return (
    <div className={`grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 ${className}`}>
      {Object.values(themes).map((theme) => (
        <button
          key={theme.id}
          onClick={() => changeTheme(theme.id)}
          className={`
            relative p-3 rounded-xl border-2 transition-all duration-200
            ${currentTheme === theme.id 
              ? 'border-current ring-2 ring-offset-2' 
              : 'border-gray-200 hover:border-gray-300'}
          `}
          style={{
            borderColor: currentTheme === theme.id ? theme.colors.primary : undefined,
            '--tw-ring-color': theme.colors.primary,
          }}
        >
          {/* Preview do tema */}
          <div className="flex gap-1 mb-2">
            <div 
              className="w-6 h-6 rounded-full"
              style={{ backgroundColor: theme.colors.primary }}
            />
            <div 
              className="w-6 h-6 rounded-full"
              style={{ backgroundColor: theme.colors.accent }}
            />
            <div 
              className="w-6 h-6 rounded-full"
              style={{ backgroundColor: theme.colors.secondary }}
            />
          </div>
          
          <div className="text-left">
            <div className="font-medium text-sm text-gray-900">{theme.name}</div>
            <div className="text-xs text-gray-500 line-clamp-1">{theme.description}</div>
          </div>

          {/* Indicador de selecionado */}
          {currentTheme === theme.id && (
            <div 
              className="absolute top-2 right-2 w-5 h-5 rounded-full flex items-center justify-center text-white text-xs"
              style={{ backgroundColor: theme.colors.primary }}
            >
              ✓
            </div>
          )}
        </button>
      ))}
    </div>
  );
};

// Componente de Preview de Tema Compacto
export const ThemePreview = ({ themeId, onClick, isSelected }) => {
  const theme = THEMES[themeId];
  if (!theme) return null;

  return (
    <button
      onClick={() => onClick?.(themeId)}
      className={`
        flex items-center gap-3 p-3 rounded-lg border transition-all
        ${isSelected ? 'border-2 shadow-md' : 'border-gray-200 hover:border-gray-300'}
      `}
      style={{
        borderColor: isSelected ? theme.colors.primary : undefined,
      }}
    >
      <div 
        className="w-10 h-10 rounded-lg"
        style={{ background: theme.colors.headerBg }}
      />
      <div className="text-left flex-1">
        <div className="font-medium text-sm">{theme.name}</div>
        <div className="text-xs text-gray-500">{theme.description}</div>
      </div>
    </button>
  );
};

export default ThemeProvider;
