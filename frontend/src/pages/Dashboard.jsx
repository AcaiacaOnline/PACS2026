import React, { useState, useEffect } from 'react';
import { Calculator, TrendingUp, FileText, BarChart3, PieChart } from 'lucide-react';
import Layout from '../components/Layout';
import api from '../utils/api';
import { toast } from 'sonner';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend
} from 'recharts';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await api.get('/pacs-geral/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
      toast.error('Erro ao carregar estatísticas');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value || 0);
  };

  const formatCurrencyShort = (value) => {
    if (value >= 1000000) {
      return `R$ ${(value / 1000000).toFixed(1)}M`;
    }
    if (value >= 1000) {
      return `R$ ${(value / 1000).toFixed(1)}K`;
    }
    return formatCurrency(value);
  };

  // Cores para o gráfico
  const COLORS = [
    '#1F4E78', '#2E7D32', '#F57C00', '#7B1FA2', 
    '#C62828', '#00838F', '#5D4037', '#455A64',
    '#AD1457', '#1565C0'
  ];

  // Preparar dados para o gráfico
  const prepareChartData = () => {
    if (!stats?.stats_by_subitem) return [];
    
    return stats.stats_by_subitem.map((item, index) => ({
      name: item.codigo 
        ? `${item.codigo} - ${item.subitem?.substring(0, 30)}${item.subitem?.length > 30 ? '...' : ''}`
        : item.subitem?.substring(0, 40) || 'Não Classificado',
      valor: item.valor_total,
      codigo: item.codigo,
      subitem: item.subitem,
      quantidade: item.quantidade_items,
      fill: COLORS[index % COLORS.length]
    }));
  };

  // Tooltip personalizado
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-card border border-border shadow-lg rounded-lg p-3">
          <p className="font-semibold text-foreground text-sm">{data.subitem || 'Não Classificado'}</p>
          {data.codigo && (
            <p className="text-xs text-muted-foreground">Código: {data.codigo}</p>
          )}
          <p className="text-primary font-bold mt-1">{formatCurrency(data.valor)}</p>
          <p className="text-xs text-muted-foreground">{data.quantidade} {data.quantidade === 1 ? 'item' : 'itens'}</p>
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

  const chartData = prepareChartData();

  return (
    <Layout>
      <div className="space-y-6 fade-in" data-testid="dashboard">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-heading font-bold text-foreground">Dashboard PAC Acaiaca 2026</h2>
            <p className="text-muted-foreground mt-1">Valores totais por Classificação Orçamentária</p>
          </div>
        </div>

        {/* Resumo Geral - Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gradient-to-br from-primary to-primary/80 p-6 rounded-lg shadow-lg text-primary-foreground">
            <div className="flex items-center justify-between mb-2">
              <div className="bg-white/20 p-2 rounded">
                <Calculator className="w-6 h-6" />
              </div>
              <TrendingUp className="w-5 h-5" />
            </div>
            <div className="text-sm opacity-90 mb-1">Total Geral de PACs Gerais</div>
            <div className="text-3xl font-heading font-bold">
              {formatCurrency(stats?.total_geral)}
            </div>
          </div>

          <div className="bg-gradient-to-br from-secondary to-secondary/80 p-6 rounded-lg shadow-lg text-secondary-foreground">
            <div className="flex items-center justify-between mb-2">
              <div className="bg-white/20 p-2 rounded">
                <FileText className="w-6 h-6" />
              </div>
            </div>
            <div className="text-sm opacity-90 mb-1">Total de Itens</div>
            <div className="text-3xl font-heading font-bold">
              {stats?.total_items || 0}
            </div>
            <div className="text-xs opacity-75 mt-1">
              Cadastrados no sistema
            </div>
          </div>

          <div className="bg-gradient-to-br from-accent to-accent/80 p-6 rounded-lg shadow-lg text-accent-foreground">
            <div className="flex items-center justify-between mb-2">
              <div className="bg-white/20 p-2 rounded">
                <PieChart className="w-6 h-6" />
              </div>
            </div>
            <div className="text-sm opacity-90 mb-1">Classificações Distintas</div>
            <div className="text-3xl font-heading font-bold">
              {stats?.stats_by_subitem?.length || 0}
            </div>
            <div className="text-xs opacity-75 mt-1">
              Categorias orçamentárias
            </div>
          </div>
        </div>

        {/* Gráfico de Barras */}
        {chartData.length > 0 && (
          <div className="bg-card border border-border rounded-xl shadow-lg overflow-hidden">
            <div className="bg-gradient-to-r from-primary/10 to-secondary/10 px-6 py-4 border-b border-border">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-primary" />
                <h3 className="text-xl font-heading font-bold text-foreground">
                  Gráfico de Valores por Classificação
                </h3>
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                Distribuição visual dos valores por Subitem da Classificação Orçamentária
              </p>
            </div>

            <div className="p-6">
              <div className="h-[400px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={chartData}
                    layout="vertical"
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                    <XAxis 
                      type="number" 
                      tickFormatter={formatCurrencyShort}
                      tick={{ fontSize: 12 }}
                    />
                    <YAxis 
                      type="category" 
                      dataKey="name" 
                      width={250}
                      tick={{ fontSize: 11 }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    <Bar 
                      dataKey="valor" 
                      name="Valor Total (R$)" 
                      radius={[0, 4, 4, 0]}
                    >
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {/* Tabela Detalhada */}
        <div className="bg-card border border-border rounded-xl shadow-lg overflow-hidden">
          <div className="bg-gradient-to-r from-primary/10 to-secondary/10 px-6 py-4 border-b border-border">
            <h3 className="text-xl font-heading font-bold text-foreground">
              Tabela Detalhada por Classificação Orçamentária
            </h3>
            <p className="text-sm text-muted-foreground mt-1">
              Lei Federal nº 14.133/2021 - Agrupado por Subitem
            </p>
          </div>

          <div className="p-6">
            {stats?.stats_by_subitem && stats.stats_by_subitem.length > 0 ? (
              <div className="space-y-3">
                {stats.stats_by_subitem.map((item, index) => {
                  const percentage = stats.total_geral > 0 
                    ? (item.valor_total / stats.total_geral) * 100 
                    : 0;
                  return (
                    <div
                      key={index}
                      className="bg-muted/30 rounded-lg p-4 hover:bg-muted/50 transition-colors border border-border"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            {item.codigo && (
                              <span 
                                className="text-white text-xs font-bold px-2 py-1 rounded"
                                style={{ backgroundColor: COLORS[index % COLORS.length] }}
                              >
                                {item.codigo}
                              </span>
                            )}
                            <span className="font-semibold text-foreground">
                              {item.subitem || 'Não Classificado'}
                            </span>
                          </div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {item.quantidade_items} {item.quantidade_items === 1 ? 'item' : 'itens'}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-xl font-bold text-foreground">
                            {formatCurrency(item.valor_total)}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {percentage.toFixed(1)}% do total
                          </div>
                        </div>
                      </div>
                      
                      {/* Barra de Progresso */}
                      <div className="w-full bg-border rounded-full h-2 mt-2">
                        <div
                          className="h-2 rounded-full transition-all duration-500"
                          style={{ 
                            width: `${percentage}%`,
                            backgroundColor: COLORS[index % COLORS.length]
                          }}
                        ></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-12">
                <BarChart3 className="w-16 h-16 text-muted-foreground mx-auto mb-4 opacity-50" />
                <p className="text-muted-foreground">
                  Nenhum item com classificação orçamentária encontrado.
                </p>
                <p className="text-sm text-muted-foreground mt-2">
                  Adicione itens aos PACs Gerais para ver as estatísticas aqui.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Info Card */}
        <div className="bg-accent/5 border border-accent/20 rounded-lg p-6">
          <h3 className="text-lg font-heading font-semibold text-foreground mb-2">
            Sobre o Sistema PAC Acaiaca 2026
          </h3>
          <p className="text-muted-foreground mb-4">
            Sistema de Planejamento Anual de Contratações desenvolvido para auxiliar as secretarias
            municipais de Acaiaca-MG no planejamento e gestão de compras públicas, em conformidade
            com a Lei Federal nº 14.133/2021.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <div className="font-semibold text-foreground mb-1">Funcionalidades</div>
              <ul className="text-muted-foreground space-y-1">
                <li>• Gestão de PACs e PACs Gerais</li>
                <li>• Classificação Orçamentária</li>
                <li>• Dashboard analítico</li>
              </ul>
            </div>
            <div>
              <div className="font-semibold text-foreground mb-1">Exportação</div>
              <ul className="text-muted-foreground space-y-1">
                <li>• Relatórios em PDF com logotipo</li>
                <li>• Planilhas Excel (XLSX)</li>
                <li>• Layout institucional</li>
              </ul>
            </div>
            <div>
              <div className="font-semibold text-foreground mb-1">Segurança</div>
              <ul className="text-muted-foreground space-y-1">
                <li>• Autenticação JWT</li>
                <li>• Login com Google</li>
                <li>• Controle de permissões</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard;
