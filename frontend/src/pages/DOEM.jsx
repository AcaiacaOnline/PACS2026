import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Newspaper, Plus, Search, Edit, Trash2, FileText, 
  Upload, X, Save, Calendar, Eye, Download, CheckCircle, Clock, Send, Users, Mail, UserPlus, PenTool
} from 'lucide-react';
import Layout from '../components/Layout';
import api from '../utils/api';
import { toast } from 'sonner';
import { EmailInput } from '../utils/masks';

// Segmentos do DOEM
const DOEM_SEGMENTOS = [
  "Portarias",
  "Leis",
  "Decretos",
  "Resoluções",
  "Editais",
  "Prestações de Contas",
  "Processos Administrativos",
  "Publicações do Legislativo",
  "Publicações do Terceiro Setor"
];

// Tipos por segmento
const TIPOS_POR_SEGMENTO = {
  "Portarias": ["Portaria", "Portaria Conjunta"],
  "Leis": ["Lei Ordinária", "Lei Complementar", "Emenda à Lei Orgânica"],
  "Decretos": ["Decreto", "Decreto Regulamentar"],
  "Resoluções": ["Resolução", "Resolução Conjunta"],
  "Editais": ["Edital de Licitação", "Edital de Convocação", "Edital de Seleção", "Aviso de Licitação"],
  "Prestações de Contas": ["Prestação de Contas", "Relatório de Gestão", "Balanço"],
  "Processos Administrativos": ["Extrato de Contrato", "Termo Aditivo", "Ata de Registro de Preços", "Homologação", "Ratificação"],
  "Publicações do Legislativo": ["Projeto de Lei", "Ata de Sessão", "Parecer", "Moção", "Requerimento"],
  "Publicações do Terceiro Setor": ["Termo de Parceria", "Convênio", "Prestação de Contas OSC", "Chamamento Público"]
};

const STATUS_COLORS = {
  'rascunho': 'bg-gray-100 text-gray-800',
  'agendado': 'bg-yellow-100 text-yellow-800',
  'publicado': 'bg-green-100 text-green-800',
};

const STATUS_ICONS = {
  'rascunho': Clock,
  'agendado': Calendar,
  'publicado': CheckCircle,
};

