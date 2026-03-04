import React, { useState, useEffect } from 'react';
import { Download, X, Smartphone } from 'lucide-react';

const PWAInstallPrompt = () => {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showPrompt, setShowPrompt] = useState(false);
  const [isIOS, setIsIOS] = useState(false);
  const [isStandalone, setIsStandalone] = useState(false);

  useEffect(() => {
    // Verificar se já está instalado
    const standalone = window.matchMedia('(display-mode: standalone)').matches 
      || window.navigator.standalone 
      || document.referrer.includes('android-app://');
    setIsStandalone(standalone);

    // Detectar iOS
    const iOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    setIsIOS(iOS);

    // Listener para o evento beforeinstallprompt (Android/Desktop)
    const handleBeforeInstall = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      
      // Mostrar prompt após 3 segundos se não estiver instalado
      if (!standalone) {
        setTimeout(() => setShowPrompt(true), 3000);
      }
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstall);

    // Mostrar prompt iOS após 5 segundos
    if (iOS && !standalone) {
      setTimeout(() => setShowPrompt(true), 5000);
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
    };
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    
    if (outcome === 'accepted') {
      setShowPrompt(false);
    }
    setDeferredPrompt(null);
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    // Não mostrar novamente por 7 dias
    localStorage.setItem('pwa-prompt-dismissed', Date.now().toString());
  };

  // Não mostrar se já foi dispensado recentemente
  useEffect(() => {
    const dismissed = localStorage.getItem('pwa-prompt-dismissed');
    if (dismissed) {
      const daysSince = (Date.now() - parseInt(dismissed)) / (1000 * 60 * 60 * 24);
      if (daysSince < 7) {
        setShowPrompt(false);
      }
    }
  }, []);

  // Não renderizar se já está instalado ou se não deve mostrar
  if (isStandalone || !showPrompt) return null;

  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 z-50 animate-slide-up">
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-800 p-4 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/20 rounded-lg">
                <Smartphone className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-semibold">Instalar Aplicativo</h3>
                <p className="text-xs text-blue-100">Acesso rápido e offline</p>
              </div>
            </div>
            <button 
              onClick={handleDismiss}
              className="p-1 hover:bg-white/20 rounded-full transition-colors"
              aria-label="Fechar"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-4">
          {isIOS ? (
            <div className="space-y-3">
              <p className="text-sm text-gray-600">
                Para instalar no seu iPhone/iPad:
              </p>
              <ol className="text-sm text-gray-700 space-y-2">
                <li className="flex items-center gap-2">
                  <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-bold">1</span>
                  <span>Toque no botão <strong>Compartilhar</strong> (ícone de seta)</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-bold">2</span>
                  <span>Role e toque em <strong>"Adicionar à Tela Inicial"</strong></span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-bold">3</span>
                  <span>Toque em <strong>"Adicionar"</strong></span>
                </li>
              </ol>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-gray-600">
                Instale o aplicativo para acesso rápido, mesmo sem internet.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={handleInstall}
                  className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white py-2.5 px-4 rounded-lg font-medium transition-colors"
                >
                  <Download className="w-5 h-5" />
                  Instalar Agora
                </button>
                <button
                  onClick={handleDismiss}
                  className="px-4 py-2.5 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  Depois
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PWAInstallPrompt;
