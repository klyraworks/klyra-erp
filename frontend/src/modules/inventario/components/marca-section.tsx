// frontend/src/modules/inventario/components/marca-section.tsx

"use client"

import {useState} from "react"
import Link from "next/link"
import {alertas} from "@/components/alerts/alertas-toast"
import {apiFetch, ApiError} from "@/src/core/api/client"
import {MarcaListItem} from "@/src/core/api/types"
import useSWR, {mutate} from "swr"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {Pagination} from "@/components/shared/Pagination";
import {usePagination} from "@/hooks/use-pagination";
import {CheckboxKlyra} from "@/components/ui/checkbox-klyra";

const swrFetcher = (url: string) => apiFetch<{ results: MarcaListItem[]; count: number }>(url)

interface MarcasSectionProps {
    compact?: boolean
}

export function MarcasSection({compact = false}: MarcasSectionProps) {
    const [search, setSearch] = useState('')
    const [incluirInactivas, setIncluirInactivas] = useState(false)
    const [actionLoading, setActionLoading] = useState<string | null>(null)

    const params = new URLSearchParams()
    if (search) params.set('search', search)
    if (incluirInactivas) params.set('incluir_inactivas', 'true')
    const url = `/api/marcas/?${params.toString()}`

    const {data, isLoading, error} = useSWR<{ results: MarcaListItem[]; count: number }>(url, swrFetcher)
    const marcas = data?.results ?? []

    const {
        paginatedData,
        currentPage,
        totalPages,
        goToPage,
        nextPage,
        prevPage,
        hasNextPage,
        hasPrevPage,
        startIndex,
        endIndex,
        totalItems,
    } = usePagination({
        data: marcas || [],
        itemsPerPage: compact ? 5 : 10, // 5 para compact, 10 para vista completa
    })

    const displayMarcas = compact ? marcas?.slice(0, 5) : paginatedData

    const handleActivar = async (id: string) => {
        setActionLoading(id)
        try {
            await apiFetch(`/api/marcas/${id}/activar/`, {method: 'POST'})
            alertas.success('Marca activada exitosamente', 'Marca Activada')
            await mutate(url)  // ← misma referencia que la key del useSWR ✅
        } catch (err) {
            if (err instanceof ApiError) alertas.error(err.mensaje, err.titulo)
            else alertas.error('Error al activar la marca', 'Error')
        } finally {
            setActionLoading(null)
        }
    }

    const handleEliminar = async (id: string, nombre: string) => {
        alertas.confirm(
            `¿Estás seguro de que deseas desactivar la marca "${nombre}"?`,
            async () => {
                setActionLoading(id)
                try {
                    await apiFetch(`/api/marcas/${id}/`, {method: 'DELETE'})
                    alertas.success('Marca desactivada exitosamente', 'Marca Desactivada')
                    await mutate(url)
                } catch (err) {
                    if (err instanceof ApiError) alertas.error(err.mensaje, err.titulo)
                    else alertas.error('Error al desactivar la marca', 'Error')
                } finally {
                    setActionLoading(null)
                }
            },
            {title: 'Desactivar Marca'}
        )
    }

    return (
        <>
            {/* Filtros */}
            <div className="bg-card rounded-xl border border-border shadow-sm p-4 mb-6">
                <div className="flex flex-col sm:flex-row gap-3">
                    <div className="relative flex-1">
                        <i className="fa-solid fa-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm"></i>
                        <input
                            type="text"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            placeholder="Buscar por nombre, código o descripción..."
                            className="w-full pl-9 pr-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                        />
                    </div>
                    <CheckboxKlyra
                        checked={incluirInactivas}
                        onChange={(e) => setIncluirInactivas(e)}
                        label="Incluir inactivas"
                        className=""
                    />
                </div>
            </div>

            {/* Tabla */}
            <div className="bg-card rounded-xl border border-border shadow-sm">
                <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-tag text-primary text-sm"></i>
                        </div>
                        <div>
                            <h3 className="text-sm font-semibold text-foreground">Marcas</h3>
                            <p className="text-xs text-muted-foreground mt-0.5">
                                {isLoading ? 'Cargando...' : `${data?.count ?? 0} registros`}
                            </p>
                        </div>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                        <tr className="bg-muted/30 border-b border-border">
                            <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider w-10">#</th>
                            <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Marca</th>
                            <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Código</th>
                            <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">País
                                de Origen
                            </th>
                            <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Productos</th>
                            <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Estado</th>
                            <th className="py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider text-center w-16">
                                <i className="fa-solid fa-ellipsis"></i>
                            </th>
                        </tr>
                        </thead>
                        <tbody className="divide-y divide-border/60">
                        {isLoading ? (
                            [1, 2, 3, 4, 5].map((i) => (
                                <tr key={i}>
                                    {[1, 2, 3, 4, 5, 6, 7].map((j) => (
                                        <td key={j} className="py-3.5 px-6">
                                            <div className="h-4 bg-muted/40 animate-pulse rounded"></div>
                                        </td>
                                    ))}
                                </tr>
                            ))
                        ) : error ? (
                            <tr>
                                <td colSpan={7} className="py-16 text-center">
                                    <div
                                        className="w-12 h-12 bg-destructive/10 rounded-full flex items-center justify-center mx-auto mb-3">
                                        <i className="fa-solid fa-circle-exclamation text-xl text-destructive"></i>
                                    </div>
                                    <p className="text-sm font-medium text-foreground">Error al cargar las marcas</p>
                                    <p className="text-xs text-muted-foreground mt-1">Intenta recargar la página</p>
                                </td>
                            </tr>
                        ) : displayMarcas.length === 0 ? (
                            <tr>
                                <td colSpan={7} className="py-16 text-center">
                                    <div
                                        className="w-14 h-14 bg-muted/60 rounded-full flex items-center justify-center mx-auto mb-4">
                                        <i className="fa-solid fa-tag text-2xl text-muted-foreground/50"></i>
                                    </div>
                                    <p className="text-sm font-medium text-muted-foreground">No hay marcas
                                        registradas</p>
                                    <p className="text-xs text-muted-foreground/70 mt-1">Crea la primera marca para
                                        comenzar</p>
                                </td>
                            </tr>
                        ) : (
                            displayMarcas.map((marca, idx) => (
                                <tr key={marca.id} className="hover:bg-muted/20 transition-colors group">
                                    <td className="py-3.5 px-6">
                                        <span
                                            className="text-xs font-medium text-muted-foreground tabular-nums">{idx + 1}</span>
                                    </td>
                                    <td className="py-3.5 px-6">
                                        <div className="flex items-center gap-3">
                                            {marca.logo ? (
                                                <img src={marca.logo} alt={marca.nombre}
                                                     className="w-8 h-8 object-contain rounded-lg border border-border bg-muted/30 p-0.5 flex-shrink-0"/>
                                            ) : (
                                                <div
                                                    className="w-8 h-8 bg-muted rounded-lg flex items-center justify-center flex-shrink-0">
                                                    <i className="fa-solid fa-tag text-xs text-muted-foreground"></i>
                                                </div>
                                            )}
                                            <div className="flex flex-col">
                                                <span
                                                    className="text-sm font-medium text-foreground leading-snug">{marca.nombre}</span>
                                                {marca.descripcion && (
                                                    <span
                                                        className="text-xs text-muted-foreground mt-0.5 line-clamp-1">{marca.descripcion}</span>
                                                )}
                                            </div>
                                        </div>
                                    </td>
                                    <td className="py-3.5 px-6">
                                        <span
                                            className="font-mono text-xs font-semibold text-foreground bg-muted/50 px-2 py-1 rounded-md">
                                            {marca.codigo}
                                        </span>
                                    </td>
                                    <td className="py-3.5 px-6">
                                        {marca.pais_origen_nombre ? (
                                            <div className="flex items-center gap-2">
                                                <i className="fa-solid fa-earth-americas text-muted-foreground text-xs"></i>
                                                <span
                                                    className="text-sm text-foreground">{marca.pais_origen_nombre}</span>
                                            </div>
                                        ) : (
                                            <span className="text-xs text-muted-foreground">—</span>
                                        )}
                                    </td>
                                    <td className="py-3.5 px-6">
                                        <span
                                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary">
                                            <i className="fa-solid fa-box text-[9px]"></i>
                                            {marca.total_productos}
                                        </span>
                                    </td>
                                    <td className="py-3.5 px-6">
                                        {marca.is_active ? (
                                            <span
                                                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                                                <i className="fa-solid fa-circle-check text-[9px]"></i>Activa
                                            </span>
                                        ) : (
                                            <span
                                                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-destructive/10 text-destructive">
                                                <i className="fa-solid fa-ban text-[9px]"></i>Inactiva
                                            </span>
                                        )}
                                    </td>
                                    <td className="py-3.5 px-6 text-center">
                                        {actionLoading === marca.id ? (
                                            <div className="w-7 h-7 inline-flex items-center justify-center">
                                                <i className="fa-solid fa-spinner fa-spin text-muted-foreground text-xs"></i>
                                            </div>
                                        ) : (
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <button
                                                        className="w-7 h-7 inline-flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors opacity-50 group-hover:opacity-100">
                                                        <i className="fa-solid fa-ellipsis-vertical text-xs"></i>
                                                    </button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end" className="w-48">
                                                    <DropdownMenuItem asChild>
                                                        <Link href={`/inventario/marcas/${marca.id}/editar`}
                                                              className="flex items-center">
                                                            <i className="fa-solid fa-pen-to-square mr-2 text-xs text-muted-foreground"></i>
                                                            Editar
                                                        </Link>
                                                    </DropdownMenuItem>
                                                    <DropdownMenuSeparator/>
                                                    {marca.is_active ? (
                                                        <DropdownMenuItem
                                                            className="text-destructive focus:text-destructive"
                                                            onClick={() => handleEliminar(marca.id, marca.nombre)}
                                                        >
                                                            <i className="fa-solid fa-ban mr-2 text-xs"></i>
                                                            Desactivar
                                                        </DropdownMenuItem>
                                                    ) : (
                                                        <DropdownMenuItem onClick={() => handleActivar(marca.id)}>
                                                            <i className="fa-solid fa-circle-check mr-2 text-xs text-muted-foreground"></i>
                                                            Activar
                                                        </DropdownMenuItem>
                                                    )}
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                        )}
                                    </td>
                                </tr>
                            ))
                        )}
                        </tbody>
                    </table>
                </div>

                {!compact && marcas && marcas.length > 0 && (
                    <div className="px-6 py-4 border-t border-border">
                        <Pagination
                            currentPage={currentPage}
                            totalPages={totalPages}
                            onPageChange={goToPage}
                            onNext={nextPage}
                            onPrev={prevPage}
                            hasNextPage={hasNextPage}
                            hasPrevPage={hasPrevPage}
                            startIndex={startIndex}
                            endIndex={endIndex}
                            totalItems={totalItems}
                        />
                    </div>
                )}
            </div>
        </>
    )
}