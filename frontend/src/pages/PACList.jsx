import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Edit, Trash2, Plus, FolderOpen } from 'lucide-react';
import Layout from '../components/Layout';
import api from '../utils/api';
import { toast } from 'sonner';

const PACList = () => {
  const navigate = useNavigate();
  const [pacs, setPacs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState(null);

  useEffect(() => {
    fetchCurrentUser();
    fetchPACs();
  }, []);

  const fetchCurrentUser = async () => {
    try {
      const response = await api.get('/auth/me');
      setCurrentUser(response.data);
    } catch (error) {
      console.error('Error fetching user:', error);
    }
  };

  const fetchPACs = async () => {
    try {
      const response = await api.get('/pacs');
      setPacs(response.data);
    } catch (error) {
      toast.error('Erro ao carregar PACs');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (pacId) => {
    if (!window.confirm('ATENÇÃO: Isso excluirá o PAC e TODOS os itens associados. Deseja continuar?')) {
      return;
    }

    try {
      await api.delete(`/pacs/${pacId}`);
      toast.success('PAC excluído com sucesso!');
      fetchPACs();
    } catch (error) {
      toast.error('Erro ao excluir PAC');
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value || 0);
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6" data-testid="pac-list">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-heading font-bold text-foreground">Meus PACs Salvos</h2>
            <p className="text-muted-foreground mt-1">{pacs.length} PAC(s) cadastrado(s)</p>
          </div>
          <button
            onClick={() => navigate('/pacs/new')}
            data-testid="create-pac-btn"
            className="flex items-center gap-2 bg-secondary text-secondary-foreground px-4 py-2 rounded-lg hover:bg-secondary/90 transition-colors shadow-sm"
          >
            <Plus size={18} />
            Criar Novo PAC
          </button>
        </div>

        {pacs.length === 0 ? (
          <div className="bg-card p-12 rounded-lg border border-border text-center">
            <FolderOpen className="mx-auto w-16 h-16 text-muted-foreground/50 mb-4" />
            <h3 className="text-xl font-heading font-semibold text-foreground mb-2">
              Nenhum PAC cadastrado
            </h3>
            <p className="text-muted-foreground mb-6">
              Você ainda não possui PACs salvos. Clique em "Criar Novo PAC" para começar.
            </p>
            <button
              onClick={() => navigate('/pacs/new')}
              className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-6 py-3 rounded-lg hover:bg-primary/90 transition-colors"
            >
              <Plus size={18} />
              Criar Primeiro PAC
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {pacs.map((pac) => (
              <div
                key={pac.pac_id}
                data-testid={`pac-item-${pac.pac_id}`}
                className="bg-card p-6 rounded-lg border border-border shadow-sm hover:shadow-md transition-all"
              >
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div className="flex-grow">
                    <h3 className="text-xl font-heading font-bold text-foreground mb-2 flex items-center gap-2">
                      {pac.secretaria || 'Sem Nome'}
                      {currentUser && pac.user_id !== currentUser.user_id && (
                        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full font-normal">
                          Somente Leitura
                        </span>
                      )}
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-sm">
                      <div>
                        <span className="font-semibold text-muted-foreground">Responsável:</span>
                        <span className="ml-2 text-foreground">{pac.secretario}</span>
                      </div>
                      <div>
                        <span className="font-semibold text-muted-foreground">Total:</span>
                        <span className="ml-2 text-foreground font-mono">
                          {formatCurrency(pac.total_value)}
                        </span>
                      </div>
                      <div>
                        <span className="font-semibold text-muted-foreground">Atualizado:</span>
                        <span className="ml-2 text-foreground">{formatDate(pac.updated_at)}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {(currentUser?.is_admin || pac.user_id === currentUser?.user_id) ? (
                      <>
                        <button
                          onClick={() => navigate(`/pacs/${pac.pac_id}/edit`)}
                          data-testid={`edit-pac-${pac.pac_id}`}
                          className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors"
                        >
                          <Edit size={16} />
                          Editar
                        </button>
                        <button
                          onClick={() => handleDelete(pac.pac_id)}
                          data-testid={`delete-pac-${pac.pac_id}`}
                          className="flex items-center gap-2 bg-destructive text-destructive-foreground px-4 py-2 rounded-lg hover:bg-destructive/90 transition-colors"
                        >
                          <Trash2 size={16} />
                          Excluir
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => navigate(`/pacs/${pac.pac_id}/edit`)}
                        data-testid={`view-pac-${pac.pac_id}`}
                        className="flex items-center gap-2 bg-muted text-foreground px-4 py-2 rounded-lg hover:bg-muted/80 transition-colors"
                      >
                        <FolderOpen size={16} />
                        Visualizar
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default PACList;
