import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ClipboardList, Plus, Search, Edit, Trash2, FileText, 
  FileSpreadsheet, Upload, X, Save, Calendar, Building2, User, BarChart3,
  TrendingUp, Clock, CheckCircle, AlertCircle, PieChart as PieChartIcon
} from 'lucide-react';
import Layout from '../components/Layout';
import api from '../utils/api';
import { toast } from 'sonner';
import { maskProcesso } from '../utils/masks';
import Pagination, { usePagination, paginateData } from '../components/Pagination';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip
} from 'recharts';

const STATUS_OPTIONS = [
  'Em Elaboração', 'Aguardando Aprovação', 'Aprovado', 'Em Licitação', 
  'Homologado', 'Contratado', 'Em Execução', 'Concluído', 'Cancelado', 'Suspenso'
];

const MODALIDADE_OPTIONS = [
  'Pregão Eletrônico', 'Pregão Presencial', 'Concorrência', 'Tomada de Preços',
  'Convite', 'Concurso', 'Leilão', 'Dispensa de Licitação', 'Dispensa por Limite',
  'Dispensa por Justificativa', 'Inexigibilidade', 'Chamamento Público', 
  'Adesão a Ata de Registro de Preços', 'Contratação Direta'
];

const STATUS_COLORS = {
  'Concluído': 'bg-green-100 text-green-800',
  'Em Elaboração': 'bg-blue-100 text-blue-800',
  'Aguardando Aprovação': 'bg-yellow-100 text-yellow-800',
  'Aprovado': 'bg-emerald-100 text-emerald-800',
  'Em Licitação': 'bg-purple-100 text-purple-800',
  'Homologado': 'bg-teal-100 text-teal-800',
  'Contratado': 'bg-indigo-100 text-indigo-800',
  'Em Execução': 'bg-orange-100 text-orange-800',
  'Cancelado': 'bg-red-100 text-red-800',
  'Suspenso': 'bg-gray-100 text-gray-800',
  // Legado (para compatibilidade)
  'Iniciado': 'bg-blue-100 text-blue-800',
  'Publicado': 'bg-purple-100 text-purple-800',
  'Aguardando Jurídico': 'bg-yellow-100 text-yellow-800',
};

