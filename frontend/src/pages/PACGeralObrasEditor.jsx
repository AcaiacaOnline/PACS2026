import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Hammer, Plus, Save, Trash2, ArrowLeft, FileText, Download,
  Building2, ChevronDown
} from 'lucide-react';
import Layout from '../components/Layout';
import api from '../utils/api';
import { toast } from 'sonner';
import Pagination, { usePagination, paginateData } from '../components/Pagination';

const CLASSIFICACAO_OBRAS = {
  "339040": {
    nome: "Serviços de TIC - PJ",
    subitens: [
      "01 - Consultoria em TI",
      "02 - Desenvolvimento de Software",
      "03 - Suporte Técnico",
      "04 - Manutenção de Sistemas",
      "05 - Licenciamento de Software",
      "06 - Hospedagem e Cloud",
      "07 - Conectividade e Redes",
      "08 - Segurança da Informação"
    ]
  },
  "449051": {
    nome: "Obras e Instalações",
    subitens: [
      "01 - Construção de Edifícios",
      "02 - Reforma e Ampliação",
      "03 - Pavimentação",
      "04 - Saneamento Básico",
      "05 - Instalações Elétricas",
      "06 - Instalações Hidráulicas",
      "07 - Sistemas de Drenagem",
      "08 - Pontes e Viadutos",
      "09 - Obras de Contenção",
      "10 - Terraplanagem"
    ]
  },
  "339039": {
    nome: "Serviços de Terceiros - PJ",
    subitens: [
      "01 - Serviços de Engenharia",
      "02 - Serviços de Arquitetura",
      "03 - Laudos e Perícias",
      "04 - Elaboração de Projetos",
      "05 - Fiscalização de Obras",
      "06 - Gerenciamento de Obras",
      "07 - Topografia"
    ]
  }
};

const SECRETARIAS_COLS = [
  { key: 'qtd_ad', label: 'AD', nome: 'Administração' },
  { key: 'qtd_fa', label: 'FA', nome: 'Fazenda' },
  { key: 'qtd_sa', label: 'SA', nome: 'Saúde' },
  { key: 'qtd_se', label: 'SE', nome: 'Educação' },
  { key: 'qtd_as', label: 'AS', nome: 'Assist. Social' },
  { key: 'qtd_ag', label: 'AG', nome: 'Agricultura' },
  { key: 'qtd_ob', label: 'OB', nome: 'Obras' },
  { key: 'qtd_tr', label: 'TR', nome: 'Transporte' },
  { key: 'qtd_cul', label: 'CUL', nome: 'Cultura' }
];

