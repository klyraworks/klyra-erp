// frontend/src/modules/inventario/components/movimientos-section.tsx

"use client"

import {useEffect, useRef} from "react"
import * as echarts from "echarts"
import {useMovimientos} from "@/src/core/store"
import {useTheme} from "@/src/core/theme/provider"
import type {MovimientoInventario} from "@/src/core/api/types"
import {usePagination} from '@/hooks/use-pagination'
import {Pagination} from '@/components/shared/Pagination'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger
} from "@/components/ui/dropdown-menu"

export function MovimientosPorTipoChart({movimientos}: { movimientos: MovimientoInventario[] | undefined }) {
    const chartRef = useRef<HTMLDivElement>(null)
    const {theme} = useTheme()

    useEffect(() => {
        if (!chartRef.current || !movimientos || movimientos.length === 0) return

        const chart = echarts.init(chartRef.current, theme === "dark" ? "dark" : undefined, {renderer: "svg"})

        const movPorTipo = movimientos.reduce(
            (acc, m) => {
                const tipo = m.tipo || "otro"
                acc[tipo] = (acc[tipo] || 0) + 1
                return acc
            },
            {} as Record<string, number>,
        )

        const tipoColors: Record<string, string> = {
            entrada: "#65B879",
            salida: "#212842",
            ajuste: "#f59e0b",
            transferencia: "#3b82f6",
            otro: "#6b7280",
        }

        const data = Object.entries(movPorTipo).map(([tipo, count]) => ({
            name: tipo.charAt(0).toUpperCase() + tipo.slice(1),
            value: count,
            itemStyle: {color: tipoColors[tipo] || "#6b7280"},
        }))

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
                orient: "vertical",
                right: 10,
                top: "center",
                textStyle: {color: theme === "dark" ? "#9ca3af" : "#6c757d", fontSize: 11},
            },
            series: [
                {
                    type: "pie",
                    radius: ["40%", "65%"],
                    center: ["35%", "50%"],
                    avoidLabelOverlap: false,
                    itemStyle: {
                        borderRadius: 4,
                        borderColor: theme === "dark" ? "#1f2937" : "#fff",
                        borderWidth: 2,
                    },
                    label: {show: false},
                    data: data,
                },
            ],
        })

        const handleResize = () => chart.resize()
        window.addEventListener("resize", handleResize)
        return () => {
            window.removeEventListener("resize", handleResize)
            chart.dispose()
        }
    }, [movimientos, theme])

    if (!movimientos || movimientos.length === 0) {
        return (
            <div className="h-[200px] flex items-center justify-center text-muted-foreground">
                <p className="text-sm">Sin movimientos registrados</p>
            </div>
        )
    }

    return <div ref={chartRef} className="w-full h-[200px]"/>
}

export function MovimientosPorFechaChart({movimientos}: { movimientos: MovimientoInventario[] | undefined }) {
    const chartRef = useRef<HTMLDivElement>(null)
    const {theme} = useTheme()

    useEffect(() => {
        if (!chartRef.current || !movimientos || movimientos.length === 0) return

        const chart = echarts.init(chartRef.current, theme === "dark" ? "dark" : undefined, {renderer: "svg"})

        const movPorFecha = movimientos.reduce(
            (acc, m) => {
                const fecha = m.fecha_local.split('T')[0]
                if (!acc[fecha]) acc[fecha] = {entrada: 0, salida: 0}
                if (m.tipo === "entrada") acc[fecha].entrada += 1
                else if (m.tipo === "salida") acc[fecha].salida += 1
                return acc
            },
            {} as Record<string, { entrada: number; salida: number }>,
        )

        const sortedDates = Object.keys(movPorFecha).sort()
        const entradas = sortedDates.map((d) => movPorFecha[d].entrada)
        const salidas = sortedDates.map((d) => movPorFecha[d].salida)

        chart.setOption({
            backgroundColor: "transparent",
            tooltip: {
                trigger: "axis",
                backgroundColor: theme === "dark" ? "#374151" : "#212842",
                borderColor: theme === "dark" ? "#374151" : "#212842",
                textStyle: {color: "#f0e7d5"},
            },
            legend: {
                data: ["Entradas", "Salidas"],
                bottom: 0,
                textStyle: {color: theme === "dark" ? "#9ca3af" : "#6c757d"},
            },
            grid: {left: 40, right: 20, top: 20, bottom: 50},
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
                axisLabel: {color: theme === "dark" ? "#9ca3af" : "#6c757d"},
            },
            series: [
                {
                    name: "Entradas",
                    type: "bar",
                    stack: "total",
                    data: entradas,
                    itemStyle: {color: "#65B879", borderRadius: [4, 4, 0, 0]},
                },
                {
                    name: "Salidas",
                    type: "bar",
                    stack: "total",
                    data: salidas,
                    itemStyle: {color: "#212842", borderRadius: [4, 4, 0, 0]},
                },
            ],
        })

        const handleResize = () => chart.resize()
        window.addEventListener("resize", handleResize)
        return () => {
            window.removeEventListener("resize", handleResize)
            chart.dispose()
        }
    }, [movimientos, theme])

    if (!movimientos || movimientos.length === 0) {
        return (
            <div className="h-[200px] flex items-center justify-center text-muted-foreground">
                <p className="text-sm">Sin movimientos registrados</p>
            </div>
        )
    }

    return <div ref={chartRef} className="w-full h-[200px]"/>
}

