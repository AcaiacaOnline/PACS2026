import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  BarChart3, Clock, Users, Building2, TrendingUp, FileText, 
  Calendar, Filter, ArrowUpDown, CheckCircle, AlertCircle, PieChart as PieChartIcon
} from 'lucide-react';
import Layout from '../components/Layout';
import api from '../utils/api';
import { toast } from 'sonner';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line, AreaChart, Area
} from 'recharts';

const COLORS = [
  '#1F4E78', '#2E7D32', '#F57C00', '#7B1FA2', '#C62828', 
  '#00838F', '#5D4037', '#455A64', '#AD1457', '#1565C0',
  '#00695C', '#EF6C00', '#6A1B9A', '#283593'
];

const DashboardProcessual = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filtroModalidade, setFiltroModalidade] = useState('');
  const [periodoInicio, setPeriodoInicio] = useState('');
  const [periodoFim, setPeriodoFim] = useState('');
  const [ordenacaoResponsavel, setOrdenacaoResponsavel] = useState('quantidade');

  useEffect(() => {
    fetchStats();
  }, [periodoInicio, periodoFim]);

  const fetchStats = async () => {
    try {
      let url = '/processos/stats';
      const params = new URLSearchParams();
      if (periodoInicio) params.append('data_inicio', periodoInicio);
      if (periodoFim) params.append('data_fim', periodoFim);
      if (params.toString()) url += `?${params.toString()}`;
      
      const response = await api.get(url);
      setStats(response.data);
    } catch (error) {
      toast.error('Erro ao carregar estatísticas');
    } finally {
      setLoading(false);
    }
  };

  const formatDias = (dias) => {
    if (dias === 0) return '0 dias';
    if (dias < 7) return `${dias} dias`;
    if (dias < 30) return `${Math.round(dias / 7)} semanas`;
    return `${Math.round(dias / 30)} meses`;
  };

  // Filtrar dados por modalidade
  const getFilteredModalidadeData = () => {
    if (!stats?.stats_by_modalidade) return [];
    if (!filtroModalidade) return stats.stats_by_modalidade;
    return stats.stats_by_modalidade.filter(m => 
      m.modalidade.toLowerCase().includes(filtroModalidade.toLowerCase())
    );
  };

  // Ordenar responsáveis
  const getSortedResponsaveis = () => {
    if (!stats?.processos_por_responsavel) return [];
    const data = [...stats.processos_por_responsavel];
    
    if (ordenacaoResponsavel === 'quantidade') {
      data.sort((a, b) => b.quantidade - a.quantidade);
    } else if (ordenacaoResponsavel === 'concluidos') {
      data.sort((a, b) => b.concluidos - a.concluidos);
    } else if (ordenacaoResponsavel === 'nome') {
      data.sort((a, b) => a.responsavel.localeCompare(b.responsavel));
    }
    
    return data.slice(0, 10); // Top 10
  };

  // Tooltip personalizado
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card border border-border shadow-lg rounded-lg p-3">
          <p className="font-semibold text-foreground">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
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

  const filteredModalidadeData = getFilteredModalidadeData();
  const sortedResponsaveis = getSortedResponsaveis();

  return (
    <Layout>
      <div className="space-y-6" data-testid="dashboard-processual">
        {/* Cabeçalho */}
        <div className="flex flex-wrap justify-between items-center gap-4">
          <div>
            <h2 className="text-3xl font-heading font-bold text-foreground flex items-center gap-2">
              <BarChart3 size={32} />
              Dashboard Gestão Processual
            </h2>
            <p className="text-muted-foreground mt-1">
              Visão geral do fluxo e eficiência dos processos
            </p>
          </div>
          
          <button
            onClick={() => navigate('/gestao-processual')}
            className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors"
          >
            <FileText size={18} />
            Ver Processos
          </button>
        </div>

        {/* Filtro por Período */}
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <Filter size={18} className="text-muted-foreground" />
              <span className="text-sm font-medium text-foreground">Filtrar por Período:</span>
            </div>
            <div className="flex items-center gap-2">
              <Calendar size={16} className="text-muted-foreground" />
              <input
                type="date"
                value={periodoInicio}
                onChange={(e) => setPeriodoInicio(e.target.value)}
                className="px-3 py-1.5 border border-input bg-background rounded-lg text-sm focus:ring-2 focus:ring-ring outline-none"
              />
              <span className="text-muted-foreground">até</span>
              <input
                type="date"
                value={periodoFim}
                onChange={(e) => setPeriodoFim(e.target.value)}
                className="px-3 py-1.5 border border-input bg-background rounded-lg text-sm focus:ring-2 focus:ring-ring outline-none"
              />
            </div>
            {(periodoInicio || periodoFim) && (
              <button
                onClick={() => { setPeriodoInicio(''); setPeriodoFim(''); }}
                className="text-sm text-primary hover:underline"
              >
                Limpar filtro
              </button>
            )}
          </div>
        </div>

        {/* Cards de Resumo */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-primary to-primary/80 p-6 rounded-xl shadow-lg text-primary-foreground">
            <div className="flex items-center justify-between mb-2">
              <div className="bg-white/20 p-2 rounded">
                <FileText className="w-6 h-6" />
              </div>
              <TrendingUp className="w-5 h-5" />
            </div>
            <div className="text-sm opacity-90">Total de Processos</div>
            <div className="text-3xl font-bold">{stats?.total_processos || 0}</div>
          </div>

          <div className="bg-gradient-to-br from-green-600 to-green-700 p-6 rounded-xl shadow-lg text-white">
            <div className="flex items-center justify-between mb-2">
              <div className="bg-white/20 p-2 rounded">
                <CheckCircle className="w-6 h-6" />
              </div>
            </div>
            <div className="text-sm opacity-90">Concluídos</div>
            <div className="text-3xl font-bold">{stats?.total_concluidos || 0}</div>
            <div className="text-xs opacity-75 mt-1">
              {stats?.taxa_conclusao || 0}% de conclusão
            </div>
          </div>

          <div className="bg-gradient-to-br from-amber-500 to-amber-600 p-6 rounded-xl shadow-lg text-white">
            <div className="flex items-center justify-between mb-2">
              <div className="bg-white/20 p-2 rounded">
                <AlertCircle className="w-6 h-6" />
              </div>
            </div>
            <div className="text-sm opacity-90">Em Andamento</div>
            <div className="text-3xl font-bold">{stats?.total_em_andamento || 0}</div>
          </div>

          <div className="bg-gradient-to-br from-purple-600 to-purple-700 p-6 rounded-xl shadow-lg text-white">
            <div className="flex items-center justify-between mb-2">
              <div className="bg-white/20 p-2 rounded">
                <Clock className="w-6 h-6" />
              </div>
            </div>
            <div className="text-sm opacity-90">Tempo Médio</div>
            <div className="text-3xl font-bold">{stats?.tempo_medio_dias || 0}</div>
            <div className="text-xs opacity-75 mt-1">dias para conclusão</div>
          </div>
        </div>

        {/* Gráficos - Primeira Linha */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Processos por Modalidade */}
          <div className="bg-card border border-border rounded-xl shadow-lg overflow-hidden">
            <div className="bg-gradient-to-r from-primary/10 to-secondary/10 px-6 py-4 border-b border-border">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <PieChartIcon className="w-5 h-5 text-primary" />
                  <h3 className="text-lg font-bold text-foreground">Processos por Modalidade</h3>
                </div>
                <input
                  type="text"
                  placeholder="Filtrar..."
                  value={filtroModalidade}
                  onChange={(e) => setFiltroModalidade(e.target.value)}
                  className="px-2 py-1 text-sm border border-input bg-background rounded focus:ring-1 focus:ring-ring outline-none w-28"
                />
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Distribuição por tipo de modalidade licitatória
              </p>
            </div>
            <div className="p-4">
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={filteredModalidadeData}
                      dataKey="quantidade"
                      nameKey="modalidade"
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      label={({ modalidade, percent }) => 
                        `${modalidade?.substring(0, 15)}${modalidade?.length > 15 ? '...' : ''} (${(percent * 100).toFixed(0)}%)`
                      }
                      labelLine={true}
                    >
                      {filteredModalidadeData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Status dos Processos */}
          <div className="bg-card border border-border rounded-xl shadow-lg overflow-hidden">
            <div className="bg-gradient-to-r from-primary/10 to-secondary/10 px-6 py-4 border-b border-border">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-primary" />
                <h3 className="text-lg font-bold text-foreground">Status dos Processos</h3>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Quantidade por situação atual
              </p>
            </div>
            <div className="p-4">
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats?.stats_by_status || []} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis 
                      type="category" 
                      dataKey="status" 
                      width={120}
                      tick={{ fontSize: 11 }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="quantidade" name="Quantidade" radius={[0, 4, 4, 0]}>
                      {stats?.stats_by_status?.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>

        {/* Tempo Médio de Finalização */}
        <div className="bg-card border border-border rounded-xl shadow-lg overflow-hidden">
          <div className="bg-gradient-to-r from-purple-500/10 to-purple-600/10 px-6 py-4 border-b border-border">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-purple-600" />
              <h3 className="text-lg font-bold text-foreground">Tempo Médio para Finalização</h3>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Evolução do tempo de conclusão ao longo dos meses (em dias)
            </p>
          </div>
          <div className="p-4">
            {stats?.tempo_medio_por_mes && stats.tempo_medio_por_mes.length > 0 ? (
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={stats.tempo_medio_por_mes}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="mes" 
                      tick={{ fontSize: 11 }}
                      tickFormatter={(value) => {
                        const [year, month] = value.split('-');
                        const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
                        return `${months[parseInt(month) - 1]}/${year.slice(2)}`;
                      }}
                    />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip 
                      formatter={(value, name) => [
                        name === 'tempo_medio' ? `${value} dias` : value,
                        name === 'tempo_medio' ? 'Tempo Médio' : 'Processos'
                      ]}
                    />
                    <Legend />
                    <Area 
                      type="monotone" 
                      dataKey="tempo_medio" 
                      name="Tempo Médio (dias)" 
                      stroke="#7B1FA2" 
                      fill="#7B1FA2" 
                      fillOpacity={0.3}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="quantidade" 
                      name="Processos Concluídos" 
                      stroke="#2E7D32" 
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <Clock size={48} className="mx-auto mb-4 opacity-50" />
                <p>Dados insuficientes para exibir o gráfico</p>
              </div>
            )}
          </div>
          
          {/* Tempo por Modalidade */}
          {stats?.tempo_medio_por_modalidade && stats.tempo_medio_por_modalidade.length > 0 && (
            <div className="px-6 pb-4">
              <h4 className="text-sm font-semibold text-foreground mb-3">
                Tempo Médio por Modalidade (dias)
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
                {stats.tempo_medio_por_modalidade.slice(0, 6).map((item, index) => (
                  <div 
                    key={item.modalidade}
                    className="bg-muted/50 rounded-lg p-3 text-center"
                  >
                    <div className="text-lg font-bold text-foreground">
                      {item.tempo_medio}
                    </div>
                    <div className="text-xs text-muted-foreground truncate" title={item.modalidade}>
                      {item.modalidade}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      ({item.quantidade} proc.)
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Processos por Responsável */}
        <div className="bg-card border border-border rounded-xl shadow-lg overflow-hidden">
          <div className="bg-gradient-to-r from-blue-500/10 to-blue-600/10 px-6 py-4 border-b border-border">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <Users className="w-5 h-5 text-blue-600" />
                  <h3 className="text-lg font-bold text-foreground">Processos por Responsável</h3>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Top 10 responsáveis por quantidade de processos
                </p>
              </div>
              <div className="flex items-center gap-2">
                <ArrowUpDown size={16} className="text-muted-foreground" />
                <select
                  value={ordenacaoResponsavel}
                  onChange={(e) => setOrdenacaoResponsavel(e.target.value)}
                  className="px-2 py-1 text-sm border border-input bg-background rounded focus:ring-1 focus:ring-ring outline-none"
                >
                  <option value="quantidade">Por Total</option>
                  <option value="concluidos">Por Concluídos</option>
                  <option value="nome">Por Nome</option>
                </select>
              </div>
            </div>
          </div>
          <div className="p-4">
            {sortedResponsaveis.length > 0 ? (
              <div className="space-y-3">
                {sortedResponsaveis.map((resp, index) => {
                  const porcentagemConcluidos = resp.quantidade > 0 
                    ? Math.round((resp.concluidos / resp.quantidade) * 100) 
                    : 0;
                  
                  return (
                    <div key={resp.responsavel} className="flex items-center gap-4">
                      <div className="w-6 text-center text-sm font-bold text-muted-foreground">
                        {index + 1}º
                      </div>
                      <div className="flex-1">
                        <div className="flex justify-between items-center mb-1">
                          <span className="font-medium text-foreground truncate max-w-xs" title={resp.responsavel}>
                            {resp.responsavel || 'Não Atribuído'}
                          </span>
                          <div className="flex items-center gap-2 text-sm">
                            <span className="text-foreground font-semibold">{resp.quantidade}</span>
                            <span className="text-green-600">({resp.concluidos} ✓)</span>
                          </div>
                        </div>
                        <div className="w-full bg-muted rounded-full h-2">
                          <div
                            className="bg-green-500 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${porcentagemConcluidos}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                Nenhum responsável encontrado
              </div>
            )}
          </div>
        </div>

        {/* Timeline de Processos */}
        <div className="bg-card border border-border rounded-xl shadow-lg overflow-hidden">
          <div className="bg-gradient-to-r from-green-500/10 to-green-600/10 px-6 py-4 border-b border-border">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-600" />
              <h3 className="text-lg font-bold text-foreground">Timeline de Processos</h3>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Evolução mensal dos processos iniciados e concluídos
            </p>
          </div>
          <div className="p-4">
            {stats?.timeline && stats.timeline.length > 0 ? (
              <div className="h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.timeline}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="mes"
                      tick={{ fontSize: 10 }}
                      tickFormatter={(value) => {
                        const [year, month] = value.split('-');
                        const months = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'];
                        return `${months[parseInt(month) - 1]}/${year.slice(2)}`;
                      }}
                    />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    <Bar dataKey="quantidade" name="Iniciados" fill="#1F4E78" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="concluidos" name="Concluídos" fill="#2E7D32" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                Dados de timeline indisponíveis
              </div>
            )}
          </div>
        </div>

        {/* Processos por Secretaria */}
        <div className="bg-card border border-border rounded-xl shadow-lg overflow-hidden">
          <div className="bg-gradient-to-r from-amber-500/10 to-amber-600/10 px-6 py-4 border-b border-border">
            <div className="flex items-center gap-2">
              <Building2 className="w-5 h-5 text-amber-600" />
              <h3 className="text-lg font-bold text-foreground">Processos por Secretaria</h3>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Distribuição por unidade requisitante
            </p>
          </div>
          <div className="p-4">
            {stats?.processos_por_secretaria && stats.processos_por_secretaria.length > 0 ? (
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.processos_por_secretaria.slice(0, 10)} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis 
                      type="category" 
                      dataKey="secretaria" 
                      width={200}
                      tick={{ fontSize: 10 }}
                      tickFormatter={(value) => value?.length > 30 ? value.substring(0, 30) + '...' : value}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="quantidade" name="Processos" fill="#F57C00" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                Nenhuma secretaria encontrada
              </div>
            )}
          </div>
        </div>

        {/* Rodapé com informações */}
        <div className="bg-muted/30 border border-border rounded-lg p-4 text-sm text-muted-foreground">
          <p className="font-semibold text-foreground mb-2">Fonte dos Dados e Metodologia:</p>
          <ul className="space-y-1">
            <li>• <b>Tempo Médio:</b> Calculado como a diferença entre Data de Início e Data do Contrato para processos concluídos</li>
            <li>• <b>Taxa de Conclusão:</b> (Processos Concluídos / Total de Processos) × 100</li>
            <li>• <b>Processos por Responsável:</b> Agrupados pelo campo "Responsável" de cada processo</li>
            <li>• <b>Dados:</b> Baseados em {stats?.total_processos || 0} processos cadastrados no sistema</li>
          </ul>
        </div>
      </div>
    </Layout>
  );
};

export default DashboardProcessual;
