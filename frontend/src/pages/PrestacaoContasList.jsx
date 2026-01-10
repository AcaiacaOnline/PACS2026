import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  DollarSign, Plus, FileText, Building2, Search, Eye, Trash2,
  CheckCircle, Clock, AlertTriangle, Send, FileCheck, Edit3,
  XCircle, History, Download
} from 'lucide-react';
import Layout from '../components/Layout';
import api from '../utils/api';
import { toast } from 'sonner';

const STATUS_CONFIG = {
  'ELABORACAO': { label: 'Em Elaboração', color: 'bg-gray-100 text-gray-700', icon: Edit3 },
  'SUBMETIDO': { label: 'Submetido', color: 'bg-blue-100 text-blue-700', icon: Send },
  'EM_ANALISE': { label: 'Em Análise', color: 'bg-purple-100 text-purple-700', icon: Clock },
  'CORRECAO_SOLICITADA': { label: 'Correção Solicitada', color: 'bg-amber-100 text-amber-700', icon: AlertTriangle },
  'APROVADO': { label: 'Aprovado', color: 'bg-green-100 text-green-700', icon: CheckCircle },
  'REJEITADO': { label: 'Rejeitado', color: 'bg-red-100 text-red-700', icon: XCircle },
  'EXECUCAO': { label: 'Em Execução', color: 'bg-cyan-100 text-cyan-700', icon: Clock },
  'PRESTACAO_CONTAS': { label: 'Prestação de Contas', color: 'bg-indigo-100 text-indigo-700', icon: FileText },
  'CONCLUIDO': { label: 'Concluído', color: 'bg-emerald-100 text-emerald-700', icon: CheckCircle }
};

