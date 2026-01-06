import React, { useState } from 'react';
import { Search, CheckCircle, XCircle, FileText, Calendar, User, Shield, QrCode } from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';

const ValidarDocumento = () => {
  const [validationCode, setValidationCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleValidate = async (e) => {
    e.preventDefault();
    if (!validationCode.trim()) {
      toast.error('Digite o código de validação');
      return;
    }

    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const response = await api.post('/validar/verificar', { 
        validation_code: validationCode.trim().toUpperCase() 
      });
      setResult(response.data);
      if (response.data.is_valid) {
        toast.success('Documento válido!');
      } else {
        toast.warning(response.data.message);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao validar documento');
      toast.error('Erro ao validar documento');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleString('pt-BR');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Header */}
      <header className="bg-white/10 backdrop-blur-md border-b border-white/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/20 rounded-lg">
                <Shield className="w-8 h-8 text-primary" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Validação de Documentos</h1>
                <p className="text-sm text-white/70">Prefeitura Municipal de Acaiaca - MG</p>
              </div>
            </div>
            <a 
              href="/"
              className="text-white/80 hover:text-white transition-colors text-sm"
            >
              Voltar ao Portal
            </a>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-12">
        {/* Formulário de Validação */}
        <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
          <div className="bg-gradient-to-r from-blue-600 to-blue-800 p-6 text-white">
            <div className="flex items-center gap-3 mb-4">
              <QrCode className="w-10 h-10" />
              <div>
                <h2 className="text-2xl font-bold">Verificar Autenticidade</h2>
                <p className="text-blue-100">Confirme se o documento é original e válido</p>
              </div>
            </div>
          </div>

          <div className="p-6">
            <form onSubmit={handleValidate} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Código de Validação
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={validationCode}
                    onChange={(e) => setValidationCode(e.target.value.toUpperCase())}
                    placeholder="DOC-XXXXXXXX-YYYYMMDD"
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-lg font-mono tracking-wider"
                    data-testid="validation-code-input"
                  />
                  <Search className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                </div>
                <p className="text-sm text-gray-500 mt-2">
                  O código está localizado no selo de assinatura do documento ou no QR Code.
                </p>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                data-testid="validate-btn"
              >
                {loading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Verificando...
                  </>
                ) : (
                  <>
                    <Shield size={20} />
                    Verificar Documento
                  </>
                )}
              </button>
            </form>

            {/* Resultado */}
            {result && (
              <div className={`mt-6 p-6 rounded-xl ${
                result.is_valid 
                  ? 'bg-green-50 border-2 border-green-200' 
                  : 'bg-red-50 border-2 border-red-200'
              }`} data-testid="validation-result">
                <div className="flex items-start gap-4">
                  {result.is_valid ? (
                    <CheckCircle className="w-12 h-12 text-green-600 flex-shrink-0" />
                  ) : (
                    <XCircle className="w-12 h-12 text-red-600 flex-shrink-0" />
                  )}
                  <div className="flex-1">
                    <h3 className={`text-xl font-bold ${result.is_valid ? 'text-green-700' : 'text-red-700'}`}>
                      {result.is_valid ? 'Documento Válido!' : 'Documento Não Validado'}
                    </h3>
                    <p className={`mt-1 ${result.is_valid ? 'text-green-600' : 'text-red-600'}`}>
                      {result.message}
                    </p>

                    {result.is_valid && result.document_info && (
                      <div className="mt-4 space-y-3 pt-4 border-t border-green-200">
                        <div className="flex items-center gap-2 text-gray-700">
                          <FileText size={18} className="text-blue-600" />
                          <span className="font-medium">Tipo:</span>
                          <span>{result.document_info.tipo_documento}</span>
                        </div>
                        
                        <div className="flex items-center gap-2 text-gray-700">
                          <Calendar size={18} className="text-blue-600" />
                          <span className="font-medium">Data da Assinatura:</span>
                          <span>{formatDate(result.document_info.data_assinatura)}</span>
                        </div>

                        {result.document_info.assinantes?.length > 0 && (
                          <div className="mt-4">
                            <h4 className="font-semibold text-gray-700 flex items-center gap-2 mb-2">
                              <User size={18} className="text-blue-600" />
                              Assinante(s):
                            </h4>
                            <div className="space-y-2">
                              {result.document_info.assinantes.map((signer, idx) => (
                                <div key={idx} className="bg-white p-3 rounded-lg border border-green-200">
                                  <p className="font-semibold text-gray-800">{signer.nome}</p>
                                  {signer.cargo && <p className="text-sm text-gray-600">{signer.cargo}</p>}
                                  <p className="text-sm text-gray-500">CPF: {signer.cpf_masked}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        <div className="text-xs text-gray-500 mt-4 pt-3 border-t border-green-200">
                          <span className="font-mono">Hash: {result.document_info.hash_parcial}</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {error && (
              <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
                <p>{error}</p>
              </div>
            )}
          </div>
        </div>

        {/* Informações */}
        <div className="mt-8 grid md:grid-cols-3 gap-4">
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 text-white">
            <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center mb-3">
              <QrCode size={24} />
            </div>
            <h3 className="font-semibold mb-1">QR Code</h3>
            <p className="text-sm text-white/70">
              Escaneie o QR Code presente no documento para validação rápida.
            </p>
          </div>
          
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 text-white">
            <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center mb-3">
              <Shield size={24} />
            </div>
            <h3 className="font-semibold mb-1">Segurança</h3>
            <p className="text-sm text-white/70">
              Todos os documentos possuem hash criptográfico único e são armazenados de forma segura.
            </p>
          </div>
          
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 text-white">
            <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center mb-3">
              <FileText size={24} />
            </div>
            <h3 className="font-semibold mb-1">LGPD</h3>
            <p className="text-sm text-white/70">
              Dados pessoais são protegidos e exibidos de forma mascarada conforme a lei.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-auto py-6 text-center text-white/50 text-sm">
        <p>© {new Date().getFullYear()} Prefeitura Municipal de Acaiaca - Todos os direitos reservados</p>
      </footer>
    </div>
  );
};

export default ValidarDocumento;
