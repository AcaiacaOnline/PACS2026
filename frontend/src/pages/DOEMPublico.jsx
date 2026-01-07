import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Newspaper, Search, Calendar, Download, ChevronDown, ChevronRight, 
  FileText, CheckCircle, ArrowLeft, Home
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

// API pública (sem autenticação)
const publicApi = axios.create({
  baseURL: `${process.env.REACT_APP_BACKEND_URL}/api`,
  headers: {
    'Content-Type': 'application/json'
  }
});

const DOEMPublico = () => {
  const navigate = useNavigate();
  const [edicoes, setEdicoes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [anos, setAnos] = useState([]);
  const [anoExpandido, setAnoExpandido] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [selectedEdicao, setSelectedEdicao] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAnos();
    fetchEdicoes();
  }, []);

  const fetchAnos = async () => {
    try {
      const response = await publicApi.get('/public/doem/anos');
      const anosDisponiveis = response.data.anos || [new Date().getFullYear()];
      setAnos(anosDisponiveis);
      if (anosDisponiveis.length > 0) {
        setAnoExpandido(anosDisponiveis[0]);
      }
    } catch (error) {
      console.error('Erro ao carregar anos:', error);
      setAnos([new Date().getFullYear()]);
    }
  };

  const fetchEdicoes = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await publicApi.get('/public/doem/edicoes?limit=100');
      setEdicoes(response.data);
    } catch (error) {
      console.error('Erro ao carregar edições:', error);
      setError('Não foi possível carregar as edições do DOEM. Tente novamente mais tarde.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchTerm || searchTerm.length < 3) {
      toast.error('Digite pelo menos 3 caracteres para buscar');
      return;
    }

    try {
      const response = await publicApi.get(`/public/doem/busca?q=${encodeURIComponent(searchTerm)}`);
      setSearchResults(response.data);
    } catch (error) {
      toast.error('Erro ao buscar');
    }
  };

  const handleDownloadPDF = async (edicao) => {
    try {
      const response = await publicApi.get(`/public/doem/edicoes/${edicao.edicao_id}/pdf`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `DOEM_Acaiaca_Edicao_${edicao.numero_edicao}_${edicao.ano}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      toast.error('Erro ao baixar PDF');
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: 'long',
        year: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  const edicoesporAno = anos.map(ano => ({
    ano,
    edicoes: edicoes.filter(e => e.ano === ano)
  }));

  const ultimaEdicao = edicoes.length > 0 ? edicoes[0] : null;

  return (
    <div 
      className="min-h-screen bg-cover bg-center bg-fixed"
      style={{ backgroundImage: 'url(/bg-acaiaca.png)' }}
    >
      <div className="min-h-screen bg-black/40 backdrop-blur-sm">
        {/* Header */}
        <header className="bg-gradient-to-r from-slate-900/95 to-slate-800/95 backdrop-blur-lg border-b border-white/10 shadow-xl">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-primary/20 rounded-xl">
                  <Newspaper className="text-primary" size={40} />
                </div>
                <div>
                  <h1 className="text-2xl md:text-3xl font-bold text-white">
                    DOEM - Diário Oficial Eletrônico
                  </h1>
                  <p className="text-slate-300">
                    Município de Acaiaca - MG
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <button
                  onClick={() => navigate('/transparencia')}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-semibold"
                >
                  <Home size={18} />
                  Portal Principal
                </button>
                <button
                  onClick={() => navigate('/login')}
                  className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors border border-white/20"
                >
                  <ArrowLeft size={18} />
                  Acesso Administrativo
                </button>
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 py-8">
          {/* Barra de Busca */}
          <div className="bg-white/95 backdrop-blur-lg rounded-2xl p-6 mb-8 shadow-xl">
            <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Search className="text-primary" size={24} />
              Pesquisar Publicações
            </h2>
            <div className="flex gap-4">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Digite o termo de busca (mínimo 3 caracteres)..."
                className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/50 outline-none"
              />
              <button
                onClick={handleSearch}
                className="px-6 py-3 bg-primary text-white rounded-xl hover:bg-primary/90 transition-colors font-semibold"
              >
                Buscar
              </button>
            </div>
            
            {searchResults && (
              <div className="mt-4 p-4 bg-gray-50 rounded-xl">
                <h3 className="font-semibold text-gray-700 mb-2">
                  {searchResults.total} resultado(s) encontrado(s)
                </h3>
                {searchResults.resultados.map((r, i) => (
                  <div key={i} className="bg-white p-3 rounded-lg mb-2 border border-gray-100">
                    <p className="text-sm text-gray-500">
                      Edição nº {r.numero_edicao} - {formatDate(r.data_publicacao)}
                    </p>
                    <p className="font-medium text-gray-800">{r.publicacao.titulo}</p>
                    <p className="text-sm text-gray-600 line-clamp-2">{r.publicacao.texto}</p>
                  </div>
                ))}
                {searchResults.total === 0 && (
                  <p className="text-gray-500 text-center py-4">
                    Nenhum resultado encontrado para "{searchTerm}"
                  </p>
                )}
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Coluna Principal - Edições por Ano */}
            <div className="lg:col-span-2">
              <div className="bg-white/95 backdrop-blur-lg rounded-2xl shadow-xl overflow-hidden">
                <div className="bg-gradient-to-r from-primary to-primary/80 p-5">
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <FileText size={24} />
                    EDIÇÕES POR ANO
                  </h2>
                </div>
                
                <div className="p-4">
                  {loading ? (
                    <div className="flex justify-center py-12">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                    </div>
                  ) : edicoesporAno.length === 0 ? (
                    <p className="text-center text-gray-500 py-8">
                      Nenhuma edição publicada ainda
                    </p>
                  ) : (
                    edicoesporAno.map(({ ano, edicoes: eds }) => (
                      <div key={ano} className="mb-2">
                        <button
                          onClick={() => setAnoExpandido(anoExpandido === ano ? null : ano)}
                          className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 rounded-xl transition-colors"
                        >
                          <span className="flex items-center gap-3 font-semibold text-gray-700">
                            <Calendar className="text-primary" size={20} />
                            📁 {ano}
                            <span className="text-sm font-normal text-gray-500">
                              ({eds.length} edição{eds.length !== 1 ? 'ões' : ''})
                            </span>
                          </span>
                          {anoExpandido === ano ? (
                            <ChevronDown className="text-gray-400" size={20} />
                          ) : (
                            <ChevronRight className="text-gray-400" size={20} />
                          )}
                        </button>
                        
                        {anoExpandido === ano && eds.length > 0 && (
                          <div className="ml-8 mt-2 space-y-2">
                            {eds.map((edicao) => (
                              <div
                                key={edicao.edicao_id}
                                className="flex items-center justify-between p-3 bg-white border border-gray-100 rounded-lg hover:border-primary/30 transition-colors cursor-pointer"
                                onClick={() => setSelectedEdicao(edicao)}
                              >
                                <div>
                                  <span className="font-medium text-gray-800">
                                    📄 Edição {edicao.numero_edicao}
                                  </span>
                                  <span className="text-sm text-gray-500 ml-2">
                                    - {formatDate(edicao.data_publicacao)}
                                  </span>
                                </div>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleDownloadPDF(edicao);
                                  }}
                                  className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
                                >
                                  <Download size={14} />
                                  PDF
                                </button>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* Coluna Lateral - Última Edição */}
            <div className="lg:col-span-1">
              <div className="bg-white/95 backdrop-blur-lg rounded-2xl shadow-xl overflow-hidden sticky top-4">
                <div className="bg-gradient-to-r from-green-600 to-green-500 p-5">
                  <h2 className="text-xl font-bold text-white">
                    ÚLTIMA EDIÇÃO PUBLICADA
                  </h2>
                </div>
                
                <div className="p-5">
                  {ultimaEdicao ? (
                    <div>
                      <div className="flex items-center gap-2 mb-3">
                        <Newspaper className="text-primary" size={24} />
                        <span className="text-xl font-bold text-gray-800">
                          Edição nº {ultimaEdicao.numero_edicao}
                        </span>
                      </div>
                      
                      <p className="text-sm text-gray-500 mb-4">
                        {formatDate(ultimaEdicao.data_publicacao)}
                      </p>
                      
                      {ultimaEdicao.assinatura_digital?.assinado && (
                        <div className="flex items-center gap-1 text-green-600 text-sm mb-4">
                          <CheckCircle size={16} />
                          Assinado digitalmente
                        </div>
                      )}
                      
                      <div className="mb-4">
                        <p className="text-sm font-medium text-gray-600 mb-2">
                          Publicações:
                        </p>
                        {ultimaEdicao.publicacoes?.map((pub, i) => (
                          <p key={i} className="text-sm text-gray-700 mb-1">
                            • {pub.titulo}
                          </p>
                        ))}
                      </div>
                      
                      <div className="flex gap-2">
                        <button
                          onClick={() => setSelectedEdicao(ultimaEdicao)}
                          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                        >
                          Ver Completo
                        </button>
                        <button
                          onClick={() => handleDownloadPDF(ultimaEdicao)}
                          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          <Download size={18} />
                          Baixar PDF
                        </button>
                      </div>
                    </div>
                  ) : (
                    <p className="text-gray-500 text-center py-8">
                      Nenhuma edição publicada
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </main>

        {/* Modal de Visualização da Edição */}
        {selectedEdicao && (
          <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={() => setSelectedEdicao(null)}>
            <div 
              className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="sticky top-0 bg-gradient-to-r from-primary to-primary/80 p-6 text-white">
                <div className="flex justify-between items-start">
                  <div>
                    <h2 className="text-2xl font-bold">
                      DOEM - Edição nº {selectedEdicao.numero_edicao}
                    </h2>
                    <p className="text-white/80">
                      {formatDate(selectedEdicao.data_publicacao)}
                    </p>
                  </div>
                  <button
                    onClick={() => setSelectedEdicao(null)}
                    className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                  >
                    ✕
                  </button>
                </div>
              </div>
              
              <div className="p-6">
                <h3 className="text-lg font-bold text-gray-800 mb-4 pb-2 border-b border-gray-200">
                  PODER EXECUTIVO
                </h3>
                
                {selectedEdicao.publicacoes?.map((pub, i) => (
                  <div key={i} className="mb-6 pb-6 border-b border-gray-100 last:border-0">
                    <span className="inline-block px-2 py-1 bg-primary/10 text-primary text-xs font-medium rounded mb-2">
                      {pub.tipo}
                    </span>
                    <p className="text-xs text-gray-500 mb-1">{pub.secretaria}</p>
                    <h4 className="text-lg font-bold text-gray-800 mb-3">
                      {pub.titulo}
                    </h4>
                    <div className="text-gray-700 whitespace-pre-wrap text-justify leading-relaxed">
                      {pub.texto}
                    </div>
                  </div>
                ))}
                
                {selectedEdicao.assinatura_digital?.assinado && (
                  <div className="mt-6 p-4 bg-green-50 rounded-xl">
                    <p className="text-green-700 font-medium flex items-center gap-2">
                      <CheckCircle size={18} />
                      Este documento foi assinado digitalmente
                    </p>
                    <p className="text-green-600 text-sm mt-1">
                      Hash: {selectedEdicao.assinatura_digital.hash_documento?.slice(0, 32)}...
                    </p>
                  </div>
                )}
                
                <div className="mt-6 flex justify-end">
                  <button
                    onClick={() => handleDownloadPDF(selectedEdicao)}
                    className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors font-semibold"
                  >
                    <Download size={20} />
                    Baixar PDF Completo
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <footer className="bg-slate-900/95 backdrop-blur-lg border-t border-white/10 py-6 mt-12">
          <div className="max-w-7xl mx-auto px-4 text-center">
            <p className="text-slate-400 text-sm">
              Prefeitura Municipal de Acaiaca | CNPJ: 18.294.659/0001-71
            </p>
            <p className="text-slate-500 text-xs mt-2">
              Desenvolvido por Cristiano Abdo de Souza - Assessor de Planejamento, Compras e Logística
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default DOEMPublico;
