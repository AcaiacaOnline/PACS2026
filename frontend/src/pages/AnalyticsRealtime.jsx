import React, { useState, useEffect, useCallback } from 'react';
import { 
  Activity, BarChart3, TrendingUp, Users, Clock, Server,
  RefreshCw, Zap, Building2, FileText, CheckCircle, AlertTriangle,
  ArrowUpRight, ArrowDownRight, Calendar, PieChart
} from 'lucide-react';
import Layout from '../components/Layout';
import api from '../utils/api';
import { toast } from 'sonner';
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line, XAxis, YAxis, 
  CartesianGrid, Tooltip, ResponsiveContainer, PieChart as RePieChart, 
  Pie, Cell, Legend
} from 'recharts';

const COLORS = ['#1F4E78', '#2E7D32', '#F57C00', '#7B1FA2', '#C62828', '#00838F', '#5D4037', '#455A64', '#AD1457', '#1565C0'];

const AnalyticsRealtime = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchMetrics = useCallback(async () => {
    try {
      const response = await api.get('/analytics/realtime');
      setMetrics(response.data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Erro ao carregar métricas:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  // Auto-refresh a cada 30 segundos
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchMetrics]);

  const formatCurrency = (value) => {
    return (value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  };

  const formatCurrencyShort = (value) => {
    if (value >= 1000000) return `R$ ${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `R$ ${(value / 1000).toFixed(0)}K`;
    return formatCurrency(value);
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  const { 
    uso_por_secretaria = [], 
    atividade_por_horario = [], 
    tendencia_gastos = [],
    metricas_desempenho = {},
    status_modulos = {},
    top_usuarios = [],
    horario_pico = {}
  } = metrics || {};

  const totalHoje = Object.values(metricas_desempenho.documentos_hoje || {}).reduce((a, b) => a + b, 0);
  const totalSemana = Object.values(metricas_desempenho.documentos_semana || {}).reduce((a, b) => a + b, 0);

  return (
    <Layout>
      <div className="space-y-6" data-testid="analytics-realtime">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Activity className="h-7 w-7 text-green-600" />
              Analytics em Tempo Real
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Monitoramento de uso e desempenho do sistema
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded border-gray-300 text-green-600 focus:ring-green-500"
              />
              <span className="text-gray-600">Auto-atualização (30s)</span>
            </label>
            
            <button
              onClick={fetchMetrics}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              data-testid="refresh-btn"
            >
              <RefreshCw className="h-4 w-4" />
              Atualizar
            </button>
          </div>
        </div>

        {/* Última atualização */}
        {lastUpdate && (
          <div className="text-xs text-gray-500 flex items-center gap-1">
            <Clock className="h-3 w-3" />
            Última atualização: {lastUpdate.toLocaleTimeString('pt-BR')}
          </div>
        )}

        {/* Cards de Resumo */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-5 text-white shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm">Usuários Ativos</p>
                <p className="text-3xl font-bold mt-1">{metricas_desempenho.usuarios_ativos || 0}</p>
                <p className="text-blue-200 text-xs mt-1">de {metricas_desempenho.usuarios_totais || 0} total</p>
              </div>
              <Users className="h-12 w-12 text-blue-200" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-5 text-white shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-100 text-sm">Documentos Hoje</p>
                <p className="text-3xl font-bold mt-1">{totalHoje}</p>
                <p className="text-green-200 text-xs mt-1 flex items-center gap-1">
                  <ArrowUpRight className="h-3 w-3" />
                  {totalSemana} esta semana
                </p>
              </div>
              <FileText className="h-12 w-12 text-green-200" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-5 text-white shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100 text-sm">Horário de Pico</p>
                <p className="text-3xl font-bold mt-1">{horario_pico.hora || '09:00'}</p>
                <p className="text-purple-200 text-xs mt-1">{horario_pico.atividade || 0} atividades</p>
              </div>
              <Clock className="h-12 w-12 text-purple-200" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl p-5 text-white shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-orange-100 text-sm">Módulos Online</p>
                <p className="text-3xl font-bold mt-1">{Object.keys(status_modulos).length}</p>
                <p className="text-orange-200 text-xs mt-1 flex items-center gap-1">
                  <CheckCircle className="h-3 w-3" />
                  Todos operacionais
                </p>
              </div>
              <Server className="h-12 w-12 text-orange-200" />
            </div>
          </div>
        </div>

        {/* Gráficos */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Atividade por Horário */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Zap className="h-5 w-5 text-yellow-500" />
              Atividade por Horário (últimos 7 dias)
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={atividade_por_horario}>
                  <defs>
                    <linearGradient id="colorAtividade" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.1}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="hora" tick={{ fontSize: 10 }} interval={2} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip 
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}
                    formatter={(value) => [`${value} atividades`, 'Total']}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="atividade" 
                    stroke="#3B82F6" 
                    fillOpacity={1} 
                    fill="url(#colorAtividade)" 
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Tendência de Gastos */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-500" />
              Tendência de Gastos (últimos 6 meses)
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={tendencia_gastos}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="mes" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => formatCurrencyShort(v)} />
                  <Tooltip 
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}
                    formatter={(value) => [formatCurrency(value), 'Valor']}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="valor" 
                    stroke="#2E7D32" 
                    strokeWidth={3}
                    dot={{ fill: '#2E7D32', strokeWidth: 2 }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Uso por Secretaria e Top Usuários */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Uso por Secretaria */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Building2 className="h-5 w-5 text-blue-500" />
              Uso por Secretaria
            </h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={uso_por_secretaria.slice(0, 8)} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                  <XAxis type="number" tick={{ fontSize: 10 }} tickFormatter={(v) => formatCurrencyShort(v)} />
                  <YAxis 
                    type="category" 
                    dataKey="secretaria" 
                    tick={{ fontSize: 9 }} 
                    width={100}
                    tickFormatter={(v) => v.length > 15 ? v.substring(0, 15) + '...' : v}
                  />
                  <Tooltip 
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}
                    formatter={(value) => [formatCurrency(value), 'Valor Total']}
                  />
                  <Bar dataKey="valor_total" radius={[0, 4, 4, 0]}>
                    {uso_por_secretaria.slice(0, 8).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Top Usuários */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Users className="h-5 w-5 text-purple-500" />
              Top 10 Usuários Ativos
            </h3>
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {top_usuarios.map((user, index) => (
                <div 
                  key={user.user_id} 
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm ${
                      index === 0 ? 'bg-yellow-500' : 
                      index === 1 ? 'bg-gray-400' : 
                      index === 2 ? 'bg-orange-600' : 'bg-gray-300'
                    }`}>
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium text-gray-800">{user.name}</p>
                      <p className="text-xs text-gray-500">{user.email}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-blue-600">{user.documentos}</p>
                    <p className="text-xs text-gray-500">documentos</p>
                  </div>
                </div>
              ))}
              {top_usuarios.length === 0 && (
                <p className="text-gray-500 text-center py-4">Nenhum usuário encontrado</p>
              )}
            </div>
          </div>
        </div>

        {/* Status dos Módulos */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Server className="h-5 w-5 text-gray-500" />
            Status dos Módulos
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {Object.entries(status_modulos).map(([modulo, dados]) => (
              <div 
                key={modulo}
                className="border rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-sm text-gray-700">{modulo}</span>
                  <span className={`w-2 h-2 rounded-full ${
                    dados.status === 'online' ? 'bg-green-500 animate-pulse' : 'bg-red-500'
                  }`}></span>
                </div>
                <div className="space-y-1">
                  <p className="text-2xl font-bold text-gray-800">{dados.total}</p>
                  <p className="text-xs text-gray-500">
                    {dados.itens ? `${dados.itens} itens` : 
                     dados.documentos ? `${dados.documentos} docs` : 
                     'registros'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Documentos Criados */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Calendar className="h-5 w-5 text-indigo-500" />
            Documentos Criados
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-3xl font-bold text-blue-600">
                {metricas_desempenho.documentos_hoje?.pacs || 0}
              </p>
              <p className="text-sm text-gray-600">PACs Hoje</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-3xl font-bold text-green-600">
                {metricas_desempenho.documentos_hoje?.processos || 0}
              </p>
              <p className="text-sm text-gray-600">Processos Hoje</p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <p className="text-3xl font-bold text-purple-600">
                {metricas_desempenho.documentos_hoje?.pac_items || 0}
              </p>
              <p className="text-sm text-gray-600">Itens PAC Hoje</p>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <p className="text-3xl font-bold text-orange-600">
                {metricas_desempenho.documentos_hoje?.mrosc || 0}
              </p>
              <p className="text-sm text-gray-600">MROSC Hoje</p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default AnalyticsRealtime;
