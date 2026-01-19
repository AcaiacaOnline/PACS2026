import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import Layout from '../components/Layout';
import ClassificacaoSelector from '../components/ClassificacaoSelector';
import QuantidadeSecretarias from '../components/QuantidadeSecretarias';
import Pagination, { usePagination } from '../components/Pagination';
import SignatureModal from '../components/SignatureModal';
import { ArrowLeft, Save, Plus, Edit, Trash2, FileText, FileSpreadsheet, Download, Upload, X } from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';
import { TelefoneInput, EmailInput, CEPInput, CurrencyInput } from '../utils/masks';

const PACGeralEditor = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEditing = !!id && id !== 'new';
  const [showSignatureModal, setShowSignatureModal] = useState(false);
  const [pdfOrientation, setPdfOrientation] = useState('landscape');
  const [currentUser, setCurrentUser] = useState(null);
  
  // Paginação de itens
  const { currentPage, setCurrentPage, pageSize, setPageSize, resetPage } = usePagination(15);

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

  const handleExportPDF = async (orientation = 'landscape', withSignature = false, signatureDate = null) => {
    try {
      let url = `/pacs-geral/${id}/export/pdf?orientation=${orientation}`;
      if (withSignature) {
        url += `&assinar=true`;
        if (signatureDate) {
          url += `&data_assinatura=${encodeURIComponent(signatureDate)}`;
        }
      }
      
      const response = await api.get(url, {
        responseType: 'blob'
      });
      const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = blobUrl;
      const orientationName = orientation === 'landscape' ? 'Paisagem' : 'Retrato';
      const signedSuffix = withSignature ? '_ASSINADO' : '';
      link.setAttribute('download', `PAC_Geral_${pac.nome_secretaria}_${orientationName}${signedSuffix}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      setShowExportModal(false);
      setShowSignatureModal(false);
      toast.success(withSignature ? 'PDF assinado gerado com sucesso!' : 'Exportado com sucesso!');
    } catch (error) {
      toast.error('Erro ao exportar PDF');
    }
  };

  const openSignatureModal = (orientation) => {
    setPdfOrientation(orientation);
    setShowSignatureModal(true);
  };

  const handleSignatureConfirm = async (signatureDate) => {
    await handleExportPDF(pdfOrientation, true, signatureDate);
  };

  const handleDownloadWithoutSignature = async () => {
    await handleExportPDF(pdfOrientation, false);
  };

  const handleImportFile = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post(`/pacs-geral/${id}/import`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success(response.data.message);
      fetchPACData();
      setShowImportModal(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao importar arquivo');
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
                Nome do Fiscal do Contrato <span className="text-destructive">*</span>
              </label>
              <input
                type="text"
                value={pac.fiscal_contrato || ''}
                onChange={(e) => setPac({ ...pac, fiscal_contrato: e.target.value })}
                className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                placeholder="Nome completo do fiscal"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-foreground mb-1">
                Telefone <span className="text-destructive">*</span>
              </label>
              <TelefoneInput
                value={pac.telefone}
                onChange={(e) => setPac({ ...pac, telefone: e.target.value })}
                className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                data-testid="telefone-input"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-foreground mb-1">
                E-mail <span className="text-destructive">*</span>
              </label>
              <EmailInput
                value={pac.email}
                onChange={(e) => setPac({ ...pac, email: e.target.value })}
                className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                data-testid="email-input"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-foreground mb-1">
                CEP <span className="text-destructive">*</span>
              </label>
              <CEPInput
                value={pac.cep}
                onChange={(e) => setPac({ ...pac, cep: e.target.value })}
                className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none"
                data-testid="cep-input"
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
              
              <button
                onClick={() => setShowImportModal(true)}
                className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Upload size={18} />
                <span>Importar Arquivo</span>
              </button>
              
              {items.length > 0 && (
                <>
                  <button
                    onClick={handleExportXLSX}
                    className="flex items-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                  >
                    <FileSpreadsheet size={18} />
                    <span>Excel</span>
                  </button>
                  
                  <button
                    onClick={() => setShowExportModal(true)}
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
                  {items
                    .slice((currentPage - 1) * pageSize, currentPage * pageSize)
                    .map((item) => (
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
            
            {/* Paginação de Itens */}
            {items.length > 0 && (
              <div className="mt-4 bg-card rounded-lg border border-border p-4 no-print">
                <Pagination
                  currentPage={currentPage}
                  totalItems={items.length}
                  pageSize={pageSize}
                  onPageChange={setCurrentPage}
                  onPageSizeChange={(newSize) => {
                    setPageSize(newSize);
                    setCurrentPage(1);
                  }}
                  pageSizeOptions={[15, 30, 50, 100]}
                />
              </div>
            )}
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
                    <CurrencyInput
                      value={tempItem.valorUnitario}
                      onChange={(e) => setTempItem({ ...tempItem, valorUnitario: e.target.value })}
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

        {/* Modal de Exportação PDF */}
        {showExportModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card rounded-xl shadow-xl max-w-md w-full">
              <div className="p-6 border-b border-border">
                <div className="flex justify-between items-center">
                  <h3 className="text-xl font-bold text-foreground">Exportar Relatório PDF</h3>
                  <button onClick={() => setShowExportModal(false)} className="text-muted-foreground hover:text-foreground">
                    <X size={24} />
                  </button>
                </div>
              </div>
              
              <div className="p-6 space-y-4">
                <p className="text-muted-foreground">Escolha a orientação do relatório:</p>
                
                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={() => openSignatureModal('landscape')}
                    className="flex flex-col items-center p-4 border-2 border-border rounded-lg hover:border-primary hover:bg-primary/5 transition-colors"
                  >
                    <div className="w-16 h-10 border-2 border-primary rounded mb-2"></div>
                    <span className="font-semibold text-foreground">Paisagem</span>
                    <span className="text-xs text-muted-foreground">A4 Horizontal</span>
                  </button>
                  
                  <button
                    onClick={() => openSignatureModal('portrait')}
                    className="flex flex-col items-center p-4 border-2 border-border rounded-lg hover:border-primary hover:bg-primary/5 transition-colors"
                  >
                    <div className="w-10 h-14 border-2 border-primary rounded mb-2"></div>
                    <span className="font-semibold text-foreground">Retrato</span>
                    <span className="text-xs text-muted-foreground">A4 Vertical</span>
                  </button>
                </div>
                
                <p className="text-xs text-muted-foreground text-center">
                  O relatório será gerado com os dados consolidados, sem detalhamento por secretaria.
                </p>
              </div>
            </div>
          </div>

          {/* Modal de Assinatura Digital */}
          <SignatureModal
            isOpen={showSignatureModal}
            onClose={() => setShowSignatureModal(false)}
            onConfirm={handleSignatureConfirm}
            onDownloadWithoutSignature={handleDownloadWithoutSignature}
            documentInfo={{
              title: `PAC Geral ${pac.ano || new Date().getFullYear()} - ${pac.nome_secretaria}`,
              subtitle: `Responsável: ${pac.secretario}`,
              type: 'PAC Consolidado'
            }}
            user={currentUser}
          />
        )}

        {/* Modal de Importação */}
        {showImportModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card rounded-xl shadow-xl max-w-lg w-full">
              <div className="p-6 border-b border-border">
                <div className="flex justify-between items-center">
                  <h3 className="text-xl font-bold text-foreground">Importar Itens</h3>
                  <button onClick={() => setShowImportModal(false)} className="text-muted-foreground hover:text-foreground">
                    <X size={24} />
                  </button>
                </div>
              </div>
              
              <div className="p-6 space-y-4">
                <p className="text-muted-foreground">
                  Selecione um arquivo para importar itens para este PAC Geral.
                </p>
                
                <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
                  <Upload size={48} className="mx-auto text-muted-foreground mb-4" />
                  <p className="text-foreground font-semibold mb-2">Formatos suportados:</p>
                  <p className="text-sm text-muted-foreground mb-4">CSV, Excel (.xlsx), JSON</p>
                  
                  <label className="cursor-pointer">
                    <span className="bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors inline-block">
                      Selecionar Arquivo
                    </span>
                    <input
                      type="file"
                      accept=".csv,.xlsx,.xls,.json"
                      onChange={handleImportFile}
                      className="hidden"
                    />
                  </label>
                </div>
                
                <div className="bg-muted/50 rounded-lg p-4">
                  <p className="text-sm font-semibold text-foreground mb-2">Estrutura esperada do arquivo:</p>
                  <ul className="text-xs text-muted-foreground space-y-1">
                    <li>• <b>codigo</b> - Código Catmat/Catser</li>
                    <li>• <b>descricao</b> - Descrição do item</li>
                    <li>• <b>unidade</b> - Unidade de medida</li>
                    <li>• <b>quantidade_total</b> - Quantidade total</li>
                    <li>• <b>valor_unitario</b> - Valor unitário</li>
                    <li>• <b>prioridade</b> - Alta, Média ou Baixa</li>
                    <li>• <b>classificacao</b> - Código de classificação (opcional)</li>
                    <li>• <b>justificativa</b> - Justificativa (opcional)</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default PACGeralEditor;