const getTipoConfig = (tipo: string) => {
    switch (tipo?.toLowerCase()) {
        case "entrada":
            return {color: "text-emerald-600 dark:text-emerald-400", bg: "bg-emerald-500/10", icon: "fa-arrow-down", label: "Entrada"}
        case "salida":
            return {color: "text-destructive", bg: "bg-destructive/10", icon: "fa-arrow-up", label: "Salida"}
        case "ajuste":
            return {color: "text-yellow-600 dark:text-yellow-400", bg: "bg-yellow-500/10", icon: "fa-sliders", label: "Ajuste"}
        case "transferencia":
            return {color: "text-primary", bg: "bg-primary/10", icon: "fa-right-left", label: "Transferencia"}
        default:
            return {color: "text-muted-foreground", bg: "bg-muted", icon: "fa-box", label: tipo || "N/A"}
    }
}

interface MovimeintosSectionProps {
    compact?: boolean
}

export function MovimientosSection({compact = false}: MovimeintosSectionProps) {
    const {data: movimientos, isLoading, error} = useMovimientos()

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
        data: movimientos || [],
        itemsPerPage: compact ? 5 : 10,
    })

    const displayMovimientos = compact ? movimientos?.slice(0, 5) : paginatedData

    if (error) {
        return (
            <div className="bg-card rounded-xl border border-border shadow-sm p-8 text-center">
                <div className="w-12 h-12 bg-destructive/10 rounded-full flex items-center justify-center mx-auto mb-3">
                    <i className="fa-solid fa-circle-exclamation text-xl text-destructive"></i>
                </div>
                <p className="text-sm font-medium text-foreground">Error al cargar movimientos</p>
                <p className="text-xs text-muted-foreground mt-1">Intenta recargar la página</p>
            </div>
        )
    }

    return (
        <div className="bg-card rounded-xl border border-border shadow-sm">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                <div className="flex items-center gap-3">
                    <div className="w-9 h-9 bg-primary/10 rounded-lg flex items-center justify-center">
                        <i className="fa-solid fa-truck-ramp-box text-primary text-sm"></i>
                    </div>
                    <div>
                        <h3 className="text-sm font-semibold text-foreground">Movimientos de Inventario</h3>
                        <p className="text-xs text-muted-foreground mt-0.5">
                            {isLoading ? "Cargando..." : `${movimientos?.length || 0} movimientos registrados`}
                        </p>
                    </div>
                </div>
            </div>

            {/* Body */}
            <div className="p-0">
                {isLoading ? (
                    <div className="p-6 space-y-3">
                        {[1, 2, 3, 4].map((i) => (
                            <div key={i} className="h-12 bg-muted/40 animate-pulse rounded-lg"></div>
                        ))}
                    </div>
                ) : !movimientos?.length ? (
                    <div className="py-16 text-center">
                        <div className="w-14 h-14 bg-muted/60 rounded-full flex items-center justify-center mx-auto mb-4">
                            <i className="fa-solid fa-inbox text-2xl text-muted-foreground/50"></i>
                        </div>
                        <p className="text-sm font-medium text-muted-foreground">Sin movimientos registrados</p>
                        <p className="text-xs text-muted-foreground/70 mt-1">Los movimientos aparecerán aquí cuando realices operaciones</p>
                    </div>
                ) : (
                    <>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="bg-muted/30 border-b border-border">
                                        <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider whitespace-nowrap">
                                            N.º Movimiento
                                        </th>
                                        <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                            Tipo
                                        </th>
                                        <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                            Referencia / Bodega
                                        </th>
                                        <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                            Fecha
                                        </th>
                                        {!compact && (
                                            <th className="py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider text-center w-16">
                                                <i className="fa-solid fa-ellipsis"></i>
                                            </th>
                                        )}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border/60">
                                    {displayMovimientos?.map((mov) => {
                                        const cfg = getTipoConfig(mov.tipo)
                                        const bodega = mov.bodega_origen_nombre || mov.bodega_destino_nombre || null
                                        return (
                                            <tr key={mov.id} className="hover:bg-muted/20 transition-colors group">
                                                {/* Número */}
                                                <td className="py-3.5 px-6">
                                                    <span className="font-mono text-xs font-semibold text-foreground bg-muted/50 px-2 py-1 rounded-md">
                                                        #{mov.numero}
                                                    </span>
                                                </td>

                                                {/* Tipo */}
                                                <td className="py-3.5 px-6">
                                                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${cfg.bg} ${cfg.color}`}>
                                                        <i className={`fa-solid ${cfg.icon} text-[9px]`}></i>
                                                        {cfg.label}
                                                    </span>
                                                </td>

                                                {/* Referencia + Bodega combinadas */}
                                                <td className="py-3.5 px-6">
                                                    <div className="flex flex-col">
                                                        <span className="text-sm text-foreground font-medium leading-snug">
                                                            {mov.referencia || <span className="text-muted-foreground/50 italic text-xs">Sin referencia</span>}
                                                        </span>
                                                        {bodega && (
                                                            <span className="text-xs text-muted-foreground mt-0.5 flex items-center gap-1">
                                                                <i className="fa-solid fa-warehouse text-[9px]"></i>
                                                                {bodega}
                                                            </span>
                                                        )}
                                                    </div>
                                                </td>

                                                {/* Fecha */}
                                                <td className="py-3.5 px-6">
                                                    <span className="text-xs text-muted-foreground tabular-nums">
                                                        {mov.fecha_local.split('T')[0]}
                                                    </span>
                                                </td>

                                                {/* Acciones */}
                                                {!compact && (
                                                    <td className="py-3.5 px-6 text-center">
                                                        <DropdownMenu>
                                                            <DropdownMenuTrigger asChild>
                                                                <button className="w-7 h-7 inline-flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors opacity-50 group-hover:opacity-100">
                                                                    <i className="fa-solid fa-ellipsis-vertical text-sm"></i>
                                                                </button>
                                                            </DropdownMenuTrigger>
                                                            <DropdownMenuContent align="end" className="w-44">
                                                                <DropdownMenuItem>
                                                                    <i className="fa-solid fa-eye mr-2 text-xs text-muted-foreground"></i>
                                                                    Ver detalles
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem>
                                                                    <i className="fa-solid fa-file-pdf mr-2 text-xs text-muted-foreground"></i>
                                                                    Descargar PDF
                                                                </DropdownMenuItem>
                                                                <DropdownMenuSeparator/>
                                                                <DropdownMenuItem className="text-destructive focus:text-destructive">
                                                                    <i className="fa-solid fa-ban mr-2 text-xs"></i>
                                                                    Anular movimiento
                                                                </DropdownMenuItem>
                                                            </DropdownMenuContent>
                                                        </DropdownMenu>
                                                    </td>
                                                )}
                                            </tr>
                                        )
                                    })}
                                </tbody>
                            </table>
                        </div>

                        {!compact && movimientos && movimientos.length > 0 && (
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