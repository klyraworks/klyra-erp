// src/modules/ventas/ventas-section.tsx
"use client"

import {useState, useEffect, useRef} from "react"
import * as echarts from "echarts"
import {useVentas, useStore, useBodegas} from "@/src/core/store"
import {apiFetch} from "@/src/core/api/client"
import type {Venta} from "@/src/core/api/types"
import {useTheme} from "@/src/core/theme/provider"
import {mutate} from "swr"
import {NuevaVentaPage} from "../pages/venta-form"
import {usePagination} from '@/hooks/use-pagination'
import {Pagination} from '@/components/shared/Pagination'
import {Select} from '@/components/select/select-klyra'
import Link from "next/link";
import {alertas} from "@/components/alerts/alertas-toast"

function VentasStatusChart({ventas}: { ventas: Venta[] | undefined }) {
    const chartRef = useRef<HTMLDivElement>(null)
    const {theme} = useTheme()

    useEffect(() => {
        if (!chartRef.current || !ventas) return

        const chart = echarts.init(chartRef.current, theme === "dark" ? "dark" : undefined, {renderer: "svg"})

        const statusCounts = ventas.reduce(
            (acc, v) => {
                acc[v.estado] = (acc[v.estado] || 0) + 1
                return acc
            },
            {} as Record<string, number>,
        )

        const statusColors: Record<string, string> = {
            borrador: "#6b7280",
            confirmada: "#22c55e",
            facturada: "#0DB8F5",
            anulada: "#DC2626FF",
        }

        const sumaBorrador = ventas.filter((p) => p.estado === 'borrador').length;
        const sumaConfirmada = ventas.filter((p) => p.estado === 'confirmada').length;
        const sumaFacturada = ventas.filter((p) => p.estado === 'facturada').length;
        const sumaAnulada = ventas.filter((p) => p.estado === 'anulada').length;

        chart.setOption({
            backgroundColor: "transparent",
            tooltip: {
                trigger: "item",
                backgroundColor: theme === "dark" ? "#374151" : "#212842",
                borderColor: theme === "dark" ? "#374151" : "#212842",
                textStyle: {color: "#f0e7d5"},
                formatter: "{b}: {c} ({d}%)",
            },
            legend: {
                top: '5%',
                left: 'center',
                textStyle: {color: theme === "dark" ? "#9ca3af" : "#6c757d", fontSize: 11},
            },
            series: [
                {
                    name: "Estado de Ventas",
                    type: "pie",
                    radius: ['40%', '70%'],
                    top: '5%',
                    padAngle: 5,
                    avoidLabelOverlap: false,
                    itemStyle: {
                        borderRadius: 7,
                        borderColor: theme === "dark" ? "#1f2937" : "#fff",
                        borderWidth: 2,
                    },
                    data: [
                        {value: sumaBorrador, name: "Borrador", itemStyle: {color: "#6b7280"}},
                        {value: sumaConfirmada, name: "Confirmada", itemStyle: {color: "#22c55e"}},
                        {
                            value: sumaFacturada,
                            name: "Facturada",
                            itemStyle: {color: theme === "dark" ? "#0DB8F5" : "#212842"}
                        },
                        {value: sumaAnulada, name: "Anulada", itemStyle: {color: "#DC2626FF"}},
                    ],
                    emphasis: {
                        label: {
                            show: true,
                            fontSize: 10,
                            fontWeight: 'bold'
                        }
                    },
                    label: {
                        show: false,
                        position: 'center'
                    },
                    labelLine: {
                        show: false
                    },
                },
            ],
        })

        const handleResize = () => chart.resize()
        window.addEventListener("resize", handleResize)
        return () => {
            window.removeEventListener("resize", handleResize)
            chart.dispose()
        }
    }, [ventas, theme])

    if (!ventas || ventas.length === 0) {
        return (
            <div className="h-[200px] flex items-center justify-center text-muted-foreground">
                <p>Sin datos para mostrar</p>
            </div>
        )
    }

    return <div ref={chartRef} className="w-full h-[300px]"/>
}

