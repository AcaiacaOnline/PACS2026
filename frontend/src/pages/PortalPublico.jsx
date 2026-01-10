import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Building2, FileText, ClipboardList, BarChart3, Download, Printer,
  Search, Shield, Eye, Lock, FileSpreadsheet, Newspaper, ChevronLeft, ChevronRight,
  Hammer, DollarSign, FileSignature
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import axios from 'axios';
import { toast } from 'sonner';

const COLORS = ['#1F4E78', '#2E7D32', '#F57C00', '#7B1FA2', '#C62828', '#00838F'];

// API pública (sem autenticação)
const publicApi = axios.create({
  baseURL: process.env.REACT_APP_BACKEND_URL || '',
});

const PortalPublico = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [pacs, setPacs] = useState([]);
  const [pacsGeral, setPacsGeral] = useState([]);
  const [pacsGeralObras, setPacsGeralObras] = useState([]);
  const [processos, setProcessos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedItem, setSelectedItem] = useState(null);
  const [itemDetails, setItemDetails] = useState([]);
  const [exporting, setExporting] = useState(false);
  
  // Paginação para Processos
  const [processosPage, setProcessosPage] = useState(1);
  const [processosPageSize, setProcessosPageSize] = useState(20);

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'dashboard') {
        const response = await publicApi.get('/api/public/dashboard/stats');
        setStats(response.data.data);
      } else if (activeTab === 'pacs') {
        const response = await publicApi.get('/api/public/pacs');
        setPacs(response.data.data);
      } else if (activeTab === 'pacs-geral') {
        const response = await publicApi.get('/api/public/pacs-geral');
        setPacsGeral(response.data.data);
      } else if (activeTab === 'pacs-geral-obras') {
        const response = await publicApi.get('/api/public/pacs-geral-obras');
        setPacsGeralObras(response.data.data);
      } else if (activeTab === 'processos') {
        const response = await publicApi.get('/api/public/processos');
        setProcessos(response.data.data);
      }
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchItemDetails = async (type, id) => {
    try {
      let endpoint = '';
      if (type === 'pac') {
        endpoint = `/api/public/pacs/${id}/items`;
      } else if (type === 'pac-geral') {
        endpoint = `/api/public/pacs-geral/${id}/items`;
      } else if (type === 'pac-geral-obras') {
        endpoint = `/api/public/pacs-geral-obras/${id}/items`;
      }
      const response = await publicApi.get(endpoint);
      setItemDetails(response.data.data);
      setSelectedItem({ type, id });
    } catch (error) {
      console.error('Erro ao carregar itens:', error);
    }
  };

  const handleExportPDF = async (type, id, orientation = 'landscape') => {
    setExporting(true);
    try {
      let endpoint = '';
      let filename = '';
      
      if (type === 'pac') {
        endpoint = `/api/public/pacs/${id}/export/pdf?orientation=${orientation}`;
        filename = `PAC_${id}.pdf`;
      } else if (type === 'pac-geral') {
        endpoint = `/api/public/pacs-geral/${id}/export/pdf?orientation=${orientation}`;
        filename = `PAC_Geral_${id}.pdf`;
      } else if (type === 'pac-geral-obras') {
        endpoint = `/api/public/pacs-geral-obras/${id}/export/pdf?orientation=${orientation}`;
        filename = `PAC_Obras_${id}.pdf`;
      } else if (type === 'processos') {
        endpoint = `/api/public/processos/export/pdf?orientation=${orientation}`;
        filename = `Processos_PAC.pdf`;
      }
      
      const response = await publicApi.get(endpoint, { responseType: 'blob' });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('PDF exportado com sucesso!');
    } catch (error) {
      toast.error('Erro ao exportar PDF');
    } finally {
      setExporting(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value || 0);
  };

  const handlePrint = () => {
    window.print();
  };

  const handleAdminAccess = () => {
    navigate('/login');
  };

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Cards de Resumo */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-600 to-blue-700 p-6 rounded-xl shadow-lg text-white">
          <FileText className="w-8 h-8 opacity-80 mb-2" />
          <div className="text-sm opacity-90">PACs Individuais</div>
          <div className="text-3xl font-bold">{stats?.resumo?.total_pacs_individuais || 0}</div>
          <div className="text-sm mt-1 opacity-75">
            {formatCurrency(stats?.resumo?.valor_total_pac)}
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-600 to-green-700 p-6 rounded-xl shadow-lg text-white">
          <Building2 className="w-8 h-8 opacity-80 mb-2" />
          <div className="text-sm opacity-90">PACs Gerais</div>
          <div className="text-3xl font-bold">{stats?.resumo?.total_pacs_gerais || 0}</div>
          <div className="text-sm mt-1 opacity-75">
            {formatCurrency(stats?.resumo?.valor_total_pac_geral)}
          </div>
        </div>

        <div className="bg-gradient-to-br from-amber-500 to-amber-600 p-6 rounded-xl shadow-lg text-white">
          <ClipboardList className="w-8 h-8 opacity-80 mb-2" />
          <div className="text-sm opacity-90">Processos</div>
          <div className="text-3xl font-bold">{stats?.resumo?.total_processos || 0}</div>
        </div>

        <div className="bg-gradient-to-br from-purple-600 to-purple-700 p-6 rounded-xl shadow-lg text-white">
          <BarChart3 className="w-8 h-8 opacity-80 mb-2" />
          <div className="text-sm opacity-90">Valor Total</div>
          <div className="text-2xl font-bold">
            {formatCurrency((stats?.resumo?.valor_total_pac || 0) + (stats?.resumo?.valor_total_pac_geral || 0))}
          </div>
        </div>
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white/95 backdrop-blur-sm border border-gray-200 rounded-xl shadow-lg overflow-hidden">
          <div className="bg-gradient-to-r from-blue-50 to-blue-100 px-6 py-4 border-b">
            <h3 className="text-lg font-bold text-gray-800">Processos por Status</h3>
          </div>
          <div className="p-4">
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats?.processos_por_status || []}
                    dataKey="quantidade"
                    nameKey="status"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={({ status, percent }) => `${status} (${(percent * 100).toFixed(0)}%)`}
                  >
                    {stats?.processos_por_status?.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="bg-white/95 backdrop-blur-sm border border-gray-200 rounded-xl shadow-lg overflow-hidden">
          <div className="bg-gradient-to-r from-green-50 to-green-100 px-6 py-4 border-b">
            <h3 className="text-lg font-bold text-gray-800">Classificações Orçamentárias</h3>
            <p className="text-xs text-gray-600 mt-1">Identificação do PAC por Subitem</p>
          </div>
          <div className="p-4">
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats?.classificacoes_principais || []} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" tickFormatter={(v) => formatCurrency(v)} />
                  <YAxis 
                    type="category" 
                    dataKey="subitem" 
                    width={150}
                    tick={{ fontSize: 10 }}
                    tickFormatter={(v) => v?.length > 25 ? v.substring(0, 25) + '...' : v}
                  />
                  <Tooltip formatter={(v) => formatCurrency(v)} />
                  <Bar dataKey="valor_total" name="Valor Total" fill="#1F4E78" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderPacs = () => (
    <div className="space-y-4">
      <div className="flex items-center gap-4 mb-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            placeholder="Buscar por secretaria..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none bg-white/90"
          />
        </div>
      </div>

      <div className="bg-white/95 backdrop-blur-sm border border-gray-200 rounded-xl shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Secretaria</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Secretário(a)</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Ano</th>
              <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">Valor Total</th>
              <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">Ações</th>
            </tr>
          </thead>
          <tbody>
            {pacs
              .filter(p => p.secretaria?.toLowerCase().includes(searchTerm.toLowerCase()))
              .map((pac) => (
              <tr key={pac.pac_id} className="border-t hover:bg-gray-50">
                <td className="px-4 py-3 text-sm">{pac.secretaria}</td>
                <td className="px-4 py-3 text-sm">{pac.secretario}</td>
                <td className="px-4 py-3 text-sm">{pac.ano}</td>
                <td className="px-4 py-3 text-sm text-right font-medium">
                  {formatCurrency(pac.total_value)}
                </td>
                <td className="px-4 py-3 text-center">
                  <div className="flex items-center justify-center gap-2">
                    <button
                      onClick={() => fetchItemDetails('pac', pac.pac_id)}
                      className="text-blue-600 hover:text-blue-800 p-1"
                      title="Ver Itens"
                    >
                      <Eye size={18} />
                    </button>
                    <button
                      onClick={() => handleExportPDF('pac', pac.pac_id)}
                      className="text-red-600 hover:text-red-800 p-1"
                      title="Exportar PDF"
                      disabled={exporting}
                    >
                      <Download size={18} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedItem?.type === 'pac' && itemDetails.length > 0 && (
        <div className="bg-white/95 backdrop-blur-sm border border-gray-200 rounded-xl shadow overflow-hidden mt-4">
          <div className="bg-blue-50 px-4 py-3 border-b flex justify-between items-center">
            <h3 className="font-semibold text-gray-800">Itens do PAC ({itemDetails.length})</h3>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleExportPDF('pac', selectedItem.id, 'landscape')}
                className="flex items-center gap-1 text-sm bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700"
                disabled={exporting}
              >
                <Download size={14} />
                PDF Paisagem
              </button>
              <button
                onClick={() => handleExportPDF('pac', selectedItem.id, 'portrait')}
                className="flex items-center gap-1 text-sm bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700"
                disabled={exporting}
              >
                <Download size={14} />
                PDF Retrato
              </button>
              <button
                onClick={() => { setSelectedItem(null); setItemDetails([]); }}
                className="text-gray-500 hover:text-gray-700 ml-2"
              >
                ✕
              </button>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left font-medium">Código</th>
                  <th className="px-3 py-2 text-left font-medium">Descrição</th>
                  <th className="px-3 py-2 text-center font-medium">Und</th>
                  <th className="px-3 py-2 text-center font-medium">Qtd</th>
                  <th className="px-3 py-2 text-right font-medium">Valor Unit.</th>
                  <th className="px-3 py-2 text-right font-medium">Valor Total</th>
                  <th className="px-3 py-2 text-left font-medium">Classificação</th>
                </tr>
              </thead>
              <tbody>
                {itemDetails.map((item) => (
                  <tr key={item.item_id} className="border-t">
                    <td className="px-3 py-2">{item.catmat}</td>
                    <td className="px-3 py-2">{item.descricao}</td>
                    <td className="px-3 py-2 text-center">{item.unidade}</td>
                    <td className="px-3 py-2 text-center">{item.quantidade}</td>
                    <td className="px-3 py-2 text-right">{formatCurrency(item.valorUnitario)}</td>
                    <td className="px-3 py-2 text-right font-medium">{formatCurrency(item.valorTotal)}</td>
                    <td className="px-3 py-2 text-xs">
                      <span className="font-medium">{item.codigo_classificacao}</span>
                      {item.subitem_classificacao && (
                        <span className="block text-gray-500">{item.subitem_classificacao}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );

  const renderPacsGeral = () => (
    <div className="space-y-4">
      <div className="bg-white/95 backdrop-blur-sm border border-gray-200 rounded-xl shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Secretaria</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Responsável</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Fiscal</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Participantes</th>
              <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">Ações</th>
            </tr>
          </thead>
          <tbody>
            {pacsGeral.map((pac) => (
              <tr key={pac.pac_geral_id} className="border-t hover:bg-gray-50">
                <td className="px-4 py-3 text-sm">{pac.nome_secretaria}</td>
                <td className="px-4 py-3 text-sm">{pac.secretario}</td>
                <td className="px-4 py-3 text-sm">{pac.fiscal_contrato || '-'}</td>
                <td className="px-4 py-3 text-sm max-w-xs truncate">
                  {pac.secretarias_selecionadas?.join(', ')}
                </td>
                <td className="px-4 py-3 text-center">
                  <div className="flex items-center justify-center gap-2">
                    <button
                      onClick={() => fetchItemDetails('pac-geral', pac.pac_geral_id)}
                      className="text-blue-600 hover:text-blue-800 p-1"
                      title="Ver Itens"
                    >
                      <Eye size={18} />
                    </button>
                    <button
                      onClick={() => handleExportPDF('pac-geral', pac.pac_geral_id)}
                      className="text-red-600 hover:text-red-800 p-1"
                      title="Exportar PDF"
                      disabled={exporting}
                    >
                      <Download size={18} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedItem?.type === 'pac-geral' && itemDetails.length > 0 && (
        <div className="bg-white/95 backdrop-blur-sm border border-gray-200 rounded-xl shadow overflow-hidden mt-4">
          <div className="bg-green-50 px-4 py-3 border-b flex justify-between items-center">
            <h3 className="font-semibold text-gray-800">Itens do PAC Geral ({itemDetails.length})</h3>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleExportPDF('pac-geral', selectedItem.id, 'landscape')}
                className="flex items-center gap-1 text-sm bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700"
                disabled={exporting}
              >
                <Download size={14} />
                PDF Paisagem
              </button>
              <button
                onClick={() => handleExportPDF('pac-geral', selectedItem.id, 'portrait')}
                className="flex items-center gap-1 text-sm bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700"
                disabled={exporting}
              >
                <Download size={14} />
                PDF Retrato
              </button>
              <button
                onClick={() => { setSelectedItem(null); setItemDetails([]); }}
                className="text-gray-500 hover:text-gray-700 ml-2"
              >
                ✕
              </button>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left font-medium">Código</th>
                  <th className="px-3 py-2 text-left font-medium">Descrição</th>
                  <th className="px-3 py-2 text-center font-medium">Und</th>
                  <th className="px-3 py-2 text-center font-medium">Qtd Total</th>
                  <th className="px-3 py-2 text-right font-medium">Valor Unit.</th>
                  <th className="px-3 py-2 text-right font-medium">Valor Total</th>
                  <th className="px-3 py-2 text-left font-medium">Classificação (Subitem)</th>
                </tr>
              </thead>
              <tbody>
                {itemDetails.map((item) => (
                  <tr key={item.item_id} className="border-t">
                    <td className="px-3 py-2">{item.catmat}</td>
                    <td className="px-3 py-2">{item.descricao}</td>
                    <td className="px-3 py-2 text-center">{item.unidade}</td>
                    <td className="px-3 py-2 text-center">{item.quantidade_total}</td>
                    <td className="px-3 py-2 text-right">{formatCurrency(item.valorUnitario)}</td>
                    <td className="px-3 py-2 text-right font-medium">{formatCurrency(item.valorTotal)}</td>
                    <td className="px-3 py-2">
                      <div className="bg-blue-50 px-2 py-1 rounded">
                        <span className="font-bold text-blue-800">{item.codigo_classificacao}</span>
                        {item.subitem_classificacao && (
                          <span className="block text-blue-600 font-medium">{item.subitem_classificacao}</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );

  const renderProcessos = () => {
    // Filtrar processos
    const filteredProcessos = processos.filter(p => 
      p.numero_processo?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.objeto?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.secretaria?.toLowerCase().includes(searchTerm.toLowerCase())
    );
    
    // Paginação
    const totalProcessos = filteredProcessos.length;
    const totalPages = Math.ceil(totalProcessos / processosPageSize);
    const startIndex = (processosPage - 1) * processosPageSize;
    const paginatedProcessos = filteredProcessos.slice(startIndex, startIndex + processosPageSize);
    
    return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mb-4">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            placeholder="Buscar por número, objeto ou secretaria..."
            value={searchTerm}
            onChange={(e) => { setSearchTerm(e.target.value); setProcessosPage(1); }}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none bg-white/90"
          />
        </div>
        <div className="flex items-center gap-2">
          <select
            value={processosPageSize}
            onChange={(e) => { setProcessosPageSize(Number(e.target.value)); setProcessosPage(1); }}
            className="border border-gray-300 rounded-lg px-3 py-2 bg-white/90 text-sm"
            data-testid="processos-page-size"
          >
            <option value={20}>20 por página</option>
            <option value={40}>40 por página</option>
            <option value={60}>60 por página</option>
            <option value={80}>80 por página</option>
            <option value={100}>100 por página</option>
          </select>
          <button
            onClick={() => handleExportPDF('processos', null, 'landscape')}
            className="flex items-center gap-2 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
            disabled={exporting}
          >
            <Download size={18} />
            Exportar PDF
          </button>
        </div>
      </div>

      <div className="bg-white/95 backdrop-blur-sm border border-gray-200 rounded-xl shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-3 text-left font-semibold text-gray-700">Processo</th>
                <th className="px-3 py-3 text-left font-semibold text-gray-700">Status</th>
                <th className="px-3 py-3 text-left font-semibold text-gray-700">Modalidade</th>
                <th className="px-3 py-3 text-left font-semibold text-gray-700">Objeto</th>
                <th className="px-3 py-3 text-left font-semibold text-gray-700">Secretaria</th>
                <th className="px-3 py-3 text-left font-semibold text-gray-700">Responsável</th>
              </tr>
            </thead>
            <tbody>
              {paginatedProcessos.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-3 py-8 text-center text-gray-500">
                    Nenhum processo encontrado.
                  </td>
                </tr>
              ) : (
                paginatedProcessos.map((processo) => (
                <tr key={processo.processo_id} className="border-t hover:bg-gray-50">
                  <td className="px-3 py-3 font-medium">{processo.numero_processo}</td>
                  <td className="px-3 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      processo.status === 'Concluído' ? 'bg-green-100 text-green-800' :
                      processo.status === 'Iniciado' ? 'bg-blue-100 text-blue-800' :
                      processo.status === 'Homologado' ? 'bg-purple-100 text-purple-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {processo.status}
                    </span>
                  </td>
                  <td className="px-3 py-3">{processo.modalidade}</td>
                  <td className="px-3 py-3 max-w-xs truncate" title={processo.objeto}>
                    {processo.objeto}
                  </td>
                  <td className="px-3 py-3">{processo.secretaria}</td>
                  <td className="px-3 py-3">{processo.responsavel}</td>
                </tr>
              )))}
            </tbody>
          </table>
        </div>
        
        {/* Paginação */}
        {totalProcessos > 0 && (
          <div className="bg-gray-50 px-4 py-3 border-t border-gray-200 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-sm text-gray-600">
              Exibindo {startIndex + 1} a {Math.min(startIndex + processosPageSize, totalProcessos)} de {totalProcessos} processos
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setProcessosPage(1)}
                disabled={processosPage === 1}
                className="px-3 py-1 rounded border border-gray-300 text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
              >
                Primeira
              </button>
              <button
                onClick={() => setProcessosPage(p => Math.max(1, p - 1))}
                disabled={processosPage === 1}
                className="px-3 py-1 rounded border border-gray-300 text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 flex items-center gap-1"
              >
                <ChevronLeft size={16} /> Anterior
              </button>
              <span className="px-3 py-1 text-sm">
                Página {processosPage} de {totalPages || 1}
              </span>
              <button
                onClick={() => setProcessosPage(p => Math.min(totalPages, p + 1))}
                disabled={processosPage >= totalPages}
                className="px-3 py-1 rounded border border-gray-300 text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 flex items-center gap-1"
              >
                Próxima <ChevronRight size={16} />
              </button>
              <button
                onClick={() => setProcessosPage(totalPages)}
                disabled={processosPage >= totalPages}
                className="px-3 py-1 rounded border border-gray-300 text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
              >
                Última
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
  };

  return (
    <div 
      className="min-h-screen bg-cover bg-center bg-fixed"
      style={{ backgroundImage: 'url(/bg-acaiaca.png)' }}
    >
      <div className="min-h-screen bg-black/30 backdrop-blur-[2px]">
        {/* Header */}
        <header className="bg-[#1F4E78]/95 backdrop-blur-sm text-white shadow-lg print:hidden">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="bg-white p-2 rounded">
                  <Building2 className="text-[#1F4E78] w-8 h-8" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold">Planejamento Acaiaca</h1>
                  <div className="text-sm opacity-90 flex items-center gap-2">
                    <Shield size={14} />
                    Portal da Transparência
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={handlePrint}
                  className="flex items-center gap-2 bg-white/20 hover:bg-white/30 px-4 py-2 rounded-lg transition-colors"
                >
                  <Printer size={18} />
                  <span className="hidden sm:inline">Imprimir</span>
                </button>
                <button
                  onClick={handleAdminAccess}
                  className="flex items-center gap-2 bg-amber-500 hover:bg-amber-600 px-4 py-2 rounded-lg transition-colors font-medium"
                >
                  <Lock size={18} />
                  <span className="hidden sm:inline">Acesso Administrativo</span>
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Navegação */}
        <nav className="bg-white/95 backdrop-blur-sm border-b shadow-sm print:hidden">
          <div className="container mx-auto px-4">
            <div className="flex gap-1 overflow-x-auto">
              {[
                { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
                { id: 'pacs', label: 'PAC Individual', icon: FileText },
                { id: 'pacs-geral', label: 'PAC Geral', icon: Building2 },
                { id: 'processos', label: 'Processos', icon: ClipboardList },
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => { setActiveTab(tab.id); setSearchTerm(''); setSelectedItem(null); setItemDetails([]); }}
                  className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors whitespace-nowrap ${
                    activeTab === tab.id 
                      ? 'border-[#1F4E78] text-[#1F4E78] font-medium' 
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <tab.icon size={18} />
                  {tab.label}
                </button>
              ))}
              {/* Link para DOEM */}
              <button
                onClick={() => navigate('/doem-publico')}
                className="flex items-center gap-2 px-4 py-3 border-b-2 border-transparent text-purple-600 hover:text-purple-800 transition-colors whitespace-nowrap"
              >
                <Newspaper size={18} />
                DOEM
              </button>
            </div>
          </div>
        </nav>

        {/* Conteúdo */}
        <main className="container mx-auto px-4 py-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
            </div>
          ) : (
            <>
              {activeTab === 'dashboard' && renderDashboard()}
              {activeTab === 'pacs' && renderPacs()}
              {activeTab === 'pacs-geral' && renderPacsGeral()}
              {activeTab === 'processos' && renderProcessos()}
            </>
          )}
        </main>

        {/* Footer */}
        <footer className="bg-[#1F4E78]/95 backdrop-blur-sm text-white py-4 mt-8 print:hidden">
          <div className="container mx-auto px-4 text-center text-sm">
            <p className="font-medium">Prefeitura Municipal de Acaiaca - MG</p>
            <p>Planejamento Acaiaca - Lei Federal nº 14.133/2021</p>
            <p className="text-xs mt-2 opacity-75">
              Desenvolvido por Cristiano Abdo de Souza - Assessor de Planejamento, Compras e Logística
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default PortalPublico;
