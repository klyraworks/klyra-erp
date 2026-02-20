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

    if (error) {
        return (
            <div className="bg-card rounded-xl border border-border p-6">
                <div className="text-center text-destructive">
                    <i className="fa-solid fa-circle-exclamation text-2xl mb-2"></i>
                    <p>Error al cargar las categorías</p>
                </div>
            </div>
        )
    }

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
        itemsPerPage: compact ? 5 : 10, // 5 para compact, 10 para vista completa
    })

    const displayCategorias = compact ? categorias?.slice(0, 5) : paginatedData

    const handleEditCategoria = (categoria: Categoria) => {
        router.push(`/inventario/categorias/${categoria.id}/editar`)
    }

    const renderJerarquia = (categoria: any) => {
        // Es categoría padre (tiene subcategorías)
        if (categoria.subcategorias && categoria.subcategorias.length > 0) {
            return (
                <div className="flex items-start gap-2">
                    <div className="flex-1 min-w-0">
                        <div className={"flex items-center mb-1"}>
                            <i className="fa-solid fa-folder-tree text-[10px] mr-2"></i>
                            <div className="text-xs text-muted-foreground mb-1">Padre</div>
                        </div>
                        <ul className="space-y-0.5">
                            {categoria.subcategorias.map((sub: any) => (
                                <li key={sub.id} className="text-xs text-muted-foreground flex items-center gap-1.5">
                                    <i className="fa-solid fa-circle text-[4px]"></i>
                                    <span className="truncate">{sub.nombre}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            )
        }

        // Es categoría hija (nivel > 1)
        if (categoria.nivel > 1) {
            return (
                <div className="flex items-start gap-2">
                    <div className="w-5 h-5 rounded flex items-center justify-center flex-shrink-0">
                        <i className="fa-solid fa-arrow-turn-up text-[10px] rotate-90"></i>
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="text-xs text-muted-foreground">Subcategoría</div>
                    </div>
                </div>
            )
        }

        // Es categoría simple
        return (
            <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded bg-slate-500/10 flex items-center justify-center">
                    <i className="fa-solid fa-tag text-[10px] text-slate-600"></i>
                </div>
                <span className="text-xs font-medium text-slate-600">Simple</span>
            </div>
        )
    }

    return (
        <>
            <div className="bg-card rounded-xl border border-border shadow-sm">
                <div className="flex items-center justify-between p-6 border-b border-border">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-muted rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-boxes-stacked text-primary text-lg"></i>
                        </div>
                        <div>
                            <h3 className="font-semibold text-foreground">Categorías de Productos</h3>
                            <p className="text-sm text-muted-foreground">
                                {categorias?.length || 0} categorías registradas
                            </p>
                        </div>
                    </div>
                </div>

                <div className="p-6">
                    {isLoading ? (
                        <div className="space-y-3">
                            {[1, 2, 3].map((i) => (
                                <div key={i} className="h-16 bg-muted/50 animate-pulse rounded-lg"></div>
                            ))}
                        </div>
                    ) : categorias?.length === 0 ? (
                        <div className="text-center py-12">
                            <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
                                <i className="fa-solid fa-inbox text-3xl text-muted-foreground"></i>
                            </div>
                            <p className="text-muted-foreground font-medium">No hay categorías registradas</p>
                            <p className="text-sm text-muted-foreground mt-1">Comienza creando tu primera categoría</p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto -mx-6">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-border">
                                        <th className="text-left py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider w-10">
                                            #
                                        </th>
                                        <th className="text-left py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                            Código
                                        </th>
                                        <th className="text-left py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                            Categoría
                                        </th>
                                        <th className="text-left py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                            Jerarquía
                                        </th>
                                        {!compact && (
                                            <th className="text-center py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                                Acciones
                                            </th>
                                        )}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                    {displayCategorias?.map((categoria: any, index: number) => (
                                        <tr key={categoria.id} className="hover:bg-muted/30 transition-colors">
                                            <td className="py-4 px-6">
                                                <span className="text-sm font-medium text-muted-foreground">
                                                    {(currentPage - 1) * (compact ? 5 : 10) + index + 1}
                                                </span>
                                            </td>
                                            <td className="py-4 px-6">
                                                <div className="flex items-center gap-2">
                                                    <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">
                                                        <i className="fa-solid fa-hashtag text-xs text-primary"></i>
                                                    </div>
                                                    <span className="text-sm font-mono font-medium text-foreground">
                                                        {categoria.codigo}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="py-4 px-6">
                                                <div className="flex flex-col">
                                                    <span className="text-sm font-medium text-foreground">
                                                        {categoria.nombre}
                                                    </span>
                                                    {categoria.descripcion && (
                                                        <span className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
                                                            {categoria.descripcion}
                                                        </span>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="py-4 px-6">
                                                {renderJerarquia(categoria)}
                                            </td>
                                            {!compact && (
                                                <td className="py-4 px-6">
                                                    <div className="flex items-center justify-center">
                                                        <DropdownMenu>
                                                            <DropdownMenuTrigger asChild>
                                                                <button className="w-8 h-8 flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors">
                                                                    <i className="fa-solid fa-ellipsis-vertical text-sm"></i>
                                                                </button>
                                                            </DropdownMenuTrigger>
                                                            <DropdownMenuContent align="end" className="w-48">
                                                                <DropdownMenuItem onClick={() => handleEditCategoria(categoria)}>
                                                                    <i className="fa-solid fa-pen-to-square mr-2 text-sm"></i>
                                                                    Editar
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem>
                                                                    <i className="fa-solid fa-eye mr-2 text-sm"></i>
                                                                    Ver detalles
                                                                </DropdownMenuItem>
                                                                <DropdownMenuSeparator/>
                                                                <DropdownMenuItem>
                                                                    <i className="fa-solid fa-sitemap mr-2 text-sm"></i>
                                                                    Agregar subcategoría
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem>
                                                                    <i className="fa-solid fa-image mr-2 text-sm"></i>
                                                                    Cambiar imagen
                                                                </DropdownMenuItem>
                                                                <DropdownMenuSeparator/>
                                                                <DropdownMenuItem className="text-destructive focus:text-destructive">
                                                                    <i className="fa-solid fa-trash mr-2 text-sm"></i>
                                                                    Eliminar
                                                                </DropdownMenuItem>
                                                            </DropdownMenuContent>
                                                        </DropdownMenu>
                                                    </div>
                                                </td>
                                            )}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {!compact && categorias && categorias.length > 0 && (
                        <div className="mt-6">
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
            </div>
        </>
    )
}
