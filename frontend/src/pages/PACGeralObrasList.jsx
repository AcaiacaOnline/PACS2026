import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, FileText, Trash2, Edit, Building2, Hammer, ArrowRight } from 'lucide-react';
import Layout from '../components/Layout';
import api from '../utils/api';
import { toast } from 'sonner';

const PACGeralObrasList = () => {
  const navigate = useNavigate();
  const [pacs, setPacs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingPac, setEditingPac] = useState(null);
  const [formData, setFormData] = useState({
    nome_secretaria: '',
    secretario: '',
    fiscal_contrato: '',
    telefone: '',
    email: '',
    endereco: '',
    cep: '',
    ano: '2026',
    tipo_contratacao: 'OBRAS',
    secretarias_selecionadas: ['AD', 'OB']
  });

  const SECRETARIAS = [
    { sigla: 'AD', nome: 'Administração' },
    { sigla: 'FA', nome: 'Fazenda' },
    { sigla: 'SA', nome: 'Saúde' },
    { sigla: 'SE', nome: 'Educação' },
    { sigla: 'AS', nome: 'Assistência Social' },
    { sigla: 'AG', nome: 'Agricultura' },
    { sigla: 'OB', nome: 'Obras' },
    { sigla: 'TR', nome: 'Transporte' },
    { sigla: 'CUL', nome: 'Cultura' }
  ];

  useEffect(() => {
    fetchPacs();
  }, []);

  const fetchPacs = async () => {
    try {
      const response = await api.get('/pacs-geral-obras');
      setPacs(response.data);
    } catch (error) {
      toast.error('Erro ao carregar PACs Obras');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingPac) {
        await api.put(`/pacs-geral-obras/${editingPac.pac_obras_id}`, formData);
        toast.success('PAC Obras atualizado!');
      } else {
        await api.post('/pacs-geral-obras', formData);
        toast.success('PAC Obras criado!');
      }
      setShowModal(false);
      setEditingPac(null);
      fetchPacs();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar');
    }
  };

  const handleDelete = async (pac) => {
    if (!window.confirm(`Excluir PAC Obras "${pac.nome_secretaria}"?`)) return;
    try {
      await api.delete(`/pacs-geral-obras/${pac.pac_obras_id}`);
      toast.success('PAC Obras excluído!');
      fetchPacs();
    } catch (error) {
      toast.error('Erro ao excluir');
    }
  };

  const openModal = (pac = null) => {
    if (pac) {
      setEditingPac(pac);
      setFormData({
        nome_secretaria: pac.nome_secretaria,
        secretario: pac.secretario,
        fiscal_contrato: pac.fiscal_contrato || '',
        telefone: pac.telefone,
        email: pac.email,
        endereco: pac.endereco,
        cep: pac.cep,
        ano: pac.ano,
        tipo_contratacao: pac.tipo_contratacao || 'OBRAS',
        secretarias_selecionadas: pac.secretarias_selecionadas || []
      });
    } else {
      setEditingPac(null);
      setFormData({
        nome_secretaria: '',
        secretario: '',
        fiscal_contrato: '',
        telefone: '',
        email: '',
        endereco: '',
        cep: '',
        ano: '2026',
        tipo_contratacao: 'OBRAS',
        secretarias_selecionadas: ['AD', 'OB']
      });
    }
    setShowModal(true);
  };

  const toggleSecretaria = (sigla) => {
    setFormData(prev => ({
      ...prev,
      secretarias_selecionadas: prev.secretarias_selecionadas.includes(sigla)
        ? prev.secretarias_selecionadas.filter(s => s !== sigla)
        : [...prev.secretarias_selecionadas, sigla]
    }));
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
              <Hammer className="text-amber-600" />
              PAC Geral - Obras e Serviços
            </h1>
            <p className="text-muted-foreground">
              Plano Anual de Contratações para Obras e Serviços de Engenharia
            </p>
          </div>
          <button
            onClick={() => openModal()}
            className="flex items-center gap-2 bg-amber-600 text-white px-4 py-2 rounded-lg hover:bg-amber-700 transition-colors"
            data-testid="create-pac-obras-btn"
          >
            <Plus size={18} />
            Novo PAC Obras
          </button>
        </div>

        {/* Lista de PACs */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600 mx-auto"></div>
          </div>
        ) : pacs.length === 0 ? (
          <div className="bg-card border border-border rounded-xl p-12 text-center">
            <Hammer size={48} className="mx-auto mb-4 text-muted-foreground opacity-50" />
            <h3 className="text-lg font-semibold text-foreground mb-2">Nenhum PAC Obras cadastrado</h3>
            <p className="text-muted-foreground mb-4">
              Crie seu primeiro PAC Geral para Obras e Serviços
            </p>
            <button
              onClick={() => openModal()}
              className="bg-amber-600 text-white px-4 py-2 rounded-lg hover:bg-amber-700"
            >
              Criar PAC Obras
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {pacs.map((pac) => (
              <div
                key={pac.pac_obras_id}
                className="bg-card border border-border rounded-xl p-4 hover:shadow-lg transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-amber-100 rounded-lg">
                      <Hammer className="text-amber-600" size={20} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-foreground">{pac.nome_secretaria}</h3>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        pac.tipo_contratacao === 'OBRAS' 
                          ? 'bg-orange-100 text-orange-700' 
                          : 'bg-blue-100 text-blue-700'
                      }`}>
                        {pac.tipo_contratacao}
                      </span>
                    </div>
                  </div>
                  <span className="text-xs bg-muted px-2 py-1 rounded">{pac.ano}</span>
                </div>

                <div className="space-y-1 text-sm text-muted-foreground mb-4">
                  <p><strong>Secretário:</strong> {pac.secretario}</p>
                  {pac.fiscal_contrato && <p><strong>Fiscal:</strong> {pac.fiscal_contrato}</p>}
                  <p><strong>Email:</strong> {pac.email}</p>
                </div>

                <div className="flex flex-wrap gap-1 mb-4">
                  {pac.secretarias_selecionadas?.map(s => (
                    <span key={s} className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded">
                      {s}
                    </span>
                  ))}
                </div>

                <div className="flex justify-between items-center pt-3 border-t border-border">
                  <div className="flex gap-2">
                    <button
                      onClick={() => openModal(pac)}
                      className="p-2 text-primary hover:bg-primary/10 rounded-lg"
                      title="Editar"
                    >
                      <Edit size={16} />
                    </button>
                    <button
                      onClick={() => handleDelete(pac)}
                      className="p-2 text-destructive hover:bg-destructive/10 rounded-lg"
                      title="Excluir"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                  <button
                    onClick={() => navigate(`/pacs-geral-obras/${pac.pac_obras_id}`)}
                    className="flex items-center gap-1 text-sm text-amber-600 hover:text-amber-700"
                    data-testid="open-pac-obras-btn"
                  >
                    Abrir <ArrowRight size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black/50 flex items-start justify-center z-50 p-4 pt-8 overflow-y-auto">
            <div className="bg-card rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-card border-b border-border px-6 py-4">
                <h3 className="text-xl font-bold text-foreground">
                  {editingPac ? 'Editar PAC Obras' : 'Novo PAC Obras'}
                </h3>
              </div>

              <form onSubmit={handleSubmit} className="p-6 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Nome da Secretaria *</label>
                    <input
                      type="text"
                      value={formData.nome_secretaria}
                      onChange={(e) => setFormData({...formData, nome_secretaria: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Secretário *</label>
                    <input
                      type="text"
                      value={formData.secretario}
                      onChange={(e) => setFormData({...formData, secretario: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Fiscal do Contrato</label>
                    <input
                      type="text"
                      value={formData.fiscal_contrato}
                      onChange={(e) => setFormData({...formData, fiscal_contrato: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Tipo de Contratação *</label>
                    <select
                      value={formData.tipo_contratacao}
                      onChange={(e) => setFormData({...formData, tipo_contratacao: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                    >
                      <option value="OBRAS">Obras e Instalações</option>
                      <option value="SERVICOS">Serviços de Engenharia</option>
                      <option value="TIC">Serviços de TIC</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Telefone *</label>
                    <input
                      type="text"
                      value={formData.telefone}
                      onChange={(e) => setFormData({...formData, telefone: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Email *</label>
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium mb-1">Endereço *</label>
                    <input
                      type="text"
                      value={formData.endereco}
                      onChange={(e) => setFormData({...formData, endereco: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">CEP *</label>
                    <input
                      type="text"
                      value={formData.cep}
                      onChange={(e) => setFormData({...formData, cep: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Secretarias Envolvidas *</label>
                  <div className="flex flex-wrap gap-2">
                    {SECRETARIAS.map(s => (
                      <button
                        key={s.sigla}
                        type="button"
                        onClick={() => toggleSecretaria(s.sigla)}
                        className={`px-3 py-1 rounded-lg text-sm transition-colors ${
                          formData.secretarias_selecionadas.includes(s.sigla)
                            ? 'bg-amber-600 text-white'
                            : 'bg-muted text-muted-foreground hover:bg-muted/80'
                        }`}
                      >
                        {s.sigla} - {s.nome}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-border">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 border border-input rounded-lg hover:bg-muted"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700"
                  >
                    {editingPac ? 'Salvar' : 'Criar'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default PACGeralObrasList;
