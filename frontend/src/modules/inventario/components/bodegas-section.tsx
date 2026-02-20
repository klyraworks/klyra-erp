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
    console.log(bodegas)

    if (error) {
        return (
            <div className="bg-card rounded-xl border border-border p-6">
                <div className="text-center text-destructive">
                    <i className="fa-solid fa-circle-exclamation text-2xl mb-2"></i>
                    <p>Error al cargar las bodegas</p>
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
                <span key="principal"
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
                    <i className="fa-solid fa-star text-[10px]"></i>
                    Principal
                </span>
            )
        }

        if (bodega.permite_ventas) {
            badges.push(
                <span key="ventas"
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-500/10 text-green-600">
                    <i className="fa-solid fa-cart-shopping text-[10px]"></i>
                    Ventas
                </span>
            )
        }

        if (!bodega.is_active) {
            badges.push(
                <span key="inactiva"
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-500/10 text-red-600">
                    <i className="fa-solid fa-ban text-[10px]"></i>
                    Inactiva
                </span>
            )
        }

        return badges.length > 0 ? (
            <div className="flex flex-wrap gap-1">{badges}</div>
        ) : (
            <span className="text-xs text-muted-foreground">Normal</span>
        )
    }

    return (
        <div className="bg-card rounded-xl border border-border shadow-sm">
            <div className="flex items-center justify-between p-6 border-b border-border">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-muted rounded-lg flex items-center justify-center">
                        <i className="fa-solid fa-warehouse text-primary text-lg"></i>
                    </div>
                    <div>
                        <h3 className="font-semibold text-foreground">Bodegas y Almacenes</h3>
                        <p className="text-sm text-muted-foreground">
                            {bodegas?.length || 0} bodegas registradas
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
                ) : bodegas?.length === 0 ? (
                    <div className="text-center py-12">
                        <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
                            <i className="fa-solid fa-inbox text-3xl text-muted-foreground"></i>
                        </div>
                        <p className="text-muted-foreground font-medium">No hay bodegas registradas</p>
                        <p className="text-sm text-muted-foreground mt-1">Comienza creando tu primera bodega</p>
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
                                    Bodega
                                </th>
                                <th className="text-left py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                    Responsable
                                </th>
                                <th className="text-center py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                    Estado
                                </th>
                                {!compact && (
                                    <th className="text-center py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                        Acciones
                                    </th>
                                )}
                            </tr>
                            </thead>
                            <tbody className="divide-y divide-border">
                            {displayBodegas?.map((bodega: Bodega, index: number) => (
                                <tr key={bodega.id} className="hover:bg-muted/30 transition-colors">
                                    <td className="py-4 px-6">
                                        <span className="text-sm font-medium text-muted-foreground">
                                            {(currentPage - 1) * (compact ? 5 : 10) + index + 1}
                                        </span>
                                    </td>
                                    <td className="py-4 px-6">
                                        <div className="flex items-center gap-2">
                                            <div
                                                className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">
                                                <i className="fa-solid fa-barcode text-xs text-primary"></i>
                                            </div>
                                            <span className="text-sm font-mono font-medium text-foreground">
                                                {bodega.codigo}
                                            </span>
                                        </div>
                                    </td>
                                    <td className="py-4 px-6">
                                        <div className="flex flex-col">
                                            <span className="text-sm font-medium text-foreground">
                                                {bodega.nombre}
                                            </span>
                                            {(bodega.ciudad_nombre) && (
                                                <span className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
                                                    {bodega.ciudad_nombre ? `${bodega.ciudad_nombre} - ` : ''}
                                                </span>
                                            )}
                                        </div>
                                    </td>
                                    <td className="py-4 px-6">
                                        <div className="flex items-center gap-2">
                                            <div
                                                className="w-6 h-6 bg-muted rounded-full flex items-center justify-center">
                                                <i className="fa-solid fa-user text-[10px] text-muted-foreground"></i>
                                            </div>
                                            <span className="text-sm text-foreground">
                                                {bodega.responsable_nombre || 'Sin asignar'}
                                            </span>
                                        </div>
                                    </td>
                                    <td className="py-4 px-6 text-center">
                                        {renderEstado(bodega)}
                                    </td>
                                    {!compact && (
                                        <td className="py-4 px-6">
                                            <div className="flex items-center justify-center">
                                                <DropdownMenu>
                                                    <DropdownMenuTrigger asChild>
                                                        <button
                                                            className="w-8 h-8 flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors">
                                                            <i className="fa-solid fa-ellipsis-vertical text-sm"></i>
                                                        </button>
                                                    </DropdownMenuTrigger>
                                                    <DropdownMenuContent align="end" className="w-48">
                                                        <DropdownMenuItem onClick={() => handleEditBodega(bodega)}>
                                                            <i className="fa-solid fa-pen-to-square mr-2 text-sm"></i>
                                                            Editar
                                                        </DropdownMenuItem>
                                                        <DropdownMenuItem>
                                                            <i className="fa-solid fa-eye mr-2 text-sm"></i>
                                                            Ver inventario
                                                        </DropdownMenuItem>
                                                        <DropdownMenuSeparator/>
                                                        <DropdownMenuItem>
                                                            <i className="fa-solid fa-exchange-alt mr-2 text-sm"></i>
                                                            Ver movimientos
                                                        </DropdownMenuItem>
                                                        <DropdownMenuItem>
                                                            <i className="fa-solid fa-chart-line mr-2 text-sm"></i>
                                                            Reportes
                                                        </DropdownMenuItem>
                                                        <DropdownMenuSeparator/>
                                                        <DropdownMenuItem
                                                            className="text-destructive focus:text-destructive">
                                                            <i className="fa-solid fa-ban mr-2 text-sm"></i>
                                                            Desactivar
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

                {!compact && bodegas && bodegas.length > 0 && (
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
    )
}