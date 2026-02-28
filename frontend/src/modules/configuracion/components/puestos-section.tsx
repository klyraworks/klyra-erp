// frontend/src/modules/configuracion/components/puestos-section.tsx
"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { mutate } from "swr"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { alertas } from "@/components/alerts/alertas-toast"
import { apiFetch, ApiError } from "@/src/core/api/client"
import { usePuestos } from "@/src/core/store"
import { usePagination } from "@/hooks/use-pagination"
import { Pagination } from "@/components/shared/Pagination"

interface PuestosSectionProps {
    compact?: boolean
}

export function PuestosSection({ compact = false }: PuestosSectionProps) {
    const router = useRouter()
    const { data: puestos, isLoading, error } = usePuestos()

    const [deletingId, setDeletingId] = useState<string | null>(null)

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
        data: puestos || [],
        itemsPerPage: compact ? 5 : 10,
    })

    const displayPuestos = compact ? puestos?.slice(0, 5) : paginatedData

    const handleEliminar = async (id: string, nombre: string) => {
        if (!confirm(`¿Eliminar el puesto "${nombre}"? Esta acción no se puede deshacer.`)) return
        setDeletingId(id)
        try {
            await apiFetch(`/api/puestos/${id}/`, { method: "DELETE" })
            alertas.success("Puesto eliminado exitosamente", "Puesto Eliminado")
            await mutate(["/api/puestos/"])
        } catch (err) {
            if (err instanceof ApiError) alertas.error(err.mensaje, err.titulo)
            else alertas.error("Error desconocido al eliminar", "Error")
        } finally {
            setDeletingId(null)
        }
    }

    return (
        <div className="bg-card rounded-xl border border-border shadow-sm">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                <div className="flex items-center gap-3">
                    <div className="w-9 h-9 bg-primary/10 rounded-lg flex items-center justify-center">
                        <i className="fa-solid fa-briefcase text-primary text-sm"></i>
                    </div>
                    <div>
                        <h3 className="text-sm font-semibold text-foreground">Puestos</h3>
                        <p className="text-xs text-muted-foreground mt-0.5">
                            {isLoading ? "Cargando..." : `${totalItems} puesto${totalItems !== 1 ? "s" : ""} registrado${totalItems !== 1 ? "s" : ""}`}
                        </p>
                    </div>
                </div>
            </div>

            {/* Body */}
            <div className="p-0">
                {isLoading ? (
                    <div className="p-6 space-y-3">
                        {[1, 2, 3, 4, 5].map((i) => (
                            <div key={i} className="h-12 bg-muted/40 animate-pulse rounded-lg"></div>
                        ))}
                    </div>
                ) : error ? (
                    <div className="py-16 text-center">
                        <div className="w-12 h-12 bg-destructive/10 rounded-full flex items-center justify-center mx-auto mb-3">
                            <i className="fa-solid fa-circle-exclamation text-xl text-destructive"></i>
                        </div>
                        <p className="text-sm font-medium text-foreground">Error al cargar los datos</p>
                        <p className="text-xs text-muted-foreground mt-1">Intenta recargar la página</p>
                    </div>
                ) : !displayPuestos?.length ? (
                    <div className="py-16 text-center">
                        <div className="w-14 h-14 bg-muted/60 rounded-full flex items-center justify-center mx-auto mb-4">
                            <i className="fa-solid fa-briefcase text-2xl text-muted-foreground/50"></i>
                        </div>
                        <p className="text-sm font-medium text-muted-foreground">Sin puestos registrados</p>
                        <p className="text-xs text-muted-foreground/70 mt-1">Crea el primer puesto para comenzar</p>
                    </div>
                ) : (
                    <>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="bg-muted/30 border-b border-border">
                                        <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Código</th>
                                        <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Puesto</th>
                                        <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Departamento</th>
                                        <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Rango Salarial</th>
                                        <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Empleados</th>
                                        <th className="py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider text-center w-16">
                                            <i className="fa-solid fa-ellipsis"></i>
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border/60">
                                    {displayPuestos.map((item) => (
                                        <tr key={item.id} className="hover:bg-muted/20 transition-colors group">
                                            {/* Código */}
                                            <td className="py-3.5 px-6">
                                                <span className="font-mono text-xs font-semibold text-foreground bg-muted/50 px-2 py-1 rounded-md">
                                                    {item.codigo}
                                                </span>
                                            </td>

                                            {/* Nombre + descripción */}
                                            <td className="py-3.5 px-6">
                                                <div className="flex flex-col">
                                                    <span className="text-sm font-medium text-foreground leading-snug">{item.nombre}</span>
                                                    {item.descripcion && (
                                                        <span className="text-xs text-muted-foreground mt-0.5 line-clamp-1">{item.descripcion}</span>
                                                    )}
                                                </div>
                                            </td>

                                            {/* Departamento */}
                                            <td className="py-3.5 px-6">
                                                {item.departamento_nombre ? (
                                                    <span className="text-sm text-foreground">{item.departamento_nombre}</span>
                                                ) : (
                                                    <span className="text-xs text-muted-foreground/60 italic">Sin asignar</span>
                                                )}
                                            </td>

                                            {/* Rango salarial */}
                                            <td className="py-3.5 px-6">
                                                {item.salario_minimo || item.salario_maximo ? (
                                                    <div className="flex flex-col">
                                                        <span className="text-sm font-medium text-foreground">
                                                            ${Number(item.salario_minimo).toLocaleString("es-EC", { minimumFractionDigits: 2 })}
                                                        </span>
                                                        {item.salario_maximo && (
                                                            <span className="text-xs text-muted-foreground mt-0.5">
                                                                hasta ${Number(item.salario_maximo).toLocaleString("es-EC", { minimumFractionDigits: 2 })}
                                                            </span>
                                                        )}
                                                    </div>
                                                ) : (
                                                    <span className="text-xs text-muted-foreground/60 italic">No definido</span>
                                                )}
                                            </td>

                                            {/* Total empleados */}
                                            <td className="py-3.5 px-6">
                                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-muted/60 text-foreground">
                                                    <i className="fa-solid fa-users text-[9px]"></i>
                                                    {item.total_empleados}
                                                </span>
                                            </td>

                                            {/* Acciones */}
                                            <td className="py-3.5 px-6 text-center">
                                                <DropdownMenu>
                                                    <DropdownMenuTrigger asChild>
                                                        <button className="w-7 h-7 inline-flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors opacity-50 group-hover:opacity-100">
                                                            <i className="fa-solid fa-ellipsis-vertical text-xs"></i>
                                                        </button>
                                                    </DropdownMenuTrigger>
                                                    <DropdownMenuContent align="end" className="w-48">
                                                        <DropdownMenuItem onClick={() => router.push(`/configuracion/puestos/${item.id}/editar`)}>
                                                            <i className="fa-solid fa-pen-to-square mr-2 text-xs text-muted-foreground"></i>
                                                            Editar
                                                        </DropdownMenuItem>
                                                        <DropdownMenuSeparator />
                                                        <DropdownMenuItem
                                                            onClick={() => handleEliminar(item.id, item.nombre)}
                                                            disabled={deletingId === item.id}
                                                            className="text-destructive focus:text-destructive"
                                                        >
                                                            <i className="fa-solid fa-trash mr-2 text-xs"></i>
                                                            {deletingId === item.id ? "Eliminando..." : "Eliminar"}
                                                        </DropdownMenuItem>
                                                    </DropdownMenuContent>
                                                </DropdownMenu>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {!compact && puestos && puestos.length > 0 && (
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