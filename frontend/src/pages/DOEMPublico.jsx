import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Newspaper, Search, Calendar, Download, ChevronDown, ChevronRight, 
  FileText, CheckCircle, ArrowLeft, Home, Eye, ZoomIn, ZoomOut,
  ChevronLeft, Filter, X, Printer, Share2, BookOpen, Building2
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

// API pública (sem autenticação)
const publicApi = axios.create({
  baseURL: `${process.env.REACT_APP_BACKEND_URL}/api`,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Categorias do DOEM inspiradas no Diário Oficial de MG
const CATEGORIAS_DOEM = [
  {
    id: 'executivo',
    nome: 'Diário do Executivo',
    icon: Building2,
    segmentos: ['Decretos', 'Portarias', 'Resoluções', 'Editais', 'Processos Administrativos']
  },
  {
    id: 'municipios',
    nome: 'Diário dos Municípios',
    icon: Newspaper,
    segmentos: ['Prestações de Contas', 'Leis']
  },
  {
    id: 'terceiros',
    nome: 'Diário de Terceiros',
    icon: BookOpen,
    segmentos: ['Publicações do Terceiro Setor', 'Publicações do Legislativo']
  }
];

const MESES = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
];

const DIAS_SEMANA = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado'];

const DOEMPublico = () => {
  const navigate = useNavigate();
  const [edicoes, setEdicoes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [selectedEdicao, setSelectedEdicao] = useState(null);
  const [error, setError] = useState(null);
  
  // Estados dos filtros
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [showCalendar, setShowCalendar] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState(['executivo']);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedSegmento, setSelectedSegmento] = useState(null);
  
  // Estados do visualizador
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [zoom, setZoom] = useState(100);
  const [showAdvancedSearch, setShowAdvancedSearch] = useState(false);

  useEffect(() => {
    fetchEdicoes();
  }, []);

  const fetchEdicoes = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await publicApi.get('/public/doem/edicoes?limit=100');
      setEdicoes(response.data);
      if (response.data.length > 0) {
        setSelectedEdicao(response.data[0]);
        setTotalPages(response.data[0].publicacoes?.length || 1);
      }
    } catch (error) {
      console.error('Erro ao carregar edições:', error);
      setError('Não foi possível carregar as edições do DOEM.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchTerm || searchTerm.length < 3) {
      toast.error('Digite pelo menos 3 caracteres para buscar');
      return;
    }

    try {
      const response = await publicApi.get(`/public/doem/busca?q=${encodeURIComponent(searchTerm)}`);
      setSearchResults(response.data);
      setShowAdvancedSearch(true);
    } catch (error) {
      toast.error('Erro ao buscar');
    }
  };

  const handleDownloadPDF = async (edicao) => {
    try {
      const response = await publicApi.get(`/public/doem/edicoes/${edicao.edicao_id}/pdf`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `DOEM_Acaiaca_Edicao_${edicao.numero_edicao}_${edicao.ano}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('PDF baixado com sucesso!');
    } catch (error) {
      toast.error('Erro ao baixar PDF');
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: 'long',
        year: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  const formatDateShort = (date) => {
    const d = new Date(date);
    return `${d.getDate().toString().padStart(2, '0')}/${(d.getMonth() + 1).toString().padStart(2, '0')}/${d.getFullYear()}`;
  };

  // Filtrar edições
  const filteredEdicoes = useMemo(() => {
    let filtered = [...edicoes];
    
    // Filtrar por data selecionada (mesmo mês/ano)
    if (selectedDate) {
      const month = selectedDate.getMonth();
      const year = selectedDate.getFullYear();
      filtered = filtered.filter(e => {
        if (!e.data_publicacao) return false;
        const pubDate = new Date(e.data_publicacao);
        return pubDate.getMonth() === month && pubDate.getFullYear() === year;
      });
    }
    
    // Filtrar por segmento
    if (selectedSegmento) {
      filtered = filtered.filter(e => 
        e.publicacoes?.some(p => p.segmento === selectedSegmento)
      );
    }
    
    return filtered;
  }, [edicoes, selectedDate, selectedSegmento]);

  const toggleCategory = (categoryId) => {
    setExpandedCategories(prev => 
      prev.includes(categoryId) 
        ? prev.filter(c => c !== categoryId)
        : [...prev, categoryId]
    );
  };

  const handleSelectSegmento = (segmento) => {
    setSelectedSegmento(selectedSegmento === segmento ? null : segmento);
  };

  // Gerar dias do calendário
  const generateCalendarDays = () => {
    const year = selectedDate.getFullYear();
    const month = selectedDate.getMonth();
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    
    const days = [];
    for (let i = 0; i < firstDay; i++) {
      days.push(null);
    }
    for (let i = 1; i <= daysInMonth; i++) {
      days.push(i);
    }
    return days;
  };

  const changeMonth = (delta) => {
    const newDate = new Date(selectedDate);
    newDate.setMonth(newDate.getMonth() + delta);
    setSelectedDate(newDate);
  };

  const selectDay = (day) => {
    if (!day) return;
    const newDate = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), day);
    setSelectedDate(newDate);
    setShowCalendar(false);
  };

  // Verificar se há edição no dia
  const hasEditionOnDay = (day) => {
    if (!day) return false;
    return edicoes.some(e => {
      if (!e.data_publicacao) return false;
      const pubDate = new Date(e.data_publicacao);
      return (
        pubDate.getDate() === day &&
        pubDate.getMonth() === selectedDate.getMonth() &&
        pubDate.getFullYear() === selectedDate.getFullYear()
      );
    });
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* ===== HEADER ESTILO DIÁRIO OFICIAL MG ===== */}
      <header className="bg-[#8B0000] text-white shadow-lg">
        <div className="flex items-stretch">
          {/* Seção de Data/Calendário */}
          <div className="bg-[#6B0000] px-4 py-3 min-w-[220px] border-r border-[#500000]">
            <div className="text-xs text-white/70 mb-1">Edição do dia</div>
            <button 
              onClick={() => setShowCalendar(!showCalendar)}
              className="flex items-center gap-3 w-full text-left hover:bg-white/10 rounded-lg p-2 transition-colors"
            >
              <div className="flex items-center gap-2">
                <Calendar size={20} className="text-white/80" />
                <span className="text-3xl font-bold">{selectedDate.getDate()}</span>
              </div>
              <div className="flex-1">
                <div className="text-sm font-semibold">{selectedDate.getFullYear()}</div>
                <div className="text-sm text-white/90">{MESES[selectedDate.getMonth()]}</div>
                <div className="text-xs text-white/70">{DIAS_SEMANA[selectedDate.getDay()]}</div>
              </div>
              <ChevronDown size={18} className="text-[#DC2626]" />
            </button>

            {/* Dropdown do Calendário */}
            {showCalendar && (
              <div className="absolute top-20 left-4 bg-white text-gray-800 rounded-xl shadow-2xl z-50 p-4 w-[300px]">
                <div className="flex items-center justify-between mb-4">
                  <button onClick={() => changeMonth(-1)} className="p-2 hover:bg-gray-100 rounded-lg">
                    <ChevronLeft size={18} />
                  </button>
                  <span className="font-semibold">
                    {MESES[selectedDate.getMonth()]} {selectedDate.getFullYear()}
                  </span>
                  <button onClick={() => changeMonth(1)} className="p-2 hover:bg-gray-100 rounded-lg">
                    <ChevronRight size={18} />
                  </button>
                </div>
                
                <div className="grid grid-cols-7 gap-1 text-center text-xs mb-2">
                  {['D', 'S', 'T', 'Q', 'Q', 'S', 'S'].map((d, i) => (
                    <div key={i} className="font-semibold text-gray-500 py-1">{d}</div>
                  ))}
                </div>
                
                <div className="grid grid-cols-7 gap-1">
                  {generateCalendarDays().map((day, i) => (
                    <button
                      key={i}
                      onClick={() => selectDay(day)}
                      disabled={!day}
                      className={`
                        p-2 text-sm rounded-lg transition-colors relative
                        ${!day ? 'invisible' : 'hover:bg-gray-100'}
                        ${day === selectedDate.getDate() ? 'bg-[#8B0000] text-white' : ''}
                        ${hasEditionOnDay(day) && day !== selectedDate.getDate() ? 'font-bold text-[#8B0000]' : ''}
                      `}
                    >
                      {day}
                      {hasEditionOnDay(day) && (
                        <span className="absolute bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 bg-[#DC2626] rounded-full"></span>
                      )}
                    </button>
                  ))}
                </div>
                
                <button 
                  onClick={() => { setSelectedDate(new Date()); setShowCalendar(false); }}
                  className="w-full mt-3 py-2 text-sm text-[#8B0000] hover:bg-gray-100 rounded-lg font-medium"
                >
                  Ir para hoje
                </button>
              </div>
            )}
          </div>

          {/* Barra de Pesquisa Avançada */}
          <div className="flex-1 flex items-center px-6">
            <div className="flex-1 relative">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Clique aqui para efetuar a pesquisa avançada"
                className="w-full px-4 py-3 bg-transparent border-none outline-none text-white placeholder-white/60 text-sm"
              />
            </div>
            <button
              onClick={handleSearch}
              className="p-3 hover:bg-white/10 rounded-lg transition-colors"
            >
              <Search size={22} className="text-white" />
            </button>
          </div>

          {/* Botões de Navegação */}
          <div className="flex items-center gap-2 px-4">
            <button
              onClick={() => navigate('/transparencia')}
              className="flex items-center gap-2 px-3 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors text-sm"
            >
              <Home size={16} />
              <span className="hidden md:inline">Portal</span>
            </button>
            <button
              onClick={() => navigate('/login')}
              className="flex items-center gap-2 px-3 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors text-sm"
            >
              <ArrowLeft size={16} />
              <span className="hidden md:inline">Admin</span>
            </button>
          </div>
        </div>
      </header>

      {/* ===== ÁREA PRINCIPAL COM SIDEBAR ===== */}
      <div className="flex flex-1 overflow-hidden">
        {/* SIDEBAR ESQUERDA - Filtros */}
        <aside className="w-[280px] bg-white border-r border-gray-200 overflow-y-auto flex-shrink-0">
          {/* Categorias Estilo Accordion */}
          <nav className="py-2">
            {CATEGORIAS_DOEM.map((categoria) => {
              const Icon = categoria.icon;
              const isExpanded = expandedCategories.includes(categoria.id);
              
              return (
                <div key={categoria.id} className="border-b border-gray-100">
                  <button
                    onClick={() => toggleCategory(categoria.id)}
                    className="w-full flex items-center gap-3 px-4 py-4 hover:bg-gray-50 transition-colors group"
                  >
                    <div className="w-1 h-8 bg-[#DC2626] rounded-full"></div>
                    <Icon size={20} className="text-gray-600 group-hover:text-[#8B0000]" />
                    <span className="flex-1 text-left font-medium text-gray-700 group-hover:text-[#8B0000]">
                      {categoria.nome}
                    </span>
                    <ChevronDown 
                      size={18} 
                      className={`text-[#DC2626] transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
                    />
                  </button>
                  
                  {isExpanded && (
                    <div className="bg-gray-50 py-2">
                      {categoria.segmentos.map((segmento) => (
                        <button
                          key={segmento}
                          onClick={() => handleSelectSegmento(segmento)}
                          className={`
                            w-full flex items-center gap-2 px-8 py-2 text-sm transition-colors
                            ${selectedSegmento === segmento 
                              ? 'bg-[#8B0000] text-white' 
                              : 'text-gray-600 hover:bg-gray-100 hover:text-[#8B0000]'}
                          `}
                        >
                          <FileText size={14} />
                          {segmento}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </nav>

          {/* Lista de Edições do Mês */}
          <div className="border-t border-gray-200 p-4">
            <h3 className="text-sm font-semibold text-gray-500 mb-3 flex items-center gap-2">
              <Calendar size={14} />
              Edições de {MESES[selectedDate.getMonth()]}
            </h3>
            
            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              {filteredEdicoes.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-4">
                  Nenhuma edição neste período
                </p>
              ) : (
                filteredEdicoes.map((edicao) => (
                  <button
                    key={edicao.edicao_id}
                    onClick={() => {
                      setSelectedEdicao(edicao);
                      setCurrentPage(1);
                      setTotalPages(edicao.publicacoes?.length || 1);
                    }}
                    className={`
                      w-full text-left p-3 rounded-lg transition-colors text-sm
                      ${selectedEdicao?.edicao_id === edicao.edicao_id 
                        ? 'bg-[#8B0000] text-white' 
                        : 'bg-gray-50 hover:bg-gray-100 text-gray-700'}
                    `}
                  >
                    <div className="font-medium">Edição nº {edicao.numero_edicao}</div>
                    <div className={`text-xs ${selectedEdicao?.edicao_id === edicao.edicao_id ? 'text-white/70' : 'text-gray-500'}`}>
                      {formatDateShort(edicao.data_publicacao)}
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Filtro Ativo */}
          {selectedSegmento && (
            <div className="border-t border-gray-200 p-4">
              <div className="flex items-center gap-2 bg-[#8B0000]/10 text-[#8B0000] px-3 py-2 rounded-lg text-sm">
                <Filter size={14} />
                <span className="flex-1">{selectedSegmento}</span>
                <button onClick={() => setSelectedSegmento(null)} className="hover:bg-[#8B0000]/20 p-1 rounded">
                  <X size={14} />
                </button>
              </div>
            </div>
          )}
        </aside>

        {/* ÁREA PRINCIPAL - Visualizador de Documento */}
        <main className="flex-1 flex flex-col bg-gray-200 overflow-hidden">
          {/* Toolbar do Visualizador */}
          <div className="bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between">
            <div className="flex items-center gap-4">
              {/* Navegação de Páginas */}
              <div className="flex items-center gap-2 text-sm">
                <button 
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage <= 1}
                  className="p-1.5 hover:bg-gray-100 rounded disabled:opacity-50"
                >
                  <ChevronLeft size={18} />
                </button>
                <div className="flex items-center gap-1">
                  <input
                    type="number"
                    value={currentPage}
                    onChange={(e) => setCurrentPage(Math.min(totalPages, Math.max(1, parseInt(e.target.value) || 1)))}
                    className="w-12 px-2 py-1 border border-gray-200 rounded text-center text-sm"
                    min={1}
                    max={totalPages}
                  />
                  <span className="text-gray-500">de {totalPages}</span>
                </div>
                <button 
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage >= totalPages}
                  className="p-1.5 hover:bg-gray-100 rounded disabled:opacity-50"
                >
                  <ChevronRight size={18} />
                </button>
              </div>

              {/* Busca no Documento */}
              <div className="flex items-center gap-2 border-l border-gray-200 pl-4">
                <input
                  type="text"
                  placeholder="Localizar..."
                  className="px-3 py-1.5 border border-gray-200 rounded text-sm w-40"
                />
              </div>

              {/* Zoom */}
              <div className="flex items-center gap-2 border-l border-gray-200 pl-4">
                <button 
                  onClick={() => setZoom(Math.max(50, zoom - 10))}
                  className="p-1.5 hover:bg-gray-100 rounded"
                >
                  <ZoomOut size={18} />
                </button>
                <span className="text-sm text-gray-600 w-12 text-center">{zoom}%</span>
                <button 
                  onClick={() => setZoom(Math.min(200, zoom + 10))}
                  className="p-1.5 hover:bg-gray-100 rounded"
                >
                  <ZoomIn size={18} />
                </button>
              </div>
            </div>

            {/* Ações do Documento */}
            <div className="flex items-center gap-2">
              <button 
                onClick={() => selectedEdicao && handleDownloadPDF(selectedEdicao)}
                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                disabled={!selectedEdicao}
              >
                <Download size={16} />
                Download
              </button>
              <button className="p-2 hover:bg-gray-100 rounded" title="Imprimir">
                <Printer size={18} className="text-gray-600" />
              </button>
              <button className="p-2 hover:bg-gray-100 rounded" title="Compartilhar">
                <Share2 size={18} className="text-gray-600" />
              </button>
            </div>
          </div>

          {/* Área de Visualização do Documento */}
          <div className="flex-1 overflow-auto p-6 flex justify-center">
            {loading ? (
              <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#8B0000]"></div>
              </div>
            ) : error ? (
              <div className="text-center py-12">
                <p className="text-red-500 mb-4">{error}</p>
                <button 
                  onClick={fetchEdicoes}
                  className="px-4 py-2 bg-[#8B0000] text-white rounded-lg hover:bg-[#6B0000]"
                >
                  Tentar Novamente
                </button>
              </div>
            ) : selectedEdicao ? (
              <div 
                className="bg-white shadow-xl rounded-lg max-w-4xl w-full"
                style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'top center' }}
              >
                {/* Cabeçalho DOEM - Estilo Oficial */}
                <div className="p-6 pb-4">
                  {/* Brasão + ACAIACA + Brasão */}
                  <div className="flex items-center justify-center gap-4 mb-4">
                    <img 
                      src="/brasao-acaiaca.png" 
                      alt="Brasão" 
                      className="h-16 w-auto"
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                    <h1 className="text-4xl font-bold tracking-wider text-[#1E3A8A]" style={{textShadow: '2px 2px 4px rgba(0,0,0,0.1)'}}>
                      ACAIACA
                    </h1>
                    <img 
                      src="/brasao-acaiaca.png" 
                      alt="Brasão" 
                      className="h-16 w-auto"
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                  </div>
                  
                  {/* Linha cinza separadora */}
                  <div className="h-0.5 bg-gray-300 my-3"></div>
                  
                  {/* Informações de publicação */}
                  <div className="flex flex-wrap items-center justify-between text-[#1E3A8A] text-sm gap-2">
                    <span>https://pac.acaiaca.mg.gov.br/doem</span>
                    <span className="font-medium">
                      ANO {selectedEdicao.ano} - Nº {selectedEdicao.numero_edicao} - {totalPages} PÁGINA(S)
                    </span>
                    <span>ACAIACA, {formatDate(selectedEdicao.data_publicacao).toUpperCase()}</span>
                  </div>
                  
                  {/* Linha azul inferior */}
                  <div className="h-1 bg-[#1E3A8A] mt-3"></div>
                  
                  {/* Título DOEM */}
                  <div className="bg-[#1E3A8A] text-white py-3 px-6 text-center text-lg font-bold tracking-widest mt-4 rounded">
                    DIÁRIO OFICIAL ELETRÔNICO MUNICIPAL
                  </div>
                </div>

                {/* Conteúdo do Documento */}
                <div className="p-8">
                  <h2 className="text-lg font-bold text-[#1a365d] border-b-2 border-gray-300 pb-2 mb-6">
                    PODER EXECUTIVO
                  </h2>

                  {/* Publicações */}
                  <div className="space-y-8">
                    {selectedEdicao.publicacoes?.slice(0, currentPage).map((pub, i) => (
                      <div key={i} className="pb-6 border-b border-gray-200 last:border-0">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="bg-[#8B0000] text-white text-xs px-2 py-0.5 rounded">
                            {pub.segmento || 'Geral'}
                          </span>
                          <span className="text-xs text-gray-500">{pub.tipo}</span>
                        </div>
                        
                        <p className="text-xs text-gray-600 mb-1 font-medium">
                          {pub.secretaria}
                        </p>
                        
                        <h3 className="text-base font-bold text-gray-800 mb-3">
                          {pub.titulo}
                        </h3>
                        
                        <div className="text-sm text-gray-700 leading-relaxed text-justify whitespace-pre-wrap">
                          {pub.texto}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Assinatura Digital */}
                  {selectedEdicao.assinatura_digital?.assinado && (
                    <div className="mt-8 pt-6 border-t-2 border-[#8B0000]">
                      <div className="flex items-center gap-3 text-green-700">
                        <CheckCircle size={20} />
                        <div>
                          <p className="font-semibold">Documento Assinado Digitalmente</p>
                          <p className="text-xs text-gray-500">
                            Código de Validação: {selectedEdicao.assinatura_digital.validation_code || 'N/A'}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Rodapé do Documento */}
                <div className="bg-gray-50 border-t border-gray-200 p-4 text-center text-xs text-gray-500">
                  <p>Prefeitura Municipal de Acaiaca - MG | CNPJ: 18.295.287/0001-90</p>
                  <p>Praça Tancredo Neves, Número 35, Centro de Acaiaca - MG, CEP: 35.438-000</p>
                  <p>Tel.: (31) 3887-1650 | Portal: https://acaiaca.mg.gov.br | E-mail: administracao@acaiaca.mg.gov.br</p>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <Newspaper size={64} className="mx-auto mb-4 opacity-50" />
                <p>Selecione uma edição para visualizar</p>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* ===== MODAL DE PESQUISA AVANÇADA ===== */}
      {showAdvancedSearch && searchResults && (
        <div className="fixed inset-0 bg-black/60 flex items-start justify-center z-50 p-4 pt-8 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[80vh] overflow-hidden">
            <div className="bg-[#8B0000] text-white px-6 py-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold">
                Resultados da Pesquisa
              </h3>
              <button 
                onClick={() => { setShowAdvancedSearch(false); setSearchResults(null); }}
                className="p-2 hover:bg-white/20 rounded-lg"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              <p className="text-sm text-gray-500 mb-4">
                {searchResults.total} resultado(s) encontrado(s)
              </p>
              
              {searchResults.total === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <Search size={48} className="mx-auto mb-4 opacity-50" />
                  <p>Nenhum resultado encontrado para sua busca</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {searchResults.resultados.map((r, i) => (
                    <div 
                      key={i} 
                      className="p-4 border border-gray-200 rounded-lg hover:border-[#8B0000] transition-colors cursor-pointer"
                      onClick={() => {
                        const edicao = edicoes.find(e => e.edicao_id === r.edicao_id);
                        if (edicao) {
                          setSelectedEdicao(edicao);
                          setShowAdvancedSearch(false);
                          setSearchResults(null);
                        }
                      }}
                    >
                      <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
                        <Calendar size={12} />
                        Edição nº {r.numero_edicao} - {formatDateShort(r.data_publicacao)}
                      </div>
                      <h4 className="font-semibold text-gray-800 mb-1">{r.publicacao.titulo}</h4>
                      <p className="text-sm text-gray-600 line-clamp-2">{r.publicacao.texto}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ===== FOOTER ===== */}
      <footer className="bg-[#1a365d] text-white py-4 text-center text-sm">
        <p>© {new Date().getFullYear()} Prefeitura Municipal de Acaiaca - MG</p>
        <p className="text-white/60 text-xs mt-1">
          Diário Oficial Eletrônico Municipal - Sistema de Gestão Municipal
        </p>
      </footer>
    </div>
  );
};

export default DOEMPublico;
