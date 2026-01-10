import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, DollarSign, Users, FileText, Plus, Trash2, Save,
  Calculator, Building2, PieChart, Upload, Download, Eye, CheckCircle, XCircle, File
} from 'lucide-react';
import Layout from '../components/Layout';
import api from '../utils/api';
import { toast } from 'sonner';

const REGIMES_CONTRATACAO = ['CLT', 'RPA', 'AUTONOMO'];

const NATUREZAS_DESPESA = {
  "319011": "Vencimentos e Vantagens Fixas",
  "319013": "Obrigações Patronais",
  "339030": "Material de Consumo",
  "339035": "Serviços de Consultoria",
  "339036": "Serviços Terceiros - PF",
  "339039": "Serviços Terceiros - PJ",
  "339046": "Auxílio-Alimentação",
  "339049": "Auxílio-Transporte",
  "449052": "Equipamentos Permanentes"
};

const TIPOS_DOCUMENTO = {
  'NOTA_FISCAL': 'Nota Fiscal',
  'RECIBO': 'Recibo',
  'CONTRATO': 'Contrato',
  'COMPROVANTE': 'Comprovante',
  'OUTRO': 'Outro'
};

const PrestacaoContasEditor = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [projeto, setProjeto] = useState(null);
  const [rhs, setRhs] = useState([]);
  const [despesas, setDespesas] = useState([]);
  const [documentos, setDocumentos] = useState([]);
  const [resumo, setResumo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('rh');
  const [showRHModal, setShowRHModal] = useState(false);
  const [showDespesaModal, setShowDespesaModal] = useState(false);
  const [showDocumentoModal, setShowDocumentoModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const [rhForm, setRhForm] = useState({
    nome_funcao: '',
    regime_contratacao: 'CLT',
    carga_horaria_semanal: 40,
    salario_bruto: 0,
    vale_transporte: 0,
    vale_alimentacao: 0,
    numero_meses: 12,
    orcamento_1: 0,
    orcamento_2: 0,
    orcamento_3: 0,
    observacoes: ''
  });

  const [despesaForm, setDespesaForm] = useState({
    natureza_despesa: '339030',
    item_despesa: '',
    descricao: '',
    unidade: 'UN',
    quantidade: 1,
    orcamento_1: 0,
    orcamento_2: 0,
    orcamento_3: 0,
    valor_unitario: 0,
    referencia_preco_municipal: 0,
    observacoes: '',
    justificativa: ''
  });

  const [docForm, setDocForm] = useState({
    tipo_documento: 'COMPROVANTE',
    numero_documento: '',
    data_documento: new Date().toISOString().split('T')[0],
    valor: 0,
    despesa_id: '',
    observacoes: '',
    file: null
  });

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    try {
      const [projetoRes, rhRes, despesasRes, resumoRes, docsRes] = await Promise.all([
        api.get(`/mrosc/projetos/${id}`),
        api.get(`/mrosc/projetos/${id}/rh`),
        api.get(`/mrosc/projetos/${id}/despesas`),
        api.get(`/mrosc/projetos/${id}/resumo`),
        api.get(`/mrosc/projetos/${id}/documentos`)
      ]);
      setProjeto(projetoRes.data);
      setRhs(rhRes.data);
      setDespesas(despesasRes.data);
      setResumo(resumoRes.data);
      setDocumentos(docsRes.data);
    } catch (error) {
      toast.error('Projeto não encontrado');
      navigate('/prestacao-contas');
    } finally {
      setLoading(false);
    }
  };

  const handleAddRH = async (e) => {
    e.preventDefault();
    try {
      await api.post(`/mrosc/projetos/${id}/rh`, rhForm);
      toast.success('Recurso humano adicionado com cálculos CLT!');
      setShowRHModal(false);
      setRhForm({
        nome_funcao: '',
        regime_contratacao: 'CLT',
        carga_horaria_semanal: 40,
        salario_bruto: 0,
        vale_transporte: 0,
        vale_alimentacao: 0,
        numero_meses: 12,
        orcamento_1: 0,
        orcamento_2: 0,
        orcamento_3: 0,
        observacoes: ''
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao adicionar RH');
    }
  };

  const handleDeleteRH = async (rh) => {
    if (!window.confirm(`Excluir "${rh.nome_funcao}"?`)) return;
    try {
      await api.delete(`/mrosc/projetos/${id}/rh/${rh.rh_id}`);
      toast.success('Recurso humano excluído!');
      fetchData();
    } catch (error) {
      toast.error('Erro ao excluir');
    }
  };

  const handleAddDespesa = async (e) => {
    e.preventDefault();
    try {
      await api.post(`/mrosc/projetos/${id}/despesas`, despesaForm);
      toast.success('Despesa adicionada!');
      setShowDespesaModal(false);
      setDespesaForm({
        natureza_despesa: '339030',
        item_despesa: '',
        descricao: '',
        unidade: 'UN',
        quantidade: 1,
        orcamento_1: 0,
        orcamento_2: 0,
        orcamento_3: 0,
        valor_unitario: 0,
        referencia_preco_municipal: 0,
        observacoes: '',
        justificativa: ''
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao adicionar despesa');
    }
  };

  const handleDeleteDespesa = async (despesa) => {
    if (!window.confirm(`Excluir despesa "${despesa.descricao}"?`)) return;
    try {
      await api.delete(`/mrosc/projetos/${id}/despesas/${despesa.despesa_id}`);
      toast.success('Despesa excluída!');
      fetchData();
    } catch (error) {
      toast.error('Erro ao excluir');
    }
  };

  // ===== FUNÇÕES DE DOCUMENTOS =====
  const handleUploadDocumento = async (e) => {
    e.preventDefault();
    if (!docForm.file) {
      toast.error('Selecione um arquivo PDF');
      return;
    }
    
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', docForm.file);
      formData.append('tipo_documento', docForm.tipo_documento);
      formData.append('numero_documento', docForm.numero_documento);
      formData.append('data_documento', new Date(docForm.data_documento).toISOString());
      formData.append('valor', docForm.valor);
      formData.append('despesa_id', docForm.despesa_id || '');
      formData.append('observacoes', docForm.observacoes || '');

      await api.post(`/mrosc/projetos/${id}/documentos/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      toast.success('Documento enviado com sucesso!');
      setShowDocumentoModal(false);
      setDocForm({
        tipo_documento: 'COMPROVANTE',
        numero_documento: '',
        data_documento: new Date().toISOString().split('T')[0],
        valor: 0,
        despesa_id: '',
        observacoes: '',
        file: null
      });
      if (fileInputRef.current) fileInputRef.current.value = '';
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao enviar documento');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocumento = async (doc) => {
    if (!window.confirm(`Excluir documento "${doc.arquivo_nome}"?`)) return;
    try {
      await api.delete(`/mrosc/projetos/${id}/documentos/${doc.documento_id}`);
      toast.success('Documento excluído!');
      fetchData();
    } catch (error) {
      toast.error('Erro ao excluir documento');
    }
  };

  const handleValidarDocumento = async (doc) => {
    try {
      await api.put(`/mrosc/projetos/${id}/documentos/${doc.documento_id}/validar`);
      toast.success('Documento validado!');
      fetchData();
    } catch (error) {
      toast.error('Erro ao validar documento');
    }
  };

  const handleViewDocumento = (doc) => {
    const backendUrl = process.env.REACT_APP_BACKEND_URL;
    window.open(`${backendUrl}${doc.arquivo_url}`, '_blank');
  };

  const formatCurrency = (value) => {
    return (value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('pt-BR');
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
        </div>
      </Layout>
    );
  }


  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/prestacao-contas')} className="p-2 hover:bg-muted rounded-lg">
            <ArrowLeft size={20} />
          </button>
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
              <DollarSign className="text-green-600" />
              {projeto?.nome_projeto}
            </h1>
            <p className="text-muted-foreground text-sm">{projeto?.organizacao_parceira}</p>
          </div>
        </div>

        {/* Resumo Orçamentário */}
        {resumo && (
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="bg-card border border-border rounded-xl p-4">
              <div className="text-sm text-muted-foreground">Valor Total Projeto</div>
              <div className="text-xl font-bold text-foreground">{formatCurrency(projeto?.valor_total)}</div>
            </div>
            <div className="bg-card border border-border rounded-xl p-4">
              <div className="text-sm text-muted-foreground">Total RH</div>
              <div className="text-xl font-bold text-blue-600">{formatCurrency(resumo.resumo?.total_recursos_humanos)}</div>
              <div className="text-xs text-muted-foreground">{resumo.resumo?.quantidade_rh} pessoas</div>
            </div>
            <div className="bg-card border border-border rounded-xl p-4">
              <div className="text-sm text-muted-foreground">Total Despesas</div>
              <div className="text-xl font-bold text-amber-600">{formatCurrency(resumo.resumo?.total_despesas)}</div>
              <div className="text-xs text-muted-foreground">{resumo.resumo?.quantidade_despesas} itens</div>
            </div>
            <div className="bg-card border border-border rounded-xl p-4">
              <div className="text-sm text-muted-foreground">Total Geral</div>
              <div className="text-xl font-bold text-green-600">{formatCurrency(resumo.resumo?.total_geral)}</div>
            </div>
            <div className={`bg-card border rounded-xl p-4 ${resumo.diferenca_orcamento >= 0 ? 'border-green-500' : 'border-red-500'}`}>
              <div className="text-sm text-muted-foreground">Saldo</div>
              <div className={`text-xl font-bold ${resumo.diferenca_orcamento >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(resumo.diferenca_orcamento)}
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 border-b border-border">
          <button
            onClick={() => setActiveTab('rh')}
            className={`px-4 py-2 font-medium text-sm transition-colors ${
              activeTab === 'rh' 
                ? 'text-green-600 border-b-2 border-green-600' 
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <Users size={16} className="inline mr-2" />
            Recursos Humanos ({rhs.length})
          </button>
          <button
            onClick={() => setActiveTab('despesas')}
            className={`px-4 py-2 font-medium text-sm transition-colors ${
              activeTab === 'despesas' 
                ? 'text-green-600 border-b-2 border-green-600' 
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <FileText size={16} className="inline mr-2" />
            Despesas ({despesas.length})
          </button>
          <button
            onClick={() => setActiveTab('documentos')}
            className={`px-4 py-2 font-medium text-sm transition-colors ${
              activeTab === 'documentos' 
                ? 'text-green-600 border-b-2 border-green-600' 
                : 'text-muted-foreground hover:text-foreground'
            }`}
            data-testid="tab-documentos"
          >
            <Upload size={16} className="inline mr-2" />
            Documentos ({documentos.length})
          </button>
        </div>

        {/* Tab Content - Recursos Humanos */}
        {activeTab === 'rh' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold">Recursos Humanos</h2>
              <button
                onClick={() => setShowRHModal(true)}
                className="flex items-center gap-2 bg-blue-600 text-white px-3 py-2 rounded-lg hover:bg-blue-700 text-sm"
              >
                <Plus size={16} /> Adicionar RH
              </button>
            </div>

            {rhs.length === 0 ? (
              <div className="bg-card border border-border rounded-xl p-8 text-center">
                <Users size={40} className="mx-auto mb-3 text-muted-foreground opacity-50" />
                <p className="text-muted-foreground">Nenhum recurso humano cadastrado</p>
              </div>
            ) : (
              <div className="space-y-3">
                {rhs.map((rh) => (
                  <div key={rh.rh_id} className="bg-card border border-border rounded-xl p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-semibold text-foreground">{rh.nome_funcao}</h3>
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          rh.regime_contratacao === 'CLT' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'
                        }`}>
                          {rh.regime_contratacao} • {rh.carga_horaria_semanal}h/sem • {rh.numero_meses} meses
                        </span>
                      </div>
                      <button
                        onClick={() => handleDeleteRH(rh)}
                        className="p-1 text-destructive hover:bg-destructive/10 rounded"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 text-sm">
                      <div>
                        <span className="text-muted-foreground block">Salário</span>
                        <span className="font-medium">{formatCurrency(rh.salario_bruto)}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground block">Férias 1/12</span>
                        <span className="font-medium">{formatCurrency(rh.provisao_ferias)}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground block">13º 1/12</span>
                        <span className="font-medium">{formatCurrency(rh.provisao_13_salario)}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground block">FGTS 8%</span>
                        <span className="font-medium">{formatCurrency(rh.fgts)}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground block">INSS 20%</span>
                        <span className="font-medium">{formatCurrency(rh.inss_patronal)}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground block">Custo/Mês</span>
                        <span className="font-semibold text-blue-600">{formatCurrency(rh.custo_mensal_total)}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground block">Total Projeto</span>
                        <span className="font-bold text-green-600">{formatCurrency(rh.custo_total_projeto)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab Content - Despesas */}
        {activeTab === 'despesas' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold">Despesas</h2>
              <button
                onClick={() => setShowDespesaModal(true)}
                className="flex items-center gap-2 bg-amber-600 text-white px-3 py-2 rounded-lg hover:bg-amber-700 text-sm"
              >
                <Plus size={16} /> Adicionar Despesa
              </button>
            </div>

            {despesas.length === 0 ? (
              <div className="bg-card border border-border rounded-xl p-8 text-center">
                <FileText size={40} className="mx-auto mb-3 text-muted-foreground opacity-50" />
                <p className="text-muted-foreground">Nenhuma despesa cadastrada</p>
              </div>
            ) : (
              <div className="bg-card border border-border rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-muted">
                    <tr>
                      <th className="px-3 py-2 text-left">Natureza</th>
                      <th className="px-3 py-2 text-left">Descrição</th>
                      <th className="px-3 py-2 text-center">Qtd</th>
                      <th className="px-3 py-2 text-right">Orç. 1</th>
                      <th className="px-3 py-2 text-right">Orç. 2</th>
                      <th className="px-3 py-2 text-right">Orç. 3</th>
                      <th className="px-3 py-2 text-right">Média</th>
                      <th className="px-3 py-2 text-right">Unit.</th>
                      <th className="px-3 py-2 text-right">Total</th>
                      <th className="px-3 py-2"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {despesas.map((d) => (
                      <tr key={d.despesa_id} className="border-b border-border hover:bg-muted/50">
                        <td className="px-3 py-2">
                          <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded">
                            {d.natureza_despesa}
                          </span>
                        </td>
                        <td className="px-3 py-2">{d.descricao}</td>
                        <td className="px-3 py-2 text-center">{d.quantidade} {d.unidade}</td>
                        <td className="px-3 py-2 text-right">{formatCurrency(d.orcamento_1)}</td>
                        <td className="px-3 py-2 text-right">{formatCurrency(d.orcamento_2)}</td>
                        <td className="px-3 py-2 text-right">{formatCurrency(d.orcamento_3)}</td>
                        <td className="px-3 py-2 text-right text-blue-600">{formatCurrency(d.media_orcamentos)}</td>
                        <td className="px-3 py-2 text-right">{formatCurrency(d.valor_unitario)}</td>
                        <td className="px-3 py-2 text-right font-semibold text-green-600">{formatCurrency(d.valor_total)}</td>
                        <td className="px-3 py-2">
                          <button
                            onClick={() => handleDeleteDespesa(d)}
                            className="p-1 text-destructive hover:bg-destructive/10 rounded"
                          >
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Tab Content - Documentos */}
        {activeTab === 'documentos' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold">Comprovantes e Documentos</h2>
              <button
                onClick={() => setShowDocumentoModal(true)}
                className="flex items-center gap-2 bg-purple-600 text-white px-3 py-2 rounded-lg hover:bg-purple-700 text-sm"
                data-testid="upload-documento-btn"
              >
                <Upload size={16} /> Enviar Documento
              </button>
            </div>

            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 text-sm">
              <p className="text-purple-800">
                <strong>Lei 13.019/2014 (MROSC):</strong> Todos os comprovantes de despesas devem ser anexados para prestação de contas.
                Apenas arquivos PDF são aceitos. Limite: 10MB por arquivo.
              </p>
            </div>

            {documentos.length === 0 ? (
              <div className="bg-card border border-border rounded-xl p-8 text-center">
                <File size={40} className="mx-auto mb-3 text-muted-foreground opacity-50" />
                <p className="text-muted-foreground">Nenhum documento anexado</p>
                <button
                  onClick={() => setShowDocumentoModal(true)}
                  className="mt-3 text-purple-600 hover:text-purple-700 font-medium text-sm"
                >
                  Enviar primeiro documento
                </button>
              </div>
            ) : (
              <div className="bg-card border border-border rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-muted">
                    <tr>
                      <th className="px-3 py-2 text-left">Tipo</th>
                      <th className="px-3 py-2 text-left">Arquivo</th>
                      <th className="px-3 py-2 text-left">Número</th>
                      <th className="px-3 py-2 text-center">Data</th>
                      <th className="px-3 py-2 text-right">Valor</th>
                      <th className="px-3 py-2 text-center">Tamanho</th>
                      <th className="px-3 py-2 text-center">Status</th>
                      <th className="px-3 py-2 text-center">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {documentos.map((doc) => (
                      <tr key={doc.documento_id} className="border-b border-border hover:bg-muted/50">
                        <td className="px-3 py-2">
                          <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                            {TIPOS_DOCUMENTO[doc.tipo_documento] || doc.tipo_documento}
                          </span>
                        </td>
                        <td className="px-3 py-2">
                          <div className="flex items-center gap-2">
                            <FileText size={14} className="text-red-500" />
                            <span className="truncate max-w-[200px]" title={doc.arquivo_nome}>
                              {doc.arquivo_nome}
                            </span>
                          </div>
                        </td>
                        <td className="px-3 py-2">{doc.numero_documento || '-'}</td>
                        <td className="px-3 py-2 text-center">{formatDate(doc.data_documento)}</td>
                        <td className="px-3 py-2 text-right font-medium text-green-600">
                          {formatCurrency(doc.valor)}
                        </td>
                        <td className="px-3 py-2 text-center text-muted-foreground">
                          {formatFileSize(doc.arquivo_tamanho)}
                        </td>
                        <td className="px-3 py-2 text-center">
                          {doc.validado ? (
                            <span className="inline-flex items-center gap-1 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                              <CheckCircle size={12} /> Validado
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded">
                              <XCircle size={12} /> Pendente
                            </span>
                          )}
                        </td>
                        <td className="px-3 py-2">
                          <div className="flex items-center justify-center gap-1">
                            <button
                              onClick={() => handleViewDocumento(doc)}
                              className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                              title="Visualizar"
                            >
                              <Eye size={14} />
                            </button>
                            <button
                              onClick={() => handleViewDocumento(doc)}
                              className="p-1 text-green-600 hover:bg-green-50 rounded"
                              title="Download"
                            >
                              <Download size={14} />
                            </button>
                            {!doc.validado && (
                              <button
                                onClick={() => handleValidarDocumento(doc)}
                                className="p-1 text-amber-600 hover:bg-amber-50 rounded"
                                title="Validar"
                              >
                                <CheckCircle size={14} />
                              </button>
                            )}
                            <button
                              onClick={() => handleDeleteDocumento(doc)}
                              className="p-1 text-destructive hover:bg-destructive/10 rounded"
                              title="Excluir"
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
            )}

            {/* Resumo de documentos */}
            {documentos.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                <div className="bg-card border border-border rounded-xl p-4">
                  <div className="text-sm text-muted-foreground">Total Documentos</div>
                  <div className="text-2xl font-bold text-foreground">{documentos.length}</div>
                </div>
                <div className="bg-card border border-border rounded-xl p-4">
                  <div className="text-sm text-muted-foreground">Validados</div>
                  <div className="text-2xl font-bold text-green-600">
                    {documentos.filter(d => d.validado).length}
                  </div>
                </div>
                <div className="bg-card border border-border rounded-xl p-4">
                  <div className="text-sm text-muted-foreground">Valor Total Comprovado</div>
                  <div className="text-2xl font-bold text-purple-600">
                    {formatCurrency(documentos.reduce((sum, d) => sum + (d.valor || 0), 0))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Modal RH */}
        {showRHModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-card border-b border-border px-6 py-4">
                <h3 className="text-xl font-bold text-foreground flex items-center gap-2">
                  <Calculator className="text-blue-600" />
                  Adicionar Recurso Humano
                </h3>
                <p className="text-sm text-muted-foreground">Encargos CLT calculados automaticamente</p>
              </div>

              <form onSubmit={handleAddRH} className="p-6 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Função *</label>
                    <input
                      type="text"
                      value={rhForm.nome_funcao}
                      onChange={(e) => setRhForm({...rhForm, nome_funcao: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      placeholder="Ex: Coordenador de Projeto"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Regime de Contratação *</label>
                    <select
                      value={rhForm.regime_contratacao}
                      onChange={(e) => setRhForm({...rhForm, regime_contratacao: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                    >
                      {REGIMES_CONTRATACAO.map(r => (
                        <option key={r} value={r}>{r}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Carga Horária Semanal *</label>
                    <input
                      type="number"
                      value={rhForm.carga_horaria_semanal}
                      onChange={(e) => setRhForm({...rhForm, carga_horaria_semanal: parseInt(e.target.value) || 0})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Salário Bruto (R$) *</label>
                    <input
                      type="number"
                      value={rhForm.salario_bruto}
                      onChange={(e) => setRhForm({...rhForm, salario_bruto: parseFloat(e.target.value) || 0})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      min="0"
                      step="0.01"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Número de Meses *</label>
                    <input
                      type="number"
                      value={rhForm.numero_meses}
                      onChange={(e) => setRhForm({...rhForm, numero_meses: parseInt(e.target.value) || 0})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      min="1"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Vale Transporte (R$)</label>
                    <input
                      type="number"
                      value={rhForm.vale_transporte}
                      onChange={(e) => setRhForm({...rhForm, vale_transporte: parseFloat(e.target.value) || 0})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      min="0"
                      step="0.01"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Vale Alimentação (R$)</label>
                    <input
                      type="number"
                      value={rhForm.vale_alimentacao}
                      onChange={(e) => setRhForm({...rhForm, vale_alimentacao: parseFloat(e.target.value) || 0})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      min="0"
                      step="0.01"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Observações</label>
                  <textarea
                    value={rhForm.observacoes}
                    onChange={(e) => setRhForm({...rhForm, observacoes: e.target.value})}
                    className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                    rows={2}
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-border">
                  <button type="button" onClick={() => setShowRHModal(false)} className="px-4 py-2 border border-input rounded-lg hover:bg-muted">
                    Cancelar
                  </button>
                  <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
                    <Save size={16} /> Adicionar com Cálculos CLT
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal Despesa */}
        {showDespesaModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card rounded-xl shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-card border-b border-border px-6 py-4">
                <h3 className="text-xl font-bold text-foreground">Adicionar Despesa</h3>
                <p className="text-sm text-muted-foreground">Informe 3 orçamentos para cálculo da média</p>
              </div>

              <form onSubmit={handleAddDespesa} className="p-6 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Natureza de Despesa *</label>
                    <select
                      value={despesaForm.natureza_despesa}
                      onChange={(e) => setDespesaForm({...despesaForm, natureza_despesa: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                    >
                      {Object.entries(NATUREZAS_DESPESA).map(([codigo, nome]) => (
                        <option key={codigo} value={codigo}>{codigo} - {nome}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Item de Despesa *</label>
                    <input
                      type="text"
                      value={despesaForm.item_despesa}
                      onChange={(e) => setDespesaForm({...despesaForm, item_despesa: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      placeholder="Ex: Material de Escritório"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Descrição *</label>
                  <textarea
                    value={despesaForm.descricao}
                    onChange={(e) => setDespesaForm({...despesaForm, descricao: e.target.value})}
                    className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                    rows={2}
                    required
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Unidade *</label>
                    <select
                      value={despesaForm.unidade}
                      onChange={(e) => setDespesaForm({...despesaForm, unidade: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                    >
                      <option value="UN">Unidade</option>
                      <option value="CX">Caixa</option>
                      <option value="PCT">Pacote</option>
                      <option value="KG">Quilograma</option>
                      <option value="L">Litro</option>
                      <option value="M">Metro</option>
                      <option value="SERV">Serviço</option>
                      <option value="MÊS">Mês</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Quantidade *</label>
                    <input
                      type="number"
                      value={despesaForm.quantidade}
                      onChange={(e) => setDespesaForm({...despesaForm, quantidade: parseFloat(e.target.value) || 0})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      min="0.01"
                      step="0.01"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Valor Unitário (R$) *</label>
                    <input
                      type="number"
                      value={despesaForm.valor_unitario}
                      onChange={(e) => setDespesaForm({...despesaForm, valor_unitario: parseFloat(e.target.value) || 0})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      min="0"
                      step="0.01"
                      required
                    />
                  </div>
                </div>

                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <h4 className="font-semibold text-amber-800 mb-3">Orçamentos (mínimo 3 cotações)</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Orçamento 1 (R$) *</label>
                      <input
                        type="number"
                        value={despesaForm.orcamento_1}
                        onChange={(e) => setDespesaForm({...despesaForm, orcamento_1: parseFloat(e.target.value) || 0})}
                        className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                        min="0"
                        step="0.01"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Orçamento 2 (R$) *</label>
                      <input
                        type="number"
                        value={despesaForm.orcamento_2}
                        onChange={(e) => setDespesaForm({...despesaForm, orcamento_2: parseFloat(e.target.value) || 0})}
                        className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                        min="0"
                        step="0.01"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Orçamento 3 (R$) *</label>
                      <input
                        type="number"
                        value={despesaForm.orcamento_3}
                        onChange={(e) => setDespesaForm({...despesaForm, orcamento_3: parseFloat(e.target.value) || 0})}
                        className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                        min="0"
                        step="0.01"
                        required
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Justificativa *</label>
                  <textarea
                    value={despesaForm.justificativa}
                    onChange={(e) => setDespesaForm({...despesaForm, justificativa: e.target.value})}
                    className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                    rows={2}
                    required
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-border">
                  <button type="button" onClick={() => setShowDespesaModal(false)} className="px-4 py-2 border border-input rounded-lg hover:bg-muted">
                    Cancelar
                  </button>
                  <button type="submit" className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 flex items-center gap-2">
                    <Save size={16} /> Adicionar Despesa
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal Upload Documento */}
        {showDocumentoModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card rounded-xl shadow-xl w-full max-w-xl max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-card border-b border-border px-6 py-4">
                <h3 className="text-xl font-bold text-foreground flex items-center gap-2">
                  <Upload className="text-purple-600" />
                  Enviar Documento
                </h3>
                <p className="text-sm text-muted-foreground">Anexe comprovantes de despesas (PDF)</p>
              </div>

              <form onSubmit={handleUploadDocumento} className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Arquivo PDF *</label>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf"
                    onChange={(e) => setDocForm({...docForm, file: e.target.files[0]})}
                    className="w-full px-3 py-2 border border-input rounded-lg bg-background file:mr-4 file:py-1 file:px-3 file:rounded file:border-0 file:bg-purple-100 file:text-purple-700 file:text-sm hover:file:bg-purple-200"
                    required
                    data-testid="documento-file-input"
                  />
                  <p className="text-xs text-muted-foreground mt-1">Máximo 10MB. Apenas arquivos PDF.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Tipo de Documento *</label>
                    <select
                      value={docForm.tipo_documento}
                      onChange={(e) => setDocForm({...docForm, tipo_documento: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                    >
                      {Object.entries(TIPOS_DOCUMENTO).map(([value, label]) => (
                        <option key={value} value={value}>{label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Número do Documento</label>
                    <input
                      type="text"
                      value={docForm.numero_documento}
                      onChange={(e) => setDocForm({...docForm, numero_documento: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      placeholder="Ex: NF 12345"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Data do Documento *</label>
                    <input
                      type="date"
                      value={docForm.data_documento}
                      onChange={(e) => setDocForm({...docForm, data_documento: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Valor (R$) *</label>
                    <input
                      type="number"
                      value={docForm.valor}
                      onChange={(e) => setDocForm({...docForm, valor: parseFloat(e.target.value) || 0})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      min="0"
                      step="0.01"
                      required
                    />
                  </div>
                </div>

                {despesas.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium mb-1">Vincular a Despesa (opcional)</label>
                    <select
                      value={docForm.despesa_id}
                      onChange={(e) => setDocForm({...docForm, despesa_id: e.target.value})}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                    >
                      <option value="">-- Sem vínculo --</option>
                      {despesas.map(d => (
                        <option key={d.despesa_id} value={d.despesa_id}>
                          {d.natureza_despesa} - {d.descricao} ({formatCurrency(d.valor_total)})
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium mb-1">Observações</label>
                  <textarea
                    value={docForm.observacoes}
                    onChange={(e) => setDocForm({...docForm, observacoes: e.target.value})}
                    className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                    rows={2}
                    placeholder="Observações sobre o documento..."
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-border">
                  <button 
                    type="button" 
                    onClick={() => {
                      setShowDocumentoModal(false);
                      if (fileInputRef.current) fileInputRef.current.value = '';
                    }} 
                    className="px-4 py-2 border border-input rounded-lg hover:bg-muted"
                    disabled={uploading}
                  >
                    Cancelar
                  </button>
                  <button 
                    type="submit" 
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2 disabled:opacity-50"
                    disabled={uploading}
                    data-testid="submit-documento-btn"
                  >
                    {uploading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        Enviando...
                      </>
                    ) : (
                      <>
                        <Upload size={16} /> Enviar Documento
                      </>
                    )}
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

export default PrestacaoContasEditor;
