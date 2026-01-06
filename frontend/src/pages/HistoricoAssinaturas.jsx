import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  FileSignature, Calendar, FileText, CheckCircle, XCircle, 
  ExternalLink, RefreshCw, Search, Filter, Clock, BarChart3,
  TrendingUp, Award, Shield
} from 'lucide-react';
import Layout from '../components/Layout';
import api from '../utils/api';
import { toast } from 'sonner';
import Pagination, { usePagination } from '../components/Pagination';

const HistoricoAssinaturas = () => {
  const navigate = useNavigate();
  const [assinaturas, setAssinaturas] = useState([]);
  const [estatisticas, setEstatisticas] = useState(null);
  const [loading, setLoading] = useState(true);
  const [totalItems, setTotalItems] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  
  const { currentPage, setCurrentPage, pageSize, setPageSize, resetPage } = usePagination(10);

  useEffect(() => {
    fetchHistorico();
    fetchEstatisticas();
  }, [currentPage, pageSize]);

  const fetchHistorico = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/assinaturas/historico?page=${currentPage}&page_size=${pageSize}`);
      setAssinaturas(response.data.items);
      setTotalItems(response.data.total);
    } catch (error) {
      toast.error('Erro ao carregar histórico de assinaturas');
    } finally {
      setLoading(false);
    }
  };

  const fetchEstatisticas = async () => {
    try {
      const response = await api.get('/assinaturas/estatisticas');
      setEstatisticas(response.data);
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleString('pt-BR');
  };

  const filteredAssinaturas = assinaturas.filter(sig => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      sig.document_type?.toLowerCase().includes(term) ||
      sig.validation_code?.toLowerCase().includes(term)
    );
  });

  return (
    <Layout>
      <div className="space-y-6" data-testid="historico-assinaturas-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h2 className="text-3xl font-heading font-bold text-foreground flex items-center gap-3">
              <FileSignature size={32} className="text-primary" />
              Histórico de Assinaturas
            </h2>
            <p className="text-muted-foreground mt-1">
              Documentos que você assinou digitalmente
            </p>
          </div>
          <button
            onClick={() => { fetchHistorico(); fetchEstatisticas(); }}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            <RefreshCw size={18} />
            Atualizar
          </button>
        </div>

        {/* Cards de Estatísticas */}
        {estatisticas && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total de Assinaturas</p>
                  <p className="text-3xl font-bold text-foreground mt-1">
                    {estatisticas.total_assinaturas}
                  </p>
                </div>
                <div className="p-3 bg-primary/10 rounded-full">
                  <Award size={24} className="text-primary" />
                </div>
              </div>
            </div>

            <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Documentos Válidos</p>
                  <p className="text-3xl font-bold text-green-600 mt-1">
                    {estatisticas.assinaturas_validas}
                  </p>
                </div>
                <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-full">
                  <CheckCircle size={24} className="text-green-600" />
                </div>
              </div>
            </div>

            <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Últimos 30 dias</p>
                  <p className="text-3xl font-bold text-blue-600 mt-1">
                    {estatisticas.ultimos_30_dias}
                  </p>
                </div>
                <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-full">
                  <TrendingUp size={24} className="text-blue-600" />
                </div>
              </div>
            </div>

            <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Tipos de Documento</p>
                  <p className="text-3xl font-bold text-purple-600 mt-1">
                    {estatisticas.por_tipo?.length || 0}
                  </p>
                </div>
                <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-full">
                  <BarChart3 size={24} className="text-purple-600" />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Última Assinatura */}
        {estatisticas?.ultima_assinatura && (
          <div className="bg-gradient-to-r from-primary/10 to-primary/5 border border-primary/20 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <Clock size={20} className="text-primary" />
              <div>
                <p className="text-sm text-muted-foreground">Última assinatura</p>
                <p className="font-medium text-foreground">
                  {estatisticas.ultima_assinatura.document_type} - {' '}
                  <span className="font-mono text-primary">
                    {estatisticas.ultima_assinatura.validation_code}
                  </span>
                  <span className="text-muted-foreground ml-2">
                    em {formatDate(estatisticas.ultima_assinatura.created_at)}
                  </span>
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Filtro e Busca */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Buscar por tipo de documento ou código..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
              data-testid="search-assinaturas"
            />
          </div>
        </div>

        {/* Tabela de Assinaturas */}
        <div className="bg-card rounded-xl border border-border shadow-sm overflow-hidden">
          {loading ? (
            <div className="flex justify-center items-center py-20">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
          ) : filteredAssinaturas.length === 0 ? (
            <div className="text-center py-20 text-muted-foreground">
              <FileSignature size={48} className="mx-auto mb-4 opacity-50" />
              <p className="text-lg">Nenhuma assinatura encontrada</p>
              <p className="text-sm mt-2">Quando você assinar documentos, eles aparecerão aqui.</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-muted text-foreground">
                    <tr>
                      <th className="px-4 py-3 text-left">Documento</th>
                      <th className="px-4 py-3 text-center">Código de Validação</th>
                      <th className="px-4 py-3 text-center">Data/Hora</th>
                      <th className="px-4 py-3 text-center">Assinantes</th>
                      <th className="px-4 py-3 text-center">Status</th>
                      <th className="px-4 py-3 text-center">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredAssinaturas.map((sig) => (
                      <tr key={sig.signature_id} className="border-b border-border hover:bg-muted/50 transition-colors">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <FileText size={18} className="text-muted-foreground" />
                            <div>
                              <p className="font-medium text-foreground">{sig.document_type}</p>
                              <p className="text-xs text-muted-foreground">
                                {sig.my_signature?.cargo || 'Sem cargo'}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <code className="px-2 py-1 bg-muted rounded text-xs font-mono">
                            {sig.validation_code}
                          </code>
                        </td>
                        <td className="px-4 py-3 text-center text-xs">
                          {formatDate(sig.created_at)}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full text-xs">
                            {sig.total_signers} assinante{sig.total_signers > 1 ? 's' : ''}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          {sig.is_valid ? (
                            <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-xs">
                              <CheckCircle size={12} />
                              Válido
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-full text-xs">
                              <XCircle size={12} />
                              Revogado
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <a
                            href={`/validar?code=${sig.validation_code}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 px-3 py-1.5 text-xs bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                          >
                            <Shield size={12} />
                            Validar
                            <ExternalLink size={10} />
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Paginação */}
              <div className="p-4 border-t border-border">
                <Pagination
                  currentPage={currentPage}
                  totalItems={totalItems}
                  pageSize={pageSize}
                  onPageChange={setCurrentPage}
                  onPageSizeChange={setPageSize}
                />
              </div>
            </>
          )}
        </div>

        {/* Tipos de Documento */}
        {estatisticas?.por_tipo && estatisticas.por_tipo.length > 0 && (
          <div className="bg-card rounded-xl border border-border shadow-sm p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <BarChart3 size={20} className="text-primary" />
              Assinaturas por Tipo de Documento
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {estatisticas.por_tipo.map((tipo, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                  <span className="text-sm text-foreground truncate">{tipo.tipo}</span>
                  <span className="px-2 py-1 bg-primary/10 text-primary rounded text-sm font-semibold">
                    {tipo.quantidade}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default HistoricoAssinaturas;
