import React, { useState, useEffect } from 'react';
import { Calculator, TrendingUp, FileText, BarChart3 } from 'lucide-react';
import Layout from '../components/Layout';
import api from '../utils/api';
import { toast } from 'sonner';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await api.get('/dashboard/stats');
      setStats(response.data);
    } catch (error) {
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
      <div className="space-y-6 fade-in" data-testid="dashboard">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-heading font-bold text-foreground">Dashboard PAC Geral 2.0</h2>
            <p className="text-muted-foreground mt-1">Valores totais por Classificação Orçamentária</p>
          </div>
        </div>

        {/* Resumo Geral */}
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
            <div className="text-sm opacity-90 mb-1">Total de Items</div>
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
                <BarChart3 className="w-6 h-6" />
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

        {/* Valores por Subitem de Classificação */}
        <div className="bg-card border border-border rounded-xl shadow-lg overflow-hidden">
          <div className="bg-gradient-to-r from-primary/10 to-secondary/10 px-6 py-4 border-b border-border">
            <h3 className="text-xl font-heading font-bold text-foreground">
              Valores por Classificação Orçamentária
            </h3>
            <p className="text-sm text-muted-foreground mt-1">
              Lei Federal nº 14.133/2021 - Agrupado por Subitem
            </p>
          </div>

          <div className="p-6">
            {stats?.stats_by_subitem && stats.stats_by_subitem.length > 0 ? (
              <div className="space-y-3">
                {stats.stats_by_subitem.map((item, index) => {
                  const percentage = (item.valor_total / stats.total_geral) * 100;
                  return (
                    <div
                      key={index}
                      className="bg-muted/30 rounded-lg p-4 hover:bg-muted/50 transition-colors border border-border"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            {item.codigo && (
                              <span className="bg-primary text-primary-foreground text-xs font-bold px-2 py-1 rounded">
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
                          className="bg-primary h-2 rounded-full transition-all duration-500"
                          style={{ width: `${percentage}%` }}
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
                  Adicione items aos PACs Gerais para ver as estatísticas aqui.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Info Card */}
        <div className="bg-accent/5 border border-accent/20 rounded-lg p-6">
          <h3 className="text-lg font-heading font-semibold text-foreground mb-2">
            Sobre o Sistema PAC 2.0 - Acaiaca
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
