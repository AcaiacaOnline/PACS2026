import React from 'react';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';

const PAGE_SIZE_OPTIONS = [20, 30, 50, 100];

/**
 * Componente de Paginação Configurável
 * @param {number} currentPage - Página atual (base 1)
 * @param {number} totalItems - Total de itens
 * @param {number} pageSize - Itens por página
 * @param {function} onPageChange - Callback quando muda a página
 * @param {function} onPageSizeChange - Callback quando muda o tamanho da página
 */
const Pagination = ({ 
  currentPage, 
  totalItems, 
  pageSize, 
  onPageChange, 
  onPageSizeChange,
  showPageSizeSelector = true,
  className = ''
}) => {
  const totalPages = Math.ceil(totalItems / pageSize);
  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  // Gerar array de páginas para exibir
  const getPageNumbers = () => {
    const pages = [];
    const maxVisible = 5;
    
    let start = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let end = Math.min(totalPages, start + maxVisible - 1);
    
    if (end - start + 1 < maxVisible) {
      start = Math.max(1, end - maxVisible + 1);
    }
    
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    
    return pages;
  };

  const handlePageSizeChange = (newSize) => {
    // Salvar preferência no localStorage
    localStorage.setItem('pac_page_size', newSize.toString());
    onPageSizeChange(newSize);
    // Volta para a primeira página ao mudar o tamanho
    onPageChange(1);
  };

  if (totalItems === 0) return null;

  return (
    <div className={`flex flex-col sm:flex-row items-center justify-between gap-4 ${className}`}>
      {/* Informações e seletor de tamanho */}
      <div className="flex items-center gap-4 text-sm text-muted-foreground">
        <span>
          Exibindo <span className="font-semibold text-foreground">{startItem}</span> a{' '}
          <span className="font-semibold text-foreground">{endItem}</span> de{' '}
          <span className="font-semibold text-foreground">{totalItems}</span> itens
        </span>
        
        {showPageSizeSelector && (
          <div className="flex items-center gap-2">
            <span>|</span>
            <label htmlFor="pageSize" className="text-sm">
              Itens por página:
            </label>
            <select
              id="pageSize"
              value={pageSize}
              onChange={(e) => handlePageSizeChange(parseInt(e.target.value))}
              className="px-2 py-1 border border-input bg-background rounded-md text-sm focus:ring-2 focus:ring-ring outline-none cursor-pointer"
              data-testid="page-size-selector"
            >
              {PAGE_SIZE_OPTIONS.map((size) => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Controles de navegação */}
      {totalPages > 1 && (
        <div className="flex items-center gap-1">
          {/* Primeira página */}
          <button
            onClick={() => onPageChange(1)}
            disabled={currentPage === 1}
            className="p-2 rounded-lg border border-border hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Primeira página"
            data-testid="pagination-first"
          >
            <ChevronsLeft size={16} />
          </button>
          
          {/* Página anterior */}
          <button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="p-2 rounded-lg border border-border hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Página anterior"
            data-testid="pagination-prev"
          >
            <ChevronLeft size={16} />
          </button>

          {/* Números das páginas */}
          <div className="flex items-center gap-1 mx-2">
            {getPageNumbers()[0] > 1 && (
              <>
                <button
                  onClick={() => onPageChange(1)}
                  className="px-3 py-1 rounded-lg border border-border hover:bg-muted transition-colors text-sm"
                >
                  1
                </button>
                {getPageNumbers()[0] > 2 && (
                  <span className="px-2 text-muted-foreground">...</span>
                )}
              </>
            )}
            
            {getPageNumbers().map((page) => (
              <button
                key={page}
                onClick={() => onPageChange(page)}
                className={`px-3 py-1 rounded-lg border transition-colors text-sm ${
                  currentPage === page
                    ? 'bg-primary text-primary-foreground border-primary'
                    : 'border-border hover:bg-muted'
                }`}
                data-testid={`pagination-page-${page}`}
              >
                {page}
              </button>
            ))}
            
            {getPageNumbers()[getPageNumbers().length - 1] < totalPages && (
              <>
                {getPageNumbers()[getPageNumbers().length - 1] < totalPages - 1 && (
                  <span className="px-2 text-muted-foreground">...</span>
                )}
                <button
                  onClick={() => onPageChange(totalPages)}
                  className="px-3 py-1 rounded-lg border border-border hover:bg-muted transition-colors text-sm"
                >
                  {totalPages}
                </button>
              </>
            )}
          </div>

          {/* Próxima página */}
          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className="p-2 rounded-lg border border-border hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Próxima página"
            data-testid="pagination-next"
          >
            <ChevronRight size={16} />
          </button>
          
          {/* Última página */}
          <button
            onClick={() => onPageChange(totalPages)}
            disabled={currentPage === totalPages}
            className="p-2 rounded-lg border border-border hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Última página"
            data-testid="pagination-last"
          >
            <ChevronsRight size={16} />
          </button>
        </div>
      )}
    </div>
  );
};

// Hook para gerenciar o estado de paginação
export const usePagination = (initialPageSize = 20) => {
  const [currentPage, setCurrentPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(() => {
    // Recuperar preferência salva do localStorage
    const saved = localStorage.getItem('pac_page_size');
    return saved ? parseInt(saved) : initialPageSize;
  });

  const resetPage = () => setCurrentPage(1);

  return {
    currentPage,
    setCurrentPage,
    pageSize,
    setPageSize,
    resetPage
  };
};

// Função utilitária para paginar dados localmente
export const paginateData = (data, currentPage, pageSize) => {
  const start = (currentPage - 1) * pageSize;
  const end = start + pageSize;
  return data.slice(start, end);
};

export default Pagination;
