import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Plus, FileText, Trash2, Edit, DollarSign, Users, Building2, 
  ArrowRight, Calendar, CheckCircle, Clock, AlertCircle
} from 'lucide-react';
import Layout from '../components/Layout';
import api from '../utils/api';
import { toast } from 'sonner';
import { maskCNPJ } from '../utils/masks';

const STATUS_COLORS = {
  'ELABORACAO': { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Em Elaboração' },
  'APROVADO': { bg: 'bg-green-100', text: 'text-green-700', label: 'Aprovado' },
  'EXECUCAO': { bg: 'bg-amber-100', text: 'text-amber-700', label: 'Em Execução' },
  'PRESTACAO_CONTAS': { bg: 'bg-purple-100', text: 'text-purple-700', label: 'Prestação de Contas' },
  'CONCLUIDO': { bg: 'bg-emerald-100', text: 'text-emerald-700', label: 'Concluído' }
};

const STATUS_OPTIONS = ['ELABORACAO', 'APROVADO', 'EXECUCAO', 'PRESTACAO_CONTAS', 'CONCLUIDO'];

const PrestacaoContasList = () => {
  const navigate = useNavigate();
  const [projetos, setProjetos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingProjeto, setEditingProjeto] = useState(null);
  const [formData, setFormData] = useState({
    nome_projeto: '',
    objeto: '',
    organizacao_parceira: '',
    cnpj_parceira: '',
    responsavel_osc: '',
    data_inicio: '',
    data_conclusao: '',
    prazo_meses: 12,
    valor_total: 0,
    valor_repasse_publico: 0,
    valor_contrapartida: 0,
    status: 'ELABORACAO'
  });

  useEffect(() => {
    fetchProjetos();
  }, []);

  const fetchProjetos = async () => {
    try {
      const response = await api.get('/mrosc/projetos');
      setProjetos(response.data);
    } catch (error) {
      toast.error('Erro ao carregar projetos');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        data_inicio: new Date(formData.data_inicio).toISOString(),
        data_conclusao: new Date(formData.data_conclusao).toISOString()
      };

      if (editingProjeto) {
        await api.put(`/mrosc/projetos/${editingProjeto.projeto_id}`, payload);
        toast.success('Projeto atualizado!');
      } else {
        await api.post('/mrosc/projetos', payload);
        toast.success('Projeto criado!');
      }
      setShowModal(false);
      setEditingProjeto(null);
      fetchProjetos();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar');
    }
  };

  const handleDelete = async (projeto) => {
    if (!window.confirm(`Excluir projeto "${projeto.nome_projeto}"? Esta ação também excluirá todos os dados de RH e despesas.`)) return;
    try {
      await api.delete(`/mrosc/projetos/${projeto.projeto_id}`);
      toast.success('Projeto excluído!');
      fetchProjetos();
    } catch (error) {
      toast.error('Erro ao excluir');
    }
  };

  const openModal = (projeto = null) => {
    if (projeto) {
      setEditingProjeto(projeto);
      setFormData({
        nome_projeto: projeto.nome_projeto,
        objeto: projeto.objeto,
        organizacao_parceira: projeto.organizacao_parceira,
        cnpj_parceira: projeto.cnpj_parceira,
        responsavel_osc: projeto.responsavel_osc,
        data_inicio: projeto.data_inicio?.split('T')[0] || '',
        data_conclusao: projeto.data_conclusao?.split('T')[0] || '',
        prazo_meses: projeto.prazo_meses,
        valor_total: projeto.valor_total,
        valor_repasse_publico: projeto.valor_repasse_publico,
        valor_contrapartida: projeto.valor_contrapartida,
        status: projeto.status
      });
    } else {
      setEditingProjeto(null);
      setFormData({
        nome_projeto: '',
        objeto: '',
        organizacao_parceira: '',
        cnpj_parceira: '',
        responsavel_osc: '',
        data_inicio: '',
        data_conclusao: '',
        prazo_meses: 12,
        valor_total: 0,
        valor_repasse_publico: 0,
        valor_contrapartida: 0,
        status: 'ELABORACAO'
      });
    }
    setShowModal(true);
  };

  const formatCurrency = (value) => {
    return (value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('pt-BR');
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
              <DollarSign className="text-green-600" />
              Prestação de Contas - MROSC
            </h1>
            <p className="text-muted-foreground">
              Lei 13.019/2014 - Marco Regulatório das Organizações da Sociedade Civil
            </p>
          </div>
          <button
            onClick={() => openModal()}
            className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
            data-testid="create-projeto-mrosc-btn"
          >
            <Plus size={18} />
            Novo Projeto
          </button>
        </div>

        {/* Estatísticas */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-card border border-border rounded-xl p-4">
            <div className="text-sm text-muted-foreground">Total de Projetos</div>
            <div className="text-2xl font-bold text-foreground">{projetos.length}</div>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <div className="text-sm text-muted-foreground">Em Execução</div>
            <div className="text-2xl font-bold text-amber-600">
              {projetos.filter(p => p.status === 'EXECUCAO').length}
            </div>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <div className="text-sm text-muted-foreground">Valor Total</div>
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(projetos.reduce((sum, p) => sum + (p.valor_total || 0), 0))}
            </div>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <div className="text-sm text-muted-foreground">Repasse Público</div>
            <div className="text-2xl font-bold text-blue-600">
              {formatCurrency(projetos.reduce((sum, p) => sum + (p.valor_repasse_publico || 0), 0))}
            </div>
          </div>
        </div>

        {/* Lista de Projetos */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto"></div>
          </div>
        ) : projetos.length === 0 ? (
          <div className="bg-card border border-border rounded-xl p-12 text-center">
            <DollarSign size={48} className="mx-auto mb-4 text-muted-foreground opacity-50" />
            <h3 className="text-lg font-semibold text-foreground mb-2">Nenhum projeto cadastrado</h3>
            <p className="text-muted-foreground mb-4">
              Crie seu primeiro projeto de parceria conforme MROSC
            </p>
            <button
              onClick={() => openModal()}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
            >
              Criar Projeto
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {projetos.map((projeto) => {
              const statusInfo = STATUS_COLORS[projeto.status] || STATUS_COLORS['ELABORACAO'];
              return (
                <div
                  key={projeto.projeto_id}
                  className="bg-card border border-border rounded-xl p-5 hover:shadow-lg transition-shadow"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h3 className="font-semibold text-foreground text-lg">{projeto.nome_projeto}</h3>
                      <p className="text-sm text-muted-foreground line-clamp-2">{projeto.objeto}</p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${statusInfo.bg} ${statusInfo.text}`}>
                      {statusInfo.label}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Building2 size={14} />
                      <span className="truncate" title={projeto.organizacao_parceira}>
                        {projeto.organizacao_parceira}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Users size={14} />
                      <span>{projeto.responsavel_osc}</span>
                    </div>
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Calendar size={14} />
                      <span>{formatDate(projeto.data_inicio)} - {formatDate(projeto.data_conclusao)}</span>
                    </div>
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Clock size={14} />
                      <span>{projeto.prazo_meses} meses</span>
                    </div>
                  </div>

                  <div className="bg-muted/30 rounded-lg p-3 mb-4">
                    <div className="grid grid-cols-3 gap-2 text-center">
                      <div>
                        <div className="text-xs text-muted-foreground">Total</div>
                        <div className="font-semibold text-green-600">{formatCurrency(projeto.valor_total)}</div>
                      </div>
                      <div>
                        <div className="text-xs text-muted-foreground">Repasse</div>
                        <div className="font-semibold text-blue-600">{formatCurrency(projeto.valor_repasse_publico)}</div>
                      </div>
                      <div>
                        <div className="text-xs text-muted-foreground">Contrapartida</div>
                        <div className="font-semibold text-amber-600">{formatCurrency(projeto.valor_contrapartida)}</div>
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-between items-center pt-3 border-t border-border">
                    <div className="flex gap-2">
                      <button
                        onClick={() => openModal(projeto)}
                        className="p-2 text-primary hover:bg-primary/10 rounded-lg"
                        title="Editar"
                      >
                        <Edit size={16} />
                      </button>
                      <button
                        onClick={() => handleDelete(projeto)}
                        className="p-2 text-destructive hover:bg-destructive/10 rounded-lg"
                        title="Excluir"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                    <button
                      onClick={() => navigate(`/prestacao-contas/${projeto.projeto_id}`)}
                      className="flex items-center gap-1 text-sm text-green-600 hover:text-green-700 font-medium"
                      data-testid="open-projeto-btn"
                    >
                      Gerenciar <ArrowRight size={14} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Modal de Projeto */}
        {showModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card rounded-xl shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-card border-b border-border px-6 py-4">
                <h3 className="text-xl font-bold text-foreground">
                  {editingProjeto ? 'Editar Projeto MROSC' : 'Novo Projeto MROSC'}
                </h3>
              </div>

              <form onSubmit={handleSubmit} className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Nome do Projeto *</label>
                  <input
                    type="text"
                    value={formData.nome_projeto}
                    onChange={(e) => setFormData({...formData, nome_projeto: e.target.value})}
                    className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                    required
                    data-testid="projeto-nome-input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Objeto *</label>
                  <textarea
                    value={formData.objeto}
                    onChange={(e) => setFormData({...formData, objeto: e.target.value})}
                    className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                    rows={3}
                    required
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Organização Parceira (OSC) *</label>
                    <input
                      type="text"
                      value={formData.organizacao_parceira}
                      onChange={(e) => setFormData({...formData, organizacao_parceira: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">CNPJ da OSC *</label>
                    <input
                      type="text"
                      value={maskCNPJ(formData.cnpj_parceira)}
                      onChange={(e) => setFormData({...formData, cnpj_parceira: e.target.value.replace(/\D/g, '')})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      placeholder="00.000.000/0001-00"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Responsável OSC *</label>
                    <input
                      type="text"
                      value={formData.responsavel_osc}
                      onChange={(e) => setFormData({...formData, responsavel_osc: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Data Início *</label>
                    <input
                      type="date"
                      value={formData.data_inicio}
                      onChange={(e) => setFormData({...formData, data_inicio: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Data Conclusão *</label>
                    <input
                      type="date"
                      value={formData.data_conclusao}
                      onChange={(e) => setFormData({...formData, data_conclusao: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Prazo (meses) *</label>
                    <input
                      type="number"
                      value={formData.prazo_meses}
                      onChange={(e) => setFormData({...formData, prazo_meses: parseInt(e.target.value) || 0})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      min="1"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Valor Total (R$) *</label>
                    <input
                      type="number"
                      value={formData.valor_total}
                      onChange={(e) => setFormData({...formData, valor_total: parseFloat(e.target.value) || 0})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      min="0"
                      step="0.01"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Repasse Público (R$) *</label>
                    <input
                      type="number"
                      value={formData.valor_repasse_publico}
                      onChange={(e) => setFormData({...formData, valor_repasse_publico: parseFloat(e.target.value) || 0})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      min="0"
                      step="0.01"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Contrapartida (R$)</label>
                    <input
                      type="number"
                      value={formData.valor_contrapartida}
                      onChange={(e) => setFormData({...formData, valor_contrapartida: parseFloat(e.target.value) || 0})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      min="0"
                      step="0.01"
                    />
                  </div>
                </div>

                {editingProjeto && (
                  <div>
                    <label className="block text-sm font-medium mb-1">Status</label>
                    <select
                      value={formData.status}
                      onChange={(e) => setFormData({...formData, status: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                    >
                      {STATUS_OPTIONS.map(s => (
                        <option key={s} value={s}>{STATUS_COLORS[s].label}</option>
                      ))}
                    </select>
                  </div>
                )}

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
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    {editingProjeto ? 'Salvar' : 'Criar'}
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

export default PrestacaoContasList;
