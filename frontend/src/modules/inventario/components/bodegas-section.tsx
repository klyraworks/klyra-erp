"use client"

import {useEffect, useRef} from "react"
import {useBodegas } from "@/src/core/store"
import {usePagination} from '@/hooks/use-pagination'
import {Pagination} from '@/components/shared/Pagination'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger
} from "@/components/ui/dropdown-menu"
import type {Bodega} from "@/src/core/api/types"
import {useRouter} from "next/navigation"

interface BodegasSectionProps {
    compact?: boolean
}

export function BodegasSection({compact = false}: BodegasSectionProps) {
    const {data: bodegas, isLoading, error} = useBodegas()
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
        data: bodegas || [],
        itemsPerPage: compact ? 5 : 10,
    })

    const displayBodegas = compact ? bodegas?.slice(0, 5) : paginatedData

    const handleEditBodega = (bodega: Bodega) => {
        router.push(`/inventario/bodegas/${bodega.id}/editar`)
    }

    const renderEstado = (bodega: Bodega) => {
    const badges = []

    if (bodega.es_principal) {
        badges.push(
            <span key="principal" className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary">
                <i className="fa-solid fa-star text-[9px]"></i>
                Principal
            </span>
        )
    }

    if (bodega.permite_ventas) {
        badges.push(
            <span key="ventas" className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                <i className="fa-solid fa-cart-shopping text-[9px]"></i>
                Ventas
            </span>
        )
    }

    if (!bodega.is_active) {
        badges.push(
            <span key="inactiva" className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-destructive/10 text-destructive">
                <i className="fa-solid fa-ban text-[9px]"></i>
                Inactiva
            </span>
        )
    }

    return badges.length > 0 ? (
        <div className="flex flex-wrap justify-center gap-1">{badges}</div>
    ) : (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-muted text-muted-foreground">
            <i className="fa-solid fa-circle-check text-[9px]"></i>
            Normal
        </span>
    )
}

    if (error) {
        return (
            <div className="bg-card rounded-xl border border-border shadow-sm p-8 text-center">
                <div className="w-12 h-12 bg-destructive/10 rounded-full flex items-center justify-center mx-auto mb-3">
                    <i className="fa-solid fa-circle-exclamation text-xl text-destructive"></i>
                </div>
                <p className="text-sm font-medium text-foreground">Error al cargar las bodegas</p>
                <p className="text-xs text-muted-foreground mt-1">Intenta recargar la página</p>
            </div>
        )
    }

    return (
    <div className="bg-card rounded-xl border border-border shadow-sm">
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
            <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-primary/10 rounded-lg flex items-center justify-center">
                    <i className="fa-solid fa-warehouse text-primary text-sm"></i>
                </div>
                <div>
                    <h3 className="text-sm font-semibold text-foreground">Bodegas y Almacenes</h3>
                    <p className="text-xs text-muted-foreground mt-0.5">
                        {bodegas?.length || 0} bodegas registradas
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
            ) : bodegas?.length === 0 ? (
                <div className="py-16 text-center">
                    <div className="w-14 h-14 bg-muted/60 rounded-full flex items-center justify-center mx-auto mb-4">
                        <i className="fa-solid fa-inbox text-2xl text-muted-foreground/50"></i>
                    </div>
                    <p className="text-sm font-medium text-muted-foreground">No hay bodegas registradas</p>
                    <p className="text-xs text-muted-foreground/70 mt-1">Comienza creando tu primera bodega</p>
                </div>
            ) : (
                <>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="bg-muted/30 border-b border-border">
                                    <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider w-10">#</th>
                                    <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Código</th>
                                    <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Bodega</th>
                                    <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Responsable</th>
                                    <th className="text-center py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Estado</th>
                                    {!compact && (
                                        <th className="py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider text-center w-16">
                                            <i className="fa-solid fa-ellipsis"></i>
                                        </th>
                                    )}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border/60">
                                {displayBodegas?.map((bodega: Bodega, index: number) => (
                                    <tr key={bodega.id} className="hover:bg-muted/20 transition-colors group">
                                        <td className="py-3.5 px-6">
                                            <span className="text-xs font-medium text-muted-foreground tabular-nums">
                                                {(currentPage - 1) * (compact ? 5 : 10) + index + 1}
                                            </span>
                                        </td>
                                        <td className="py-3.5 px-6">
                                            <span className="font-mono text-xs font-semibold text-foreground bg-muted/50 px-2 py-1 rounded-md">
                                                {bodega.codigo}
                                            </span>
                                        </td>
                                        <td className="py-3.5 px-6">
                                            <div className="flex flex-col">
                                                <span className="text-sm font-medium text-foreground leading-snug">
                                                    {bodega.nombre}
                                                </span>
                                                {bodega.ciudad_nombre && (
                                                    <span className="text-xs text-muted-foreground mt-0.5">
                                                        {bodega.ciudad_nombre}
                                                    </span>
                                                )}
                                            </div>
                                        </td>
                                        <td className="py-3.5 px-6">
                                            <div className="flex items-center gap-2">
                                                <div className="w-6 h-6 bg-muted rounded-full flex items-center justify-center flex-shrink-0">
                                                    <i className="fa-solid fa-user text-[9px] text-muted-foreground"></i>
                                                </div>
                                                <span className="text-sm text-foreground">
                                                    {bodega.responsable_nombre || <span className="text-muted-foreground italic">Sin asignar</span>}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="py-3.5 px-6 text-center">
                                            {renderEstado(bodega)}
                                        </td>
                                        {!compact && (
                                            <td className="py-3.5 px-6 text-center">
                                                <DropdownMenu>
                                                    <DropdownMenuTrigger asChild>
                                                        <button className="w-7 h-7 inline-flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors opacity-50 group-hover:opacity-100">
                                                            <i className="fa-solid fa-ellipsis-vertical text-xs"></i>
                                                        </button>
                                                    </DropdownMenuTrigger>
                                                    <DropdownMenuContent align="end" className="w-48">
                                                        <DropdownMenuItem onClick={() => handleEditBodega(bodega)}>
                                                            <i className="fa-solid fa-pen-to-square mr-2 text-xs text-muted-foreground"></i>
                                                            Editar
                                                        </DropdownMenuItem>
                                                        <DropdownMenuItem>
                                                            <i className="fa-solid fa-eye mr-2 text-xs text-muted-foreground"></i>
                                                            Ver inventario
                                                        </DropdownMenuItem>
                                                        <DropdownMenuSeparator/>
                                                        <DropdownMenuItem>
                                                            <i className="fa-solid fa-exchange-alt mr-2 text-xs text-muted-foreground"></i>
                                                            Ver movimientos
                                                        </DropdownMenuItem>
                                                        <DropdownMenuItem>
                                                            <i className="fa-solid fa-chart-line mr-2 text-xs text-muted-foreground"></i>
                                                            Reportes
                                                        </DropdownMenuItem>
                                                        <DropdownMenuSeparator/>
                                                        <DropdownMenuItem className="text-destructive focus:text-destructive">
                                                            <i className="fa-solid fa-ban mr-2 text-xs"></i>
                                                            Desactivar
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

                    {!compact && bodegas && bodegas.length > 0 && (
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
)
}