// components/select/select-klyra.tsx
import React, {useState, useRef, useEffect} from 'react'

interface SelectOption {
    value: string | number
    label: string
    icon?: string
    description?: string
    disabled?: boolean
}

interface SelectProps {
    options: SelectOption[]
    value?: string | number
    onChange: (value: string | number) => void
    onSearch?: (query: string) => void
    placeholder?: string
    label?: string
    error?: string
    disabled?: boolean
    required?: boolean
    searchable?: boolean
    loading?: boolean
    className?: string
    icon?: string
}

export function Select({
                           options,
                           value,
                           onChange,
                           onSearch,
                           placeholder = 'Selecciona una opción',
                           label,
                           error,
                           disabled = false,
                           required = false,
                           searchable = false,
                           loading = false,
                           className = '',
                           icon,
                       }: SelectProps) {
    const [isOpen, setIsOpen] = useState(false)
    const [searchTerm, setSearchTerm] = useState('')
    const selectRef = useRef<HTMLDivElement>(null)

    const selectedOption = options.find(opt => opt.value === value)

    // Filtrar opciones según búsqueda (solo si no hay onSearch)
    const filteredOptions = searchable && !onSearch
        ? options.filter(opt =>
            opt.label?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false
        )
        : options

    // Cerrar al hacer click fuera
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
                setIsOpen(false)
                setSearchTerm('')
            }
        }

        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside)
        } else {
            setSearchTerm('') // Limpiar cuando se cierra
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside)
        }
    }, [isOpen])

    // Ejecutar búsqueda cuando cambia el término
    useEffect(() => {
        if (!onSearch || !isOpen) return

        const timer = setTimeout(() => {
            onSearch(searchTerm)
        }, 500)

        return () => clearTimeout(timer)
    }, [searchTerm])

    const handleSelect = (option: SelectOption) => {
        if (!option.disabled) {
            onChange(option.value)
            setIsOpen(false)
            setSearchTerm('')
        }
    }

    return (
        <div className={`relative ${className}`} ref={selectRef}>
            {label && (
                <label className="block text-sm font-medium text-foreground mb-2">
                    {label}
                    {required && <span className="text-destructive ml-1">*</span>}
                </label>
            )}

            <button
                type="button"
                onClick={() => !disabled && setIsOpen(!isOpen)}
                disabled={disabled}
                className={`
          w-full flex items-center justify-between gap-2 px-4 py-2.5 
          bg-background border rounded-lg text-left
          transition-all duration-200
          ${disabled
                    ? 'opacity-50 cursor-not-allowed bg-muted'
                    : 'hover:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20'
                }
          ${error
                    ? 'border-destructive focus:ring-destructive/20'
                    : 'border-border'
                }
          ${isOpen ? 'border-primary ring-2 ring-primary/20' : ''}
        `}
            >
                <div className="flex items-center gap-2 flex-1 min-w-0">
                    {(icon || selectedOption?.icon) && (
                        <i className={`${selectedOption?.icon || icon} text-muted-foreground flex-shrink-0`}></i>
                    )}

                    {selectedOption ? (
                        <div className="flex flex-col min-w-0">
              <span className="text-sm text-foreground truncate">
                {selectedOption.label || 'Sin etiqueta'}
              </span>
                            {selectedOption.description && (
                                <span className="text-xs text-muted-foreground truncate">
                  {selectedOption.description}
                </span>
                            )}
                        </div>
                    ) : (
                        <span className="text-sm text-muted-foreground truncate">
              {placeholder}
            </span>
                    )}
                </div>

                <i className={`fa-solid fa-chevron-down text-xs text-muted-foreground transition-transform ${
                    isOpen ? 'rotate-180' : ''
                }`}></i>
            </button>

            {isOpen && (
                <div
                    className="absolute z-50 w-full mt-2 bg-card border border-border rounded-lg shadow-lg overflow-hidden">
                    {searchable && (
                        <div className="p-2 border-b border-border">
                            <div className="relative">
                                <i className="fa-solid fa-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-xs"></i>
                                <input
                                    type="text"
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    placeholder="Buscar..."
                                    className="w-full pl-9 pr-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                                    onClick={(e) => e.stopPropagation()}
                                />
                            </div>
                        </div>
                    )}

                    <div className="max-h-60 overflow-y-auto py-1">
                        {loading ? (
                            <div className="px-4 py-8 text-center text-sm text-muted-foreground">
                                <i className="fa-solid fa-spinner fa-spin text-2xl mb-2"></i>
                                <p>Buscando...</p>
                            </div>
                        ) : filteredOptions.length === 0 ? (
                            <div className="px-4 py-8 text-center text-sm text-muted-foreground">
                                <i className="fa-solid fa-inbox text-2xl mb-2"></i>
                                <p>No se encontraron opciones</p>
                            </div>
                        ) : (
                            filteredOptions.map((option) => (
                                <button
                                    key={option.value}
                                    type="button"
                                    onClick={() => handleSelect(option)}
                                    disabled={option.disabled}
                                    className={`
                                    w-full flex items-center gap-3 px-4 py-2.5 text-left
                                    transition-colors
                                    ${option.disabled
                                        ? 'opacity-50 cursor-not-allowed'
                                        : 'hover:bg-muted cursor-pointer'
                                    }
                                    ${option.value === value
                                        ? 'bg-primary/10 text-primary font-medium'
                                        : 'text-foreground'
                                    }
                                  `}
                                >
                                    {option.icon && (
                                        <i className={`${option.icon} flex-shrink-0 ${
                                            option.value === value ? 'text-primary' : 'text-muted-foreground'
                                        }`}></i>
                                    )}

                                    <div className="flex flex-col flex-1 min-w-0">
                                        <span className="text-sm truncate">
                                          {option.label || 'Sin etiqueta'}
                                        </span>
                                        {option.description && (
                                            <span className="text-xs text-muted-foreground truncate">
                                            {option.description}
                                          </span>
                                        )}
                                    </div>

                                    {option.value === value && (
                                        <i className="fa-solid fa-check text-primary flex-shrink-0"></i>
                                    )}
                                </button>
                            ))
                        )}
                    </div>
                </div>
            )}

            {error && (
                <p className="mt-1.5 text-xs text-destructive flex items-center gap-1">
                    <i className="fa-solid fa-circle-exclamation"></i>
                    {error}
                </p>
            )}
        </div>
    )
}

export function SimpleSelect({
                                 options,
                                 value,
                                 onChange,
                                 placeholder,
                                 disabled = false,
                                 className = '',
                             }: {
    options: Array<{ value: string | number; label: string }>
    value?: string | number
    onChange: (value: string | number) => void
    placeholder?: string
    disabled?: boolean
    className?: string
}) {
    return (
        <select
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            className={`
        w-full px-4 py-2.5 bg-background border border-border rounded-lg
        text-sm text-foreground
        focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary
        disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-muted
        ${className}
      `}
        >
            {placeholder && (
                <option value="" disabled>
                    {placeholder}
                </option>
            )}
            {options.map((option) => (
                <option key={option.value} value={option.value}>
                    {option.label}
                </option>
            ))}
        </select>
    )
}