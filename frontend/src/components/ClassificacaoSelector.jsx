import React, { useState, useEffect } from 'react';
import { Search, X } from 'lucide-react';
import api from '../utils/api';

/**
 * Componente para seleção de Classificação Orçamentária (Lei 14.133/2021)
 * 
 * @param {Object} props
 * @param {string} props.codigoSelecionado - Código selecionado
 * @param {string} props.subitemSelecionado - Subitem selecionado
 * @param {Function} props.onCodigoChange - Callback ao selecionar código
 * @param {Function} props.onSubitemChange - Callback ao selecionar subitem
 * @param {boolean} props.disabled - Se o componente está desabilitado
 */
const ClassificacaoSelector = ({ 
  codigoSelecionado, 
  subitemSelecionado, 
  onCodigoChange, 
  onSubitemChange,
  disabled = false
}) => {
  const [codigos, setCodigos] = useState({});
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    fetchCodigos();
  }, []);

  const fetchCodigos = async () => {
    try {
      const response = await api.get('/classificacao/codigos');
      setCodigos(response.data);
    } catch (error) {
      console.error('Erro ao carregar códigos:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCodigoSelect = (codigo) => {
    console.log('[ClassificacaoSelector] Selecionando código:', codigo);
    onCodigoChange(codigo);
    onSubitemChange(''); // Limpar subitem ao trocar código
    setShowDropdown(false);
    setSearchTerm('');
  };

  const handleClearSelection = () => {
    onCodigoChange('');
    onSubitemChange('');
    setSearchTerm('');
  };

  // Filtrar códigos pela busca
  const codigosFiltrados = Object.entries(codigos).filter(([codigo, dados]) => {
    const termoBusca = searchTerm.toLowerCase();
    return (
      codigo.includes(termoBusca) ||
      dados.nome.toLowerCase().includes(termoBusca) ||
      dados.subitens.some(sub => sub.toLowerCase().includes(termoBusca))
    );
  });

  if (loading) {
    return <div className="text-sm text-muted-foreground">Carregando classificações...</div>;
  }

  const codigoData = codigoSelecionado ? codigos[codigoSelecionado] : null;
  
  // Debug
  console.log('[ClassificacaoSelector] Estado atual:', {
    codigoSelecionado,
    subitemSelecionado,
    codigoData: codigoData ? `${codigoData.nome} com ${codigoData.subitens.length} subitens` : 'null',
    totalCodigos: Object.keys(codigos).length
  });

  return (
    <div className="space-y-4">
      {/* Seleção de Código */}
      <div>
        <label className="block text-sm font-semibold text-foreground mb-2">
          Código de Classificação Orçamentária
          <span className="text-xs text-muted-foreground ml-2">(Lei 14.133/2021)</span>
        </label>
        
        <div className="relative">
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <input
                type="text"
                value={codigoSelecionado ? `${codigoSelecionado} - ${codigoData?.nome}` : searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setShowDropdown(true);
                }}
                onFocus={() => setShowDropdown(true)}
                placeholder="Digite para buscar código ou nome..."
                disabled={disabled}
                className="w-full px-3 py-2 pl-10 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                data-testid="classificacao-search-input"
              />
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            </div>
            
            {codigoSelecionado && !disabled && (
              <button
                type="button"
                onClick={handleClearSelection}
                className="px-3 py-2 border border-input rounded-md hover:bg-accent transition-colors"
                title="Limpar seleção"
              >
                <X size={16} />
              </button>
            )}
          </div>

          {/* Dropdown de Códigos */}
          {showDropdown && !disabled && !codigoSelecionado && (
            <div className="absolute z-50 w-full mt-1 bg-card border border-border rounded-lg shadow-lg max-h-96 overflow-auto">
              {codigosFiltrados.length === 0 ? (
                <div className="p-4 text-center text-muted-foreground">
                  Nenhum código encontrado
                </div>
              ) : (
                <div className="py-2">
                  {codigosFiltrados.map(([codigo, dados]) => (
                    <button
                      key={codigo}
                      type="button"
                      onClick={() => handleCodigoSelect(codigo)}
                      className="w-full text-left px-4 py-3 hover:bg-accent transition-colors border-b border-border last:border-b-0"
                      data-testid={`classificacao-codigo-${codigo}`}
                    >
                      <div className="font-semibold text-foreground">
                        {codigo} - {dados.nome}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {dados.subitens.length} subitem(ns) disponível(is)
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Seleção de Subitem */}
      {codigoSelecionado && codigoData && (
        <div>
          <label className="block text-sm font-semibold text-foreground mb-2">
            Subitem da Classificação
          </label>
          <select
            value={subitemSelecionado}
            onChange={(e) => {
              console.log('[ClassificacaoSelector] Selecionando subitem:', e.target.value);
              onSubitemChange(e.target.value);
            }}
            disabled={disabled}
            className="w-full px-3 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:border-ring outline-none disabled:opacity-50 disabled:cursor-not-allowed"
            data-testid="classificacao-subitem-select"
          >
            <option value="">Selecione um subitem...</option>
            {codigoData.subitens.map((subitem, index) => (
              <option key={index} value={subitem}>
                {subitem}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Informação sobre o código selecionado */}
      {codigoSelecionado && codigoData && (
        <div className="bg-accent/5 border border-accent/20 rounded-md p-3 text-sm">
          <div className="font-semibold text-foreground mb-1">
            Código Selecionado:
          </div>
          <div className="text-muted-foreground">
            <strong>{codigoSelecionado}</strong> - {codigoData.nome}
          </div>
          {subitemSelecionado && (
            <div className="mt-2 text-muted-foreground">
              <strong>Subitem:</strong> {subitemSelecionado}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ClassificacaoSelector;
