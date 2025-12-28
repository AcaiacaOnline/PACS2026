import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Save, Plus, Edit, Trash2, FileSpreadsheet, FileText, Upload, Download, X, ArrowLeft } from 'lucide-react';
import Layout from '../components/Layout';
import ClassificacaoSelector from '../components/ClassificacaoSelector';
import api from '../utils/api';
import { toast } from 'sonner';

const PACEditor = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(id);

  const [loading, setLoading] = useState(isEditing);
  const [saving, setSaving] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [pacOwner, setPacOwner] = useState(null);
  const [isReadOnly, setIsReadOnly] = useState(false);
  
  // PAC Header Data
  const [headerData, setHeaderData] = useState({
    secretaria: '',
    secretario: '',
    fiscal: '',
    telefone: '',
    email: '',
    endereco: '',
    ano: '2026'
  });

  // Items
  const [items, setItems] = useState([]);
  
  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [tempItem, setTempItem] = useState({
    tipo: 'Material de Consumo',
    catmat: '',
    descricao: '',
    unidade: 'Unidade',
    quantidade: 0,
    valorUnitario: 0,
    prioridade: 'Alta',
    justificativa: '',
    codigo_classificacao: '',
    subitem_classificacao: ''
  });

  useEffect(() => {
    fetchCurrentUser();
    if (isEditing) {
      fetchPACData();
    }
  }, [id]);

  const fetchCurrentUser = async () => {
    try {
      const response = await api.get('/auth/me');
      setCurrentUser(response.data);
    } catch (error) {
      console.error('Error fetching user:', error);
    }
  };

  const fetchPACData = async () => {
    try {
      const [pacResponse, itemsResponse] = await Promise.all([
        api.get(`/pacs/${id}`),
        api.get(`/pacs/${id}/items`)
      ]);
      setHeaderData(pacResponse.data);
      setItems(itemsResponse.data);
      setPacOwner(pacResponse.data.user_id);
      
      // Verificar se é read-only
      const userResponse = await api.get('/auth/me');
      const user = userResponse.data;
      const isOwner = pacResponse.data.user_id === user.user_id;
      setIsReadOnly(!user.is_admin && !isOwner);
    } catch (error) {
      toast.error('Erro ao carregar dados do PAC');
      navigate('/pacs');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveHeader = async () => {
    if (!headerData.secretaria) {
      toast.error('Informe o nome da Secretaria');
      return;
    }

    setSaving(true);
    try {
      if (isEditing) {
        await api.put(`/pacs/${id}`, headerData);
        toast.success('Dados atualizados com sucesso!');
      } else {
        const response = await api.post('/pacs', headerData);
        toast.success('PAC criado com sucesso!');
        navigate(`/pacs/${response.data.pac_id}/edit`, { replace: true });
      }
    } catch (error) {
      toast.error('Erro ao salvar dados');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveItem = async () => {
    if (!tempItem.descricao || !tempItem.quantidade || !tempItem.valorUnitario) {
      toast.error('Preencha os campos obrigatórios');
      return;
    }

    if (!isEditing) {
      toast.error('Salve os dados da secretaria primeiro');
      return;
    }

    try {
      if (editingItem) {
        await api.put(`/pacs/${id}/items/${editingItem.item_id}`, tempItem);
        toast.success('Item atualizado!');
      } else {
        await api.post(`/pacs/${id}/items`, tempItem);
        toast.success('Item adicionado!');
      }
      
      fetchPACData();
      closeModal();
    } catch (error) {
      toast.error('Erro ao salvar item');
    }
  };

  const handleDeleteItem = async (itemId) => {
    if (!window.confirm('Excluir este item?')) return;

    try {
      await api.delete(`/pacs/${id}/items/${itemId}`);
      toast.success('Item excluído!');
      fetchPACData();
    } catch (error) {
      toast.error('Erro ao excluir item');
    }
  };

  const openModal = (item = null) => {
    if (item) {
      setEditingItem(item);
      setTempItem(item);
    } else {
      setEditingItem(null);
      setTempItem({
        tipo: 'Material de Consumo',
        catmat: '',
        descricao: '',
        unidade: 'Unidade',
        quantidade: 0,
        valorUnitario: 0,
        prioridade: 'Alta',
        justificativa: '',
        codigo_classificacao: '',
        subitem_classificacao: ''
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingItem(null);
  };

  const handleExportXLSX = async () => {
    try {
      const response = await api.get(`/pacs/${id}/export/xlsx`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `PAC_${headerData.secretaria.replace(/\s+/g, '_')}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Exportado com sucesso!');
    } catch (error) {
      toast.error('Erro ao exportar XLSX');
    }
  };

  const handleExportPDF = async () => {
    try {
      const response = await api.get(`/pacs/${id}/export/pdf`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `PAC_${headerData.secretaria.replace(/\s+/g, '_')}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('PDF gerado com sucesso!');
    } catch (error) {
      toast.error('Erro ao gerar PDF');
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await api.get('/template/download', {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'Template_PAC.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Template baixado!');
    } catch (error) {
      toast.error('Erro ao baixar template');
    }
  };

  const handleImportXLSX = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post(`/pacs/${id}/import`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      toast.success(response.data.message);
      fetchPACData();
    } catch (error) {
      toast.error('Erro ao importar planilha');
    }
    
    event.target.value = '';
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value || 0);
  };

  const calculateTotal = () => {
    return items.reduce((acc, item) => acc + (item.valorTotal || 0), 0);
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
      <div className="space-y-6" data-testid="pac-editor">
        {/* Toolbar */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-card p-4 rounded-lg border border-border shadow-sm no-print">
          <div>
            <h2 className="text-2xl font-heading font-bold text-foreground flex items-center gap-2">
              {isEditing ? `${isReadOnly ? 'Visualizando' : 'Editando'}: ${headerData.secretaria}` : 'Novo PAC'}
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              {isReadOnly 
                ? 'Você está visualizando este PAC. Apenas o criador ou administradores podem editar.' 
                : isEditing 
                  ? 'Altere os dados abaixo ou adicione itens.' 
                  : 'Preencha os dados da secretaria e clique em Salvar.'}
            </p>
          </div>
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => navigate('/pacs')}
              data-testid="back-btn"
              className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border hover:bg-accent hover:text-accent-foreground transition-colors"
            >
              <ArrowLeft size={16} />
              Voltar
            </button>
            {!isReadOnly && (
              <button
                onClick={handleSaveHeader}
                disabled={saving}
                data-testid="save-header-btn"
                className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                <Save size={16} />
                Salvar Dados
              </button>
            )}
            {isEditing && (
              <>
                {!isReadOnly && (
                  <button
                    onClick={() => openModal()}
                    data-testid="add-item-btn"
                    className="flex items-center gap-2 bg-secondary text-secondary-foreground px-4 py-2 rounded-lg hover:bg-secondary/90 transition-colors"
                  >
                    <Plus size={16} />
                    Adicionar Item
                  </button>
                )}
                <button
                  onClick={handleDownloadTemplate}
                  data-testid="download-template-btn"
                  className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border hover:bg-accent hover:text-accent-foreground transition-colors"
                >
                  <Download size={16} />
                  Template
                </button>
                <label className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border hover:bg-accent hover:text-accent-foreground transition-colors cursor-pointer">
                  <Upload size={16} />
                  Importar
                  <input
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={handleImportXLSX}
                    className="hidden"
                    data-testid="import-file-input"
                  />
                </label>
                {items.length > 0 && (
                  <>
                    <button
                      onClick={handleExportXLSX}
                      data-testid="export-xlsx-btn"
                      className="flex items-center gap-2 bg-emerald-600 text-white px-4 py-2 rounded-lg hover:bg-emerald-700 transition-colors"
                    >
                      <FileSpreadsheet size={16} />
                      XLSX
                    </button>
                    <button
                      onClick={handleExportPDF}
                      data-testid="export-pdf-btn"
                      className="flex items-center gap-2 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
                    >
                      <FileText size={16} />
                      PDF
                    </button>
                  </>
                )}
              </>
            )}
          </div>
        </div>

        {/* Header for Print */}
        <div className="hidden print:block text-center mb-8 border-b-2 border-black pb-4">
          <h1 className="text-2xl font-bold uppercase">Prefeitura Municipal de Acaiaca - MG</h1>
          <h2 className="text-xl font-bold">PAC 2.0 - Plano Anual de Contratações - Exercício 2026</h2>
          <div className="mt-2 text-sm">
            <p>Lei Federal nº 14.133/2021</p>
          </div>
        </div>

        {/* Form - Dados da Secretaria */}
        <div className="bg-card p-6 rounded-lg border border-border shadow-sm">
          <h3 className="text-lg font-heading font-bold text-foreground mb-4 pb-2 border-b border-border">
            Dados da Unidade Requisitante
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-semibold text-foreground mb-1">
                Secretaria / Unidade <span className="text-destructive">*</span>
              </label>
              <input
                type="text"
                value={headerData.secretaria}
                onChange={(e) => setHeaderData({ ...headerData, secretaria: e.target.value })}
                className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                data-testid="secretaria-input"
                disabled={isReadOnly}
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-foreground mb-1">Secretário(a)</label>
              <input
                type="text"
                value={headerData.secretario}
                onChange={(e) => setHeaderData({ ...headerData, secretario: e.target.value })}
                className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                data-testid="secretario-input"
                disabled={isReadOnly}
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-foreground mb-1">Fiscal do Contrato</label>
              <input
                type="text"
                value={headerData.fiscal}
                onChange={(e) => setHeaderData({ ...headerData, fiscal: e.target.value })}
                className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                data-testid="fiscal-input"
                disabled={isReadOnly}
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-foreground mb-1">Telefone</label>
              <input
                type="text"
                value={headerData.telefone}
                onChange={(e) => setHeaderData({ ...headerData, telefone: e.target.value })}
                className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                data-testid="telefone-input"
                disabled={isReadOnly}
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-foreground mb-1">E-mail</label>
              <input
                type="email"
                value={headerData.email}
                onChange={(e) => setHeaderData({ ...headerData, email: e.target.value })}
                className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={isReadOnly}
              />
            </div>
            <div className="lg:col-span-1">
              <label className="block text-sm font-semibold text-foreground mb-1">Ano</label>
              <input
                type="text"
                value={headerData.ano}
                onChange={(e) => setHeaderData({ ...headerData, ano: e.target.value })}
                className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={isReadOnly}
              />
            </div>
            <div className="lg:col-span-3">
              <label className="block text-sm font-semibold text-foreground mb-1">Endereço Completo</label>
              <input
                type="text"
                value={headerData.endereco}
                onChange={(e) => setHeaderData({ ...headerData, endereco: e.target.value })}
                className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                data-testid="endereco-input"
                disabled={isReadOnly}
              />
            </div>
          </div>
        </div>

        {/* Items Table */}
        {isEditing && (
          <div className="bg-card rounded-lg border border-border shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm" data-testid="items-table">
                <thead className="bg-muted text-foreground">
                  <tr>
                    <th className="px-4 py-3 text-left">Tipo</th>
                    <th className="px-4 py-3 text-left">Código</th>
                    <th className="px-4 py-3 text-left">Descrição</th>
                    <th className="px-4 py-3 text-center">Und</th>
                    <th className="px-4 py-3 text-center">Qtd</th>
                    <th className="px-4 py-3 text-right">Valor Unit</th>
                    <th className="px-4 py-3 text-right">Total</th>
                    <th className="px-4 py-3 text-center">Prior</th>
                    <th className="px-4 py-3 text-left">Classificação</th>
                    <th className="px-4 py-3 text-center no-print">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {items.length === 0 ? (
                    <tr>
                      <td colSpan="10" className="px-4 py-8 text-center text-muted-foreground">
                        Nenhum item cadastrado. Clique em "Adicionar Item" para começar.
                      </td>
                    </tr>
                  ) : (
                    items.map((item) => (
                      <tr key={item.item_id} className="border-b border-border hover:bg-muted/50 transition-colors">
                        <td className="px-4 py-3 font-medium">{item.tipo}</td>
                        <td className="px-4 py-3 font-mono text-xs">{item.catmat}</td>
                        <td className="px-4 py-3">
                          <div className="font-semibold">{item.descricao}</div>
                          {item.justificativa && (
                            <div className="text-xs text-muted-foreground italic mt-1">{item.justificativa}</div>
                          )}
                        </td>
                        <td className="px-4 py-3 text-center">{item.unidade}</td>
                        <td className="px-4 py-3 text-center font-bold">{item.quantidade}</td>
                        <td className="px-4 py-3 text-right font-mono">{formatCurrency(item.valorUnitario)}</td>
                        <td className="px-4 py-3 text-right font-mono font-bold">{formatCurrency(item.valorTotal)}</td>
                        <td className="px-4 py-3 text-center">
                          <span className={`px-2 py-1 rounded text-xs ${
                            item.prioridade === 'Alta' ? 'bg-red-100 text-red-800' :
                            item.prioridade === 'Média' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {item.prioridade}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-left">
                          {item.codigo_classificacao ? (
                            <div className="text-xs">
                              <div className="font-semibold">{item.codigo_classificacao}</div>
                              {item.subitem_classificacao && (
                                <div className="text-muted-foreground">{item.subitem_classificacao}</div>
                              )}
                            </div>
                          ) : (
                            <span className="text-muted-foreground text-xs">-</span>
                          )}
                        </td>
                        <td className="px-4 py-3 no-print">
                          {!isReadOnly && (
                            <div className="flex justify-center gap-2">
                              <button
                                onClick={() => openModal(item)}
                                data-testid={`edit-item-${item.item_id}`}
                                className="text-accent hover:text-accent/80 transition-colors p-1"
                              >
                                <Edit size={16} />
                              </button>
                              <button
                                onClick={() => handleDeleteItem(item.item_id)}
                                data-testid={`delete-item-${item.item_id}`}
                                className="text-destructive hover:text-destructive/80 transition-colors p-1"
                              >
                                <Trash2 size={16} />
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
                {items.length > 0 && (
                  <tfoot className="bg-muted font-bold text-foreground">
                    <tr>
                      <td colSpan="6" className="px-4 py-3 text-right uppercase">Total Geral Estimado:</td>
                      <td className="px-4 py-3 text-right font-mono text-lg">{formatCurrency(calculateTotal())}</td>
                      <td colSpan="3"></td>
                    </tr>
                  </tfoot>
                )}
              </table>
            </div>
          </div>
        )}

        {/* Footer for Print */}
        <div className="hidden print:block mt-12 pt-8 border-t border-black">
          <div className="flex justify-between text-center px-12">
            <div className="border-t border-black w-64 pt-2">
              <p>{headerData.secretario}</p>
              <p className="text-xs">Secretário(a) Responsável</p>
            </div>
            <div className="border-t border-black w-64 pt-2">
              <p>{headerData.fiscal}</p>
              <p className="text-xs">Fiscal do Contrato</p>
            </div>
          </div>
          <div className="mt-8 text-center text-xs text-gray-500">
            Documento gerado eletronicamente pelo Sistema PAC - Plano Anual de Contratações em {new Date().toLocaleDateString('pt-BR')}.
          </div>
        </div>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 no-print">
          <div className="bg-card rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto border border-border">
            <div className="flex justify-between items-center p-6 border-b border-border sticky top-0 bg-card z-10">
              <h3 className="text-xl font-heading font-bold text-foreground">
                {editingItem ? 'Editar Item' : 'Novo Item'}
              </h3>
              <button
                onClick={closeModal}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <X size={24} />
              </button>
            </div>
            <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-foreground mb-1">
                  Tipo <span className="text-destructive">*</span>
                </label>
                <select
                  value={tempItem.tipo}
                  onChange={(e) => setTempItem({ ...tempItem, tipo: e.target.value })}
                  className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                  data-testid="item-tipo-select"
                >
                  <option value="Material de Consumo">Material de Consumo</option>
                  <option value="Material Permanente">Material Permanente</option>
                  <option value="Serviço">Serviço</option>
                  <option value="Obras">Obras</option>
                  <option value="Soluções de TIC">Soluções de TIC</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold text-foreground mb-1">Código CATMAT/CATSER</label>
                <input
                  type="text"
                  value={tempItem.catmat}
                  onChange={(e) => setTempItem({ ...tempItem, catmat: e.target.value })}
                  className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                  data-testid="item-catmat-input"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-semibold text-foreground mb-1">
                  Descrição do Objeto <span className="text-destructive">*</span>
                </label>
                <textarea
                  value={tempItem.descricao}
                  onChange={(e) => setTempItem({ ...tempItem, descricao: e.target.value })}
                  rows="2"
                  className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                  placeholder="Descrição detalhada..."
                  data-testid="item-descricao-input"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-foreground mb-1">Unidade</label>
                <input
                  type="text"
                  value={tempItem.unidade}
                  onChange={(e) => setTempItem({ ...tempItem, unidade: e.target.value })}
                  className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                  data-testid="item-unidade-input"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-foreground mb-1">
                  Quantidade <span className="text-destructive">*</span>
                </label>
                <input
                  type="number"
                  value={tempItem.quantidade}
                  onChange={(e) => setTempItem({ ...tempItem, quantidade: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                  data-testid="item-quantidade-input"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-foreground mb-1">
                  Valor Unitário (R$) <span className="text-destructive">*</span>
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={tempItem.valorUnitario}
                  onChange={(e) => setTempItem({ ...tempItem, valorUnitario: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                  data-testid="item-valor-input"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-foreground mb-1">Total (Estimado)</label>
                <div className="bg-muted p-2 rounded-md font-bold text-accent border border-border font-mono">
                  {formatCurrency(tempItem.quantidade * tempItem.valorUnitario)}
                </div>
              </div>
              <div>
                <label className="block text-sm font-semibold text-foreground mb-1">Prioridade</label>
                <select
                  value={tempItem.prioridade}
                  onChange={(e) => setTempItem({ ...tempItem, prioridade: e.target.value })}
                  className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                >
                  <option value="Alta">Alta</option>
                  <option value="Média">Média</option>
                  <option value="Baixa">Baixa</option>
                </select>
              </div>
              
              <div className="md:col-span-2">
                <label className="block text-sm font-semibold text-foreground mb-1">
                  Justificativa <span className="text-destructive">*</span>
                </label>
                <textarea
                  value={tempItem.justificativa}
                  onChange={(e) => setTempItem({ ...tempItem, justificativa: e.target.value })}
                  rows="3"
                  className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                  placeholder="Justificativa da contratação conforme Lei 14.133/2021..."
                  data-testid="item-justificativa-input"
                />
              </div>
              
              {/* Classificação Orçamentária */}
              <div className="md:col-span-2">
                <ClassificacaoSelector
                  codigoSelecionado={tempItem.codigo_classificacao || ''}
                  subitemSelecionado={tempItem.subitem_classificacao || ''}
                  onCodigoChange={(codigo) => setTempItem(prev => ({ ...prev, codigo_classificacao: codigo }))}
                  onSubitemChange={(subitem) => setTempItem(prev => ({ ...prev, subitem_classificacao: subitem }))}
                  disabled={false}
                />
              </div>
            </div>
            <div className="p-6 border-t border-border bg-muted/50 rounded-b-xl flex justify-end gap-3">
              <button
                onClick={closeModal}
                className="px-4 py-2 border border-border rounded-lg hover:bg-accent hover:text-accent-foreground transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleSaveItem}
                data-testid="save-item-btn"
                className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors"
              >
                <Save size={16} />
                Salvar Item
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};

export default PACEditor;
