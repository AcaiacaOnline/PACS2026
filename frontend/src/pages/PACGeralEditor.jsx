import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import Layout from '../components/Layout';
import ClassificacaoSelector from '../components/ClassificacaoSelector';
import QuantidadeSecretarias from '../components/QuantidadeSecretarias';
import { ArrowLeft, Save, Plus, Edit, Trash2, FileText, FileSpreadsheet, Download, Upload, X } from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';

const PACGeralEditor = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEditing = !!id && id !== 'new';

  const [pac, setPac] = useState({
    nome_secretaria: '',
    secretario: '',
    fiscal_contrato: '',  // NOVO - Nome do Fiscal do Contrato
    telefone: '',
    email: '',
    endereco: '',
    cep: '',
    secretarias_selecionadas: []
  });

  const [items, setItems] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [user, setUser] = useState(null);
  const [showExportModal, setShowExportModal] = useState(false);  // NOVO
  const [showImportModal, setShowImportModal] = useState(false);  // NOVO
  const [tempItem, setTempItem] = useState({
    catmat: '',
    descricao: '',
    unidade: 'Unidade',
    qtd_ad: 0,
    qtd_fa: 0,
    qtd_sa: 0,
    qtd_se: 0,
    qtd_as: 0,
    qtd_ag: 0,
    qtd_ob: 0,
    qtd_tr: 0,
    qtd_cul: 0,
    valorUnitario: 0,
    prioridade: 'Alta',
    justificativa: '',
    codigo_classificacao: '',
    subitem_classificacao: ''
  });

  const [loading, setLoading] = useState(false);
  const [isSaved, setIsSaved] = useState(false);

  const secretariasDisponiveis = [
    { sigla: 'AD', nome: 'Administração' },
    { sigla: 'FA', nome: 'Fazenda' },
    { sigla: 'SA', nome: 'Saúde' },
    { sigla: 'SE', nome: 'Educação' },
    { sigla: 'AS', nome: 'Assistência Social' },
    { sigla: 'AG', nome: 'Agricultura' },
    { sigla: 'OB', nome: 'Obras' },
    { sigla: 'TR', nome: 'Transporte' },
    { sigla: 'CUL', nome: 'Cultura' }
  ];

  useEffect(() => {
    if (isEditing) {
      fetchPACData();
    }
    loadUser();
  }, [id]);

  const loadUser = () => {
    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
    }
  };

  const canEdit = () => {
    if (!user || !pac.user_id) return false;
    return user.is_admin || user.user_id === pac.user_id;
  };

  const fetchPACData = async () => {
    try {
      const [pacResponse, itemsResponse] = await Promise.all([
        api.get(`/pacs-geral/${id}`),
        api.get(`/pacs-geral/${id}/items`)
      ]);
      setPac(pacResponse.data);
      setItems(itemsResponse.data);
      setIsSaved(true);
    } catch (error) {
      toast.error('Erro ao carregar dados do PAC Geral');
    }
  };

  const handleSavePAC = async () => {
    if (!pac.nome_secretaria || !pac.secretario || !pac.telefone || !pac.email) {
      toast.error('Preencha todos os campos obrigatórios');
      return;
    }

    if (pac.secretarias_selecionadas.length === 0) {
      toast.error('Selecione pelo menos uma secretaria');
      return;
    }

    setLoading(true);
    try {
      if (isEditing) {
        await api.put(`/pacs-geral/${id}`, pac);
        toast.success('PAC Geral atualizado!');
      } else {
        const response = await api.post('/pacs-geral', pac);
        toast.success('PAC Geral criado!');
        navigate(`/pacs-geral/${response.data.pac_geral_id}/edit`, { replace: true });
      }
      setIsSaved(true);
      if (isEditing) fetchPACData();
    } catch (error) {
      toast.error('Erro ao salvar PAC Geral');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAllSecretarias = (e) => {
    if (e.target.checked) {
      setPac({ ...pac, secretarias_selecionadas: secretariasDisponiveis.map(s => s.sigla) });
    } else {
      setPac({ ...pac, secretarias_selecionadas: [] });
    }
  };

  const handleToggleSecretaria = (sigla) => {
    const selected = pac.secretarias_selecionadas.includes(sigla);
    if (selected) {
      setPac({ ...pac, secretarias_selecionadas: pac.secretarias_selecionadas.filter(s => s !== sigla) });
    } else {
      setPac({ ...pac, secretarias_selecionadas: [...pac.secretarias_selecionadas, sigla] });
    }
  };

  const openModal = (item = null) => {
    if (item) {
      setEditingItem(item);
      setTempItem({ ...item });
    } else {
      setEditingItem(null);
      setTempItem({
        catmat: '',
        descricao: '',
        unidade: 'Unidade',
        qtd_ad: 0,
        qtd_fa: 0,
        qtd_sa: 0,
        qtd_se: 0,
        qtd_as: 0,
        qtd_ag: 0,
        qtd_ob: 0,
        qtd_tr: 0,
        qtd_cul: 0,
        valorUnitario: 0,
        prioridade: 'Alta',
        justificativa: '',
        codigo_classificacao: '',
        subitem_classificacao: ''
      });
    }
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingItem(null);
  };

  const handleSaveItem = async () => {
    if (!tempItem.descricao || !tempItem.catmat) {
      toast.error('Preencha os campos obrigatórios');
      return;
    }

    if (!isSaved) {
      toast.error('Salve os dados da secretaria primeiro');
      return;
    }

    try {
      if (editingItem) {
        await api.put(`/pacs-geral/${id}/items/${editingItem.item_id}`, tempItem);
        toast.success('Item atualizado!');
      } else {
        await api.post(`/pacs-geral/${id}/items`, tempItem);
        toast.success('Item adicionado!');
      }
      
      fetchPACData();
      closeModal();
    } catch (error) {
      toast.error('Erro ao salvar item');
    }
  };

  const handleDeleteItem = async (itemId) => {
    if (!window.confirm('Tem certeza que deseja excluir este item?')) return;

    try {
      await api.delete(`/pacs-geral/${id}/items/${itemId}`);
      toast.success('Item excluído!');
      fetchPACData();
    } catch (error) {
      toast.error('Erro ao excluir item');
    }
  };

  const handleQuantidadeChange = (sigla, value) => {
    setTempItem(prev => ({
      ...prev,
      [`qtd_${sigla}`]: value
    }));
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
  };

  const calculateTotal = () => {
    return items.reduce((sum, item) => sum + (item.valorTotal || 0), 0);
  };

  const handleExportXLSX = async () => {
    try {
      const response = await api.get(`/pacs-geral/${id}/export/xlsx`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `PAC_Geral_${pac.nome_secretaria}.xlsx`);
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
      const response = await api.get(`/pacs-geral/${id}/export/pdf`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `PAC_Geral_${pac.nome_secretaria}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Exportado com sucesso!');
    } catch (error) {
      toast.error('Erro ao exportar PDF');
    }
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6 no-print">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/pacs-geral')}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft size={24} />
            </button>
            <div>
              <h1 className="text-3xl font-heading font-bold text-foreground">
                {isEditing ? 'Editar PAC Geral' : 'Novo PAC Geral'}
              </h1>
              <p className="text-muted-foreground text-sm">Plano Anual de Contratações Compartilhado</p>
            </div>
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={() => navigate('/pacs-geral')}
              className="px-4 py-2 border border-border rounded-lg hover:bg-muted transition-colors"
            >
              Voltar
            </button>
            <button
              onClick={handleSavePAC}
              disabled={loading}
              className="flex items-center space-x-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              <Save size={18} />
              <span>Salvar Dados</span>
            </button>
          </div>
        </div>

        {/* Form */}
        <div className="bg-card border border-border rounded-xl p-6 mb-6">
          <h2 className="text-xl font-bold text-foreground mb-4 border-b border-border pb-2">
            Dados da Secretaria Responsável
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-foreground mb-1">
                Nome da Secretaria <span className="text-destructive">*</span>
              </label>
              <input
                type="text"
                value={pac.nome_secretaria}
                onChange={(e) => setPac({ ...pac, nome_secretaria: e.target.value })}
                className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                placeholder="Ex: Secretaria de Administração"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-foreground mb-1">
                Secretário Responsável <span className="text-destructive">*</span>
              </label>
              <input
                type="text"
                value={pac.secretario}
                onChange={(e) => setPac({ ...pac, secretario: e.target.value })}
                className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                placeholder="Nome completo"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-foreground mb-1">
                Telefone <span className="text-destructive">*</span>
              </label>
              <input
                type="tel"
                value={pac.telefone}
                onChange={(e) => setPac({ ...pac, telefone: e.target.value })}
                className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                placeholder="(00) 00000-0000"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-foreground mb-1">
                E-mail <span className="text-destructive">*</span>
              </label>
              <input
                type="email"
                value={pac.email}
                onChange={(e) => setPac({ ...pac, email: e.target.value })}
                className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                placeholder="email@prefeitura.gov.br"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-foreground mb-1">
                CEP <span className="text-destructive">*</span>
              </label>
              <input
                type="text"
                value={pac.cep}
                onChange={(e) => setPac({ ...pac, cep: e.target.value })}
                className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                placeholder="00000-000"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-foreground mb-1">
                Endereço Completo <span className="text-destructive">*</span>
              </label>
              <input
                type="text"
                value={pac.endereco}
                onChange={(e) => setPac({ ...pac, endereco: e.target.value })}
                className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                placeholder="Rua, Número, Bairro, Cidade - UF"
              />
            </div>
          </div>

          {/* Seleção de Secretarias */}
          <div className="mt-6">
            <label className="block text-sm font-semibold text-foreground mb-3">
              Secretarias Participantes <span className="text-destructive">*</span>
            </label>
            
            <div className="mb-4">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={pac.secretarias_selecionadas.length === secretariasDisponiveis.length}
                  onChange={handleSelectAllSecretarias}
                  className="w-5 h-5 rounded border-input text-primary focus:ring-ring"
                />
                <span className="text-sm font-bold text-foreground">Selecionar Todas as Secretarias</span>
              </label>
            </div>

            <div className="grid grid-cols-3 gap-3">
              {secretariasDisponiveis.map((sec) => (
                <label key={sec.sigla} className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={pac.secretarias_selecionadas.includes(sec.sigla)}
                    onChange={() => handleToggleSecretaria(sec.sigla)}
                    className="w-4 h-4 rounded border-input text-primary focus:ring-ring"
                  />
                  <span className="text-sm text-foreground">
                    <span className="font-bold">{sec.sigla}</span> - {sec.nome}
                  </span>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Botões de Ação */}
        {isSaved && (
          <div className="bg-card border border-border rounded-xl p-6 mb-6 no-print">
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => openModal()}
                data-testid="add-item-btn"
                className="flex items-center space-x-2 bg-secondary text-secondary-foreground px-4 py-2 rounded-lg hover:bg-secondary/90 transition-colors"
              >
                <Plus size={18} />
                <span>Adicionar Item</span>
              </button>
              
              {items.length > 0 && (
                <>
                  <button
                    onClick={handleExportXLSX}
                    className="flex items-center space-x-2 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
                  >
                    <FileSpreadsheet size={18} />
                    <span>Excel</span>
                  </button>
                  
                  <button
                    onClick={handleExportPDF}
                    className="flex items-center space-x-2 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
                  >
                    <FileText size={18} />
                    <span>PDF</span>
                  </button>
                </>
              )}
            </div>
          </div>
        )}

        {/* Tabela de Items */}
        {isSaved && items.length > 0 && (
          <div className="bg-card border border-border rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-semibold">Código</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">Descrição</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold">Und</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold">Qtd Total</th>
                    <th className="px-4 py-3 text-right text-sm font-semibold">Valor Unit</th>
                    <th className="px-4 py-3 text-right text-sm font-semibold">Total</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold">Prior</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">Classificação</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold no-print">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.item_id} className="border-b border-border hover:bg-muted/50 transition-colors">
                      <td className="px-4 py-3 font-mono text-xs">{item.catmat}</td>
                      <td className="px-4 py-3">
                        <div className="font-semibold">{item.descricao}</div>
                        {item.justificativa && (
                          <div className="text-xs text-muted-foreground italic mt-1">{item.justificativa}</div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">{item.unidade}</td>
                      <td className="px-4 py-3 text-center font-bold">{item.quantidade_total}</td>
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
                        <div className="flex justify-center gap-2">
                          <button
                            onClick={() => openModal(item)}
                            className="text-accent hover:text-accent/80 transition-colors p-1"
                            title="Editar"
                          >
                            <Edit size={16} />
                          </button>
                          {user?.is_admin && (
                            <button
                              onClick={() => handleDeleteItem(item.item_id)}
                              className="text-destructive hover:text-destructive/80 transition-colors p-1"
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
                <tfoot className="bg-muted font-bold text-foreground">
                  <tr>
                    <td colSpan="5" className="px-4 py-3 text-right uppercase">Total Geral Estimado:</td>
                    <td className="px-4 py-3 text-right font-mono text-lg">{formatCurrency(calculateTotal())}</td>
                    <td colSpan="3"></td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        )}

        {/* Modal Adicionar/Editar Item */}
        {showModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card rounded-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
              <div className="p-6 border-b border-border flex justify-between items-center">
                <h2 className="text-xl font-bold text-foreground">
                  {editingItem ? 'Editar Item' : 'Adicionar Item'}
                </h2>
                <button
                  onClick={closeModal}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  <X size={24} />
                </button>
              </div>

              <div className="p-6 overflow-y-auto flex-1">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-foreground mb-1">
                      Código CATMAT/CATSER <span className="text-destructive">*</span>
                    </label>
                    <input
                      type="text"
                      value={tempItem.catmat}
                      onChange={(e) => setTempItem({ ...tempItem, catmat: e.target.value })}
                      className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                      data-testid="item-catmat-input"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-foreground mb-1">Unidade</label>
                    <select
                      value={tempItem.unidade}
                      onChange={(e) => setTempItem({ ...tempItem, unidade: e.target.value })}
                      className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                    >
                      <option value="Unidade">Unidade</option>
                      <option value="Caixa">Caixa</option>
                      <option value="Pacote">Pacote</option>
                      <option value="Metro">Metro</option>
                      <option value="Litro">Litro</option>
                      <option value="Quilo">Quilo</option>
                      <option value="Serviço">Serviço</option>
                    </select>
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-semibold text-foreground mb-1">
                      Descrição do Objeto <span className="text-destructive">*</span>
                    </label>
                    <textarea
                      value={tempItem.descricao}
                      onChange={(e) => setTempItem({ ...tempItem, descricao: e.target.value })}
                      rows="3"
                      className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                      placeholder="Descrição detalhada do item..."
                      data-testid="item-descricao-input"
                    />
                  </div>

                  {/* Quantidades por Secretaria */}
                  <div className="md:col-span-2">
                    <QuantidadeSecretarias
                      valores={tempItem}
                      onChange={handleQuantidadeChange}
                      disabled={false}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-foreground mb-1">
                      Valor Unitário (R$) <span className="text-destructive">*</span>
                    </label>
                    <input
                      type="number"
                      value={tempItem.valorUnitario}
                      onChange={(e) => setTempItem({ ...tempItem, valorUnitario: parseFloat(e.target.value) || 0 })}
                      step="0.01"
                      min="0"
                      className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                      data-testid="item-valor-input"
                    />
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

                  {/* Justificativa */}
                  <div className="md:col-span-2">
                    <label className="block text-sm font-semibold text-foreground mb-1">
                      Justificativa Sucinta da Contratação <span className="text-destructive">*</span>
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
              </div>

              <div className="p-6 border-t border-border bg-muted/50 rounded-b-xl flex justify-end gap-3">
                <button
                  onClick={closeModal}
                  className="px-4 py-2 border border-border rounded-lg hover:bg-background transition-colors"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleSaveItem}
                  data-testid="save-item-btn"
                  className="flex items-center space-x-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors"
                >
                  <Save size={18} />
                  <span>Salvar Item</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default PACGeralEditor;