const PACGeralObrasEditor = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [pac, setPac] = useState(null);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  
  const { currentPage, setCurrentPage, pageSize, setPageSize, resetPage } = usePagination(15);
  
  const [formData, setFormData] = useState({
    catmat: '',
    descricao: '',
    unidade: 'UN',
    qtd_ad: 0, qtd_fa: 0, qtd_sa: 0, qtd_se: 0, qtd_as: 0,
    qtd_ag: 0, qtd_ob: 0, qtd_tr: 0, qtd_cul: 0,
    valorUnitario: 0,
    prioridade: 'MÉDIA',
    justificativa: '',
    codigo_classificacao: '449051',
    subitem_classificacao: '',
    prazo_execucao: null
  });

  useEffect(() => {
    fetchPac();
    fetchItems();
  }, [id]);

  const fetchPac = async () => {
    try {
      const response = await api.get(`/pacs-geral-obras/${id}`);
      setPac(response.data);
    } catch (error) {
      toast.error('PAC não encontrado');
      navigate('/pacs-geral-obras');
    }
  };

  const fetchItems = async () => {
    try {
      const response = await api.get(`/pacs-geral-obras/${id}/items`);
      setItems(response.data);
    } catch (error) {
      toast.error('Erro ao carregar itens');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingItem) {
        await api.put(`/pacs-geral-obras/${id}/items/${editingItem.item_id}`, formData);
        toast.success('Item atualizado!');
      } else {
        await api.post(`/pacs-geral-obras/${id}/items`, formData);
        toast.success('Item adicionado!');
      }
      setShowModal(false);
      setEditingItem(null);
      fetchItems();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar item');
    }
  };

  const handleDelete = async (item) => {
    if (!window.confirm('Excluir este item?')) return;
    try {
      await api.delete(`/pacs-geral-obras/${id}/items/${item.item_id}`);
      toast.success('Item excluído!');
      fetchItems();
    } catch (error) {
      toast.error('Erro ao excluir item');
    }
  };

  const openModal = (item = null) => {
    if (item) {
      setEditingItem(item);
      setFormData({
        catmat: item.catmat,
        descricao: item.descricao,
        unidade: item.unidade,
        qtd_ad: item.qtd_ad || 0,
        qtd_fa: item.qtd_fa || 0,
        qtd_sa: item.qtd_sa || 0,
        qtd_se: item.qtd_se || 0,
        qtd_as: item.qtd_as || 0,
        qtd_ag: item.qtd_ag || 0,
        qtd_ob: item.qtd_ob || 0,
        qtd_tr: item.qtd_tr || 0,
        qtd_cul: item.qtd_cul || 0,
        valorUnitario: item.valorUnitario,
        prioridade: item.prioridade,
        justificativa: item.justificativa || '',
        codigo_classificacao: item.codigo_classificacao || '449051',
        subitem_classificacao: item.subitem_classificacao || '',
        prazo_execucao: item.prazo_execucao || null
      });
    } else {
      setEditingItem(null);
      setFormData({
        catmat: '',
        descricao: '',
        unidade: 'UN',
        qtd_ad: 0, qtd_fa: 0, qtd_sa: 0, qtd_se: 0, qtd_as: 0,
        qtd_ag: 0, qtd_ob: 0, qtd_tr: 0, qtd_cul: 0,
        valorUnitario: 0,
        prioridade: 'MÉDIA',
        justificativa: '',
        codigo_classificacao: '449051',
        subitem_classificacao: '',
        prazo_execucao: null
      });
    }
    setShowModal(true);
  };

  const calcularTotal = () => {
    return items.reduce((sum, item) => sum + (item.valorTotal || 0), 0);
  };

  const calcularQuantidadeTotal = () => {
    const qtds = [
      formData.qtd_ad, formData.qtd_fa, formData.qtd_sa, formData.qtd_se,
      formData.qtd_as, formData.qtd_ag, formData.qtd_ob, formData.qtd_tr, formData.qtd_cul
    ];
    return qtds.reduce((sum, q) => sum + (parseFloat(q) || 0), 0);
  };

  const paginatedItems = paginateData(items, currentPage, pageSize);

  const handleExportPDF = async () => {
    try {
      const response = await api.get(`/pacs-geral-obras/${id}/export/pdf`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `PAC_Obras_${pac?.nome_secretaria?.replace(/\s+/g, '_')}_${pac?.ano}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('PDF exportado com sucesso!');
    } catch (error) {
      toast.error('Erro ao exportar PDF');
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/pacs-geral-obras')}
              className="p-2 hover:bg-muted rounded-lg"
            >
              <ArrowLeft size={20} />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
                <Hammer className="text-amber-600" />
                {pac?.nome_secretaria}
              </h1>
              <p className="text-muted-foreground">
                PAC Obras {pac?.ano} • {pac?.tipo_contratacao}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleExportPDF}
              className="flex items-center gap-2 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
              data-testid="export-pdf-obras-btn"
            >
              <Download size={18} />
              PDF
            </button>
            <button
              onClick={() => openModal()}
              className="flex items-center gap-2 bg-amber-600 text-white px-4 py-2 rounded-lg hover:bg-amber-700"
              data-testid="add-item-btn"
            >
              <Plus size={18} />
              Adicionar Item
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-card border border-border rounded-xl p-4">
            <div className="text-sm text-muted-foreground">Total de Itens</div>
            <div className="text-2xl font-bold text-foreground">{items.length}</div>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <div className="text-sm text-muted-foreground">Valor Total</div>
            <div className="text-2xl font-bold text-amber-600">
              {calcularTotal().toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
            </div>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <div className="text-sm text-muted-foreground">Secretarias</div>
            <div className="flex flex-wrap gap-1 mt-1">
              {pac?.secretarias_selecionadas?.map(s => (
                <span key={s} className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded">
                  {s}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Tabela de Itens */}
        <div className="bg-card border border-border rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted">
                <tr>
                  <th className="px-3 py-2 text-left">Código</th>
                  <th className="px-3 py-2 text-left">Descrição</th>
                  <th className="px-3 py-2 text-center">Classificação</th>
                  <th className="px-3 py-2 text-center">Qtd Total</th>
                  <th className="px-3 py-2 text-right">Valor Unit.</th>
                  <th className="px-3 py-2 text-right">Valor Total</th>
                  <th className="px-3 py-2 text-center">Prior.</th>
                  <th className="px-3 py-2 text-center">Ações</th>
                </tr>
              </thead>
              <tbody>
                {paginatedItems.map((item) => (
                  <tr key={item.item_id} className="border-b border-border hover:bg-muted/50">
                    <td className="px-3 py-2 font-mono text-xs">{item.catmat}</td>
                    <td className="px-3 py-2">
                      <div className="max-w-xs truncate" title={item.descricao}>
                        {item.descricao}
                      </div>
                    </td>
                    <td className="px-3 py-2 text-center">
                      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                        {item.codigo_classificacao}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-center">{item.quantidade_total}</td>
                    <td className="px-3 py-2 text-right">
                      {item.valorUnitario?.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                    </td>
                    <td className="px-3 py-2 text-right font-semibold">
                      {item.valorTotal?.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                    </td>
                    <td className="px-3 py-2 text-center">
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        item.prioridade === 'ALTA' ? 'bg-red-100 text-red-700' :
                        item.prioridade === 'MÉDIA' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-green-100 text-green-700'
                      }`}>
                        {item.prioridade}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-center">
                      <div className="flex justify-center gap-1">
                        <button
                          onClick={() => openModal(item)}
                          className="p-1 text-primary hover:bg-primary/10 rounded"
                        >
                          <FileText size={14} />
                        </button>
                        <button
                          onClick={() => handleDelete(item)}
                          className="p-1 text-destructive hover:bg-destructive/10 rounded"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {items.length > pageSize && (
            <div className="p-4 border-t border-border">
              <Pagination
                currentPage={currentPage}
                totalItems={items.length}
                pageSize={pageSize}
                onPageChange={setCurrentPage}
                onPageSizeChange={setPageSize}
              />
            </div>
          )}

          {items.length === 0 && (
            <div className="text-center py-12 text-muted-foreground">
              <Hammer size={48} className="mx-auto mb-4 opacity-50" />
              <p>Nenhum item cadastrado</p>
            </div>
          )}
        </div>

        {/* Modal de Item */}
        {showModal && (
          <div className="fixed inset-0 bg-black/50 flex items-start justify-center z-50 p-4 pt-8 overflow-y-auto">
            <div className="bg-card rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-card border-b border-border px-6 py-4">
                <h3 className="text-xl font-bold text-foreground">
                  {editingItem ? 'Editar Item' : 'Novo Item'}
                </h3>
              </div>

              <form onSubmit={handleSubmit} className="p-6 space-y-4">
                {/* Classificação Orçamentária */}
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <h4 className="font-semibold text-amber-800 mb-3">
                    Classificação Orçamentária (Lei 14.133/2021)
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Código de Classificação *</label>
                      <select
                        value={formData.codigo_classificacao}
                        onChange={(e) => setFormData({...formData, codigo_classificacao: e.target.value, subitem_classificacao: ''})}
                        className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                        required
                      >
                        {Object.entries(CLASSIFICACAO_OBRAS).map(([codigo, info]) => (
                          <option key={codigo} value={codigo}>{codigo} - {info.nome}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Subitem da Classificação *</label>
                      <select
                        value={formData.subitem_classificacao}
                        onChange={(e) => setFormData({...formData, subitem_classificacao: e.target.value})}
                        className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                        required
                      >
                        <option value="">Selecione...</option>
                        {CLASSIFICACAO_OBRAS[formData.codigo_classificacao]?.subitens.map(sub => (
                          <option key={sub} value={sub}>{sub}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>

                {/* Dados do Item */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Código CATSER *</label>
                    <input
                      type="text"
                      value={formData.catmat}
                      onChange={(e) => setFormData({...formData, catmat: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      placeholder="Ex: 12345"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Unidade *</label>
                    <select
                      value={formData.unidade}
                      onChange={(e) => setFormData({...formData, unidade: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                    >
                      <option value="UN">Unidade</option>
                      <option value="M²">Metro Quadrado</option>
                      <option value="M³">Metro Cúbico</option>
                      <option value="ML">Metro Linear</option>
                      <option value="KM">Quilômetro</option>
                      <option value="TON">Tonelada</option>
                      <option value="SERV">Serviço</option>
                      <option value="MÊS">Mês</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Prazo (meses)</label>
                    <input
                      type="number"
                      value={formData.prazo_execucao || ''}
                      onChange={(e) => setFormData({...formData, prazo_execucao: e.target.value ? parseInt(e.target.value) : null})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      min="1"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Descrição *</label>
                  <textarea
                    value={formData.descricao}
                    onChange={(e) => setFormData({...formData, descricao: e.target.value})}
                    className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                    rows={2}
                    required
                  />
                </div>

                {/* Quantidades por Secretaria */}
                <div>
                  <label className="block text-sm font-medium mb-2">Quantidades por Secretaria</label>
                  <div className="grid grid-cols-3 md:grid-cols-5 lg:grid-cols-9 gap-2">
                    {SECRETARIAS_COLS.map(sec => (
                      <div key={sec.key} className="text-center">
                        <label className="block text-xs text-muted-foreground mb-1" title={sec.nome}>
                          {sec.label}
                        </label>
                        <input
                          type="number"
                          value={formData[sec.key]}
                          onChange={(e) => setFormData({...formData, [sec.key]: parseFloat(e.target.value) || 0})}
                          className="w-full px-2 py-1 text-center border border-input rounded bg-background text-sm"
                          min="0"
                          step="0.01"
                        />
                      </div>
                    ))}
                  </div>
                  <div className="mt-2 text-sm text-muted-foreground">
                    Total: <strong>{calcularQuantidadeTotal()}</strong>
                  </div>
                </div>

                {/* Valores e Prioridade */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Valor Unitário (R$) *</label>
                    <input
                      type="number"
                      value={formData.valorUnitario}
                      onChange={(e) => setFormData({...formData, valorUnitario: parseFloat(e.target.value) || 0})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      min="0"
                      step="0.01"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Valor Total</label>
                    <div className="px-3 py-2 bg-muted rounded-lg font-semibold text-amber-600">
                      {(calcularQuantidadeTotal() * formData.valorUnitario).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Prioridade *</label>
                    <select
                      value={formData.prioridade}
                      onChange={(e) => setFormData({...formData, prioridade: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                    >
                      <option value="ALTA">Alta</option>
                      <option value="MÉDIA">Média</option>
                      <option value="BAIXA">Baixa</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Justificativa *</label>
                  <textarea
                    value={formData.justificativa}
                    onChange={(e) => setFormData({...formData, justificativa: e.target.value})}
                    className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                    rows={2}
                    required
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-border">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 border border-input rounded-lg hover:bg-muted"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 flex items-center gap-2"
                  >
                    <Save size={16} />
                    {editingItem ? 'Salvar' : 'Adicionar'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default PACGeralObrasEditor;