const PrestacaoContasList = () => {
  const navigate = useNavigate();
  const [projetos, setProjetos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [user, setUser] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [showCorrecaoModal, setShowCorrecaoModal] = useState(false);
  const [showHistoricoModal, setShowHistoricoModal] = useState(false);
  const [selectedProjeto, setSelectedProjeto] = useState(null);
  const [motivoCorrecao, setMotivoCorrecao] = useState('');
  const [historico, setHistorico] = useState([]);
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
    valor_contrapartida: 0
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [projetosRes, userRes] = await Promise.all([
        api.get('/mrosc/projetos'),
        api.get('/auth/me')
      ]);
      setProjetos(projetosRes.data);
      setUser(userRes.data);
    } catch (error) {
      toast.error('Erro ao carregar projetos');
    } finally {
      setLoading(false);
    }
  };

  const isAdmin = user?.is_admin;
  const isExternalUser = user?.tipo_usuario === 'PESSOA_EXTERNA' || user?.permissions?.mrosc_only;

  const handleCreateProjeto = async (e) => {
    e.preventDefault();
    try {
      await api.post('/mrosc/projetos', {
        ...formData,
        data_inicio: new Date(formData.data_inicio).toISOString(),
        data_conclusao: new Date(formData.data_conclusao).toISOString()
      });
      toast.success('Projeto criado com sucesso!');
      setShowModal(false);
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
        valor_contrapartida: 0
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao criar projeto');
    }
  };

  const handleDeleteProjeto = async (projeto) => {
    // Verificar se pode deletar
    if (projeto.submetido && !projeto.pode_editar) {
      toast.error('Não é possível excluir um projeto já submetido');
      return;
    }
    if (!window.confirm(`Excluir projeto "${projeto.nome_projeto}"?`)) return;
    
    try {
      await api.delete(`/mrosc/projetos/${projeto.projeto_id}`);
      toast.success('Projeto excluído!');
      fetchData();
    } catch (error) {
      toast.error('Erro ao excluir');
    }
  };

  // ===== AÇÕES DE WORKFLOW =====
  
  const handleSubmeterPrestacao = async (projeto) => {
    if (!window.confirm('Deseja submeter esta prestação de contas para análise? Após submissão, você não poderá editar até que o gestor autorize.')) return;
    
    try {
      await api.post(`/mrosc/projetos/${projeto.projeto_id}/submeter`);
      toast.success('Prestação de contas submetida com sucesso!');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao submeter');
    }
  };

  const handleReceberPrestacao = async (projeto) => {
    try {
      await api.post(`/mrosc/projetos/${projeto.projeto_id}/receber`);
      toast.success('Prestação de contas recebida!');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao receber');
    }
  };

  const openCorrecaoModal = (projeto) => {
    setSelectedProjeto(projeto);
    setMotivoCorrecao('');
    setShowCorrecaoModal(true);
  };

  const handleSolicitarCorrecao = async () => {
    if (!motivoCorrecao.trim()) {
      toast.error('Informe o motivo da correção');
      return;
    }
    
    try {
      await api.post(`/mrosc/projetos/${selectedProjeto.projeto_id}/solicitar-correcao`, {
        motivo: motivoCorrecao
      });
      toast.success('Correção solicitada! O usuário pode editar novamente.');
      setShowCorrecaoModal(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao solicitar correção');
    }
  };

  const handleAprovarPrestacao = async (projeto) => {
    if (!window.confirm('Confirma a aprovação desta prestação de contas?')) return;
    
    try {
      await api.post(`/mrosc/projetos/${projeto.projeto_id}/aprovar`);
      toast.success('Prestação de contas aprovada!');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao aprovar');
    }
  };

  const openHistoricoModal = async (projeto) => {
    try {
      const response = await api.get(`/mrosc/projetos/${projeto.projeto_id}/historico`);
      setHistorico(response.data.historico);
      setSelectedProjeto(projeto);
      setShowHistoricoModal(true);
    } catch (error) {
      toast.error('Erro ao carregar histórico');
    }
  };

  const formatCurrency = (value) => {
    return (value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('pt-BR');
  };

  const filteredProjetos = projetos.filter(p => 
    p.nome_projeto?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.organizacao_parceira?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Determinar ações disponíveis baseado no status e tipo de usuário
  const getAcoesDisponiveis = (projeto) => {
    const acoes = [];
    
    // Visualizar/Editar sempre disponível
    acoes.push({ 
      action: 'visualizar', 
      label: 'Editar/Gerenciar', 
      icon: Edit3, 
      color: 'text-blue-600 hover:bg-blue-50' 
    });
    
    // Histórico sempre disponível
    acoes.push({ 
      action: 'historico', 
      label: 'Histórico', 
      icon: History, 
      color: 'text-purple-600 hover:bg-purple-50' 
    });

    // Download PDF
    acoes.push({ 
      action: 'download', 
      label: 'Baixar PDF', 
      icon: Download, 
      color: 'text-red-600 hover:bg-red-50' 
    });
    
    // Ações para usuário externo
    if (isExternalUser) {
      if (projeto.pode_editar && !projeto.aprovado) {
        acoes.push({ 
          action: 'submeter', 
          label: 'Submeter para Análise', 
          icon: Send, 
          color: 'text-green-600 hover:bg-green-50' 
        });
      }
      if (projeto.pode_editar && !projeto.submetido) {
        acoes.push({ 
          action: 'excluir', 
          label: 'Excluir', 
          icon: Trash2, 
          color: 'text-red-600 hover:bg-red-50' 
        });
      }
    }
    
    // Ações para administrador
    if (isAdmin) {
      // Receber - só quando foi submetido mas não recebido ainda
      if (projeto.submetido && projeto.status === 'SUBMETIDO') {
        acoes.push({ 
          action: 'receber', 
          label: 'Confirmar Recebimento', 
          icon: FileCheck, 
          color: 'text-teal-600 hover:bg-teal-50' 
        });
      }
      
      // Pedir Correção - quando submetido e não aprovado
      if (projeto.submetido && !projeto.aprovado) {
        acoes.push({ 
          action: 'correcao', 
          label: 'Pedir Correção', 
          icon: AlertTriangle, 
          color: 'text-amber-600 hover:bg-amber-50' 
        });
      }
      
      // Aprovar - quando submetido e não aprovado
      if (projeto.submetido && !projeto.aprovado) {
        acoes.push({ 
          action: 'aprovar', 
          label: 'Aprovar Prestação', 
          icon: CheckCircle, 
          color: 'text-green-600 hover:bg-green-50' 
        });
      }
      
      // Excluir - admin sempre pode
      acoes.push({ 
        action: 'excluir', 
        label: 'Excluir', 
        icon: Trash2, 
        color: 'text-red-600 hover:bg-red-50' 
      });
    }
    
    return acoes;
  };

  const handleDownloadPdf = async (projeto) => {
    try {
      const response = await api.get(`/mrosc/projetos/${projeto.projeto_id}/export/pdf`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `MROSC_${projeto.nome_projeto.replace(/\s/g, '_')}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('PDF baixado!');
    } catch (error) {
      toast.error('Erro ao baixar PDF');
    }
  };

  const handleAction = (action, projeto) => {
    switch (action) {
      case 'visualizar':
        navigate(`/prestacao-contas/${projeto.projeto_id}`);
        break;
      case 'historico':
        openHistoricoModal(projeto);
        break;
      case 'download':
        handleDownloadPdf(projeto);
        break;
      case 'submeter':
        handleSubmeterPrestacao(projeto);
        break;
      case 'receber':
        handleReceberPrestacao(projeto);
        break;
      case 'correcao':
        openCorrecaoModal(projeto);
        break;
      case 'aprovar':
        handleAprovarPrestacao(projeto);
        break;
      case 'excluir':
        handleDeleteProjeto(projeto);
        break;
      default:
        break;
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
        </div>
      </Layout>
    );
  }

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
            <p className="text-muted-foreground">Lei 13.019/2014 - Marco Regulatório das OSC</p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
            data-testid="create-projeto-btn"
          >
            <Plus size={18} />
            Novo Projeto
          </button>
        </div>

        {/* Info para usuário externo */}
        {isExternalUser && (
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <p className="text-purple-800 text-sm">
              <strong>Bem-vindo(a)!</strong> Como representante de Organização da Sociedade Civil (OSC), 
              você pode criar e gerenciar projetos de prestação de contas conforme a Lei 13.019/2014. 
              Após submeter, aguarde a análise do gestor municipal.
            </p>
          </div>
        )}

        {/* Info para admin */}
        {isAdmin && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-blue-800 text-sm">
              <strong>Painel Administrativo:</strong> Você pode receber, analisar, solicitar correções e aprovar 
              as prestações de contas das organizações parceiras.
            </p>
          </div>
        )}

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" size={18} />
          <input
            type="text"
            placeholder="Buscar por nome do projeto ou organização..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-input rounded-lg bg-background focus:ring-2 focus:ring-ring"
          />
        </div>

        {/* Lista de Projetos */}
        {filteredProjetos.length === 0 ? (
          <div className="bg-card border border-border rounded-xl p-12 text-center">
            <Building2 size={48} className="mx-auto text-muted-foreground opacity-50 mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">Nenhum projeto encontrado</h3>
            <p className="text-muted-foreground mb-4">Comece criando seu primeiro projeto de parceria.</p>
            <button
              onClick={() => setShowModal(true)}
              className="inline-flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
            >
              <Plus size={18} /> Criar Projeto
            </button>
          </div>
        ) : (
          <div className="grid gap-4">
            {filteredProjetos.map((projeto) => {
              const statusConfig = STATUS_CONFIG[projeto.status] || STATUS_CONFIG['ELABORACAO'];
              const StatusIcon = statusConfig.icon;
              const acoes = getAcoesDisponiveis(projeto);
              
              return (
                <div
                  key={projeto.projeto_id}
                  className="bg-card border border-border rounded-xl p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex flex-col md:flex-row justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-start gap-3">
                        <div className="bg-green-100 p-2 rounded-lg">
                          <FileText className="text-green-600" size={20} />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h3 className="font-semibold text-foreground">{projeto.nome_projeto}</h3>
                            <span className={`text-xs px-2 py-0.5 rounded-full flex items-center gap-1 ${statusConfig.color}`}>
                              <StatusIcon size={12} />
                              {statusConfig.label}
                            </span>
                            {projeto.correcao_solicitada && (
                              <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 flex items-center gap-1">
                                <AlertTriangle size={12} />
                                Correção Pendente
                              </span>
                            )}
                            {projeto.aprovado && (
                              <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 flex items-center gap-1">
                                <CheckCircle size={12} />
                                Aprovado
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground mt-1">{projeto.organizacao_parceira}</p>
                          <p className="text-xs text-muted-foreground">{projeto.objeto?.substring(0, 100)}...</p>
                          
                          {/* Alerta de correção */}
                          {projeto.correcao_solicitada && projeto.motivo_correcao && (
                            <div className="mt-2 p-2 bg-amber-50 border border-amber-200 rounded text-xs text-amber-800">
                              <strong>Motivo da correção:</strong> {projeto.motivo_correcao}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex flex-col items-end gap-2">
                      <div className="text-right">
                        <div className="text-lg font-bold text-green-600">{formatCurrency(projeto.valor_total)}</div>
                        <div className="text-xs text-muted-foreground">
                          {formatDate(projeto.data_inicio)} - {formatDate(projeto.data_conclusao)}
                        </div>
                      </div>
                      
                      {/* Botões de Ação */}
                      <div className="flex flex-wrap gap-1">
                        {acoes.map((acao, idx) => (
                          <button
                            key={idx}
                            onClick={() => handleAction(acao.action, projeto)}
                            className={`p-2 rounded-lg transition-colors ${acao.color}`}
                            title={acao.label}
                            data-testid={`action-${acao.action}-${projeto.projeto_id}`}
                          >
                            <acao.icon size={16} />
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Modal Criar Projeto */}
        {showModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-card border-b border-border px-6 py-4">
                <h3 className="text-xl font-bold text-foreground flex items-center gap-2">
                  <DollarSign className="text-green-600" />
                  Novo Projeto MROSC
                </h3>
              </div>
              
              <form onSubmit={handleCreateProjeto} className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Nome do Projeto *</label>
                  <input
                    type="text"
                    value={formData.nome_projeto}
                    onChange={(e) => setFormData({...formData, nome_projeto: e.target.value})}
                    className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Objeto/Descrição *</label>
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
                      value={formData.cnpj_parceira}
                      onChange={(e) => setFormData({...formData, cnpj_parceira: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      required
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Responsável da OSC *</label>
                  <input
                    type="text"
                    value={formData.responsavel_osc}
                    onChange={(e) => setFormData({...formData, responsavel_osc: e.target.value})}
                    className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                    required
                  />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                  <div>
                    <label className="block text-sm font-medium mb-1">Prazo (meses)</label>
                    <input
                      type="number"
                      value={formData.prazo_meses}
                      onChange={(e) => setFormData({...formData, prazo_meses: parseInt(e.target.value)})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      min="1"
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Valor Total (R$) *</label>
                    <input
                      type="number"
                      value={formData.valor_total}
                      onChange={(e) => setFormData({...formData, valor_total: parseFloat(e.target.value)})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      min="0"
                      step="0.01"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Repasse Público (R$)</label>
                    <input
                      type="number"
                      value={formData.valor_repasse_publico}
                      onChange={(e) => setFormData({...formData, valor_repasse_publico: parseFloat(e.target.value)})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      min="0"
                      step="0.01"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Contrapartida (R$)</label>
                    <input
                      type="number"
                      value={formData.valor_contrapartida}
                      onChange={(e) => setFormData({...formData, valor_contrapartida: parseFloat(e.target.value)})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      min="0"
                      step="0.01"
                    />
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
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
                  >
                    <Plus size={16} /> Criar Projeto
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal Solicitar Correção */}
        {showCorrecaoModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card rounded-xl shadow-xl w-full max-w-md">
              <div className="border-b border-border px-6 py-4">
                <h3 className="text-lg font-bold text-foreground flex items-center gap-2">
                  <AlertTriangle className="text-amber-600" />
                  Solicitar Correção
                </h3>
              </div>
              
              <div className="p-6 space-y-4">
                <p className="text-sm text-muted-foreground">
                  Informe o motivo pelo qual a prestação de contas precisa ser corrigida. 
                  O usuário externo será notificado e poderá editar o projeto novamente.
                </p>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Motivo da Correção *</label>
                  <textarea
                    value={motivoCorrecao}
                    onChange={(e) => setMotivoCorrecao(e.target.value)}
                    className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                    rows={4}
                    placeholder="Descreva o que precisa ser corrigido..."
                    required
                  />
                </div>
                
                <div className="flex justify-end gap-3 pt-4 border-t border-border">
                  <button
                    type="button"
                    onClick={() => setShowCorrecaoModal(false)}
                    className="px-4 py-2 border border-input rounded-lg hover:bg-muted"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleSolicitarCorrecao}
                    className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 flex items-center gap-2"
                  >
                    <AlertTriangle size={16} /> Solicitar Correção
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Modal Histórico */}
        {showHistoricoModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card rounded-xl shadow-xl w-full max-w-md max-h-[80vh] overflow-y-auto">
              <div className="sticky top-0 bg-card border-b border-border px-6 py-4">
                <h3 className="text-lg font-bold text-foreground flex items-center gap-2">
                  <History className="text-purple-600" />
                  Histórico do Projeto
                </h3>
                <p className="text-sm text-muted-foreground">{selectedProjeto?.nome_projeto}</p>
              </div>
              
              <div className="p-6">
                {historico.length === 0 ? (
                  <p className="text-muted-foreground text-center py-4">Nenhuma ação registrada</p>
                ) : (
                  <div className="space-y-4">
                    {historico.map((item, idx) => (
                      <div key={idx} className="flex gap-3 pb-4 border-b border-border last:border-0">
                        <div className="w-2 h-2 bg-purple-600 rounded-full mt-2"></div>
                        <div className="flex-1">
                          <div className="font-medium text-foreground">{item.acao}</div>
                          <div className="text-xs text-muted-foreground">
                            {item.usuario && <span>Por: {item.usuario} • </span>}
                            {item.data && formatDate(item.data)}
                          </div>
                          {item.motivo && (
                            <div className="text-sm text-amber-600 mt-1">Motivo: {item.motivo}</div>
                          )}
                          {item.observacoes && (
                            <div className="text-sm text-muted-foreground mt-1">{item.observacoes}</div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                <div className="pt-4 border-t border-border mt-4">
                  <button
                    onClick={() => setShowHistoricoModal(false)}
                    className="w-full px-4 py-2 border border-input rounded-lg hover:bg-muted"
                  >
                    Fechar
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default PrestacaoContasList;
