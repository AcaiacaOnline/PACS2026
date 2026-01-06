import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { Plus, Edit, Trash2, Building2, Calendar } from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';
import Pagination, { usePagination } from '../components/Pagination';

const PACGeralList = () => {
  const navigate = useNavigate();
  const [pacs, setPacs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  const [anos, setAnos] = useState([]);
  const [anoSelecionado, setAnoSelecionado] = useState(null);
  const [totalPacs, setTotalPacs] = useState(0);
  
  // Paginação
  const { currentPage, setCurrentPage, pageSize, setPageSize, resetPage } = usePagination(20);

  useEffect(() => {
    fetchAnos();
    loadUser();
  }, []);

  useEffect(() => {
    if (anoSelecionado !== null) {
      fetchPACs();
    }
  }, [anoSelecionado, currentPage, pageSize]);

  const loadUser = () => {
    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
    }
  };

  const fetchAnos = async () => {
    try {
      const response = await api.get('/pacs-geral/anos');
      setAnos(response.data.anos);
      setAnoSelecionado(response.data.ano_atual);
    } catch (error) {
      console.error('Erro ao carregar anos:', error);
      setAnoSelecionado(new Date().getFullYear());
    }
  };

  const fetchPACs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (anoSelecionado) params.append('ano', anoSelecionado);
      params.append('page', currentPage);
      params.append('page_size', pageSize);
      
      const response = await api.get(`/pacs-geral/paginado?${params.toString()}`);
      setPacs(response.data.items);
      setTotalPacs(response.data.total);
    } catch (error) {
      toast.error('Erro ao carregar PACs Gerais');
      // Fallback para endpoint antigo
      try {
        const params = anoSelecionado ? `?ano=${anoSelecionado}` : '';
        const response = await api.get(`/pacs-geral${params}`);
        setPacs(response.data);
        setTotalPacs(response.data.length);
      } catch (e) {
        console.error('Erro no fallback:', e);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Tem certeza que deseja excluir este PAC Geral?')) return;
    
    try {
      await api.delete(`/pacs-geral/${id}`);
      toast.success('PAC Geral excluído com sucesso!');
      fetchPACs();
    } catch (error) {
      toast.error('Erro ao excluir PAC Geral');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const getSecretariasSiglas = (secretarias) => {
    if (!secretarias || secretarias.length === 0) return '-';
    if (secretarias.length === 9) return 'TODAS';
    return secretarias.join(', ');
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto p-6">
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center space-x-3">
            <Building2 className="text-primary" size={32} />
            <div>
              <h1 className="text-3xl font-heading font-bold text-foreground">PAC Geral</h1>
              <p className="text-muted-foreground">Plano Anual de Contratações Compartilhado</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {/* Seletor de Ano */}
            <div className="flex items-center gap-2 bg-card border border-border rounded-lg px-3 py-2">
              <Calendar size={18} className="text-primary" />
              <select
                value={anoSelecionado || ''}
                onChange={(e) => setAnoSelecionado(parseInt(e.target.value))}
                data-testid="year-filter-select-geral"
                className="bg-transparent border-none outline-none text-foreground font-semibold cursor-pointer"
              >
                {anos.map((ano) => (
                  <option key={ano} value={ano}>
                    📁 {ano}
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={() => navigate('/pacs-geral/new')}
              className="flex items-center space-x-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors shadow-md"
            >
              <Plus size={20} />
              <span>Novo PAC Geral</span>
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        ) : pacs.length === 0 ? (
          <div className="bg-card border border-border rounded-xl p-12 text-center">
            <Building2 className="mx-auto text-muted-foreground mb-4" size={64} />
            <h3 className="text-xl font-semibold text-foreground mb-2">Nenhum PAC Geral cadastrado</h3>
            <p className="text-muted-foreground mb-6">Clique no botão acima para criar seu primeiro PAC Geral</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {pacs.map((pac) => (
              <div
                key={pac.pac_geral_id}
                className="bg-card border border-border rounded-xl p-6 hover:shadow-lg transition-shadow"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-foreground mb-1">{pac.nome_secretaria}</h3>
                    <p className="text-sm text-muted-foreground">{pac.secretario}</p>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => navigate(`/pacs-geral/${pac.pac_geral_id}/edit`)}
                      className="text-accent hover:text-accent/80 transition-colors p-2"
                      title="Editar"
                    >
                      <Edit size={18} />
                    </button>
                    {user?.is_admin && (
                      <button
                        onClick={() => handleDelete(pac.pac_geral_id)}
                        className="text-destructive hover:text-destructive/80 transition-colors p-2"
                        title="Excluir"
                      >
                        <Trash2 size={18} />
                      </button>
                    )}
                  </div>
                </div>

                <div className="space-y-2 text-sm">
                  <div>
                    <span className="font-semibold text-foreground">Secretarias:</span>
                    <span className="text-muted-foreground ml-2">
                      {getSecretariasSiglas(pac.secretarias_selecionadas)}
                    </span>
                  </div>
                  <div>
                    <span className="font-semibold text-foreground">Contato:</span>
                    <span className="text-muted-foreground ml-2">{pac.telefone}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-foreground">Criado em:</span>
                    <span className="text-muted-foreground ml-2">{formatDate(pac.created_at)}</span>
                  </div>
                </div>

                <button
                  onClick={() => navigate(`/pacs-geral/${pac.pac_geral_id}/edit`)}
                  className="w-full mt-4 bg-secondary text-secondary-foreground py-2 rounded-lg hover:bg-secondary/90 transition-colors font-semibold"
                >
                  Abrir PAC Geral
                </button>
              </div>
            ))}
          </div>
        )}
        
        {/* Paginação */}
        {totalPacs > 0 && (
          <div className="mt-6 bg-card rounded-lg border border-border p-4">
            <Pagination
              currentPage={currentPage}
              totalItems={totalPacs}
              pageSize={pageSize}
              onPageChange={setCurrentPage}
              onPageSizeChange={setPageSize}
            />
          </div>
        )}
      </div>
    </Layout>
  );
};

export default PACGeralList;