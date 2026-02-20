// components/shared/Pagination.tsx
interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
  onNext: () => void
  onPrev: () => void
  hasNextPage: boolean
  hasPrevPage: boolean
  startIndex: number
  endIndex: number
  totalItems: number
}

export function Pagination({
  currentPage,
  totalPages,
  onPageChange,
  onNext,
  onPrev,
  hasNextPage,
  hasPrevPage,
  startIndex,
  endIndex,
  totalItems,
}: PaginationProps) {
  // Generar números de página a mostrar
  const getPageNumbers = () => {
    const pages: (number | string)[] = []
    const maxVisible = 5

    if (totalPages <= maxVisible) {
      // Mostrar todas las páginas
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i)
      }
    } else {
      // Siempre mostrar primera página
      pages.push(1)

      if (currentPage > 3) {
        pages.push('...')
      }

      // Páginas alrededor de la actual
      const start = Math.max(2, currentPage - 1)
      const end = Math.min(totalPages - 1, currentPage + 1)

      for (let i = start; i <= end; i++) {
        pages.push(i)
      }

      if (currentPage < totalPages - 2) {
        pages.push('...')
      }

      // Siempre mostrar última página
      pages.push(totalPages)
    }

    return pages
  }

  if (totalPages <= 1) return null

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-t border-border pt-4 mt-4">
      {/* Info de resultados */}
      <div></div>
      {/* Controles de paginación */}
      <div className="flex items-center justify-center gap-2 order-1 sm:order-2 mb-2">
        {/* Botón anterior */}
        <button
          onClick={onPrev}
          disabled={!hasPrevPage}
          className="p-2 sm:p-2.5 rounded-lg border border-border hover:bg-muted transition-colors disabled:opacity-50 disabled:cursor-not-allowed min-w-[2.5rem] sm:min-w-0"
          title="Página anterior"
        >
          <i className="fa-solid fa-chevron-left text-xs sm:text-sm"></i>
        </button>

        {/* Números de página - Desktop */}
        <div className="hidden md:flex items-center gap-1">
          {getPageNumbers().map((page, index) => (
            <div key={index}>
              {page === '...' ? (
                <span className="px-3 py-2 text-muted-foreground">...</span>
              ) : (
                <button
                  onClick={() => onPageChange(page as number)}
                  className={`min-w-[2.5rem] px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    currentPage === page
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted text-foreground border border-transparent hover:border-border'
                  }`}
                >
                  {page}
                </button>
              )}
            </div>
          ))}
        </div>

        {/* Indicador de página - Tablet */}
        <div className="hidden sm:flex md:hidden items-center gap-2 px-3 py-2">
          <span className="text-sm font-medium text-foreground">{currentPage}</span>
          <span className="text-xs text-muted-foreground">/</span>
          <span className="text-sm text-muted-foreground">{totalPages}</span>
        </div>

        {/* Indicador de página - Mobile con selector */}
        <div className="sm:hidden flex items-center gap-2">
          <select
            value={currentPage}
            onChange={(e) => onPageChange(Number(e.target.value))}
            className="px-3 py-2 text-sm font-medium bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
          >
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
              <option key={page} value={page}>
                {page} de {totalPages}
              </option>
            ))}
          </select>
        </div>

        {/* Botón siguiente */}
        <button
          onClick={onNext}
          disabled={!hasNextPage}
          className="p-2 sm:p-2.5 rounded-lg border border-border hover:bg-muted transition-colors disabled:opacity-50 disabled:cursor-not-allowed min-w-[2.5rem] sm:min-w-0"
          title="Página siguiente"
        >
          <i className="fa-solid fa-chevron-right text-xs sm:text-sm"></i>
        </button>
      </div>
    </div>
  )
}