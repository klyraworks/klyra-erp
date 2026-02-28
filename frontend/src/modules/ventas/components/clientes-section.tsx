"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { mutate } from "swr"
import { alertas } from "@/components/alerts/alertas-toast"
import { apiFetch, ApiError } from "@/src/core/api/client"
import { ClienteListItem, ClienteSaldo } from "@/src/core/api/types"
import { useClientes } from "@/src/core/store"
import { usePagination } from "@/hooks/use-pagination"
import { Pagination } from "@/components/shared/Pagination"
import {
    DropdownMenu,
    DropdownMenuTrigger,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"
import React from "react"

interface ClientesSectionProps {
    compact?: boolean
}

interface SaldoModalState {
    open: boolean
    cliente: ClienteListItem | null
    saldo: ClienteSaldo | null
    loading: boolean
}

export function ClientesSection({ compact = false }: ClientesSectionProps) {
    const router = useRouter()
    const { data: items, isLoading, error } = useClientes()

    const [saldoModal, setSaldoModal] = useState<SaldoModalState>({
        open: false,
        cliente: null,
        saldo: null,
        loading: false,
    })

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
        data: items || [],
        itemsPerPage: compact ? 5 : 10,
    })

    const displayItems = compact ? items?.slice(0, 5) : paginatedData

    const handleEditar = (id: string) => {
        router.push(`/ventas/clientes/${id}/editar`)
    }

    const handleEliminar = async (cliente: ClienteListItem) => {
        if (!confirm(`¿Eliminar a "${cliente.razon_social}"?`)) return
        try {
            await apiFetch(`/api/personas/clientes/${cliente.id}/`, { method: "DELETE" })
            alertas.success("Cliente eliminado", "Eliminado")
            await mutate(["/api/personas/clientes/"])
        } catch (err) {
            if (err instanceof ApiError) alertas.error(err.mensaje, err.titulo)
            else alertas.error("Error al eliminar el cliente", "Error")
        }
    }

    const handleCambiarEstado = async (cliente: ClienteListItem) => {
        try {
            await apiFetch(`/api/personas/clientes/${cliente.id}/cambiar_estado/`, { method: "PATCH" })
            alertas.success(
                cliente.is_active ? "Cliente desactivado" : "Cliente activado",
                "Estado actualizado"
            )
            await mutate(["/api/personas/clientes/"])
        } catch (err) {
            if (err instanceof ApiError) alertas.error(err.mensaje, err.titulo)
            else alertas.error("Error al cambiar el estado", "Error")
        }
    }

    const handleVerSaldo = async (cliente: ClienteListItem) => {
        setSaldoModal({ open: true, cliente, saldo: null, loading: true })
        try {
            const res = await apiFetch<{ success: boolean; data: ClienteSaldo }>(
                `/api/personas/clientes/${cliente.id}/saldo_credito/`
            )
            setSaldoModal(prev => ({ ...prev, saldo: res.data, loading: false }))
        } catch (err) {
            setSaldoModal(prev => ({ ...prev, loading: false }))
            if (err instanceof ApiError) alertas.error(err.mensaje, err.titulo)
            else alertas.error("Error al consultar el saldo", "Error")
        }
    }

    const closeSaldoModal = () =>
        setSaldoModal({ open: false, cliente: null, saldo: null, loading: false })

    const TIPO_LABELS: Record<string, string> = {
        natural: "Natural",
        juridica: "Jurídica",
    }

    const ID_LABELS: Record<string, string> = {
        ruc: "RUC",
        cedula: "Cédula",
        pasaporte: "Pasaporte",
        consumidor_final: "Consumidor Final",
    }

    return (
        <>
            <div className="bg-card rounded-xl border border-border shadow-sm">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-users text-primary text-sm"></i>
                        </div>
                        <div>
                            <h3 className="text-sm font-semibold text-foreground">Clientes</h3>
                            <p className="text-xs text-muted-foreground mt-0.5">
                                Gestión de clientes registrados
                            </p>
                        </div>
                    </div>
                </div>

                {/* Body */}
                <div className="p-0">
                    {isLoading ? (
                        <div className="flex items-center justify-center py-16">
                            <div className="flex flex-col items-center gap-3">
                                <i className="fa-solid fa-spinner fa-spin text-2xl text-muted-foreground"></i>
                                <p className="text-sm text-muted-foreground">Cargando clientes...</p>
                            </div>
                        </div>
                    ) : error ? (
                        <div className="flex items-center justify-center py-16">
                            <div className="flex flex-col items-center gap-3">
                                <i className="fa-solid fa-circle-exclamation text-2xl text-destructive"></i>
                                <p className="text-sm text-muted-foreground">Error al cargar los clientes</p>
                            </div>
                        </div>
                    ) : !displayItems?.length ? (
                        <div className="flex items-center justify-center py-16">
                            <div className="flex flex-col items-center gap-3">
                                <i className="fa-solid fa-users-slash text-2xl text-muted-foreground"></i>
                                <p className="text-sm text-muted-foreground">No hay clientes registrados</p>
                            </div>
                        </div>
                    ) : (
                        <>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="bg-muted/30 border-b border-border">
                                            <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                                Código
                                            </th>
                                            <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                                Cliente
                                            </th>
                                            <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                                Identificación
                                            </th>
                                            <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                                Tipo
                                            </th>
                                            <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                                Crédito
                                            </th>
                                            <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                                Estado
                                            </th>
                                            <th className="py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider text-center w-16">
                                                <i className="fa-solid fa-ellipsis"></i>
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-border/60">
                                        {displayItems.map((cliente) => (
                                            <tr
                                                key={cliente.id}
                                                className="hover:bg-muted/20 transition-colors group"
                                            >
                                                {/* Código */}
                                                <td className="py-3.5 px-6">
                                                    <span className="font-mono text-xs font-semibold text-foreground bg-muted/50 px-2 py-1 rounded-md">
                                                        {cliente.codigo}
                                                    </span>
                                                </td>

                                                {/* Razón Social */}
                                                <td className="py-3.5 px-6">
                                                    <span className="text-sm font-medium text-foreground leading-snug">
                                                        {cliente.razon_social}
                                                    </span>
                                                </td>

                                                {/* Identificación */}
                                                <td className="py-3.5 px-6">
                                                    <div className="flex flex-col">
                                                        <span className="text-sm font-medium text-foreground leading-snug">
                                                            {cliente.identificacion}
                                                        </span>
                                                        <span className="text-xs text-muted-foreground mt-0.5">
                                                            {ID_LABELS[cliente.tipo_identificacion] ?? cliente.tipo_identificacion}
                                                        </span>
                                                    </div>
                                                </td>

                                                {/* Tipo */}
                                                <td className="py-3.5 px-6">
                                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary">
                                                        <i className={`fa-solid ${cliente.tipo === "juridica" ? "fa-building" : "fa-user"} text-[9px]`}></i>
                                                        {TIPO_LABELS[cliente.tipo] ?? cliente.tipo}
                                                    </span>
                                                </td>

                                                {/* Crédito */}
                                                <td className="py-3.5 px-6">
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-sm font-medium text-foreground">
                                                            ${parseFloat(cliente.limite_credito).toFixed(2)}
                                                        </span>
                                                        <button
                                                            onClick={() => handleVerSaldo(cliente)}
                                                            className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-medium text-primary bg-primary/10 rounded hover:bg-primary/20 transition-colors"
                                                            title="Ver saldo de crédito"
                                                        >
                                                            <i className="fa-solid fa-chart-pie text-[9px]"></i>
                                                            Saldo
                                                        </button>
                                                    </div>
                                                </td>

                                                {/* Estado */}
                                                <td className="py-3.5 px-6">
                                                    {cliente.is_active ? (
                                                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600">
                                                            <i className="fa-solid fa-circle-check text-[9px]"></i>
                                                            Activo
                                                        </span>
                                                    ) : (
                                                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-destructive/10 text-destructive">
                                                            <i className="fa-solid fa-ban text-[9px]"></i>
                                                            Inactivo
                                                        </span>
                                                    )}
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
                                                            <DropdownMenuItem onClick={() => handleEditar(cliente.id)}>
                                                                <i className="fa-solid fa-pen-to-square mr-2 text-xs text-muted-foreground"></i>
                                                                Editar
                                                            </DropdownMenuItem>
                                                            <DropdownMenuItem onClick={() => handleCambiarEstado(cliente)}>
                                                                <i className={`fa-solid ${cliente.is_active ? "fa-ban" : "fa-circle-check"} mr-2 text-xs text-muted-foreground`}></i>
                                                                {cliente.is_active ? "Desactivar" : "Activar"}
                                                            </DropdownMenuItem>
                                                            <DropdownMenuSeparator />
                                                            <DropdownMenuItem
                                                                onClick={() => handleEliminar(cliente)}
                                                                className="text-destructive focus:text-destructive"
                                                            >
                                                                <i className="fa-solid fa-trash mr-2 text-xs"></i>
                                                                Eliminar
                                                            </DropdownMenuItem>
                                                        </DropdownMenuContent>
                                                    </DropdownMenu>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            {!compact && items && items.length > 0 && (
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

            {/* Modal Saldo de Crédito */}
            {saldoModal.open && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
                    onClick={closeSaldoModal}
                >
                    <div
                        className="bg-card rounded-xl border border-border shadow-xl w-full max-w-sm mx-4"
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Modal Header */}
                        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                            <div className="flex items-center gap-3">
                                <div className="w-9 h-9 bg-primary/10 rounded-lg flex items-center justify-center">
                                    <i className="fa-solid fa-chart-pie text-primary text-sm"></i>
                                </div>
                                <div>
                                    <h3 className="text-sm font-semibold text-foreground">Saldo de Crédito</h3>
                                    <p className="text-xs text-muted-foreground mt-0.5">
                                        {saldoModal.cliente?.razon_social}
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={closeSaldoModal}
                                className="w-7 h-7 inline-flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors"
                            >
                                <i className="fa-solid fa-xmark text-xs"></i>
                            </button>
                        </div>

                        {/* Modal Body */}
                        <div className="p-6">
                            {saldoModal.loading ? (
                                <div className="flex items-center justify-center py-8">
                                    <i className="fa-solid fa-spinner fa-spin text-2xl text-muted-foreground"></i>
                                </div>
                            ) : saldoModal.saldo ? (
                                <div className="space-y-1">
                                    <div className="flex items-center justify-between py-2 border-b border-border">
                                        <span className="text-xs text-muted-foreground flex items-center gap-2">
                                            <i className="fa-solid fa-credit-card"></i>
                                            Límite de crédito
                                        </span>
                                        <span className="text-sm font-semibold text-foreground">
                                            ${saldoModal.saldo.limite_credito.toFixed(2)}
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between py-2 border-b border-border">
                                        <span className="text-xs text-muted-foreground flex items-center gap-2">
                                            <i className="fa-solid fa-circle-check text-emerald-500"></i>
                                            Disponible
                                        </span>
                                        <span className="text-sm font-semibold text-emerald-600">
                                            ${saldoModal.saldo.credito_disponible.toFixed(2)}
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between py-2 border-b border-border">
                                        <span className="text-xs text-muted-foreground flex items-center gap-2">
                                            <i className="fa-solid fa-arrow-trend-up text-destructive"></i>
                                            Usado
                                        </span>
                                        <span className="text-sm font-semibold text-destructive">
                                            ${saldoModal.saldo.credito_usado.toFixed(2)}
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between py-2">
                                        <span className="text-xs text-muted-foreground flex items-center gap-2">
                                            <i className="fa-solid fa-percent"></i>
                                            % Utilizado
                                        </span>
                                        <div className="flex items-center gap-2">
                                            <div className="w-20 h-1.5 bg-muted rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-primary rounded-full"
                                                    style={{ width: `${Math.min(saldoModal.saldo.porcentaje_usado, 100)}%` }}
                                                />
                                            </div>
                                            <span className="text-xs font-semibold text-foreground">
                                                {saldoModal.saldo.porcentaje_usado.toFixed(1)}%
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ) : null}
                        </div>
                    </div>
                </div>
            )}
        </>
    )
}