const DASHBOARD_COLORS = ['#1F4E78', '#2E7D32', '#F57C00', '#7B1FA2', '#C62828', '#00838F'];

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
  
  // Dashboard stats
  const [dashboardStats, setDashboardStats] = useState(null);
  const [showDashboard, setShowDashboard] = useState(true);
  
  // Paginação
  const { currentPage, setCurrentPage, pageSize, setPageSize, resetPage } = usePagination(20);
  const [totalProcessos, setTotalProcessos] = useState(0);
  
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
    observacoes: '',
    ano: null
  });

  useEffect(() => {
    fetchUser();
    fetchAnos();
    fetchDashboardStats();
  }, []);

  useEffect(() => {
    if (anoSelecionado !== null) {
      fetchProcessos();
    }
  }, [anoSelecionado, currentPage, pageSize, searchTerm, filterStatus, filterModalidade]);

  const fetchDashboardStats = async () => {
    try {
      const response = await api.get('/processos/stats');
      setDashboardStats(response.data);
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
    }
  };

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
      const response = await api.get('/processos/anos');
      const anos = response.data.anos;
      setAnos(anos);
      // Selecionar o primeiro ano disponível (mais recente com dados)
      if (anos && anos.length > 0) {
        // Se existem processos em 2025, selecionar 2025
        if (anos.includes(2025)) {
          setAnoSelecionado(2025);
        } else {
          setAnoSelecionado(anos[0]);
        }
      } else {
        setAnoSelecionado(new Date().getFullYear());
      }
    } catch (error) {
      console.error('Erro ao carregar anos:', error);
      setAnoSelecionado(new Date().getFullYear());
    }
  };

  const fetchProcessos = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (anoSelecionado) params.append('ano', anoSelecionado);
      params.append('page', currentPage);
      params.append('page_size', pageSize);
      if (searchTerm) params.append('search', searchTerm);
      if (filterStatus) params.append('status', filterStatus);
      if (filterModalidade) params.append('modalidade', filterModalidade);
      
      const response = await api.get(`/processos/paginado?${params.toString()}`);
      setProcessos(response.data.items);
      setTotalProcessos(response.data.total || 0);
    } catch (error) {
      toast.error('Erro ao carregar processos');
      // Fallback para endpoint antigo se o novo falhar
      try {
        const params = anoSelecionado ? `?ano=${anoSelecionado}` : '';
        const response = await api.get(`/processos${params}`);
        setProcessos(response.data);
        setTotalProcessos(response.data.length || 0);
      } catch (e) {
        console.error('Erro no fallback:', e);
      }
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
        observacoes: processo.observacoes || '',
        ano: processo.ano || anoSelecionado
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
        observacoes: '',
        ano: anoSelecionado
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
      const params = new URLSearchParams({ orientation });
      if (anoSelecionado) params.append('ano', anoSelecionado);
      
      const response = await api.get(`/processos/export/pdf?${params.toString()}`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const orientationName = orientation === 'landscape' ? 'Paisagem' : 'Retrato';
      const yearSuffix = anoSelecionado ? `_${anoSelecionado}` : '';
      link.setAttribute('download', `Gestao_Processual_${orientationName}${yearSuffix}.pdf`);
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
      const params = anoSelecionado ? `?ano=${anoSelecionado}` : '';
      const response = await api.get(`/processos/export/xlsx${params}`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const yearSuffix = anoSelecionado ? `_${anoSelecionado}` : '';
      link.setAttribute('download', `Gestao_Processual${yearSuffix}.xlsx`);
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

  // Os dados já vêm paginados e filtrados do backend
  const paginatedProcessos = processos;
  
  // Reset página quando filtros mudam
  useEffect(() => {
    resetPage();
  }, [searchTerm, filterStatus, filterModalidade, anoSelecionado]);

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
            <p className="text-muted-foreground mt-1">{totalProcessos} processo(s) cadastrado(s)</p>
          </div>
          
          <div className="flex flex-wrap gap-2 items-center">
            {/* Seletor de Ano Visual */}
            <div className="flex items-center gap-2 bg-card border border-border rounded-lg px-3 py-2">
              <Calendar size={18} className="text-primary" />
              <select
                value={anoSelecionado || ''}
                onChange={(e) => setAnoSelecionado(parseInt(e.target.value))}
                data-testid="year-filter-select-processos"
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
              onClick={() => setShowDashboard(!showDashboard)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                showDashboard 
                  ? 'bg-purple-600 text-white hover:bg-purple-700' 
                  : 'bg-card border border-border text-foreground hover:bg-muted'
              }`}
              data-testid="toggle-dashboard-btn"
            >
              <BarChart3 size={18} />
              {showDashboard ? 'Ocultar Dashboard' : 'Mostrar Dashboard'}
            </button>
            
            <button
              onClick={() => navigate('/gestao-processual/dashboard')}
              className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
            >
              <PieChartIcon size={18} />
              Dashboard Completo
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

        {/* Dashboard Resumido */}
        {showDashboard && dashboardStats && (
          <div className="space-y-4">
            {/* Cards de KPIs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Total de Processos */}
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-4 text-white shadow-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-blue-100 text-sm">Total de Processos</p>
                    <p className="text-3xl font-bold mt-1">{dashboardStats.total_processos}</p>
                  </div>
                  <div className="bg-white/20 rounded-lg p-3">
                    <ClipboardList size={24} />
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t border-white/20 text-sm">
                  <span className="text-blue-100">Todos os anos</span>
                </div>
              </div>

              {/* Concluídos */}
              <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-4 text-white shadow-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-green-100 text-sm">Concluídos</p>
                    <p className="text-3xl font-bold mt-1">
                      {dashboardStats.stats_by_status?.find(s => s.status === 'Concluído')?.quantidade || 0}
                    </p>
                  </div>
                  <div className="bg-white/20 rounded-lg p-3">
                    <CheckCircle size={24} />
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t border-white/20 text-sm">
                  <span className="text-green-100">
                    {dashboardStats.total_processos > 0 
                      ? `${Math.round(((dashboardStats.stats_by_status?.find(s => s.status === 'Concluído')?.quantidade || 0) / dashboardStats.total_processos) * 100)}% do total`
                      : '0% do total'
                    }
                  </span>
                </div>
              </div>

              {/* Em Andamento */}
              <div className="bg-gradient-to-br from-amber-500 to-amber-600 rounded-xl p-4 text-white shadow-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-amber-100 text-sm">Em Andamento</p>
                    <p className="text-3xl font-bold mt-1">
                      {dashboardStats.total_processos - (dashboardStats.stats_by_status?.find(s => s.status === 'Concluído')?.quantidade || 0) - (dashboardStats.stats_by_status?.find(s => s.status === 'Cancelado')?.quantidade || 0)}
                    </p>
                  </div>
                  <div className="bg-white/20 rounded-lg p-3">
                    <Clock size={24} />
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t border-white/20 text-sm">
                  <span className="text-amber-100">Ativos</span>
                </div>
              </div>

              {/* Tempo Médio */}
              <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-4 text-white shadow-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-purple-100 text-sm">Tempo Médio</p>
                    <p className="text-3xl font-bold mt-1">{dashboardStats.tempo_medio_finalizacao || 0}</p>
                  </div>
                  <div className="bg-white/20 rounded-lg p-3">
                    <TrendingUp size={24} />
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t border-white/20 text-sm">
                  <span className="text-purple-100">Dias para concluir</span>
                </div>
              </div>
            </div>

            {/* Gráficos Resumidos */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Por Status */}
              <div className="bg-card border border-border rounded-xl p-4">
                <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                  <PieChartIcon size={18} className="text-primary" />
                  Processos por Status
                </h3>
                <div className="h-48">
                  {dashboardStats.stats_by_status && dashboardStats.stats_by_status.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={dashboardStats.stats_by_status}
                          dataKey="quantidade"
                          nameKey="status"
                          cx="50%"
                          cy="50%"
                          innerRadius={40}
                          outerRadius={70}
                          paddingAngle={2}
                        >
                          {dashboardStats.stats_by_status.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={DASHBOARD_COLORS[index % DASHBOARD_COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip 
                          formatter={(value, name) => [`${value} processos`, name]}
                          contentStyle={{ backgroundColor: 'var(--card)', border: '1px solid var(--border)' }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full text-muted-foreground">
                      Sem dados disponíveis
                    </div>
                  )}
                </div>
                <div className="flex flex-wrap gap-2 mt-2">
                  {dashboardStats.stats_by_status?.slice(0, 4).map((item, index) => (
                    <span 
                      key={item.status} 
                      className="text-xs px-2 py-1 rounded-full flex items-center gap-1"
                      style={{ backgroundColor: `${DASHBOARD_COLORS[index % DASHBOARD_COLORS.length]}20`, color: DASHBOARD_COLORS[index % DASHBOARD_COLORS.length] }}
                    >
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: DASHBOARD_COLORS[index % DASHBOARD_COLORS.length] }}></span>
                      {item.status}: {item.quantidade}
                    </span>
                  ))}
                </div>
              </div>

              {/* Por Modalidade */}
              <div className="bg-card border border-border rounded-xl p-4">
                <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                  <BarChart3 size={18} className="text-primary" />
                  Top Modalidades
                </h3>
                <div className="space-y-3">
                  {dashboardStats.stats_by_modalidade?.slice(0, 5).map((item, index) => (
                    <div key={item.modalidade} className="flex items-center gap-3">
                      <div className="w-24 text-xs text-muted-foreground truncate" title={item.modalidade}>
                        {item.modalidade}
                      </div>
                      <div className="flex-1 h-6 bg-muted rounded-full overflow-hidden">
                        <div 
                          className="h-full rounded-full transition-all duration-500"
                          style={{ 
                            width: `${(item.quantidade / (dashboardStats.stats_by_modalidade[0]?.quantidade || 1)) * 100}%`,
                            backgroundColor: DASHBOARD_COLORS[index % DASHBOARD_COLORS.length]
                          }}
                        />
                      </div>
                      <div className="w-8 text-right font-semibold text-sm">
                        {item.quantidade}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filtros */}
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
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
              value={anoSelecionado || ''}
              onChange={(e) => setAnoSelecionado(e.target.value ? parseInt(e.target.value) : null)}
              className="px-4 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
            >
              <option value="">Todos os Anos</option>
              {anos.map(ano => (
                <option key={ano} value={ano}>{ano}</option>
              ))}
            </select>
            
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
              {totalProcessos} resultado(s)
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
                {paginatedProcessos.map((processo) => (
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

          {/* Paginação */}
          <div className="p-4 border-t border-border">
            <Pagination
              currentPage={currentPage}
              totalItems={totalProcessos}
              pageSize={pageSize}
              onPageChange={setCurrentPage}
              onPageSizeChange={setPageSize}
            />
          </div>

          {processos.length === 0 && (
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
                      onChange={(e) => setFormData({ ...formData, numero_processo: maskProcesso(e.target.value) })}
                      className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring outline-none"
                      placeholder="PRC - 0001/2025"
                      maxLength={16}
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
