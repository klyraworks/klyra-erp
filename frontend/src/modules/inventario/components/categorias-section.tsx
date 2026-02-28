"use client"

import {useEffect, useRef} from "react"
import * as echarts from "echarts"
import {useCategoriasArbolExpandido} from "@/src/core/store"
import {usePagination} from '@/hooks/use-pagination'
import {Pagination} from '@/components/shared/Pagination'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import type {Categoria, Producto} from "@/src/core/api/types";
import {useRouter} from "next/navigation";

interface CategoriasSectionProps {
    compact?: boolean
}

export function CategoriasSection({compact = false}: CategoriasSectionProps) {
    const {data: categorias, total, isLoading, error} = useCategoriasArbolExpandido()
    const router = useRouter()

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
        data: categorias || [],
        itemsPerPage: compact ? 5 : 10,
    })

    const displayCategorias = compact ? categorias?.slice(0, 5) : paginatedData

    const handleEditCategoria = (categoria: Categoria) => {
        router.push(`/inventario/categorias/${categoria.id}/editar`)
    }

    const renderJerarquia = (categoria: any) => {
    if (categoria.subcategorias && categoria.subcategorias.length > 0) {
        return (
            <div className="flex flex-col gap-1">
                <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
                    <i className="fa-solid fa-folder-tree text-[9px]"></i>
                    Padre
                </span>
                <ul className="space-y-0.5">
                    {categoria.subcategorias.map((sub: any) => (
                        <li key={sub.id} className="text-xs text-muted-foreground flex items-center gap-1.5">
                            <i className="fa-solid fa-circle text-[4px]"></i>
                            <span className="truncate">{sub.nombre}</span>
                        </li>
                    ))}
                </ul>
            </div>
        )
    }

    if (categoria.nivel > 1) {
        return (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary">
                <i className="fa-solid fa-arrow-turn-up rotate-90 text-[9px]"></i>
                Subcategoría
            </span>
        )
    }

    return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-muted text-muted-foreground">
            <i className="fa-solid fa-tag text-[9px]"></i>
            Simple
        </span>
    )
}

    if (error) {
        return (
            <div className="bg-card rounded-xl border border-border shadow-sm p-8 text-center">
                <div className="w-12 h-12 bg-destructive/10 rounded-full flex items-center justify-center mx-auto mb-3">
                    <i className="fa-solid fa-circle-exclamation text-xl text-destructive"></i>
                </div>
                <p className="text-sm font-medium text-foreground">Error al cargar las categorías</p>
                <p className="text-xs text-muted-foreground mt-1">Intenta recargar la página</p>
            </div>
        )
    }

    return (
        <>
            <div className="bg-card rounded-xl border border-border shadow-sm">
                <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-boxes-stacked text-primary text-sm"></i>
                        </div>
                        <div>
                            <h3 className="text-sm font-semibold text-foreground">Categorías de Productos</h3>
                            <p className="text-xs text-muted-foreground mt-0.5">
                                {categorias?.length || 0} categorías registradas
                            </p>
                        </div>
                    </div>
                </div>

                <div className="p-0">
                    {isLoading ? (
                        <div className="p-6 space-y-3">
                            {[1, 2, 3, 4].map((i) => (
                                <div key={i} className="h-12 bg-muted/40 animate-pulse rounded-lg"></div>
                            ))}
                        </div>
                    ) : categorias?.length === 0 ? (
                        <div className="py-16 text-center">
                            <div
                                className="w-14 h-14 bg-muted/60 rounded-full flex items-center justify-center mx-auto mb-4">
                                <i className="fa-solid fa-inbox text-2xl text-muted-foreground/50"></i>
                            </div>
                            <p className="text-sm font-medium text-muted-foreground">No hay categorías registradas</p>
                            <p className="text-xs text-muted-foreground/70 mt-1">Comienza creando tu primera
                                categoría</p>
                        </div>
                    ) : (
                        <>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                    <tr className="bg-muted/30 border-b border-border">
                                        <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider w-10">#</th>
                                        <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Código</th>
                                        <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Categoría</th>
                                        <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Jerarquía</th>
                                        {!compact && (
                                            <th className="py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider text-center w-16">
                                                <i className="fa-solid fa-ellipsis"></i>
                                            </th>
                                        )}
                                    </tr>
                                    </thead>
                                    <tbody className="divide-y divide-border/60">
                                    {displayCategorias?.map((categoria: any, index: number) => (
                                        <tr key={categoria.id} className="hover:bg-muted/20 transition-colors group">
                                            <td className="py-3.5 px-6">
                                                <span
                                                    className="text-xs font-medium text-muted-foreground tabular-nums">
                                                    {(currentPage - 1) * (compact ? 5 : 10) + index + 1}
                                                </span>
                                            </td>
                                            <td className="py-3.5 px-6">
                                                <span
                                                    className="font-mono text-xs font-semibold text-foreground bg-muted/50 px-2 py-1 rounded-md">
                                                    {categoria.codigo}
                                                </span>
                                            </td>
                                            <td className="py-3.5 px-6">
                                                <div className="flex flex-col">
                                                    <span className="text-sm font-medium text-foreground leading-snug">
                                                        {categoria.nombre}
                                                    </span>
                                                    {categoria.descripcion && (
                                                        <span
                                                            className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
                                                            {categoria.descripcion}
                                                        </span>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="py-3.5 px-6">
                                                {renderJerarquia(categoria)}
                                            </td>
                                            {!compact && (
                                                <td className="py-3.5 px-6 text-center">
                                                    <DropdownMenu>
                                                        <DropdownMenuTrigger asChild>
                                                            <button
                                                                className="w-7 h-7 inline-flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors opacity-50 group-hover:opacity-100">
                                                                <i className="fa-solid fa-ellipsis-vertical text-xs"></i>
                                                            </button>
                                                        </DropdownMenuTrigger>
                                                        <DropdownMenuContent align="end" className="w-48">
                                                            <DropdownMenuItem
                                                                onClick={() => handleEditCategoria(categoria)}>
                                                                <i className="fa-solid fa-pen-to-square mr-2 text-xs text-muted-foreground"></i>
                                                                Editar
                                                            </DropdownMenuItem>
                                                            <DropdownMenuItem>
                                                                <i className="fa-solid fa-eye mr-2 text-xs text-muted-foreground"></i>
                                                                Ver detalles
                                                            </DropdownMenuItem>
                                                            <DropdownMenuSeparator/>
                                                            <DropdownMenuItem>
                                                                <i className="fa-solid fa-sitemap mr-2 text-xs text-muted-foreground"></i>
                                                                Agregar subcategoría
                                                            </DropdownMenuItem>
                                                            <DropdownMenuItem>
                                                                <i className="fa-solid fa-image mr-2 text-xs text-muted-foreground"></i>
                                                                Cambiar imagen
                                                            </DropdownMenuItem>
                                                            <DropdownMenuSeparator/>
                                                            <DropdownMenuItem
                                                                className="text-destructive focus:text-destructive">
                                                                <i className="fa-solid fa-trash mr-2 text-xs"></i>
                                                                Eliminar
                                                            </DropdownMenuItem>
                                                        </DropdownMenuContent>
                                                    </DropdownMenu>
                                                </td>
                                            )}
                                        </tr>
                                    ))}
                                    </tbody>
                                </table>
                            </div>

                            {!compact && categorias && categorias.length > 0 && (
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
                        </>
                    )}
                </div>
            </div>
        </>
    )
}