function VentasPorFechaChart({ventas}: { ventas: Venta[] | undefined }) {
    const chartRef = useRef<HTMLDivElement>(null)
    const {theme} = useTheme()

    useEffect(() => {
        if (!chartRef.current || !ventas) return

        const chart = echarts.init(chartRef.current, theme === "dark" ? "dark" : undefined, {renderer: "svg"})

        const ventasPorFecha = ventas
            .filter((v) => v.estado !== "anulada")
            .reduce(
                (acc, v) => {
                    const fecha = v.fecha_local.split('T')[0]
                    if (!acc[fecha]) {
                        acc[fecha] = {total: 0, count: 0}
                    }
                    acc[fecha].total += Number.parseFloat(String(v.total))
                    acc[fecha].count += 1
                    return acc
                },
                {} as Record<string, { total: number; count: number }>,
            )

        const sortedDates = Object.keys(ventasPorFecha).sort()
        const totales = sortedDates.map((d) => ventasPorFecha[d].total)

        chart.setOption({
            backgroundColor: "transparent",
            tooltip: {
                trigger: "axis",
                backgroundColor: theme === "dark" ? "#374151" : "#212842",
                borderColor: theme === "dark" ? "#374151" : "#212842",
                textStyle: {color: "#f0e7d5"},
                formatter: (params: { name: string; value: number }[]) => {
                    const p = params[0]
                    const info = ventasPorFecha[p.name]
                    return `<div><strong>${p.name}</strong></div>
                  <div>Total: $${p.value.toFixed(2)}</div>
                  <div>Ventas: ${info?.count || 0}</div>`
                },
            },
            grid: {left: 60, right: 20, top: 20, bottom: 40},
            xAxis: {
                type: "category",
                data: sortedDates,
                axisLine: {show: false},
                axisTick: {show: false},
                axisLabel: {color: theme === "dark" ? "#9ca3af" : "#6c757d", fontSize: 10, rotate: 45},
            },
            yAxis: {
                type: "value",
                axisLine: {show: false},
                axisTick: {show: false},
                splitLine: {lineStyle: {color: theme === "dark" ? "#374151" : "#e9ecef"}},
                axisLabel: {color: theme === "dark" ? "#9ca3af" : "#6c757d", formatter: "${value}"},
            },
            series: [
                {
                    type: "bar",
                    data: totales,
                    barWidth: "60%",
                    itemStyle: {color: theme === "dark" ? "#0DB8F5" : "#212842", borderRadius: [4, 4, 0, 0]},
                },
            ],
        })

        const handleResize = () => chart.resize()
        window.addEventListener("resize", handleResize)
        return () => {
            window.removeEventListener("resize", handleResize)
            chart.dispose()
        }
    }, [ventas, theme])

    if (!ventas || ventas.length === 0) {
        return (
            <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                <p>Sin datos para mostrar</p>
            </div>
        )
    }

    return <div ref={chartRef} className="w-full h-[300px]"/>
}

interface VentasSectionProps {
    compact?: boolean
}

