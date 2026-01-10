import React, { useState, useEffect } from 'react';
import { 
  BarChart3, PieChart, TrendingUp, AlertTriangle, Bell, 
  DollarSign, FileText, Users, Building2, Clock, CheckCircle,
  XCircle, AlertCircle, ChevronRight, RefreshCw
} from 'lucide-react';
import Layout from '../components/Layout';
import api from '../utils/api';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart as RePieChart, Pie, Cell, Legend, LineChart, Line
} from 'recharts';

const COLORS = ['#1F4E78', '#2E7D32', '#F57C00', '#7B1FA2', '#C62828', '#00838F', '#5D4037', '#455A64', '#AD1457'];
const PRIORIDADE_COLORS = { CRITICA: '#DC2626', ALTA: '#F59E0B', MEDIA: '#3B82F6', BAIXA: '#6B7280' };

const DashboardAnalitico = () => {
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState(null);
  const [alertas, setAlertas] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('visao-geral');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [analyticsRes, alertasRes] = await Promise.all([
        api.get('/analytics/dashboard'),
        api.get('/alertas/')
      ]);
      setAnalytics(analyticsRes.data);
      setAlertas(alertasRes.data);
    } catch (error) {
      toast.error('Erro ao carregar dados do dashboard');
    } finally {
      setLoading(false);
    }
  };

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

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
              <BarChart3 className="text-blue-600" />
              Dashboard Analítico
            </h1>
            <p className="text-muted-foreground">Visão consolidada de todos os módulos</p>
          </div>
          <button
            onClick={fetchData}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <RefreshCw size={16} /> Atualizar
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-border">
          <div className="flex gap-1">
            {[
              { id: 'visao-geral', label: 'Visão Geral', icon: PieChart },
              { id: 'orcamento', label: 'Orçamento', icon: DollarSign },
              { id: 'alertas', label: `Alertas (${alertas?.total || 0})`, icon: Bell }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 font-medium text-sm flex items-center gap-2 transition-colors border-b-2 ${
                  activeTab === tab.id
                    ? 'text-blue-600 border-blue-600'
                    : 'text-muted-foreground border-transparent hover:text-foreground'
                }`}
              >
                <tab.icon size={16} /> {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab: Visão Geral */}
        {activeTab === 'visao-geral' && (
          <div className="space-y-6">
            {/* KPIs */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gradient-to-br from-blue-500 to-blue-700 text-white rounded-xl p-4">
                <div className="flex items-center gap-2 text-blue-100 text-sm">
                  <DollarSign size={16} /> Total Planejado
                </div>
                <div className="text-2xl font-bold mt-1">
                  {formatCurrencyShort(analytics?.resumo?.total_geral)}
                </div>
                <div className="text-xs text-blue-200 mt-1">PACs + Obras</div>
              </div>
              
              <div className="bg-gradient-to-br from-green-500 to-green-700 text-white rounded-xl p-4">
                <div className="flex items-center gap-2 text-green-100 text-sm">
                  <FileText size={16} /> Processos
                </div>
                <div className="text-2xl font-bold mt-1">
                  {analytics?.contadores?.processos || 0}
                </div>
                <div className="text-xs text-green-200 mt-1">Total cadastrados</div>
              </div>
              
              <div className="bg-gradient-to-br from-purple-500 to-purple-700 text-white rounded-xl p-4">
                <div className="flex items-center gap-2 text-purple-100 text-sm">
                  <Building2 size={16} /> Projetos MROSC
                </div>
                <div className="text-2xl font-bold mt-1">
                  {analytics?.contadores?.projetos_mrosc || 0}
                </div>
                <div className="text-xs text-purple-200 mt-1">
                  {formatCurrencyShort(analytics?.resumo?.total_mrosc)}
                </div>
              </div>
              
              <div className="bg-gradient-to-br from-amber-500 to-amber-700 text-white rounded-xl p-4">
                <div className="flex items-center gap-2 text-amber-100 text-sm">
                  <AlertTriangle size={16} /> Alertas
                </div>
                <div className="text-2xl font-bold mt-1">
                  {alertas?.criticos || 0} <span className="text-lg font-normal">críticos</span>
                </div>
                <div className="text-xs text-amber-200 mt-1">{alertas?.total || 0} total</div>
              </div>
            </div>

            {/* Gráficos */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Distribuição por Secretaria */}
              <div className="bg-card border border-border rounded-xl p-4">
                <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                  <PieChart size={18} className="text-blue-600" />
                  Distribuição por Secretaria
                </h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <RePieChart>
                      <Pie
                        data={analytics?.distribuicao_secretarias || []}
                        dataKey="valor"
                        nameKey="secretaria"
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        label={({ secretaria, percent }) => `${secretaria} (${(percent * 100).toFixed(0)}%)`}
                        labelLine={false}
                      >
                        {(analytics?.distribuicao_secretarias || []).map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => formatCurrency(value)} />
                    </RePieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Processos por Status */}
              <div className="bg-card border border-border rounded-xl p-4">
                <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                  <BarChart3 size={18} className="text-green-600" />
                  Processos por Status
                </h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={analytics?.processos_por_status || []} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis dataKey="status" type="category" width={120} tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Bar dataKey="quantidade" fill="#2E7D32" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Contadores Detalhados */}
            <div className="bg-card border border-border rounded-xl p-4">
              <h3 className="font-semibold text-foreground mb-4">Resumo de Itens Cadastrados</h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {[
                  { label: 'PACs Individuais', value: analytics?.contadores?.pacs, sub: `${analytics?.contadores?.itens_pac} itens` },
                  { label: 'PACs Gerais', value: analytics?.contadores?.pacs_geral, sub: `${analytics?.contadores?.itens_pac_geral} itens` },
                  { label: 'PACs Obras', value: analytics?.contadores?.pacs_obras, sub: `${analytics?.contadores?.itens_pac_obras} itens` },
                  { label: 'Funcionários MROSC', value: analytics?.contadores?.funcionarios_mrosc, sub: 'cadastrados' },
                  { label: 'Documentos MROSC', value: analytics?.contadores?.documentos_mrosc, sub: 'anexados' }
                ].map((item, idx) => (
                  <div key={idx} className="text-center p-3 bg-muted/30 rounded-lg">
                    <div className="text-2xl font-bold text-foreground">{item.value || 0}</div>
                    <div className="text-sm text-muted-foreground">{item.label}</div>
                    <div className="text-xs text-muted-foreground">{item.sub}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Tab: Orçamento */}
        {activeTab === 'orcamento' && (
          <div className="space-y-6">
            {/* Totais por Módulo */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-card border border-border rounded-xl p-4">
                <div className="text-sm text-muted-foreground">PAC Individual</div>
                <div className="text-2xl font-bold text-blue-600">{formatCurrency(analytics?.resumo?.total_pac_individual)}</div>
              </div>
              <div className="bg-card border border-border rounded-xl p-4">
                <div className="text-sm text-muted-foreground">PAC Geral (Consolidado)</div>
                <div className="text-2xl font-bold text-green-600">{formatCurrency(analytics?.resumo?.total_pac_geral)}</div>
              </div>
              <div className="bg-card border border-border rounded-xl p-4">
                <div className="text-sm text-muted-foreground">PAC Obras e Serviços</div>
                <div className="text-2xl font-bold text-amber-600">{formatCurrency(analytics?.resumo?.total_pac_obras)}</div>
              </div>
            </div>

            {/* Execução MROSC */}
            <div className="bg-card border border-border rounded-xl p-4">
              <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                <TrendingUp size={18} className="text-purple-600" />
                Execução Orçamentária - MROSC
              </h3>
              {analytics?.execucao_mrosc?.length > 0 ? (
                <div className="space-y-4">
                  {analytics.execucao_mrosc.map((proj, idx) => (
                    <div key={idx} className="border border-border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <div className="font-medium text-foreground">{proj.nome}</div>
                          <div className="text-sm text-muted-foreground">
                            {proj.documentos} documentos anexados
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold text-purple-600">{proj.percentual}%</div>
                          <div className="text-xs text-muted-foreground">executado</div>
                        </div>
                      </div>
                      <div className="w-full bg-muted rounded-full h-3 mb-2">
                        <div
                          className={`h-3 rounded-full transition-all ${
                            proj.percentual > 100 ? 'bg-red-500' : 
                            proj.percentual > 80 ? 'bg-amber-500' : 'bg-purple-600'
                          }`}
                          style={{ width: `${Math.min(proj.percentual, 100)}%` }}
                        />
                      </div>
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>RH: {formatCurrency(proj.rh)} | Despesas: {formatCurrency(proj.despesas)}</span>
                        <span>Saldo: <span className={proj.saldo < 0 ? 'text-red-600' : 'text-green-600'}>{formatCurrency(proj.saldo)}</span></span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground text-center py-8">Nenhum projeto MROSC cadastrado</p>
              )}
            </div>

            {/* Top Itens */}
            <div className="bg-card border border-border rounded-xl p-4">
              <h3 className="font-semibold text-foreground mb-4">Top 5 Itens por Valor (PAC Geral)</h3>
              <div className="space-y-2">
                {(analytics?.top_itens || []).map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                    <div className="flex items-center gap-3">
                      <span className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">
                        {idx + 1}
                      </span>
                      <div>
                        <div className="font-medium text-sm">{item.descricao}</div>
                        <div className="text-xs text-muted-foreground">CATMAT: {item.catmat}</div>
                      </div>
                    </div>
                    <div className="font-bold text-green-600">{formatCurrency(item.valor)}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Tab: Alertas */}
        {activeTab === 'alertas' && (
          <div className="space-y-6">
            {/* Resumo de Alertas */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Críticos', value: alertas?.criticos, color: 'bg-red-500', icon: XCircle },
                { label: 'Altos', value: alertas?.altos, color: 'bg-amber-500', icon: AlertTriangle },
                { label: 'Médios', value: alertas?.medios, color: 'bg-blue-500', icon: AlertCircle },
                { label: 'Baixos', value: alertas?.baixos, color: 'bg-gray-500', icon: Clock }
              ].map((item, idx) => (
                <div key={idx} className="bg-card border border-border rounded-xl p-4 flex items-center gap-3">
                  <div className={`${item.color} text-white p-2 rounded-lg`}>
                    <item.icon size={20} />
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-foreground">{item.value || 0}</div>
                    <div className="text-sm text-muted-foreground">{item.label}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Lista de Alertas */}
            <div className="bg-card border border-border rounded-xl overflow-hidden">
              <div className="px-4 py-3 bg-muted border-b border-border">
                <h3 className="font-semibold text-foreground flex items-center gap-2">
                  <Bell size={18} /> Todos os Alertas
                </h3>
              </div>
              
              {alertas?.alertas?.length > 0 ? (
                <div className="divide-y divide-border">
                  {alertas.alertas.map((alerta, idx) => (
                    <div
                      key={idx}
                      className="p-4 hover:bg-muted/50 transition-colors cursor-pointer flex items-start gap-3"
                      onClick={() => {
                        if (alerta.modulo === 'MROSC' && alerta.referencia_id) {
                          navigate(`/prestacao-contas/${alerta.referencia_id}`);
                        } else if (alerta.modulo === 'PROCESSO' && alerta.referencia_id) {
                          navigate('/processos');
                        }
                      }}
                    >
                      <div
                        className="w-3 h-3 rounded-full mt-1.5 flex-shrink-0"
                        style={{ backgroundColor: PRIORIDADE_COLORS[alerta.prioridade] }}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-foreground">{alerta.titulo}</span>
                          <span className={`text-xs px-2 py-0.5 rounded ${
                            alerta.modulo === 'MROSC' ? 'bg-purple-100 text-purple-700' :
                            alerta.modulo === 'PROCESSO' ? 'bg-green-100 text-green-700' :
                            'bg-gray-100 text-gray-700'
                          }`}>
                            {alerta.modulo}
                          </span>
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">{alerta.mensagem}</p>
                        {alerta.dias_restantes !== undefined && (
                          <p className="text-xs mt-1">
                            {alerta.dias_restantes < 0 
                              ? <span className="text-red-600 font-medium">Vencido há {Math.abs(alerta.dias_restantes)} dias</span>
                              : <span className="text-amber-600">Vence em {alerta.dias_restantes} dias</span>
                            }
                          </p>
                        )}
                      </div>
                      <ChevronRight size={16} className="text-muted-foreground flex-shrink-0" />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-8 text-center">
                  <CheckCircle size={40} className="mx-auto text-green-500 mb-2" />
                  <p className="text-muted-foreground">Nenhum alerta no momento</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default DashboardAnalitico;
