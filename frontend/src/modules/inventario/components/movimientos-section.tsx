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
} from "@/components/ui/dropdown-menu";

function MovimientosPorTipoChart({movimientos}: { movimientos: MovimientoInventario[] | undefined }) {
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
                <p>Sin movimientos registrados</p>
            </div>
        )
    }

    return <div ref={chartRef} className="w-full h-[200px]"/>
}

function MovimientosPorFechaChart({movimientos}: { movimientos: MovimientoInventario[] | undefined }) {
    const chartRef = useRef<HTMLDivElement>(null)
    const {theme} = useTheme()

    useEffect(() => {
        if (!chartRef.current || !movimientos || movimientos.length === 0) return

        const chart = echarts.init(chartRef.current, theme === "dark" ? "dark" : undefined, {renderer: "svg"})

        const movPorFecha = movimientos.reduce(
            (acc, m) => {
                const fecha = m.fecha_local.split('T')[0]
                if (!acc[fecha]) {
                    acc[fecha] = {entrada: 0, salida: 0}
                }
                if (m.tipo === "entrada") {
                    acc[fecha].entrada += 1
                } else if (m.tipo === "salida") {
                    acc[fecha].salida += 1
                }
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
                <p>Sin movimientos registrados</p>
            </div>
        )
    }

    return <div ref={chartRef} className="w-full h-[200px]"/>
}

interface MovimeintosSectionProps {
    compact?: boolean
}

export function MovimientosSection({compact = false}: MovimeintosSectionProps) {
    const {data: movimientos, isLoading, error} = useMovimientos()

    const getTipoStyles = (tipo: string) => {
        switch (tipo?.toLowerCase()) {
            case "entrada":
                return {color: "text-success", bg: "bg-success/10", icon: "fa-arrow-down"}
            case "salida":
                return {color: "text-destructive", bg: "bg-destructive/10", icon: "fa-arrow-up"}
            case "ajuste":
                return {color: "text-yellow-600 dark:text-yellow-400", bg: "bg-yellow-500/10", icon: "fa-sliders"}
            case "transferencia":
                return {color: "text-primary", bg: "bg-primary/10", icon: "fa-right-left"}
            default:
                return {color: "text-muted-foreground", bg: "bg-muted", icon: "fa-box"}
        }
    }

    if (error) {
        return (
            <div className="bg-card rounded-xl border border-border p-6">
                <div className="text-center text-destructive">
                    <i className="fa-solid fa-circle-exclamation text-2xl mb-2"></i>
                    <p>Error al cargar movimientos</p>
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
        data: movimientos || [],
        itemsPerPage: compact ? 5 : 10, // 5 para compact, 10 para vista completa
    })

    const displayMovimientos = compact ? movimientos?.slice(0, 5) : paginatedData

    return (
        <>
            {movimientos && movimientos.length > 0 && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                    <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">
                            MOVIMIENTOS POR TIPO
                        </h3>
                        <MovimientosPorTipoChart movimientos={movimientos}/>
                    </div>
                    <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">
                            ACTIVIDAD DIARIA
                        </h3>
                        <MovimientosPorFechaChart movimientos={movimientos}/>
                    </div>
                </div>
            )}

            <div className="bg-card rounded-xl border border-border shadow-sm">
                <div className="flex items-center justify-between p-6 border-b border-border">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-muted rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-truck-ramp-box text-primary text-lg"></i>
                        </div>
                        <div>
                            <h3 className="font-semibold text-foreground">Movimientos de Inventario</h3>
                            <p className="text-sm text-muted-foreground">
                                {movimientos?.length || 0} movimientos registrados
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
                    ) : movimientos?.length === 0 ? (
                        <div className="text-center py-12">
                            <div
                                className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
                                <i className="fa-solid fa-inbox text-3xl text-muted-foreground"></i>
                            </div>
                            <p className="text-muted-foreground font-medium">No hay movimientos registrados</p>
                            <p className="text-sm text-muted-foreground mt-1">Los movimientos aparecerán aquí cuando
                                realices operaciones</p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto -mx-6">
                            <table className="w-full">
                                <thead>
                                <tr className="border-b border-border">
                                    <th className="text-left py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                        Número
                                    </th>
                                    <th className="text-left py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                        Tipo
                                    </th>
                                    <th className="text-left py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                        Referencia
                                    </th>
                                    <th className="text-left py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                        Bodega
                                    </th>
                                    <th className="text-left py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                        Fecha
                                    </th>
                                    {!compact && (
                                        <th className="text-center py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                            Acciones
                                        </th>
                                    )}
                                </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                {displayMovimientos?.map((mov) => {
                                    const tipoStyle = getTipoStyles(mov.tipo)
                                    return (
                                        <tr key={mov.id} className="hover:bg-muted/30 transition-colors">
                                            <td className="py-4 px-6">
                                                <div className="flex items-center gap-2">
                                                    <div
                                                        className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">
                                                        <i className="fa-solid fa-hashtag text-xs text-primary"></i>
                                                    </div>
                                                    <span className="text-sm font-mono font-medium text-foreground">
                                                        {mov.numero}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="py-4 px-6">
                                                <span
                                                    className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${tipoStyle.bg} ${tipoStyle.color}`}>
                                                    <i className={`fa-solid ${tipoStyle.icon} text-[10px]`}></i>
                                                    {mov.tipo?.toUpperCase() || "N/A"}
                                                </span>
                                            </td>
                                            <td className="py-4 px-6">
                                                <span className="text-sm text-muted-foreground">
                                                    {mov.referencia || "—"}
                                                </span>
                                            </td>
                                            <td className="py-4 px-6">
                                                <span className="text-sm font-medium text-foreground">
                                                    {mov.bodega_origen_nombre || mov.bodega_destino_nombre || "—"}
                                                </span>
                                            </td>
                                            <td className="py-4 px-6">
                                                <span className="text-sm text-muted-foreground">
                                                    {mov.fecha_local.split('T')[0]}
                                                </span>
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
                                                                <DropdownMenuItem>
                                                                    <i className="fa-solid fa-eye mr-2 text-sm"></i>
                                                                    Ver detalles
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem>
                                                                    <i className="fa-solid fa-file-pdf mr-2 text-sm"></i>
                                                                    Descargar PDF
                                                                </DropdownMenuItem>
                                                                <DropdownMenuSeparator/>
                                                                <DropdownMenuItem
                                                                    className="text-destructive focus:text-destructive">
                                                                    <i className="fa-solid fa-ban mr-2 text-sm"></i>
                                                                    Anular movimiento
                                                                </DropdownMenuItem>
                                                            </DropdownMenuContent>
                                                        </DropdownMenu>
                                                    </div>
                                                </td>
                                            )}
                                        </tr>
                                    )
                                })}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {!compact && movimientos && movimientos.length > 0 && (
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