const DOEM = () => {
  const navigate = useNavigate();
  const [edicoes, setEdicoes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  const [anos, setAnos] = useState([]);
  const [anoSelecionado, setAnoSelecionado] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState('edicoes'); // edicoes, newsletter
  
  const [showModal, setShowModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showNewsletterModal, setShowNewsletterModal] = useState(false);
  const [showAssinantesModal, setShowAssinantesModal] = useState(false);
  const [editingEdicao, setEditingEdicao] = useState(null);
  const [importedPubs, setImportedPubs] = useState([]);
  const [inscritos, setInscritos] = useState([]);
  const [newsletterStats, setNewsletterStats] = useState(null);
  const [usuariosDisponiveis, setUsuariosDisponiveis] = useState([]);
  const [assinantesEdicao, setAssinantesEdicao] = useState([]);
  const [edicaoParaAssinar, setEdicaoParaAssinar] = useState(null);
  
  const [formData, setFormData] = useState({
    data_publicacao: '',
    publicacoes: []
  });
  
  const [newPub, setNewPub] = useState({
    titulo: '',
    texto: '',
    secretaria: 'Gabinete do Prefeito',
    segmento: 'Decretos',
    tipo: 'Decreto'
  });
  
  const [newInscrito, setNewInscrito] = useState({
    email: '',
    nome: '',
    segmentos_interesse: []
  });

  useEffect(() => {
    fetchUser();
    fetchAnos();
  }, []);

  useEffect(() => {
    if (anoSelecionado !== null) {
      fetchEdicoes();
    }
  }, [anoSelecionado]);

  useEffect(() => {
    if (activeTab === 'newsletter' && user?.is_admin) {
      fetchInscritos();
      fetchNewsletterStats();
    }
  }, [activeTab, user]);

  const fetchUser = async () => {
    try {
      const response = await api.get('/auth/me');
      setUser(response.data);
    } catch (error) {
      navigate('/');
    }
  };

  const fetchAnos = async () => {
    try {
      const response = await api.get('/doem/edicoes/anos');
      setAnos(response.data.anos);
      setAnoSelecionado(response.data.ano_atual);
    } catch (error) {
      console.error('Erro ao carregar anos:', error);
      setAnoSelecionado(new Date().getFullYear());
    }
  };

  const fetchEdicoes = async () => {
    setLoading(true);
    try {
      const params = anoSelecionado ? `?ano=${anoSelecionado}` : '';
      const response = await api.get(`/doem/edicoes${params}`);
      setEdicoes(response.data);
    } catch (error) {
      toast.error('Erro ao carregar edições');
    } finally {
      setLoading(false);
    }
  };

  const fetchInscritos = async () => {
    try {
      const response = await api.get('/newsletter/inscritos');
      setInscritos(response.data);
    } catch (error) {
      console.error('Erro ao carregar inscritos:', error);
    }
  };

  const fetchNewsletterStats = async () => {
    try {
      const response = await api.get('/newsletter/estatisticas');
      setNewsletterStats(response.data);
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
    }
  };

  const openModal = (edicao = null) => {
    if (edicao) {
      setEditingEdicao(edicao);
      const dataPub = edicao.data_publicacao ? new Date(edicao.data_publicacao).toISOString().split('T')[0] : '';
      setFormData({
        data_publicacao: dataPub,
        publicacoes: edicao.publicacoes || []
      });
    } else {
      setEditingEdicao(null);
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      setFormData({
        data_publicacao: tomorrow.toISOString().split('T')[0],
        publicacoes: []
      });
    }
    setShowModal(true);
  };

  const handleAddPub = () => {
    if (!newPub.titulo || !newPub.texto) {
      toast.error('Preencha título e texto da publicação');
      return;
    }
    
    setFormData({
      ...formData,
      publicacoes: [...formData.publicacoes, { ...newPub, ordem: formData.publicacoes.length + 1 }]
    });
    
    setNewPub({
      titulo: '',
      texto: '',
      secretaria: 'Gabinete do Prefeito',
      segmento: 'Decretos',
      tipo: 'Decreto'
    });
    
    toast.success('Publicação adicionada');
  };

  const handleRemovePub = (index) => {
    const newPubs = [...formData.publicacoes];
    newPubs.splice(index, 1);
    setFormData({ ...formData, publicacoes: newPubs });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.publicacoes.length === 0) {
      toast.error('Adicione pelo menos uma publicação');
      return;
    }

    try {
      const submitData = {
        data_publicacao: formData.data_publicacao ? new Date(formData.data_publicacao).toISOString() : null,
        publicacoes: formData.publicacoes.map((p, i) => ({
          titulo: p.titulo,
          texto: p.texto,
          secretaria: p.secretaria,
          segmento: p.segmento || 'Decretos',
          tipo: p.tipo,
          ordem: i + 1
        }))
      };

      if (editingEdicao) {
        await api.put(`/doem/edicoes/${editingEdicao.edicao_id}`, submitData);
        toast.success('Edição atualizada com sucesso!');
      } else {
        await api.post('/doem/edicoes', submitData);
        toast.success('Edição criada com sucesso!');
      }
      setShowModal(false);
      fetchEdicoes();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar edição');
    }
  };

  const handleDelete = async (edicao) => {
    if (edicao.status !== 'rascunho') {
      toast.error('Apenas rascunhos podem ser excluídos');
      return;
    }

    if (!window.confirm(`Tem certeza que deseja excluir a Edição nº ${edicao.numero_edicao}?`)) {
      return;
    }

    try {
      await api.delete(`/doem/edicoes/${edicao.edicao_id}`);
      toast.success('Edição excluída com sucesso!');
      fetchEdicoes();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao excluir edição');
    }
  };

  const handlePublish = async (edicao) => {
    if (!window.confirm(`Publicar a Edição nº ${edicao.numero_edicao}? Esta ação não pode ser desfeita.`)) {
      return;
    }

    try {
      await api.post(`/doem/edicoes/${edicao.edicao_id}/publicar`);
      toast.success('Edição publicada com sucesso!');
      fetchEdicoes();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao publicar edição');
    }
  };

  const handleDownloadPDF = async (edicao) => {
    try {
      const response = await api.get(`/doem/edicoes/${edicao.edicao_id}/pdf`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `DOEM_Edicao_${edicao.numero_edicao}_${edicao.ano}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('PDF baixado com sucesso!');
    } catch (error) {
      toast.error('Erro ao baixar PDF');
    }
  };

  const handleImportRTF = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formDataUpload = new FormData();
    formDataUpload.append('file', file);

    try {
      const response = await api.post('/doem/import-rtf', formDataUpload, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setImportedPubs(response.data.publicacoes);
      toast.success(`${response.data.publicacoes_extraidas} publicação(ões) extraída(s) do RTF`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao importar arquivo RTF');
    }
  };

  const handleUseImported = () => {
    const newPubs = importedPubs.map((p, i) => ({
      titulo: p.titulo,
      texto: p.texto,
      secretaria: 'Gabinete do Prefeito',
      segmento: 'Decretos',
      tipo: 'Decreto',
      ordem: formData.publicacoes.length + i + 1
    }));
    
    setFormData({
      ...formData,
      publicacoes: [...formData.publicacoes, ...newPubs]
    });
    
    setImportedPubs([]);
    setShowImportModal(false);
    toast.success('Publicações adicionadas à edição');
  };

  // Funções de Newsletter
  const handleAddInscrito = async (e) => {
    e.preventDefault();
    if (!newInscrito.email || !newInscrito.nome) {
      toast.error('Preencha email e nome');
      return;
    }
    
    try {
      await api.post('/newsletter/inscritos', {
        ...newInscrito,
        confirmado: true
      });
      toast.success('Inscrito adicionado com sucesso!');
      setNewInscrito({ email: '', nome: '', segmentos_interesse: [] });
      setShowNewsletterModal(false);
      fetchInscritos();
      fetchNewsletterStats();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao adicionar inscrito');
    }
  };

  const handleToggleInscrito = async (inscritoId) => {
    try {
      await api.put(`/newsletter/inscritos/${inscritoId}/toggle`);
      fetchInscritos();
      fetchNewsletterStats();
    } catch (error) {
      toast.error('Erro ao alterar status');
    }
  };

  const handleRemoveInscrito = async (inscritoId) => {
    if (!window.confirm('Tem certeza que deseja remover este inscrito?')) return;
    
    try {
      await api.delete(`/newsletter/inscritos/${inscritoId}`);
      toast.success('Inscrito removido');
      fetchInscritos();
      fetchNewsletterStats();
    } catch (error) {
      toast.error('Erro ao remover inscrito');
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR');
    } catch {
      return dateStr;
    }
  };

  const filteredEdicoes = edicoes.filter(e => {
    const matchSearch = 
      String(e.numero_edicao).includes(searchTerm) ||
      e.publicacoes?.some(p => 
        p.titulo?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    return matchSearch;
  });

  if (loading && anoSelecionado === null) {
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
      <div className="space-y-6" data-testid="doem-page">
        {/* Cabeçalho */}
        <div className="flex flex-wrap justify-between items-center gap-4">
          <div>
            <h2 className="text-3xl font-heading font-bold text-foreground flex items-center gap-2">
              <Newspaper size={32} />
              DOEM - Diário Oficial Eletrônico
            </h2>
            <p className="text-muted-foreground mt-1">{edicoes.length} edição(ões) cadastrada(s)</p>
          </div>
          
          <div className="flex flex-wrap gap-2 items-center">
            {/* Seletor de Ano */}
            <div className="flex items-center gap-2 bg-card border border-border rounded-lg px-3 py-2">
              <Calendar size={18} className="text-primary" />
              <select
                value={anoSelecionado || ''}
                onChange={(e) => setAnoSelecionado(parseInt(e.target.value))}
                data-testid="year-filter-doem"
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
              onClick={() => openModal()}
              className="flex items-center gap-2 bg-secondary text-secondary-foreground px-4 py-2 rounded-lg hover:bg-secondary/90 transition-colors"
            >
              <Plus size={18} />
              Nova Edição
            </button>
            
            {user?.is_admin && (
              <button
                onClick={() => setActiveTab(activeTab === 'newsletter' ? 'edicoes' : 'newsletter')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                  activeTab === 'newsletter' 
                    ? 'bg-purple-600 text-white' 
                    : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                }`}
              >
                <Mail size={18} />
                Newsletter
              </button>
            )}
          </div>
        </div>

        {/* Abas de conteúdo */}
        {activeTab === 'edicoes' ? (
          <>
            {/* Filtros */}
            <div className="bg-card border border-border rounded-xl p-4">
              <div className="flex flex-wrap gap-4">
                <div className="relative flex-1 min-w-64">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" size={18} />
                  <input
                    type="text"
                    placeholder="Buscar por número ou título..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                  />
                </div>
                
                <div className="text-sm text-muted-foreground flex items-center">
                  {filteredEdicoes.length} resultado(s)
                </div>
              </div>
            </div>

            {/* Lista de Edições */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {loading ? (
            <div className="col-span-full flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
          ) : filteredEdicoes.length === 0 ? (
            <div className="col-span-full text-center py-12 text-muted-foreground">
              <Newspaper size={48} className="mx-auto mb-4 opacity-50" />
              <p>Nenhuma edição encontrada</p>
            </div>
          ) : (
            filteredEdicoes.map((edicao) => {
              const StatusIcon = STATUS_ICONS[edicao.status] || Clock;
              return (
                <div
                  key={edicao.edicao_id}
                  className="bg-card border border-border rounded-xl p-5 hover:shadow-lg transition-all"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="text-lg font-bold text-foreground">
                        Edição nº {edicao.numero_edicao}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        {formatDate(edicao.data_publicacao)}
                      </p>
                    </div>
                    <span className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold ${STATUS_COLORS[edicao.status]}`}>
                      <StatusIcon size={12} />
                      {edicao.status.charAt(0).toUpperCase() + edicao.status.slice(1)}
                    </span>
                  </div>
                  
                  <div className="mb-4">
                    <p className="text-sm text-muted-foreground">
                      {edicao.publicacoes?.length || 0} publicação(ões)
                    </p>
                    {edicao.publicacoes?.slice(0, 3).map((pub, i) => (
                      <p key={i} className="text-xs text-foreground truncate">
                        • {pub.titulo}
                      </p>
                    ))}
                    {edicao.publicacoes?.length > 3 && (
                      <p className="text-xs text-muted-foreground">
                        ... e mais {edicao.publicacoes.length - 3}
                      </p>
                    )}
                  </div>
                  
                  {edicao.assinatura_digital?.assinado && (
                    <div className="mb-3 p-2 bg-green-50 rounded-lg">
                      <p className="text-xs text-green-700 flex items-center gap-1">
                        <CheckCircle size={12} />
                        Assinado digitalmente
                      </p>
                    </div>
                  )}
                  
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => handleDownloadPDF(edicao)}
                      className="flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      <Download size={14} />
                      PDF
                    </button>
                    
                    {edicao.status !== 'publicado' && (
                      <>
                        <button
                          onClick={() => openModal(edicao)}
                          className="flex items-center gap-1 px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                        >
                          <Edit size={14} />
                          Editar
                        </button>
                        
                        <button
                          onClick={() => handlePublish(edicao)}
                          className="flex items-center gap-1 px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                        >
                          <Send size={14} />
                          Publicar
                        </button>
                        
                        <button
                          onClick={() => handleDelete(edicao)}
                          className="flex items-center gap-1 px-3 py-1.5 text-sm bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90 transition-colors"
                        >
                          <Trash2 size={14} />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
          </>
        ) : (
          /* Seção de Newsletter */
          <div className="space-y-6">
            {/* Estatísticas */}
            {newsletterStats && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-card border border-border rounded-xl p-4">
                  <div className="text-3xl font-bold text-primary">{newsletterStats.total}</div>
                  <div className="text-sm text-muted-foreground">Total de Inscritos</div>
                </div>
                <div className="bg-card border border-border rounded-xl p-4">
                  <div className="text-3xl font-bold text-green-600">{newsletterStats.ativos}</div>
                  <div className="text-sm text-muted-foreground">Ativos e Confirmados</div>
                </div>
                <div className="bg-card border border-border rounded-xl p-4">
                  <div className="text-3xl font-bold text-yellow-600">{newsletterStats.pendentes}</div>
                  <div className="text-sm text-muted-foreground">Pendentes de Confirmação</div>
                </div>
                <div className="bg-card border border-border rounded-xl p-4">
                  <div className="text-sm text-muted-foreground mb-2">Por Tipo:</div>
                  <div className="text-xs space-y-1">
                    <div className="flex justify-between"><span>Público:</span> <span className="font-bold">{newsletterStats.por_tipo?.publico || 0}</span></div>
                    <div className="flex justify-between"><span>Manual:</span> <span className="font-bold">{newsletterStats.por_tipo?.manual || 0}</span></div>
                    <div className="flex justify-between"><span>Usuários:</span> <span className="font-bold">{newsletterStats.por_tipo?.usuario || 0}</span></div>
                  </div>
                </div>
              </div>
            )}

            {/* Adicionar Inscrito */}
            <div className="bg-card border border-border rounded-xl p-6">
              <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
                <Users size={20} />
                Adicionar Inscrito Manualmente
              </h3>
              <form onSubmit={handleAddInscrito} className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <EmailInput
                  value={newInscrito.email}
                  onChange={(e) => setNewInscrito({ ...newInscrito, email: e.target.value })}
                  className="px-3 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                  data-testid="newsletter-email-input"
                />
                <input
                  type="text"
                  placeholder="Nome"
                  value={newInscrito.nome}
                  onChange={(e) => setNewInscrito({ ...newInscrito, nome: e.target.value })}
                  className="px-3 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                  required
                />
                <select
                  multiple
                  value={newInscrito.segmentos_interesse}
                  onChange={(e) => setNewInscrito({ 
                    ...newInscrito, 
                    segmentos_interesse: Array.from(e.target.selectedOptions, o => o.value) 
                  })}
                  className="px-3 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                >
                  <option value="">Todos os segmentos</option>
                  {DOEM_SEGMENTOS.map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
                <button
                  type="submit"
                  className="flex items-center justify-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors"
                >
                  <Plus size={18} />
                  Adicionar
                </button>
              </form>
            </div>

            {/* Lista de Inscritos */}
            <div className="bg-card border border-border rounded-xl overflow-hidden">
              <div className="px-6 py-4 border-b border-border">
                <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                  <Mail size={20} />
                  Lista de Inscritos ({inscritos.length})
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-muted/50">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-foreground">Nome</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-foreground">Email</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-foreground">Tipo</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-foreground">Status</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-foreground">Segmentos</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-foreground">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {inscritos.map((inscrito) => (
                      <tr key={inscrito.inscrito_id} className={!inscrito.ativo ? 'opacity-50' : ''}>
                        <td className="px-4 py-3 text-sm">{inscrito.nome}</td>
                        <td className="px-4 py-3 text-sm">{inscrito.email}</td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            inscrito.tipo === 'publico' ? 'bg-blue-100 text-blue-700' :
                            inscrito.tipo === 'manual' ? 'bg-purple-100 text-purple-700' :
                            'bg-gray-100 text-gray-700'
                          }`}>
                            {inscrito.tipo}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm">
                          {inscrito.confirmado ? (
                            <span className="flex items-center gap-1 text-green-600">
                              <CheckCircle size={14} /> Confirmado
                            </span>
                          ) : (
                            <span className="flex items-center gap-1 text-yellow-600">
                              <Clock size={14} /> Pendente
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          {inscrito.segmentos_interesse?.length > 0 
                            ? inscrito.segmentos_interesse.join(', ') 
                            : 'Todos'}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleToggleInscrito(inscrito.inscrito_id)}
                              className={`px-2 py-1 text-xs rounded ${
                                inscrito.ativo 
                                  ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200' 
                                  : 'bg-green-100 text-green-700 hover:bg-green-200'
                              }`}
                            >
                              {inscrito.ativo ? 'Desativar' : 'Ativar'}
                            </button>
                            <button
                              onClick={() => handleRemoveInscrito(inscrito.inscrito_id)}
                              className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
                            >
                              <Trash2 size={12} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Modal de Criação/Edição */}
        {showModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-card border-b border-border px-6 py-4 flex justify-between items-center">
                <h3 className="text-xl font-bold text-foreground">
                  {editingEdicao ? `Editar Edição nº ${editingEdicao.numero_edicao}` : 'Nova Edição do DOEM'}
                </h3>
                <button onClick={() => setShowModal(false)} className="text-muted-foreground hover:text-foreground">
                  <X size={24} />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="p-6 space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-foreground mb-1">
                      <Calendar size={14} className="inline mr-1" />
                      Data de Publicação
                    </label>
                    <input
                      type="date"
                      value={formData.data_publicacao}
                      onChange={(e) => setFormData({ ...formData, data_publicacao: e.target.value })}
                      className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                    />
                  </div>
                  
                  <div className="flex items-end">
                    <button
                      type="button"
                      onClick={() => setShowImportModal(true)}
                      className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      <Upload size={18} />
                      Importar RTF
                    </button>
                  </div>
                </div>

                {/* Lista de Publicações */}
                <div>
                  <h4 className="text-lg font-semibold text-foreground mb-3">
                    Publicações ({formData.publicacoes.length})
                  </h4>
                  
                  {formData.publicacoes.map((pub, index) => (
                    <div key={index} className="bg-muted/50 p-4 rounded-lg mb-3">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <div className="flex gap-2 mb-1">
                            <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                              {pub.segmento}
                            </span>
                            <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded">
                              {pub.tipo}
                            </span>
                          </div>
                          <h5 className="font-semibold text-foreground mt-1">{pub.titulo}</h5>
                          <p className="text-xs text-muted-foreground">{pub.secretaria}</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleRemovePub(index)}
                          className="text-destructive hover:bg-destructive/10 p-1 rounded"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                      <p className="text-sm text-foreground line-clamp-3">{pub.texto}</p>
                    </div>
                  ))}
                </div>

                {/* Adicionar Nova Publicação */}
                <div className="border border-border rounded-lg p-4">
                  <h4 className="font-semibold text-foreground mb-3">Adicionar Publicação</h4>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">Título *</label>
                      <input
                        type="text"
                        value={newPub.titulo}
                        onChange={(e) => setNewPub({ ...newPub, titulo: e.target.value })}
                        className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                        placeholder="Ex: DECRETO Nº 001/2026"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">Segmento</label>
                      <select
                        value={newPub.segmento}
                        onChange={(e) => setNewPub({ 
                          ...newPub, 
                          segmento: e.target.value,
                          tipo: TIPOS_POR_SEGMENTO[e.target.value]?.[0] || 'Decreto'
                        })}
                        className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                      >
                        {DOEM_SEGMENTOS.map(s => (
                          <option key={s} value={s}>{s}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">Tipo</label>
                      <select
                        value={newPub.tipo}
                        onChange={(e) => setNewPub({ ...newPub, tipo: e.target.value })}
                        className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                      >
                        {(TIPOS_POR_SEGMENTO[newPub.segmento] || []).map(t => (
                          <option key={t} value={t}>{t}</option>
                        ))}
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">Secretaria</label>
                      <input
                        type="text"
                        value={newPub.secretaria}
                        onChange={(e) => setNewPub({ ...newPub, secretaria: e.target.value })}
                        className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                        placeholder="Gabinete do Prefeito"
                      />
                    </div>
                  </div>
                  
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-foreground mb-1">Texto *</label>
                    <textarea
                      value={newPub.texto}
                      onChange={(e) => setNewPub({ ...newPub, texto: e.target.value })}
                      className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                      rows={5}
                      placeholder="Conteúdo completo da publicação..."
                    />
                  </div>
                  
                  <button
                    type="button"
                    onClick={handleAddPub}
                    className="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/90 transition-colors"
                  >
                    <Plus size={18} />
                    Adicionar Publicação
                  </button>
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
                    {editingEdicao ? 'Salvar Alterações' : 'Criar Edição'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal de Importação RTF */}
        {showImportModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b border-border">
                <div className="flex justify-between items-center">
                  <h3 className="text-xl font-bold text-foreground">Importar Arquivo RTF</h3>
                  <button onClick={() => { setShowImportModal(false); setImportedPubs([]); }} className="text-muted-foreground hover:text-foreground">
                    <X size={24} />
                  </button>
                </div>
              </div>
              
              <div className="p-6 space-y-4">
                <p className="text-muted-foreground text-sm">
                  Selecione um arquivo RTF para extrair as publicações. O formato esperado usa === TÍTULO === para separar publicações.
                </p>
                
                <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
                  <Upload size={48} className="mx-auto text-muted-foreground mb-4" />
                  <p className="text-foreground font-semibold mb-2">Formato: Arial, tamanho 9</p>
                  <p className="text-sm text-muted-foreground mb-4">Extensão .rtf</p>
                  
                  <label className="cursor-pointer">
                    <span className="bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors inline-block">
                      Selecionar Arquivo RTF
                    </span>
                    <input
                      type="file"
                      accept=".rtf"
                      onChange={handleImportRTF}
                      className="hidden"
                    />
                  </label>
                </div>
                
                {importedPubs.length > 0 && (
                  <div className="mt-4">
                    <h4 className="font-semibold text-foreground mb-2">
                      Publicações Extraídas ({importedPubs.length})
                    </h4>
                    {importedPubs.map((pub, i) => (
                      <div key={i} className="bg-muted/50 p-3 rounded-lg mb-2">
                        <h5 className="font-medium text-foreground">{pub.titulo}</h5>
                        <p className="text-sm text-muted-foreground line-clamp-2">{pub.texto}</p>
                      </div>
                    ))}
                    
                    <button
                      onClick={handleUseImported}
                      className="w-full mt-4 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                    >
                      <CheckCircle size={18} />
                      Usar Publicações Extraídas
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default DOEM;