export function VentasSection({compact = false}: VentasSectionProps) {
    const {data: ventas, isLoading, error} = useVentas()
    const [showNuevaVenta, setShowNuevaVenta] = useState(false)
    const [showPaymentModal, setShowPaymentModal] = useState(false)
    const [showDispatchModal, setShowDispatchModal] = useState(false)
    const [selectedVenta, setSelectedVenta] = useState<Venta | null>(null)
    const [actionLoading, setActionLoading] = useState(false)

    if (showNuevaVenta) {
        return <NuevaVentaPage onBack={() => setShowNuevaVenta(false)}/>
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
        data: ventas || [],
        itemsPerPage: compact ? 5 : 10, // 5 para compact, 10 para vista completa
    })

    const displayVentas = compact ? ventas?.slice(0, 5) : paginatedData

    const getEstadoStyles = (estado: string) => {
        switch (estado) {
            case "confirmada":
                return "bg-success/10 text-success"
            case "pendiente":
                return "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400"
            case "borrador":
                return "bg-muted text-muted-foreground"
            case "facturada":
                return "bg-primary/10 text-primary"
            case "anulada":
                return "bg-destructive/10 text-destructive"
            default:
                return "bg-muted text-muted-foreground"
        }
    }

    const handleAnular = async (venta: Venta) => {
        const motivo = prompt("Motivo de anulación:")
        if (!motivo) return

        setActionLoading(true)
        try {
            await apiFetch(`/api/ventas/${venta.id}/anular/`, {
                method: "POST",
                body: JSON.stringify({motivo}),
            })

            mutate(["/api/ventas/"])
            alertas.success("Venta anulada exitosamente", "")
        } catch (err) {
            alert("Error al anular: " + (err as Error).message)
        } finally {
            setActionLoading(false)
        }
    }

    const openPaymentModal = (venta: Venta) => {
        setSelectedVenta(venta)
        setShowPaymentModal(true)
    }

    const openDispatchModal = (venta: Venta) => {
        setSelectedVenta(venta)
        setShowDispatchModal(true)
    }

    if (error) {
        return (
            <div className="bg-card rounded-xl border border-border p-6">
                <div className="text-center text-destructive">
                    <i className="fa-solid fa-circle-exclamation text-2xl mb-2"></i>
                    <p>Error al cargar ventas</p>
                </div>
            </div>
        )
    }

    return (
        <>
            {!compact && ventas && ventas.length > 0 && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                    <div className="bg-card rounded-xl border border-border p-6">
                        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
                            <i className="fa-solid fa-chart-pie mr-2"></i>
                            VENTAS POR ESTADO
                        </h3>
                        <VentasStatusChart ventas={ventas}/>
                    </div>
                    <div className="bg-card rounded-xl border border-border p-6">
                        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
                            <i className="fa-solid fa-chart-column mr-2"></i>
                            VENTAS POR FECHA
                        </h3>
                        <VentasPorFechaChart ventas={ventas}/>
                    </div>
                </div>
            )}

            <div className="bg-card rounded-xl border border-border p-6">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-muted rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-receipt text-primary"></i>
                        </div>
                        <div>
                            <h3 className="font-semibold text-foreground">{compact ? "Ventas Recientes" : "Gestión de Ventas"}</h3>
                            <p className="text-sm text-muted-foreground">
                                {compact ? "Últimas transacciones" : `${ventas?.length || 0} ventas registradas`}
                            </p>
                        </div>
                    </div>
                </div>

                {isLoading ? (
                    <div className="space-y-3">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="h-16 bg-muted animate-pulse rounded-lg"></div>
                        ))}
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                            <tr className="border-b border-border">
                                <th className="text-left py-3 px-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                    <i className="fa-solid fa-hashtag mr-1"></i>
                                    Número
                                </th>
                                <th className="text-left py-3 px-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                    <i className="fa-solid fa-calendar mr-1"></i>
                                    Fecha
                                </th>
                                <th className="text-left py-3 px-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                    <i className="fa-solid fa-user mr-1"></i>
                                    Cliente
                                </th>
                                <th className="text-left py-3 px-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                    <i className="fa-solid fa-circle-info mr-1"></i>
                                    Estado
                                </th>
                                <th className="text-right py-3 px-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                    <i className="fa-solid fa-dollar-sign mr-1"></i>
                                    Total
                                </th>
                                <th className="text-right py-3 px-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                    <i className="fa-solid fa-scale-unbalanced mr-1"></i>
                                    Saldo
                                </th>
                                {!compact && (
                                    <th className="text-right py-3 px-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                        <i className="fa-solid fa-gears mr-1"></i>
                                        Acciones
                                    </th>
                                )}
                            </tr>
                            </thead>
                            <tbody>
                            {displayVentas?.map((venta) => {
                                const saldo = Number.parseFloat(String(venta.saldo_pendiente || 0))
                                const total = Number.parseFloat(String(venta.total))
                                return (
                                    <tr key={venta.id}
                                        className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                                        <td className="py-3 px-2">
                                            <span className="font-medium text-primary text-sm">{venta.numero}</span>
                                        </td>
                                        <td className="py-3 px-2 text-sm text-muted-foreground">
                                            <div className="flex flex-col">
                            <span className="text-sm text-foreground font-medium">
                                {venta.fecha_local.split('T')[0]}
                            </span>
                                                <span className="text-xs text-muted-foreground">
                              {venta.fecha_local.split('T')[1]?.substring(0, 5)}
                          </span>
                                            </div>
                                        </td>
                                        <td className="py-3 px-2 text-sm text-foreground">
                                            {venta.cliente_nombre || "Consumidor Final"}
                                        </td>
                                        <td className="py-3 px-2">
                        <span
                            className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${getEstadoStyles(venta.estado)}`}
                        >
                          {venta.estado.charAt(0).toUpperCase() + venta.estado.slice(1)}
                        </span>
                                        </td>
                                        <td className="py-3 px-2 text-right text-sm font-medium text-foreground">${total.toFixed(2)}</td>
                                        <td
                                            className={`py-3 px-2 text-right text-sm font-medium ${saldo > 0 ? "text-destructive" : "text-success"}`}
                                        >
                                            ${saldo.toFixed(2)}
                                        </td>
                                        {!compact && (
                                            <td className="py-3 px-2 text-right">
                                                <div className="flex items-center justify-end gap-1">
                                                    {venta.estado === "borrador" && (
                                                        <button
                                                            onClick={() => openDispatchModal(venta)}
                                                            disabled={actionLoading}
                                                            className="p-1.5 text-primary hover:bg-primary/10 rounded transition-colors"
                                                            title="Despachar"
                                                        >
                                                            <i className="fa-solid fa-truck-fast text-sm"></i>
                                                        </button>
                                                    )}
                                                    {(venta.estado === "confirmada" || venta.estado === "facturada") && saldo > 0 && (
                                                        <button
                                                            onClick={() => openPaymentModal(venta)}
                                                            disabled={actionLoading}
                                                            className="p-1.5 text-success hover:bg-success/10 rounded transition-colors"
                                                            title="Registrar Pago"
                                                        >
                                                            <i className="fa-solid fa-money-bill-wave text-sm"></i>
                                                        </button>
                                                    )}
                                                    {venta.estado !== "anulada" && (
                                                        <button
                                                            onClick={() => handleAnular(venta)}
                                                            disabled={actionLoading}
                                                            className="p-1.5 text-destructive hover:bg-destructive/10 rounded transition-colors"
                                                            title="Anular"
                                                        >
                                                            <i className="fa-solid fa-ban text-sm"></i>
                                                        </button>
                                                    )}
                                                </div>
                                            </td>
                                        )}
                                    </tr>
                                )
                            })}
                            </tbody>
                        </table>
                        {!compact && (
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
                        )}
                    </div>
                )}
            </div>

            {showPaymentModal && selectedVenta && (
                <PaymentModal venta={selectedVenta} onClose={() => setShowPaymentModal(false)}/>
            )}
            {showDispatchModal && selectedVenta && (
                <DispatchModal venta={selectedVenta} onClose={() => setShowDispatchModal(false)}/>
            )}
        </>
    )
}

function PaymentModal({venta, onClose}: { venta: Venta; onClose: () => void }) {
    const [monto, setMonto] = useState(String(venta.saldo_pendiente || 0))
    const [metodo, setMetodo] = useState("efectivo")
    const [referencia, setReferencia] = useState("")
    const [loading, setLoading] = useState(false)
    const csrfToken = getCsrfToken()

    const handleSubmit = async () => {
        setLoading(true)
        try {
            await apiFetch(`/api/ventas/${venta.id}/registrar-pago/`, {
                method: "POST",
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    ...(csrfToken && {'X-CSRFToken': csrfToken})
                },
                body: JSON.stringify({
                    monto: Number.parseFloat(monto),
                    metodo,
                    referencia,
                }),
            })
            mutate(["/api/ventas/"])
            mutate(["/api/pagos/"])
            alertas.success("El pago ha sido registrado exitosamente", "Pago registrado")
            onClose()
        } catch (err) {
            alert("Error: " + (err as Error).message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-card rounded-xl border border-border w-full max-w-md">
                <div className="p-6 border-b border-border flex items-center justify-between">
                    <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
                        <i className="fa-solid fa-money-bill-wave text-success"></i>
                        Registrar Pago
                    </h2>
                    <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
                        <i className="fa-solid fa-xmark text-xl"></i>
                    </button>
                </div>

                <div className="p-6 space-y-4">
                    <div className="p-4 bg-muted rounded-lg">
                        <p className="text-sm text-muted-foreground">Venta</p>
                        <p className="font-semibold text-foreground">{venta.numero}</p>
                        <p className="text-sm text-muted-foreground mt-2">Saldo Pendiente</p>
                        <p className="text-xl font-bold text-destructive">${Number(venta.saldo_pendiente || 0).toFixed(2)}</p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                            <i className="fa-solid fa-dollar-sign mr-1"></i>
                            Monto a Pagar
                        </label>
                        <input
                            type="number"
                            value={monto}
                            onChange={(e) => setMonto(e.target.value)}
                            step="0.01"
                            className="w-full px-4 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                            <i className="fa-solid fa-credit-card mr-1"></i>
                            Método de Pago
                        </label>
                        <select
                            value={metodo}
                            onChange={(e) => setMetodo(e.target.value)}
                            className="w-full px-4 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                        >
                            <option value="efectivo">Efectivo</option>
                            <option value="transferencia">Transferencia</option>
                            <option value="tarjeta">Tarjeta</option>
                            <option value="cheque">Cheque</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                            <i className="fa-solid fa-hashtag mr-1"></i>
                            Referencia
                        </label>
                        <input
                            type="text"
                            value={referencia}
                            onChange={(e) => setReferencia(e.target.value)}
                            className="w-full px-4 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                            placeholder="Número de referencia (opcional)"
                        />
                    </div>
                </div>

                <div className="p-6 border-t border-border flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 border border-border rounded-lg text-sm font-medium text-foreground hover:bg-muted transition-colors"
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={loading}
                        className="px-4 py-2 bg-success text-white rounded-lg text-sm font-medium hover:bg-success/90 transition-colors disabled:opacity-50"
                    >
                        {loading ? "Procesando..." : "Registrar Pago"}
                    </button>
                </div>
            </div>
        </div>
    )
}

function DispatchModal({venta, onClose}: { venta: Venta; onClose: () => void }) {
    const {data: bodegas} = useBodegas()
    const [bodega, setBodega] = useState("")
    const [loading, setLoading] = useState(false)
    const [metodo, setMetodo] = useState("efectivo")
    const csrfToken = getCsrfToken()

    const bodegaPrincipal = bodegas?.find((b) => b.es_principal)

    const handleSubmit = async () => {
        if (!bodega) {
            alert("Selecciona una bodega")
            return
        }

        setLoading(true)
        try {
            // console.log(venta);
            await apiFetch(`/api/ventas/${venta.id}/despachar/`, {
                method: "POST",
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    ...(csrfToken && {'X-CSRFToken': csrfToken})
                },
                body: JSON.stringify({bodega}),
            })
            mutate(["/api/ventas/"])
            mutate(["/api/movimientos-inventario/"])
            alert("Venta despachada exitosamente")
            onClose()
        } catch (err) {
            alert("Error: " + (err as Error).message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-card rounded-xl border border-border w-full max-w-md">
                <div className="p-6 border-b border-border flex items-center justify-between">
                    <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
                        <i className="fa-solid fa-truck-fast text-primary"></i>
                        Despachar Venta
                    </h2>
                    <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
                        <i className="fa-solid fa-xmark text-xl"></i>
                    </button>
                </div>

                <div className="p-6 space-y-4">
                    <div className="bg-muted/50 rounded-lg p-4 space-y-2">
                        <p className="text-sm text-muted-foreground">
                            Venta: <span className="font-semibold text-foreground">{venta.numero}</span>
                        </p>
                        <p className="text-sm text-muted-foreground">
                            Total:{" "}
                            <span className="font-semibold text-foreground">
                            ${Number.parseFloat(String(venta.total)).toFixed(2)}
                          </span>
                        </p>
                        <p className="text-sm text-muted-foreground">
                            Bodega:{" "}
                            <span
                                className="font-semibold text-foreground">{bodegaPrincipal?.nombre || "No configurada"}</span>
                        </p>
                    </div>

                    <div>
                        <Select
                            label="Método de Pago"
                            options={[
                                {
                                    value: 'efectivo',
                                    label: 'Efectivo',
                                    icon: 'fa-solid fa-money-bill-wave'
                                },
                                {
                                    value: 'transferencia',
                                    label: 'Transferencia Bancaria',
                                    icon: 'fa-solid fa-building-columns'
                                },
                                {
                                    value: 'tarjeta',
                                    label: 'Tarjeta de Crédito/Débito',
                                    icon: 'fa-solid fa-credit-card'
                                },
                                {
                                    value: 'cheque',
                                    label: 'Cheque',
                                    icon: 'fa-solid fa-money-check'
                                },
                            ]}
                            value={metodo}
                            onChange={(value) => setMetodo(String(value))}
                            icon="fa-solid fa-credit-card"
                            required
                        />
                    </div>
                </div>

                <div className="p-6 border-t border-border flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-muted text-muted-foreground rounded-lg text-sm font-medium hover:bg-muted/80 transition-colors"
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={loading || !bodegaPrincipal}
                        className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
                    >
                        {loading && <i className="fa-solid fa-spinner fa-spin"></i>}
                        <i className="fa-solid fa-check"></i>
                        Confirmar Despacho
                    </button>
                </div>
            </div>
        </div>
    )
}
