import React, { useState, useEffect } from 'react';
import { Calculator, TrendingUp, Package, Wrench, Building } from 'lucide-react';
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
            <h2 className="text-3xl font-heading font-bold text-foreground">Visão Geral</h2>
            <p className="text-muted-foreground mt-1">Todos os PACs cadastrados</p>
          </div>
          <div className="text-right">
            <div className="text-sm text-muted-foreground">Total de PACs</div>
            <div className="text-2xl font-heading font-bold text-accent" data-testid="total-pacs">
              {stats?.totalPacs || 0}
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div
            className="bg-card p-6 rounded-lg border border-border shadow-sm hover:shadow-md transition-all"
            data-testid="total-geral-card"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="bg-primary/10 p-2 rounded">
                <Calculator className="w-6 h-6 text-primary" />
              </div>
              <TrendingUp className="w-4 h-4 text-muted-foreground" />
            </div>
            <div className="text-sm text-muted-foreground mb-1">Total Geral Previsto</div>
            <div className="text-2xl font-heading font-bold text-foreground">
              {formatCurrency(stats?.totalGeral)}
            </div>
          </div>

          <div
            className="bg-card p-6 rounded-lg border border-border shadow-sm hover:shadow-md transition-all"
            data-testid="consumo-card"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="bg-secondary/10 p-2 rounded">
                <Package className="w-6 h-6 text-secondary" />
              </div>
            </div>
            <div className="text-sm text-muted-foreground mb-1">Material de Consumo</div>
            <div className="text-xl font-heading font-bold text-foreground">
              {formatCurrency(stats?.consumo?.valor)}
            </div>
            <div className="text-xs text-secondary font-mono mt-1">
              {stats?.consumo?.qtd || 0} itens
            </div>
          </div>

          <div
            className="bg-card p-6 rounded-lg border border-border shadow-sm hover:shadow-md transition-all"
            data-testid="servicos-card"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="bg-accent/10 p-2 rounded">
                <Wrench className="w-6 h-6 text-accent" />
              </div>
            </div>
            <div className="text-sm text-muted-foreground mb-1">Serviços</div>
            <div className="text-xl font-heading font-bold text-foreground">
              {formatCurrency(stats?.servicos?.valor)}
            </div>
            <div className="text-xs text-accent font-mono mt-1">
              {stats?.servicos?.qtd || 0} itens
            </div>
          </div>

          <div
            className="bg-card p-6 rounded-lg border border-border shadow-sm hover:shadow-md transition-all"
            data-testid="permanente-obras-card"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="bg-amber-500/10 p-2 rounded">
                <Building className="w-6 h-6 text-amber-600" />
              </div>
            </div>
            <div className="text-sm text-muted-foreground mb-1">Permanente / Obras</div>
            <div className="text-xl font-heading font-bold text-foreground">
              {formatCurrency((stats?.permanente?.valor || 0) + (stats?.obras?.valor || 0))}
            </div>
            <div className="text-xs text-amber-600 font-mono mt-1">
              {(stats?.permanente?.qtd || 0) + (stats?.obras?.qtd || 0)} itens
            </div>
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
                <li>• Gestão de múltiplos PACs</li>
                <li>• Cadastro detalhado de itens</li>
                <li>• Dashboard analítico</li>
              </ul>
            </div>
            <div>
              <div className="font-semibold text-foreground mb-1">Exportação</div>
              <ul className="text-muted-foreground space-y-1">
                <li>• Relatórios em PDF</li>
                <li>• Planilhas Excel (XLSX)</li>
                <li>• Importação em lote</li>
              </ul>
            </div>
            <div>
              <div className="font-semibold text-foreground mb-1">Segurança</div>
              <ul className="text-muted-foreground space-y-1">
                <li>• Autenticação segura</li>
                <li>• Login com Google</li>
                <li>• Dados protegidos</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard;
