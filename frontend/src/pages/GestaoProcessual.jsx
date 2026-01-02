import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ClipboardList, Plus, Search, Edit, Trash2, FileText, 
  FileSpreadsheet, Upload, X, Save, Calendar, Building2, User, BarChart3
} from 'lucide-react';
import Layout from '../components/Layout';
import api from '../utils/api';
import { toast } from 'sonner';

const STATUS_OPTIONS = [
  'Iniciado', 'Publicado', 'Aguardando Jurídico', 'Homologado', 'Concluído', 'Cancelado'
];

const MODALIDADE_OPTIONS = [
  'Dispensa por Limite', 'Dispensa por Justificativa', 'Chamamento Público', 
  'Inexigibilidade', 'Pregão', 'Pregão SRP', 'Concorrência', 'Adesão'
];

const STATUS_COLORS = {
  'Concluído': 'bg-green-100 text-green-800',
  'Iniciado': 'bg-blue-100 text-blue-800',
  'Publicado': 'bg-purple-100 text-purple-800',
  'Aguardando Jurídico': 'bg-yellow-100 text-yellow-800',
  'Homologado': 'bg-emerald-100 text-emerald-800',
  'Cancelado': 'bg-red-100 text-red-800',
};

const GestaoProcessual = () => {
  const navigate = useNavigate();
  const [processos, setProcessos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterModalidade, setFilterModalidade] = useState('');
  const [anos, setAnos] = useState([]);
  const [anoSelecionado, setAnoSelecionado] = useState(null);
  
  const [showModal, setShowModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [editingProcesso, setEditingProcesso] = useState(null);
  
  const [formData, setFormData] = useState({
    numero_processo: '',
    status: 'Iniciado',
    modalidade: '',
    objeto: '',
    situacao: '',
    responsavel: '',
    data_inicio: '',
    data_autuacao: '',
    data_contrato: '',
    secretaria: '',
    secretario: '',
    observacoes: ''
  });

  useEffect(() => {
    fetchUser();
    fetchProcessos();
  }, []);

  const fetchUser = async () => {
    try {
      const response = await api.get('/auth/me');
      setUser(response.data);
    } catch (error) {
      navigate('/');
    }
  };

  const fetchProcessos = async () => {
    try {
      const response = await api.get('/processos');
      setProcessos(response.data);
    } catch (error) {
      toast.error('Erro ao carregar processos');
    } finally {
      setLoading(false);
    }
  };

  const openModal = (processo = null) => {
    if (processo) {
      setEditingProcesso(processo);
      setFormData({
        numero_processo: processo.numero_processo || '',
        status: processo.status || 'Iniciado',
        modalidade: processo.modalidade || '',
        objeto: processo.objeto || '',
        situacao: processo.situacao || '',
        responsavel: processo.responsavel || '',
        data_inicio: processo.data_inicio ? processo.data_inicio.split('T')[0] : '',
        data_autuacao: processo.data_autuacao ? processo.data_autuacao.split('T')[0] : '',
        data_contrato: processo.data_contrato ? processo.data_contrato.split('T')[0] : '',
        secretaria: processo.secretaria || '',
        secretario: processo.secretario || '',
        observacoes: processo.observacoes || ''
      });
    } else {
      setEditingProcesso(null);
      setFormData({
        numero_processo: '',
        status: 'Iniciado',
        modalidade: '',
        objeto: '',
        situacao: '',
        responsavel: '',
        data_inicio: '',
        data_autuacao: '',
        data_contrato: '',
        secretaria: '',
        secretario: '',
        observacoes: ''
      });
    }
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.numero_processo || !formData.objeto || !formData.secretaria) {
      toast.error('Preencha os campos obrigatórios');
      return;
    }

    try {
      const submitData = { ...formData };
      // Converter datas vazias para null
      if (!submitData.data_inicio) submitData.data_inicio = null;
      if (!submitData.data_autuacao) submitData.data_autuacao = null;
      if (!submitData.data_contrato) submitData.data_contrato = null;

      if (editingProcesso) {
        await api.put(`/processos/${editingProcesso.processo_id}`, submitData);
        toast.success('Processo atualizado com sucesso!');
      } else {
        await api.post('/processos', submitData);
        toast.success('Processo criado com sucesso!');
      }
      setShowModal(false);
      fetchProcessos();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar processo');
    }
  };

  const handleDelete = async (processo) => {
    if (!user?.is_admin) {
      toast.error('Apenas administradores podem excluir processos');
      return;
    }

    if (!window.confirm(`Tem certeza que deseja excluir o processo "${processo.numero_processo}"?`)) {
      return;
    }

    try {
      await api.delete(`/processos/${processo.processo_id}`);
      toast.success('Processo excluído com sucesso!');
      fetchProcessos();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao excluir processo');
    }
  };

  const handleExportPDF = async (orientation) => {
    try {
      const response = await api.get(`/processos/export/pdf?orientation=${orientation}`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const orientationName = orientation === 'landscape' ? 'Paisagem' : 'Retrato';
      link.setAttribute('download', `Gestao_Processual_${orientationName}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      setShowExportModal(false);
      toast.success('PDF exportado com sucesso!');
    } catch (error) {
      toast.error('Erro ao exportar PDF');
    }
  };

  const handleExportXLSX = async () => {
    try {
      const response = await api.get('/processos/export/xlsx', {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'Gestao_Processual.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Excel exportado com sucesso!');
    } catch (error) {
      toast.error('Erro ao exportar Excel');
    }
  };

  const handleImportFile = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post('/processos/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success(response.data.message);
      fetchProcessos();
      setShowImportModal(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao importar arquivo');
    }
  };

  const filteredProcessos = processos.filter(p => {
    const matchSearch = 
      p.numero_processo?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.objeto?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.secretaria?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchStatus = !filterStatus || p.status === filterStatus;
    const matchModalidade = !filterModalidade || p.modalidade === filterModalidade;
    return matchSearch && matchStatus && matchModalidade;
  });

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR');
    } catch {
      return dateStr;
    }
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
      <div className="space-y-6" data-testid="gestao-processual">
        {/* Cabeçalho */}
        <div className="flex flex-wrap justify-between items-center gap-4">
          <div>
            <h2 className="text-3xl font-heading font-bold text-foreground flex items-center gap-2">
              <ClipboardList size={32} />
              Gestão Processual
            </h2>
            <p className="text-muted-foreground mt-1">{processos.length} processo(s) cadastrado(s)</p>
          </div>
          
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => navigate('/gestao-processual/dashboard')}
              className="flex items-center gap-2 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
            >
              <BarChart3 size={18} />
              Dashboard
            </button>
            
            <button
              onClick={() => openModal()}
              className="flex items-center gap-2 bg-secondary text-secondary-foreground px-4 py-2 rounded-lg hover:bg-secondary/90 transition-colors"
            >
              <Plus size={18} />
              Novo Processo
            </button>
            
            <button
              onClick={() => setShowImportModal(true)}
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Upload size={18} />
              Importar
            </button>
            
            {processos.length > 0 && (
              <>
                <button
                  onClick={handleExportXLSX}
                  className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                >
                  <FileSpreadsheet size={18} />
                  Excel
                </button>
                
                <button
                  onClick={() => setShowExportModal(true)}
                  className="flex items-center gap-2 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
                >
                  <FileText size={18} />
                  PDF
                </button>
              </>
            )}
          </div>
        </div>

        {/* Filtros */}
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" size={18} />
              <input
                type="text"
                placeholder="Buscar processo..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
              />
            </div>
            
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
            >
              <option value="">Todos os Status</option>
              {STATUS_OPTIONS.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            
            <select
              value={filterModalidade}
              onChange={(e) => setFilterModalidade(e.target.value)}
              className="px-4 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
            >
              <option value="">Todas as Modalidades</option>
              {MODALIDADE_OPTIONS.map(m => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
            
            <div className="text-sm text-muted-foreground flex items-center">
              {filteredProcessos.length} resultado(s)
            </div>
          </div>
        </div>

        {/* Tabela de Processos */}
        <div className="bg-card border border-border rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted text-foreground">
                <tr>
                  <th className="px-4 py-3 text-left">Processo</th>
                  <th className="px-4 py-3 text-center">Status</th>
                  <th className="px-4 py-3 text-left">Modalidade</th>
                  <th className="px-4 py-3 text-left">Objeto</th>
                  <th className="px-4 py-3 text-left">Secretaria</th>
                  <th className="px-4 py-3 text-center">Data Início</th>
                  <th className="px-4 py-3 text-center">Ações</th>
                </tr>
              </thead>
              <tbody>
                {filteredProcessos.map((processo) => (
                  <tr key={processo.processo_id} className="border-b border-border hover:bg-muted/50 transition-colors">
                    <td className="px-4 py-3 font-medium">
                      <div className="font-semibold text-foreground">{processo.numero_processo}</div>
                      <div className="text-xs text-muted-foreground">{processo.responsavel}</div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${STATUS_COLORS[processo.status] || 'bg-gray-100 text-gray-800'}`}>
                        {processo.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs">{processo.modalidade}</span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="max-w-xs truncate" title={processo.objeto}>
                        {processo.objeto}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-xs">{processo.secretaria}</div>
                      <div className="text-xs text-muted-foreground">{processo.secretario}</div>
                    </td>
                    <td className="px-4 py-3 text-center text-xs">
                      {formatDate(processo.data_inicio)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex justify-center gap-2">
                        <button
                          onClick={() => openModal(processo)}
                          className="p-2 text-primary hover:bg-primary/10 rounded-lg transition-colors"
                          title="Editar"
                        >
                          <Edit size={16} />
                        </button>
                        {user?.is_admin && (
                          <button
                            onClick={() => handleDelete(processo)}
                            className="p-2 text-destructive hover:bg-destructive/10 rounded-lg transition-colors"
                            title="Excluir"
                          >
                            <Trash2 size={16} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {filteredProcessos.length === 0 && (
            <div className="text-center py-12 text-muted-foreground">
              <ClipboardList size={48} className="mx-auto mb-4 opacity-50" />
              <p>Nenhum processo encontrado</p>
            </div>
          )}
        </div>

        {/* Modal de Criação/Edição */}
        {showModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-card border-b border-border px-6 py-4 flex justify-between items-center">
                <h3 className="text-xl font-bold text-foreground">
                  {editingProcesso ? 'Editar Processo' : 'Novo Processo'}
                </h3>
                <button onClick={() => setShowModal(false)} className="text-muted-foreground hover:text-foreground">
                  <X size={24} />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="p-6 space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-foreground mb-1">
                      Número do Processo *
                    </label>
                    <input
                      type="text"
                      value={formData.numero_processo}
                      onChange={(e) => setFormData({ ...formData, numero_processo: e.target.value })}
                      className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                      placeholder="PRC - 0001/2025"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-foreground mb-1">
                      Status *
                    </label>
                    <select
                      value={formData.status}
                      onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                      className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                      required
                    >
                      {STATUS_OPTIONS.map(s => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-foreground mb-1">
                      Modalidade *
                    </label>
                    <select
                      value={formData.modalidade}
                      onChange={(e) => setFormData({ ...formData, modalidade: e.target.value })}
                      className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                      required
                    >
                      <option value="">Selecione...</option>
                      {MODALIDADE_OPTIONS.map(m => (
                        <option key={m} value={m}>{m}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-foreground mb-1">
                    Objeto *
                  </label>
                  <textarea
                    value={formData.objeto}
                    onChange={(e) => setFormData({ ...formData, objeto: e.target.value })}
                    className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                    rows={3}
                    placeholder="Descrição do objeto da contratação"
                    required
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-foreground mb-1">
                      Situação
                    </label>
                    <input
                      type="text"
                      value={formData.situacao}
                      onChange={(e) => setFormData({ ...formData, situacao: e.target.value })}
                      className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                      placeholder="OK"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-foreground mb-1">
                      Responsável
                    </label>
                    <input
                      type="text"
                      value={formData.responsavel}
                      onChange={(e) => setFormData({ ...formData, responsavel: e.target.value })}
                      className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                      placeholder="Nome do responsável"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-foreground mb-1">
                      <Calendar size={14} className="inline mr-1" />
                      Data de Início
                    </label>
                    <input
                      type="date"
                      value={formData.data_inicio}
                      onChange={(e) => setFormData({ ...formData, data_inicio: e.target.value })}
                      className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-foreground mb-1">
                      <Calendar size={14} className="inline mr-1" />
                      Data de Autuação
                    </label>
                    <input
                      type="date"
                      value={formData.data_autuacao}
                      onChange={(e) => setFormData({ ...formData, data_autuacao: e.target.value })}
                      className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-foreground mb-1">
                      <Calendar size={14} className="inline mr-1" />
                      Data do Contrato
                    </label>
                    <input
                      type="date"
                      value={formData.data_contrato}
                      onChange={(e) => setFormData({ ...formData, data_contrato: e.target.value })}
                      className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-foreground mb-1">
                      <Building2 size={14} className="inline mr-1" />
                      Secretaria *
                    </label>
                    <input
                      type="text"
                      value={formData.secretaria}
                      onChange={(e) => setFormData({ ...formData, secretaria: e.target.value })}
                      className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                      placeholder="Nome da Secretaria"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-foreground mb-1">
                      <User size={14} className="inline mr-1" />
                      Secretário
                    </label>
                    <input
                      type="text"
                      value={formData.secretario}
                      onChange={(e) => setFormData({ ...formData, secretario: e.target.value })}
                      className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                      placeholder="Nome do Secretário"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-foreground mb-1">
                    Observações
                  </label>
                  <textarea
                    value={formData.observacoes}
                    onChange={(e) => setFormData({ ...formData, observacoes: e.target.value })}
                    className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                    rows={2}
                    placeholder="Observações adicionais"
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-border">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                  >
                    <Save size={18} />
                    {editingProcesso ? 'Salvar Alterações' : 'Criar Processo'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal de Exportação PDF */}
        {showExportModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card rounded-xl shadow-xl max-w-md w-full">
              <div className="p-6 border-b border-border">
                <div className="flex justify-between items-center">
                  <h3 className="text-xl font-bold text-foreground">Exportar PDF</h3>
                  <button onClick={() => setShowExportModal(false)} className="text-muted-foreground hover:text-foreground">
                    <X size={24} />
                  </button>
                </div>
              </div>
              
              <div className="p-6 space-y-4">
                <p className="text-muted-foreground">Escolha a orientação do relatório:</p>
                
                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={() => handleExportPDF('landscape')}
                    className="flex flex-col items-center p-4 border-2 border-border rounded-lg hover:border-primary hover:bg-primary/5 transition-colors"
                  >
                    <div className="w-16 h-10 border-2 border-primary rounded mb-2"></div>
                    <span className="font-semibold text-foreground">Paisagem</span>
                    <span className="text-xs text-muted-foreground">A4 Horizontal</span>
                  </button>
                  
                  <button
                    onClick={() => handleExportPDF('portrait')}
                    className="flex flex-col items-center p-4 border-2 border-border rounded-lg hover:border-primary hover:bg-primary/5 transition-colors"
                  >
                    <div className="w-10 h-14 border-2 border-primary rounded mb-2"></div>
                    <span className="font-semibold text-foreground">Retrato</span>
                    <span className="text-xs text-muted-foreground">A4 Vertical</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Modal de Importação */}
        {showImportModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card rounded-xl shadow-xl max-w-lg w-full">
              <div className="p-6 border-b border-border">
                <div className="flex justify-between items-center">
                  <h3 className="text-xl font-bold text-foreground">Importar Processos</h3>
                  <button onClick={() => setShowImportModal(false)} className="text-muted-foreground hover:text-foreground">
                    <X size={24} />
                  </button>
                </div>
              </div>
              
              <div className="p-6 space-y-4">
                <p className="text-muted-foreground">
                  Selecione um arquivo para importar processos.
                </p>
                
                <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
                  <Upload size={48} className="mx-auto text-muted-foreground mb-4" />
                  <p className="text-foreground font-semibold mb-2">Formatos suportados:</p>
                  <p className="text-sm text-muted-foreground mb-4">Excel (.xlsx), CSV</p>
                  
                  <label className="cursor-pointer">
                    <span className="bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors inline-block">
                      Selecionar Arquivo
                    </span>
                    <input
                      type="file"
                      accept=".csv,.xlsx,.xls"
                      onChange={handleImportFile}
                      className="hidden"
                    />
                  </label>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default GestaoProcessual;
