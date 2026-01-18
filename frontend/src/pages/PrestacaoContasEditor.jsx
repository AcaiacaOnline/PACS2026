import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, DollarSign, Users, FileText, Plus, Trash2, Save,
  Calculator, Building2, PieChart, Upload, Download, Eye, CheckCircle, XCircle, File,
  Lock, AlertTriangle, Send, Briefcase, Package, Wrench, Settings, Info, ClipboardList, FileSpreadsheet
} from 'lucide-react';
import Layout from '../components/Layout';
import api from '../utils/api';
import { toast } from 'sonner';

const REGIMES_CONTRATACAO = ['CLT', 'RPA', 'AUTONOMO', 'ESTAGIARIO', 'MENOR_APRENDIZ'];

const TIPOS_CONCEDENTE = [
  { value: 'PARLAMENTAR', label: 'Parlamentar' },
  { value: 'COMISSAO', label: 'Comissão' },
  { value: 'BANCADA', label: 'Bancada' },
  { value: 'ORGAO', label: 'Órgão Público' },
  { value: 'OUTRO', label: 'Outro' }
];

const STATUS_PROJETO = {
  'ELABORACAO': { label: 'Em Elaboração', color: 'bg-blue-100 text-blue-800', icon: FileText },
  'APROVADO': { label: 'Aprovado', color: 'bg-green-100 text-green-800', icon: CheckCircle },
  'EXECUCAO': { label: 'Em Execução', color: 'bg-purple-100 text-purple-800', icon: Settings },
  'PRESTACAO_CONTAS': { label: 'Prestação de Contas', color: 'bg-orange-100 text-orange-800', icon: ClipboardList },
  'CONCLUIDO': { label: 'Concluído', color: 'bg-gray-100 text-gray-800', icon: CheckCircle },
  'CORRECAO': { label: 'Correção Solicitada', color: 'bg-yellow-100 text-yellow-800', icon: AlertTriangle },
  'REPROVADO': { label: 'Reprovado', color: 'bg-red-100 text-red-800', icon: XCircle }
};

const CATEGORIAS_NATUREZA = {
  'RH': { label: 'Recursos Humanos', icon: Users, color: 'text-blue-600' },
  'MATERIAIS': { label: 'Materiais de Consumo', icon: Package, color: 'text-green-600' },
  'SERVICOS': { label: 'Serviços', icon: Wrench, color: 'text-purple-600' },
  'BENEFICIOS': { label: 'Benefícios', icon: DollarSign, color: 'text-orange-600' },
  'TRIBUTOS': { label: 'Tributos', icon: Building2, color: 'text-red-600' },
  'INVESTIMENTOS': { label: 'Investimentos', icon: Briefcase, color: 'text-indigo-600' },
  'VIAGENS': { label: 'Viagens', icon: FileText, color: 'text-teal-600' },
  'PREMIACOES': { label: 'Premiações', icon: FileText, color: 'text-pink-600' }
};

const TIPOS_DOCUMENTO = {
  'NOTA_FISCAL': 'Nota Fiscal',
  'CUPOM_FISCAL': 'Cupom Fiscal',
  'RECIBO': 'Recibo',
  'CONTRATO': 'Contrato',
  'FOLHA_PAGAMENTO': 'Folha de Pagamento',
  'GUIA_INSS': 'Guia INSS',
  'GUIA_FGTS': 'Guia FGTS',
  'COMPROVANTE_TRANSFERENCIA': 'Comprovante de Transferência',
  'EXTRATO_BANCARIO': 'Extrato Bancário',
  'RELATORIO_EXECUCAO': 'Relatório de Execução',
  'TERMO_ACEITE': 'Termo de Aceite',
  'PLANO_TRABALHO': 'Plano de Trabalho',
  'CERTIDAO_NEGATIVA': 'Certidão Negativa',
  'FOTO_COMPROVACAO': 'Foto de Comprovação',
  'ORCAMENTO': 'Orçamento/Cotação',
  'ATA_REGISTRO_PRECO': 'Ata de Registro de Preço',
  'IMAGEM': 'Imagem/Foto',
  'COMPROVANTE': 'Comprovante',
  'OUTRO': 'Outro'
};

