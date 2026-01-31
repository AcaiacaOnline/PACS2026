import React, { useState, useEffect } from 'react';
import { FileText, X, AlertTriangle, CheckCircle, Calendar, User, Shield } from 'lucide-react';

/**
 * Modal de Confirmação de Assinatura Digital
 * Componente reutilizável para assinatura de documentos PDF
 * 
 * Props:
 * - isOpen: boolean - Controla visibilidade do modal
 * - onClose: () => void - Callback para fechar modal
 * - onConfirm: (signatureDate: string) => void - Callback para confirmar assinatura
 * - onDownloadWithoutSignature: () => void - Callback para download sem assinatura
 * - documentInfo: { title: string, subtitle?: string, type?: string } - Info do documento
 * - user: { name: string, signature_data?: { cpf: string, cargo: string } } - Dados do usuário
 */
const SignatureModal = ({
  isOpen,
  onClose,
  onConfirm,
  onDownloadWithoutSignature,
  documentInfo = {},
  user = null
}) => {
  const [signatureDate, setSignatureDate] = useState('');
  const [useCurrentDate, setUseCurrentDate] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      // Definir data/hora atual como padrão
      const now = new Date();
      const formatted = `${now.getDate().toString().padStart(2, '0')}/${(now.getMonth() + 1).toString().padStart(2, '0')}/${now.getFullYear()} ${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
      setSignatureDate(formatted);
      setUseCurrentDate(true);
    }
  }, [isOpen]);

  const handleConfirm = async () => {
    if (!signatureDate) {
      alert('Por favor, informe a data da assinatura');
      return;
    }

    // Validar formato da data
    const dateRegex = /^\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}:\d{2}$/;
    if (!dateRegex.test(signatureDate)) {
      alert('Formato de data inválido. Use: DD/MM/YYYY HH:MM:SS');
      return;
    }

    setIsSubmitting(true);
    try {
      await onConfirm(signatureDate);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDownloadOnly = async () => {
    setIsSubmitting(true);
    try {
      await onDownloadWithoutSignature();
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  const setCurrentDateTime = () => {
    const now = new Date();
    const formatted = `${now.getDate().toString().padStart(2, '0')}/${(now.getMonth() + 1).toString().padStart(2, '0')}/${now.getFullYear()} ${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
    setSignatureDate(formatted);
    setUseCurrentDate(true);
  };

  // Verificar se o usuário pode assinar
  const canSign = user?.signature_data?.cpf && user?.signature_data?.cargo;
  const cpfMasked = user?.signature_data?.cpf 
    ? `***${user.signature_data.cpf.slice(3, 6)}.${user.signature_data.cpf.slice(6, 9)}-**`
    : '***.***.***-**';

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-start justify-center z-50 p-4 pt-8 backdrop-blur-sm overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="bg-gradient-to-r from-red-600 to-red-700 text-white px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/20 rounded-lg">
                <FileText size={24} />
              </div>
              <div>
                <h3 className="text-lg font-bold">Assinatura Digital</h3>
                <p className="text-sm text-white/80">Confirme para assinar o documento</p>
              </div>
            </div>
            <button 
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Alerta */}
          <div className="flex gap-3 p-4 bg-amber-50 border border-amber-200 rounded-xl mb-5">
            <AlertTriangle size={20} className="text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm text-amber-800 font-medium">Atenção: Esta ação é irreversível</p>
              <p className="text-xs text-amber-700 mt-1">
                A assinatura será registrada permanentemente com seus dados e não poderá ser desfeita.
              </p>
            </div>
          </div>

          {/* Informações do Documento */}
          <div className="mb-5">
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
              Documento
            </label>
            <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
              <div className="font-semibold text-gray-900">{documentInfo.title || 'Documento'}</div>
              {documentInfo.subtitle && (
                <div className="text-sm text-gray-600 mt-1">{documentInfo.subtitle}</div>
              )}
              {documentInfo.type && (
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded-full">
                    {documentInfo.type}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Informações do Assinante */}
          <div className="mb-5">
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
              Assinante
            </label>
            <div className="p-4 bg-blue-50 rounded-xl border border-blue-100">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
                  <User size={20} className="text-white" />
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-gray-900">{user?.name || 'Usuário não identificado'}</div>
                  <div className="text-sm text-gray-600">
                    {user?.signature_data?.cargo || 'Cargo não informado'}
                  </div>
                  <div className="text-xs text-gray-500">
                    CPF: {cpfMasked}
                  </div>
                </div>
                {canSign && (
                  <CheckCircle size={20} className="text-green-500" />
                )}
              </div>
            </div>
            
            {!canSign && (
              <p className="text-xs text-red-600 mt-2 flex items-center gap-1">
                <Shield size={12} />
                Complete seu CPF e Cargo no perfil para poder assinar documentos.
              </p>
            )}
          </div>

          {/* Data e Hora da Assinatura */}
          <div className="mb-6">
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
              Data e Hora da Assinatura
            </label>
            <div className="relative">
              <input
                type="text"
                value={signatureDate}
                onChange={(e) => {
                  setSignatureDate(e.target.value);
                  setUseCurrentDate(false);
                }}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all"
                placeholder="DD/MM/YYYY HH:MM:SS"
              />
              <button
                onClick={setCurrentDateTime}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title="Usar data/hora atual"
              >
                <Calendar size={18} className="text-gray-400" />
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Formato: DD/MM/YYYY HH:MM:SS • Você pode usar data retroativa se necessário.
            </p>
          </div>

          {/* Botões de Ação */}
          <div className="flex flex-col gap-3">
            <button
              onClick={handleConfirm}
              disabled={isSubmitting || !canSign}
              className="w-full py-3 px-4 bg-gradient-to-r from-red-600 to-red-700 text-white font-semibold rounded-xl hover:from-red-700 hover:to-red-800 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isSubmitting ? (
                <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></div>
              ) : (
                <>
                  <CheckCircle size={18} />
                  Assinar e Baixar PDF
                </>
              )}
            </button>
            
            <button
              onClick={handleDownloadOnly}
              disabled={isSubmitting}
              className="w-full py-3 px-4 bg-gray-100 text-gray-700 font-medium rounded-xl hover:bg-gray-200 transition-all disabled:opacity-50"
            >
              Baixar sem Assinar
            </button>
            
            <button
              onClick={onClose}
              disabled={isSubmitting}
              className="w-full py-2 text-gray-500 text-sm hover:text-gray-700 transition-colors"
            >
              Cancelar
            </button>
          </div>
        </div>

        {/* Footer com Info Legal */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-100">
          <p className="text-xs text-gray-500 text-center">
            Esta assinatura digital tem validade jurídica conforme Lei nº 14.063/2020.
            O documento será registrado com código de autenticidade verificável.
          </p>
        </div>
      </div>
    </div>
  );
};

export default SignatureModal;