const PrestacaoContasEditor = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  
  // Estado principal
  const [projeto, setProjeto] = useState(null);
  const [user, setUser] = useState(null);
  const [naturezasDespesa, setNaturezasDespesa] = useState({});
  const [rhs, setRhs] = useState([]);
  const [despesas, setDespesas] = useState([]);
  const [documentos, setDocumentos] = useState([]);
  const [resumo, setResumo] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Abas: orcamentacao, rh, despesas, documentos, resumo
  const [activeTab, setActiveTab] = useState('orcamentacao');
  const [activeCategoria, setActiveCategoria] = useState('MATERIAIS');
  
  // Modais
  const [showRHModal, setShowRHModal] = useState(false);
  const [showDespesaModal, setShowDespesaModal] = useState(false);
  const [showDocumentoModal, setShowDocumentoModal] = useState(false);
  const [showProjetoModal, setShowProjetoModal] = useState(false);
  const [showAssinaturaModal, setShowAssinaturaModal] = useState(false);
  const [tipoAssinatura, setTipoAssinatura] = useState('pdf'); // 'pdf' ou 'consolidado'
  const [dataAssinatura, setDataAssinatura] = useState('');
  const [uploading, setUploading] = useState(false);
  
  // Formulários
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
  
  const [documentoForm, setDocumentoForm] = useState({
    tipo_documento: 'NOTA_FISCAL',
    numero_documento: '',
    data_documento: '',
    valor: 0,
    despesa_id: '',
    observacoes: '',
    file: null
  });

  // Carregar dados
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [projetoRes, naturezasRes, rhsRes, despesasRes, docsRes, resumoRes, userRes] = await Promise.all([
          api.get(`/mrosc/projetos/${id}`),
          api.get('/mrosc/naturezas-despesa'),
          api.get(`/mrosc/projetos/${id}/rh`),
          api.get(`/mrosc/projetos/${id}/despesas`),
          api.get(`/mrosc/projetos/${id}/documentos`),
          api.get(`/mrosc/projetos/${id}/resumo`),
          api.get('/auth/me')
        ]);
        
        setProjeto(projetoRes.data);
        setNaturezasDespesa(naturezasRes.data || {});
        setRhs(rhsRes.data || []);
        setDespesas(despesasRes.data || []);
        setDocumentos(docsRes.data || []);
        setResumo(resumoRes.data);
        setUser(userRes.data);
      } catch (error) {
        console.error('Erro ao carregar dados:', error);
        if (error.response?.status === 404) {
          toast.error('Projeto não encontrado');
          navigate('/prestacao-contas');
        } else {
          toast.error('Erro ao carregar dados do projeto');
        }
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [id, navigate]);

  // Calcular encargos CLT
  const calcularEncargosCLT = (salario) => {
    const ferias = (salario / 12) + (salario / 12 / 3); // salário/12 + 1/3 de férias/12
    const decimoTerceiro = salario / 12;
    const fgts = salario * 0.08;
    const inssPatronal = salario * 0.20;
    const fgtsDemissao = fgts * 0.50;
    
    return {
      provisao_ferias: ferias,
      provisao_13_salario: decimoTerceiro,
      fgts: fgts,
      inss_patronal: inssPatronal,
      fgts_demissao: fgtsDemissao,
      total_encargos: ferias + decimoTerceiro + fgts + inssPatronal
    };
  };
  
  // Calcular média de orçamentos
  const calcularMediaOrcamentos = (orc1, orc2, orc3) => {
    const valores = [orc1, orc2, orc3].filter(v => v > 0);
    if (valores.length === 0) return 0;
    return valores.reduce((a, b) => a + b, 0) / valores.length;
  };

  // Adicionar RH
  const handleAddRH = async () => {
    try {
      const response = await api.post(`/mrosc/projetos/${id}/rh`, rhForm);
      setRhs([...rhs, response.data]);
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
      toast.success('Recurso Humano adicionado com sucesso!');
      
      // Atualizar resumo
      const resumoRes = await api.get(`/mrosc/projetos/${id}/resumo`);
      setResumo(resumoRes.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao adicionar RH');
    }
  };

  // Excluir RH
  const handleDeleteRH = async (rhId) => {
    if (!window.confirm('Deseja excluir este recurso humano?')) return;
    
    try {
      await api.delete(`/mrosc/projetos/${id}/rh/${rhId}`);
      setRhs(rhs.filter(r => r.rh_id !== rhId));
      toast.success('Recurso Humano removido!');
      
      const resumoRes = await api.get(`/mrosc/projetos/${id}/resumo`);
      setResumo(resumoRes.data);
    } catch (error) {
      toast.error('Erro ao remover RH');
    }
  };

  // Adicionar Despesa
  const handleAddDespesa = async () => {
    try {
      const media = calcularMediaOrcamentos(
        despesaForm.orcamento_1,
        despesaForm.orcamento_2,
        despesaForm.orcamento_3
      );
      
      const response = await api.post(`/mrosc/projetos/${id}/despesas`, {
        ...despesaForm,
        valor_unitario: despesaForm.valor_unitario || media
      });
      
      setDespesas([...despesas, response.data]);
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
      toast.success('Despesa adicionada com sucesso!');
      
      const resumoRes = await api.get(`/mrosc/projetos/${id}/resumo`);
      setResumo(resumoRes.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao adicionar despesa');
    }
  };

  // Excluir Despesa
  const handleDeleteDespesa = async (despesaId) => {
    if (!window.confirm('Deseja excluir esta despesa?')) return;
    
    try {
      await api.delete(`/mrosc/projetos/${id}/despesas/${despesaId}`);
      setDespesas(despesas.filter(d => d.despesa_id !== despesaId));
      toast.success('Despesa removida!');
      
      const resumoRes = await api.get(`/mrosc/projetos/${id}/resumo`);
      setResumo(resumoRes.data);
    } catch (error) {
      toast.error('Erro ao remover despesa');
    }
  };

  // Upload Documento
  const handleUploadDocumento = async () => {
    if (!documentoForm.file) {
      toast.error('Selecione um arquivo');
      return;
    }
    
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', documentoForm.file);
      formData.append('tipo_documento', documentoForm.tipo_documento);
      formData.append('numero_documento', documentoForm.numero_documento);
      formData.append('data_documento', documentoForm.data_documento);
      formData.append('valor', documentoForm.valor.toString());
      formData.append('despesa_id', documentoForm.despesa_id);
      formData.append('observacoes', documentoForm.observacoes);
      
      const response = await api.post(`/mrosc/projetos/${id}/documentos/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setDocumentos([...documentos, response.data]);
      setShowDocumentoModal(false);
      setDocumentoForm({
        tipo_documento: 'NOTA_FISCAL',
        numero_documento: '',
        data_documento: '',
        valor: 0,
        despesa_id: '',
        observacoes: '',
        file: null
      });
      toast.success('Documento enviado com sucesso!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao enviar documento');
    } finally {
      setUploading(false);
    }
  };

  // Excluir Documento
  const handleDeleteDocumento = async (docId) => {
    if (!window.confirm('Deseja excluir este documento?')) return;
    
    try {
      await api.delete(`/mrosc/projetos/${id}/documentos/${docId}`);
      setDocumentos(documentos.filter(d => d.documento_id !== docId));
      toast.success('Documento removido!');
    } catch (error) {
      toast.error('Erro ao remover documento');
    }
  };

  // Atualizar projeto
  const handleUpdateProjeto = async (data) => {
    try {
      const response = await api.put(`/mrosc/projetos/${id}`, data);
      setProjeto(response.data);
      setShowProjetoModal(false);
      toast.success('Projeto atualizado!');
    } catch (error) {
      toast.error('Erro ao atualizar projeto');
    }
  };

  // Download PDF
  const handleDownloadPDF = async () => {
    try {
      const response = await api.get(`/mrosc/projetos/${id}/relatorio/pdf`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Prestacao_Contas_${projeto.nome_projeto.replace(/\s+/g, '_')}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('PDF gerado com sucesso!');
    } catch (error) {
      toast.error('Erro ao gerar PDF');
    }
  };

  // Download PDF Consolidado
  const handleDownloadPDFConsolidado = async () => {
    try {
      const response = await api.get(`/mrosc/projetos/${id}/relatorio/consolidado/pdf`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `MROSC_Consolidado_${projeto.nome_projeto.replace(/\s+/g, '_')}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('PDF Consolidado gerado com sucesso!');
    } catch (error) {
      toast.error('Erro ao gerar PDF Consolidado');
    }
  };

  // Formatar moeda
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value || 0);
  };

  // Agrupar despesas por categoria
  const getDespesasPorCategoria = (categoria) => {
    return despesas.filter(d => {
      const nat = naturezasDespesa[d.natureza_despesa];
      return nat && nat.categoria === categoria;
    });
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      </Layout>
    );
  }

  if (!projeto) {
    return (
      <Layout>
        <div className="p-6 text-center">
          <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold">Projeto não encontrado</h2>
          <button 
            onClick={() => navigate('/prestacao-contas')}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Voltar para lista
          </button>
        </div>
      </Layout>
    );
  }

  const statusConfig = STATUS_PROJETO[projeto.status] || STATUS_PROJETO['ELABORACAO'];
  const StatusIcon = statusConfig.icon;

  return (
    <Layout>
      <div className="p-6 max-w-7xl mx-auto" data-testid="prestacao-contas-editor">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/prestacao-contas')}
              className="p-2 hover:bg-gray-100 rounded-lg"
              data-testid="btn-voltar"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{projeto.nome_projeto}</h1>
              <p className="text-sm text-gray-500">{projeto.organizacao_parceira}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${statusConfig.color}`}>
              <StatusIcon className="h-4 w-4" />
              {statusConfig.label}
            </span>
            
            <button
              onClick={handleDownloadPDF}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              data-testid="btn-download-pdf"
            >
              <Download className="h-4 w-4" />
              PDF
            </button>
            
            <button
              onClick={handleDownloadPDFConsolidado}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              data-testid="btn-download-consolidado"
            >
              <FileSpreadsheet className="h-4 w-4" />
              PDF + Anexos
            </button>
          </div>
        </div>

        {/* Resumo Financeiro Compacto */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-white rounded-lg border p-4">
            <div className="text-sm text-gray-500">Valor Total Projeto</div>
            <div className="text-xl font-bold text-gray-900">{formatCurrency(projeto.valor_total)}</div>
          </div>
          <div className="bg-white rounded-lg border p-4">
            <div className="text-sm text-gray-500">Total RH</div>
            <div className="text-xl font-bold text-blue-600">{formatCurrency(resumo?.total_rh || 0)}</div>
          </div>
          <div className="bg-white rounded-lg border p-4">
            <div className="text-sm text-gray-500">Total Despesas</div>
            <div className="text-xl font-bold text-green-600">{formatCurrency(resumo?.total_despesas || 0)}</div>
          </div>
          <div className="bg-white rounded-lg border p-4">
            <div className="text-sm text-gray-500">Total Geral</div>
            <div className="text-xl font-bold text-purple-600">{formatCurrency((resumo?.total_rh || 0) + (resumo?.total_despesas || 0))}</div>
          </div>
          <div className="bg-white rounded-lg border p-4">
            <div className="text-sm text-gray-500">Saldo</div>
            <div className={`text-xl font-bold ${projeto.valor_total - ((resumo?.total_rh || 0) + (resumo?.total_despesas || 0)) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(projeto.valor_total - ((resumo?.total_rh || 0) + (resumo?.total_despesas || 0)))}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg border mb-6">
          <div className="flex border-b overflow-x-auto">
            <button
              onClick={() => setActiveTab('orcamentacao')}
              className={`flex items-center gap-2 px-6 py-3 text-sm font-medium whitespace-nowrap ${
                activeTab === 'orcamentacao' 
                  ? 'border-b-2 border-blue-600 text-blue-600' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              data-testid="tab-orcamentacao"
            >
              <FileSpreadsheet className="h-4 w-4" />
              Orçamentação
            </button>
            <button
              onClick={() => setActiveTab('rh')}
              className={`flex items-center gap-2 px-6 py-3 text-sm font-medium whitespace-nowrap ${
                activeTab === 'rh' 
                  ? 'border-b-2 border-blue-600 text-blue-600' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              data-testid="tab-rh"
            >
              <Users className="h-4 w-4" />
              Recursos Humanos ({rhs.length})
            </button>
            <button
              onClick={() => setActiveTab('despesas')}
              className={`flex items-center gap-2 px-6 py-3 text-sm font-medium whitespace-nowrap ${
                activeTab === 'despesas' 
                  ? 'border-b-2 border-blue-600 text-blue-600' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              data-testid="tab-despesas"
            >
              <Package className="h-4 w-4" />
              Despesas ({despesas.length})
            </button>
            <button
              onClick={() => setActiveTab('documentos')}
              className={`flex items-center gap-2 px-6 py-3 text-sm font-medium whitespace-nowrap ${
                activeTab === 'documentos' 
                  ? 'border-b-2 border-blue-600 text-blue-600' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              data-testid="tab-documentos"
            >
              <FileText className="h-4 w-4" />
              Documentos ({documentos.length})
            </button>
            <button
              onClick={() => setActiveTab('resumo')}
              className={`flex items-center gap-2 px-6 py-3 text-sm font-medium whitespace-nowrap ${
                activeTab === 'resumo' 
                  ? 'border-b-2 border-blue-600 text-blue-600' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              data-testid="tab-resumo"
            >
              <PieChart className="h-4 w-4" />
              Resumo
            </button>
          </div>

          {/* Tab Content - Orçamentação */}
          {activeTab === 'orcamentacao' && (
            <div className="p-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Dados do Projeto */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                      <Building2 className="h-5 w-5 text-blue-600" />
                      Dados do Projeto
                    </h3>
                    <button
                      onClick={() => setShowProjetoModal(true)}
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      Editar
                    </button>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div><span className="text-gray-500">OSC:</span> <span className="font-medium">{projeto.organizacao_parceira}</span></div>
                    <div><span className="text-gray-500">CNPJ:</span> <span className="font-medium">{projeto.cnpj_parceira}</span></div>
                    <div><span className="text-gray-500">Responsável:</span> <span className="font-medium">{projeto.responsavel_osc}</span></div>
                    <div><span className="text-gray-500">Objeto:</span> <span className="font-medium">{projeto.objeto}</span></div>
                    <div><span className="text-gray-500">Período:</span> <span className="font-medium">
                      {new Date(projeto.data_inicio).toLocaleDateString('pt-BR')} a {new Date(projeto.data_conclusao).toLocaleDateString('pt-BR')} ({projeto.prazo_meses} meses)
                    </span></div>
                  </div>
                </div>

                {/* Dados do Concedente (MPC 01/2025) */}
                <div className="bg-blue-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 flex items-center gap-2 mb-4">
                    <Info className="h-5 w-5 text-blue-600" />
                    Dados do Concedente (Rec. MPC 01/2025)
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div><span className="text-gray-500">Tipo:</span> <span className="font-medium">{projeto.tipo_concedente || 'Não informado'}</span></div>
                    <div><span className="text-gray-500">Concedente:</span> <span className="font-medium">{projeto.nome_concedente || 'Não informado'}</span></div>
                    <div><span className="text-gray-500">Nº Emenda:</span> <span className="font-medium">{projeto.numero_emenda || 'N/A'}</span></div>
                    <div><span className="text-gray-500">Nº Termo:</span> <span className="font-medium">{projeto.numero_termo || 'N/A'}</span></div>
                  </div>
                </div>

                {/* Gestor Responsável */}
                <div className="bg-green-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 flex items-center gap-2 mb-4">
                    <Users className="h-5 w-5 text-green-600" />
                    Gestor Responsável
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div><span className="text-gray-500">Nome:</span> <span className="font-medium">{projeto.gestor_responsavel_nome || 'Não informado'}</span></div>
                    <div><span className="text-gray-500">CPF:</span> <span className="font-medium">{projeto.gestor_responsavel_cpf || 'Não informado'}</span></div>
                    <div><span className="text-gray-500">Cargo:</span> <span className="font-medium">{projeto.gestor_responsavel_cargo || 'Não informado'}</span></div>
                  </div>
                </div>

                {/* Conta Bancária */}
                <div className="bg-yellow-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 flex items-center gap-2 mb-4">
                    <DollarSign className="h-5 w-5 text-yellow-600" />
                    Conta Bancária Específica
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div><span className="text-gray-500">Banco:</span> <span className="font-medium">{projeto.banco_nome || 'Não informado'}</span></div>
                    <div><span className="text-gray-500">Agência:</span> <span className="font-medium">{projeto.banco_agencia || 'Não informado'}</span></div>
                    <div><span className="text-gray-500">Conta:</span> <span className="font-medium">{projeto.banco_conta || 'Não informado'}</span></div>
                  </div>
                </div>
              </div>

              {/* Valores do Projeto */}
              <div className="mt-6 bg-purple-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 flex items-center gap-2 mb-4">
                  <Calculator className="h-5 w-5 text-purple-600" />
                  Valores do Projeto
                </h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-3 bg-white rounded-lg">
                    <div className="text-sm text-gray-500">Repasse Público</div>
                    <div className="text-lg font-bold text-blue-600">{formatCurrency(projeto.valor_repasse_publico)}</div>
                  </div>
                  <div className="text-center p-3 bg-white rounded-lg">
                    <div className="text-sm text-gray-500">Contrapartida</div>
                    <div className="text-lg font-bold text-green-600">{formatCurrency(projeto.valor_contrapartida)}</div>
                  </div>
                  <div className="text-center p-3 bg-white rounded-lg">
                    <div className="text-sm text-gray-500">Valor Total</div>
                    <div className="text-lg font-bold text-purple-600">{formatCurrency(projeto.valor_total)}</div>
                  </div>
                </div>
              </div>

              {/* Instruções */}
              <div className="mt-6 p-4 bg-gray-100 rounded-lg text-sm text-gray-600">
                <p className="font-medium mb-2">📋 Instruções para Orçamentação (Modelo SUCC/BH):</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Preencha os dados do projeto e concedente conforme Recomendação MPC 01/2025</li>
                  <li>Na aba <strong>Recursos Humanos</strong>, cadastre cada profissional com regime de contratação</li>
                  <li>Na aba <strong>Despesas</strong>, cadastre cada item com 3 orçamentos/cotações</li>
                  <li>Na aba <strong>Documentos</strong>, anexe comprovantes (PDF, JPG, PNG)</li>
                  <li>Use o botão <strong>PDF + Anexos</strong> para gerar o relatório consolidado final</li>
                </ul>
              </div>
            </div>
          )}

          {/* Tab Content - Recursos Humanos */}
          {activeTab === 'rh' && (
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-semibold text-gray-900">Recursos Humanos (ANEXO I)</h3>
                <button
                  onClick={() => setShowRHModal(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  data-testid="btn-add-rh"
                >
                  <Plus className="h-4 w-4" />
                  Adicionar Profissional
                </button>
              </div>

              {rhs.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Users className="h-12 w-12 mx-auto mb-4 opacity-30" />
                  <p>Nenhum recurso humano cadastrado</p>
                  <p className="text-sm">Clique em "Adicionar Profissional" para começar</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cargo/Função</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Regime</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">CH/Sem</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Salário</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Férias</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">13º</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">FGTS</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">INSS</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Custo/Mês</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Meses</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Ações</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {rhs.map((rh) => (
                        <tr key={rh.rh_id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm font-medium text-gray-900">{rh.nome_funcao}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{rh.regime_contratacao}</td>
                          <td className="px-4 py-3 text-sm text-right">{rh.carga_horaria_semanal}h</td>
                          <td className="px-4 py-3 text-sm text-right">{formatCurrency(rh.salario_bruto)}</td>
                          <td className="px-4 py-3 text-sm text-right">{formatCurrency(rh.provisao_ferias)}</td>
                          <td className="px-4 py-3 text-sm text-right">{formatCurrency(rh.provisao_13_salario)}</td>
                          <td className="px-4 py-3 text-sm text-right">{formatCurrency(rh.fgts)}</td>
                          <td className="px-4 py-3 text-sm text-right">{formatCurrency(rh.inss_patronal)}</td>
                          <td className="px-4 py-3 text-sm text-right font-medium text-blue-600">{formatCurrency(rh.custo_mensal_total)}</td>
                          <td className="px-4 py-3 text-sm text-right">{rh.numero_meses}</td>
                          <td className="px-4 py-3 text-sm text-right font-bold text-green-600">{formatCurrency(rh.custo_total_projeto)}</td>
                          <td className="px-4 py-3 text-center">
                            <button
                              onClick={() => handleDeleteRH(rh.rh_id)}
                              className="p-1 text-red-600 hover:bg-red-50 rounded"
                              data-testid={`btn-delete-rh-${rh.rh_id}`}
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-blue-50">
                      <tr>
                        <td colSpan="10" className="px-4 py-3 text-sm font-bold text-right text-gray-700">TOTAL RH:</td>
                        <td className="px-4 py-3 text-sm font-bold text-right text-blue-700">{formatCurrency(resumo?.total_rh || 0)}</td>
                        <td></td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              )}

              {/* Nota sobre cálculos */}
              <div className="mt-4 p-3 bg-yellow-50 rounded-lg text-sm text-yellow-800">
                <strong>Memória de Cálculo CLT:</strong> Férias = Salário/12 + 1/3 de Férias/12 | 13º = Salário/12 | FGTS = 8% | INSS Patronal = 20%
              </div>
            </div>
          )}

          {/* Tab Content - Despesas */}
          {activeTab === 'despesas' && (
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-semibold text-gray-900">Despesas por Natureza (ANEXO II e III)</h3>
                <button
                  onClick={() => setShowDespesaModal(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  data-testid="btn-add-despesa"
                >
                  <Plus className="h-4 w-4" />
                  Adicionar Despesa
                </button>
              </div>

              {/* Sub-abas de categorias */}
              <div className="flex flex-wrap gap-2 mb-4">
                {Object.entries(CATEGORIAS_NATUREZA).filter(([key]) => key !== 'RH').map(([key, cat]) => {
                  const CatIcon = cat.icon;
                  const count = getDespesasPorCategoria(key).length;
                  return (
                    <button
                      key={key}
                      onClick={() => setActiveCategoria(key)}
                      className={`flex items-center gap-1 px-3 py-1 rounded-full text-sm ${
                        activeCategoria === key 
                          ? 'bg-blue-600 text-white' 
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      <CatIcon className="h-3 w-3" />
                      {cat.label} ({count})
                    </button>
                  );
                })}
              </div>

              {/* Lista de despesas da categoria */}
              {getDespesasPorCategoria(activeCategoria).length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Package className="h-12 w-12 mx-auto mb-4 opacity-30" />
                  <p>Nenhuma despesa cadastrada nesta categoria</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Item</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Natureza</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Qtd</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Orç. 1</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Orç. 2</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Orç. 3</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Média</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Valor Unit.</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Ações</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {getDespesasPorCategoria(activeCategoria).map((desp) => (
                        <tr key={desp.despesa_id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm">
                            <div className="font-medium text-gray-900">{desp.item_despesa}</div>
                            <div className="text-xs text-gray-500">{desp.descricao}</div>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">{desp.natureza_despesa}</td>
                          <td className="px-4 py-3 text-sm text-center">{desp.quantidade} {desp.unidade}</td>
                          <td className="px-4 py-3 text-sm text-right">{formatCurrency(desp.orcamento_1)}</td>
                          <td className="px-4 py-3 text-sm text-right">{formatCurrency(desp.orcamento_2)}</td>
                          <td className="px-4 py-3 text-sm text-right">{formatCurrency(desp.orcamento_3)}</td>
                          <td className="px-4 py-3 text-sm text-right text-blue-600">{formatCurrency(desp.media_orcamentos)}</td>
                          <td className="px-4 py-3 text-sm text-right">{formatCurrency(desp.valor_unitario)}</td>
                          <td className="px-4 py-3 text-sm text-right font-bold text-green-600">{formatCurrency(desp.valor_total)}</td>
                          <td className="px-4 py-3 text-center">
                            <button
                              onClick={() => handleDeleteDespesa(desp.despesa_id)}
                              className="p-1 text-red-600 hover:bg-red-50 rounded"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Resumo por categoria */}
              <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(CATEGORIAS_NATUREZA).filter(([key]) => key !== 'RH').map(([key, cat]) => {
                  const total = getDespesasPorCategoria(key).reduce((sum, d) => sum + (d.valor_total || 0), 0);
                  const CatIcon = cat.icon;
                  return (
                    <div key={key} className="bg-gray-50 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <CatIcon className={`h-4 w-4 ${cat.color}`} />
                        <span className="text-xs text-gray-500">{cat.label}</span>
                      </div>
                      <div className="font-bold text-gray-900">{formatCurrency(total)}</div>
                    </div>
                  );
                })}
              </div>

              <div className="mt-4 p-3 bg-green-50 rounded-lg text-sm">
                <strong>Total de Despesas:</strong> {formatCurrency(resumo?.total_despesas || 0)}
              </div>
            </div>
          )}

          {/* Tab Content - Documentos */}
          {activeTab === 'documentos' && (
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-semibold text-gray-900">Documentos Comprobatórios</h3>
                <button
                  onClick={() => setShowDocumentoModal(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                  data-testid="btn-add-documento"
                >
                  <Upload className="h-4 w-4" />
                  Anexar Documento
                </button>
              </div>

              {documentos.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <FileText className="h-12 w-12 mx-auto mb-4 opacity-30" />
                  <p>Nenhum documento anexado</p>
                  <p className="text-sm">Anexe notas fiscais, recibos, comprovantes, etc.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {documentos.map((doc) => (
                    <div key={doc.documento_id} className="bg-gray-50 rounded-lg p-4 border">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <File className="h-5 w-5 text-blue-600" />
                          <span className="font-medium text-sm">{TIPOS_DOCUMENTO[doc.tipo_documento] || doc.tipo_documento}</span>
                        </div>
                        {doc.validado && <CheckCircle className="h-4 w-4 text-green-500" />}
                      </div>
                      <div className="text-xs text-gray-500 space-y-1">
                        {doc.numero_documento && <div>Nº: {doc.numero_documento}</div>}
                        {doc.data_documento && <div>Data: {new Date(doc.data_documento).toLocaleDateString('pt-BR')}</div>}
                        {doc.valor > 0 && <div>Valor: {formatCurrency(doc.valor)}</div>}
                      </div>
                      <div className="flex gap-2 mt-3">
                        {doc.arquivo_url && (
                          <a
                            href={doc.arquivo_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                          >
                            <Eye className="h-3 w-3" /> Ver
                          </a>
                        )}
                        <button
                          onClick={() => handleDeleteDocumento(doc.documento_id)}
                          className="flex items-center gap-1 px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
                        >
                          <Trash2 className="h-3 w-3" /> Excluir
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="mt-4 p-3 bg-blue-50 rounded-lg text-sm text-blue-800">
                <strong>Formatos aceitos:</strong> PDF, JPG, JPEG, PNG (máx. 10MB por arquivo)
              </div>
            </div>
          )}

          {/* Tab Content - Resumo */}
          {activeTab === 'resumo' && (
            <div className="p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Resumo da Prestação de Contas</h3>
              
              {/* Gráfico de distribuição */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium mb-4">Distribuição por Categoria</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Recursos Humanos</span>
                      <span className="font-bold text-blue-600">{formatCurrency(resumo?.total_rh || 0)}</span>
                    </div>
                    {Object.entries(CATEGORIAS_NATUREZA).filter(([k]) => k !== 'RH').map(([key, cat]) => {
                      const total = getDespesasPorCategoria(key).reduce((sum, d) => sum + (d.valor_total || 0), 0);
                      if (total === 0) return null;
                      return (
                        <div key={key} className="flex items-center justify-between">
                          <span className="text-sm text-gray-600">{cat.label}</span>
                          <span className="font-medium">{formatCurrency(total)}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium mb-4">Totalizadores</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between border-b pb-2">
                      <span>Receita do Projeto:</span>
                      <span className="font-bold">{formatCurrency(projeto.valor_total)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Total RH:</span>
                      <span>{formatCurrency(resumo?.total_rh || 0)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Total Despesas:</span>
                      <span>{formatCurrency(resumo?.total_despesas || 0)}</span>
                    </div>
                    <div className="flex justify-between border-t pt-2 font-bold">
                      <span>Total Geral:</span>
                      <span className="text-purple-600">{formatCurrency((resumo?.total_rh || 0) + (resumo?.total_despesas || 0))}</span>
                    </div>
                    <div className="flex justify-between border-t pt-2">
                      <span>Saldo:</span>
                      <span className={projeto.valor_total - ((resumo?.total_rh || 0) + (resumo?.total_despesas || 0)) >= 0 ? 'text-green-600 font-bold' : 'text-red-600 font-bold'}>
                        {formatCurrency(projeto.valor_total - ((resumo?.total_rh || 0) + (resumo?.total_despesas || 0)))}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Status dos documentos */}
              <div className="mt-6 bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium mb-4">Status dos Documentos</h4>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-gray-900">{documentos.length}</div>
                    <div className="text-sm text-gray-500">Total</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-green-600">{documentos.filter(d => d.validado).length}</div>
                    <div className="text-sm text-gray-500">Validados</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-yellow-600">{documentos.filter(d => !d.validado).length}</div>
                    <div className="text-sm text-gray-500">Pendentes</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal RH */}
        {showRHModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <h3 className="text-lg font-semibold mb-4">Adicionar Recurso Humano</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm font-medium mb-1">Cargo ou Função *</label>
                  <input
                    type="text"
                    value={rhForm.nome_funcao}
                    onChange={(e) => setRhForm({...rhForm, nome_funcao: e.target.value})}
                    className="w-full border rounded-lg px-3 py-2"
                    placeholder="Ex: Coordenador de Projeto"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Regime de Contratação *</label>
                  <select
                    value={rhForm.regime_contratacao}
                    onChange={(e) => setRhForm({...rhForm, regime_contratacao: e.target.value})}
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    {REGIMES_CONTRATACAO.map(r => (
                      <option key={r} value={r}>{r}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Carga Horária Semanal *</label>
                  <input
                    type="number"
                    value={rhForm.carga_horaria_semanal}
                    onChange={(e) => setRhForm({...rhForm, carga_horaria_semanal: parseInt(e.target.value)})}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Salário Bruto Mensal *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={rhForm.salario_bruto}
                    onChange={(e) => setRhForm({...rhForm, salario_bruto: parseFloat(e.target.value)})}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Número de Meses *</label>
                  <input
                    type="number"
                    value={rhForm.numero_meses}
                    onChange={(e) => setRhForm({...rhForm, numero_meses: parseInt(e.target.value)})}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Vale Transporte (mensal)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={rhForm.vale_transporte}
                    onChange={(e) => setRhForm({...rhForm, vale_transporte: parseFloat(e.target.value)})}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Vale Alimentação (mensal)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={rhForm.vale_alimentacao}
                    onChange={(e) => setRhForm({...rhForm, vale_alimentacao: parseFloat(e.target.value)})}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>
                
                <div className="col-span-2">
                  <label className="block text-sm font-medium mb-1">Observações</label>
                  <textarea
                    value={rhForm.observacoes}
                    onChange={(e) => setRhForm({...rhForm, observacoes: e.target.value})}
                    className="w-full border rounded-lg px-3 py-2"
                    rows={2}
                    placeholder="Nota técnica sobre este profissional..."
                  />
                </div>
              </div>
              
              {/* Preview de cálculos */}
              {rhForm.regime_contratacao === 'CLT' && rhForm.salario_bruto > 0 && (
                <div className="mt-4 p-3 bg-blue-50 rounded-lg text-sm">
                  <strong>Cálculo CLT (automático):</strong>
                  {(() => {
                    const calc = calcularEncargosCLT(rhForm.salario_bruto);
                    const custoMensal = rhForm.salario_bruto + calc.total_encargos + rhForm.vale_transporte + rhForm.vale_alimentacao;
                    return (
                      <div className="grid grid-cols-2 gap-2 mt-2">
                        <span>Provisão Férias: {formatCurrency(calc.provisao_ferias)}</span>
                        <span>Provisão 13º: {formatCurrency(calc.provisao_13_salario)}</span>
                        <span>FGTS (8%): {formatCurrency(calc.fgts)}</span>
                        <span>INSS Patronal (20%): {formatCurrency(calc.inss_patronal)}</span>
                        <span className="col-span-2 font-bold">Custo Mensal Total: {formatCurrency(custoMensal)}</span>
                        <span className="col-span-2 font-bold text-green-600">Custo Total ({rhForm.numero_meses} meses): {formatCurrency(custoMensal * rhForm.numero_meses)}</span>
                      </div>
                    );
                  })()}
                </div>
              )}
              
              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => setShowRHModal(false)}
                  className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleAddRH}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Adicionar
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal Despesa */}
        {showDespesaModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <h3 className="text-lg font-semibold mb-4">Adicionar Despesa</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Natureza de Despesa *</label>
                  <select
                    value={despesaForm.natureza_despesa}
                    onChange={(e) => setDespesaForm({...despesaForm, natureza_despesa: e.target.value, item_despesa: ''})}
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    {Object.entries(naturezasDespesa).map(([cod, nat]) => (
                      <option key={cod} value={cod}>{cod} - {nat.nome}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Item de Despesa *</label>
                  <select
                    value={despesaForm.item_despesa}
                    onChange={(e) => setDespesaForm({...despesaForm, item_despesa: e.target.value})}
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    <option value="">Selecione...</option>
                    {(naturezasDespesa[despesaForm.natureza_despesa]?.itens || []).map(item => (
                      <option key={item} value={item}>{item}</option>
                    ))}
                    <option value="OUTRO">Outro (especificar)</option>
                  </select>
                </div>
                
                <div className="col-span-2">
                  <label className="block text-sm font-medium mb-1">Descrição *</label>
                  <input
                    type="text"
                    value={despesaForm.descricao}
                    onChange={(e) => setDespesaForm({...despesaForm, descricao: e.target.value})}
                    className="w-full border rounded-lg px-3 py-2"
                    placeholder="Descreva o item detalhadamente"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Quantidade *</label>
                  <input
                    type="number"
                    value={despesaForm.quantidade}
                    onChange={(e) => setDespesaForm({...despesaForm, quantidade: parseInt(e.target.value)})}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Unidade *</label>
                  <select
                    value={despesaForm.unidade}
                    onChange={(e) => setDespesaForm({...despesaForm, unidade: e.target.value})}
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    <option value="UN">Unidade</option>
                    <option value="MES">Mês</option>
                    <option value="HORA">Hora</option>
                    <option value="DIA">Dia</option>
                    <option value="KG">Quilograma</option>
                    <option value="LT">Litro</option>
                    <option value="M2">Metro Quadrado</option>
                    <option value="PCT">Pacote</option>
                    <option value="CX">Caixa</option>
                    <option value="GLOBAL">Global</option>
                  </select>
                </div>
                
                <div className="col-span-2 p-3 bg-yellow-50 rounded-lg">
                  <label className="block text-sm font-medium mb-2">Cotações (mínimo 3 orçamentos) *</label>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="text-xs text-gray-500">Orçamento 1</label>
                      <input
                        type="number"
                        step="0.01"
                        value={despesaForm.orcamento_1}
                        onChange={(e) => setDespesaForm({...despesaForm, orcamento_1: parseFloat(e.target.value)})}
                        className="w-full border rounded-lg px-3 py-2"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Orçamento 2</label>
                      <input
                        type="number"
                        step="0.01"
                        value={despesaForm.orcamento_2}
                        onChange={(e) => setDespesaForm({...despesaForm, orcamento_2: parseFloat(e.target.value)})}
                        className="w-full border rounded-lg px-3 py-2"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Orçamento 3</label>
                      <input
                        type="number"
                        step="0.01"
                        value={despesaForm.orcamento_3}
                        onChange={(e) => setDespesaForm({...despesaForm, orcamento_3: parseFloat(e.target.value)})}
                        className="w-full border rounded-lg px-3 py-2"
                      />
                    </div>
                  </div>
                  <div className="mt-2 text-sm font-medium">
                    Média: {formatCurrency(calcularMediaOrcamentos(despesaForm.orcamento_1, despesaForm.orcamento_2, despesaForm.orcamento_3))}
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Valor Unitário Previsto *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={despesaForm.valor_unitario || calcularMediaOrcamentos(despesaForm.orcamento_1, despesaForm.orcamento_2, despesaForm.orcamento_3)}
                    onChange={(e) => setDespesaForm({...despesaForm, valor_unitario: parseFloat(e.target.value)})}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Ref. Preço Municipal</label>
                  <input
                    type="number"
                    step="0.01"
                    value={despesaForm.referencia_preco_municipal}
                    onChange={(e) => setDespesaForm({...despesaForm, referencia_preco_municipal: parseFloat(e.target.value)})}
                    className="w-full border rounded-lg px-3 py-2"
                    placeholder="Ata de Registro de Preço"
                  />
                </div>
                
                <div className="col-span-2">
                  <label className="block text-sm font-medium mb-1">Observações</label>
                  <textarea
                    value={despesaForm.observacoes}
                    onChange={(e) => setDespesaForm({...despesaForm, observacoes: e.target.value})}
                    className="w-full border rounded-lg px-3 py-2"
                    rows={2}
                  />
                </div>
              </div>
              
              {/* Preview do total */}
              <div className="mt-4 p-3 bg-green-50 rounded-lg text-sm">
                <strong>Total previsto:</strong> {despesaForm.quantidade} x {formatCurrency(despesaForm.valor_unitario || calcularMediaOrcamentos(despesaForm.orcamento_1, despesaForm.orcamento_2, despesaForm.orcamento_3))} = 
                <span className="font-bold text-green-600 ml-2">
                  {formatCurrency(despesaForm.quantidade * (despesaForm.valor_unitario || calcularMediaOrcamentos(despesaForm.orcamento_1, despesaForm.orcamento_2, despesaForm.orcamento_3)))}
                </span>
              </div>
              
              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => setShowDespesaModal(false)}
                  className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleAddDespesa}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  Adicionar
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal Documento */}
        {showDocumentoModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-lg">
              <h3 className="text-lg font-semibold mb-4">Anexar Documento</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Tipo de Documento *</label>
                  <select
                    value={documentoForm.tipo_documento}
                    onChange={(e) => setDocumentoForm({...documentoForm, tipo_documento: e.target.value})}
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    {Object.entries(TIPOS_DOCUMENTO).map(([val, label]) => (
                      <option key={val} value={val}>{label}</option>
                    ))}
                  </select>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Número do Documento</label>
                    <input
                      type="text"
                      value={documentoForm.numero_documento}
                      onChange={(e) => setDocumentoForm({...documentoForm, numero_documento: e.target.value})}
                      className="w-full border rounded-lg px-3 py-2"
                      placeholder="Ex: NF 12345"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Data</label>
                    <input
                      type="date"
                      value={documentoForm.data_documento}
                      onChange={(e) => setDocumentoForm({...documentoForm, data_documento: e.target.value})}
                      className="w-full border rounded-lg px-3 py-2"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Valor (R$)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={documentoForm.valor}
                    onChange={(e) => setDocumentoForm({...documentoForm, valor: parseFloat(e.target.value)})}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Vincular a Despesa</label>
                  <select
                    value={documentoForm.despesa_id}
                    onChange={(e) => setDocumentoForm({...documentoForm, despesa_id: e.target.value})}
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    <option value="">Nenhuma (geral)</option>
                    {despesas.map(d => (
                      <option key={d.despesa_id} value={d.despesa_id}>{d.item_despesa} - {formatCurrency(d.valor_total)}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Arquivo * (PDF, JPG, PNG)</label>
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={(e) => setDocumentoForm({...documentoForm, file: e.target.files[0]})}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Observações</label>
                  <textarea
                    value={documentoForm.observacoes}
                    onChange={(e) => setDocumentoForm({...documentoForm, observacoes: e.target.value})}
                    className="w-full border rounded-lg px-3 py-2"
                    rows={2}
                  />
                </div>
              </div>
              
              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => setShowDocumentoModal(false)}
                  className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleUploadDocumento}
                  disabled={uploading || !documentoForm.file}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                >
                  {uploading ? 'Enviando...' : 'Anexar'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal Editar Projeto */}
        {showProjetoModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-3xl max-h-[90vh] overflow-y-auto">
              <h3 className="text-lg font-semibold mb-4">Editar Dados do Projeto</h3>
              
              <ProjetoForm 
                projeto={projeto} 
                onSave={handleUpdateProjeto}
                onCancel={() => setShowProjetoModal(false)}
              />
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

// Componente de Formulário do Projeto
const ProjetoForm = ({ projeto, onSave, onCancel }) => {
  const [form, setForm] = useState({
    nome_projeto: projeto.nome_projeto || '',
    objeto: projeto.objeto || '',
    organizacao_parceira: projeto.organizacao_parceira || '',
    cnpj_parceira: projeto.cnpj_parceira || '',
    responsavel_osc: projeto.responsavel_osc || '',
    valor_total: projeto.valor_total || 0,
    valor_repasse_publico: projeto.valor_repasse_publico || 0,
    valor_contrapartida: projeto.valor_contrapartida || 0,
    tipo_concedente: projeto.tipo_concedente || '',
    nome_concedente: projeto.nome_concedente || '',
    numero_emenda: projeto.numero_emenda || '',
    numero_termo: projeto.numero_termo || '',
    gestor_responsavel_nome: projeto.gestor_responsavel_nome || '',
    gestor_responsavel_cpf: projeto.gestor_responsavel_cpf || '',
    gestor_responsavel_cargo: projeto.gestor_responsavel_cargo || '',
    banco_nome: projeto.banco_nome || '',
    banco_agencia: projeto.banco_agencia || '',
    banco_conta: projeto.banco_conta || '',
    plano_trabalho_finalidade: projeto.plano_trabalho_finalidade || '',
    plano_trabalho_cronograma: projeto.plano_trabalho_cronograma || ''
  });

  return (
    <div className="space-y-6">
      {/* Dados básicos */}
      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <label className="block text-sm font-medium mb-1">Nome do Projeto *</label>
          <input
            type="text"
            value={form.nome_projeto}
            onChange={(e) => setForm({...form, nome_projeto: e.target.value})}
            className="w-full border rounded-lg px-3 py-2"
          />
        </div>
        <div className="col-span-2">
          <label className="block text-sm font-medium mb-1">Objeto *</label>
          <textarea
            value={form.objeto}
            onChange={(e) => setForm({...form, objeto: e.target.value})}
            className="w-full border rounded-lg px-3 py-2"
            rows={2}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">OSC *</label>
          <input
            type="text"
            value={form.organizacao_parceira}
            onChange={(e) => setForm({...form, organizacao_parceira: e.target.value})}
            className="w-full border rounded-lg px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">CNPJ *</label>
          <input
            type="text"
            value={form.cnpj_parceira}
            onChange={(e) => setForm({...form, cnpj_parceira: e.target.value})}
            className="w-full border rounded-lg px-3 py-2"
          />
        </div>
      </div>

      {/* Concedente (MPC 01/2025) */}
      <div className="p-4 bg-blue-50 rounded-lg">
        <h4 className="font-medium text-blue-900 mb-3">Dados do Concedente (Rec. MPC 01/2025)</h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Tipo do Concedente</label>
            <select
              value={form.tipo_concedente}
              onChange={(e) => setForm({...form, tipo_concedente: e.target.value})}
              className="w-full border rounded-lg px-3 py-2"
            >
              <option value="">Selecione...</option>
              {TIPOS_CONCEDENTE.map(t => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Nome do Concedente</label>
            <input
              type="text"
              value={form.nome_concedente}
              onChange={(e) => setForm({...form, nome_concedente: e.target.value})}
              className="w-full border rounded-lg px-3 py-2"
              placeholder="Nome do parlamentar/órgão"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Nº da Emenda</label>
            <input
              type="text"
              value={form.numero_emenda}
              onChange={(e) => setForm({...form, numero_emenda: e.target.value})}
              className="w-full border rounded-lg px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Nº do Termo</label>
            <input
              type="text"
              value={form.numero_termo}
              onChange={(e) => setForm({...form, numero_termo: e.target.value})}
              className="w-full border rounded-lg px-3 py-2"
            />
          </div>
        </div>
      </div>

      {/* Gestor Responsável */}
      <div className="p-4 bg-green-50 rounded-lg">
        <h4 className="font-medium text-green-900 mb-3">Gestor Responsável</h4>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Nome Completo</label>
            <input
              type="text"
              value={form.gestor_responsavel_nome}
              onChange={(e) => setForm({...form, gestor_responsavel_nome: e.target.value})}
              className="w-full border rounded-lg px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">CPF</label>
            <input
              type="text"
              value={form.gestor_responsavel_cpf}
              onChange={(e) => setForm({...form, gestor_responsavel_cpf: e.target.value})}
              className="w-full border rounded-lg px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Cargo</label>
            <input
              type="text"
              value={form.gestor_responsavel_cargo}
              onChange={(e) => setForm({...form, gestor_responsavel_cargo: e.target.value})}
              className="w-full border rounded-lg px-3 py-2"
            />
          </div>
        </div>
      </div>

      {/* Conta Bancária */}
      <div className="p-4 bg-yellow-50 rounded-lg">
        <h4 className="font-medium text-yellow-900 mb-3">Conta Bancária Específica</h4>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Banco</label>
            <input
              type="text"
              value={form.banco_nome}
              onChange={(e) => setForm({...form, banco_nome: e.target.value})}
              className="w-full border rounded-lg px-3 py-2"
              placeholder="Ex: Banco do Brasil"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Agência</label>
            <input
              type="text"
              value={form.banco_agencia}
              onChange={(e) => setForm({...form, banco_agencia: e.target.value})}
              className="w-full border rounded-lg px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Conta</label>
            <input
              type="text"
              value={form.banco_conta}
              onChange={(e) => setForm({...form, banco_conta: e.target.value})}
              className="w-full border rounded-lg px-3 py-2"
            />
          </div>
        </div>
      </div>

      {/* Valores */}
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Repasse Público (R$)</label>
          <input
            type="number"
            step="0.01"
            value={form.valor_repasse_publico}
            onChange={(e) => setForm({...form, valor_repasse_publico: parseFloat(e.target.value)})}
            className="w-full border rounded-lg px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Contrapartida (R$)</label>
          <input
            type="number"
            step="0.01"
            value={form.valor_contrapartida}
            onChange={(e) => setForm({...form, valor_contrapartida: parseFloat(e.target.value)})}
            className="w-full border rounded-lg px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Valor Total (R$)</label>
          <input
            type="number"
            step="0.01"
            value={form.valor_total}
            onChange={(e) => setForm({...form, valor_total: parseFloat(e.target.value)})}
            className="w-full border rounded-lg px-3 py-2"
          />
        </div>
      </div>

      <div className="flex justify-end gap-3">
        <button
          onClick={onCancel}
          className="px-4 py-2 border rounded-lg hover:bg-gray-50"
        >
          Cancelar
        </button>
        <button
          onClick={() => onSave(form)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Salvar
        </button>
      </div>
    </div>
  );
};

export default PrestacaoContasEditor;
