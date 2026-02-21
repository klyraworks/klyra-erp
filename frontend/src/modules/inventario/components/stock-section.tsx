// frontend/src/modules/inventario/components/stock-section.tsx
"use client"

import {useEffect, useRef, useState} from "react"
import * as echarts from "echarts"
import {useTheme} from "@/src/core/theme/provider"
import {usePagination} from '@/hooks/use-pagination'
import {Pagination} from '@/components/shared/Pagination'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import {alertas} from "@/components/alerts/alertas-toast"
import {useRouter} from 'next/navigation'
import {useStock} from "@/src/core/store"
import {AjustarStockBodegaModal} from "@/src/modules/inventario/modals/ajustar-stock-bodega-modal"
import {CambiarUbicacionModal} from "@/src/modules/inventario/modals/cambiar-ubicacion-modal"
import {ReservarStockModal} from "@/src/modules/inventario/modals/reservar-stock-modal"
import {StockItem} from "@/src/core/api/types"

export function StockPorBodegaChart({inventario}: { inventario: StockItem[] | undefined }) {
    const chartRef = useRef<HTMLDivElement>(null)
    const {theme} = useTheme()

    useEffect(() => {
        if (!chartRef.current || !inventario || inventario.length === 0) return

        const chart = echarts.init(chartRef.current, theme === "dark" ? "dark" : undefined, {renderer: "svg"})

        // Agrupar stock por bodega
        const stockPorBodega = inventario.reduce((acc, item) => {
            if (!acc[item.bodega_nombre]) {
                acc[item.bodega_nombre] = 0
            }
            acc[item.bodega_nombre] += item.cantidad
            return acc
        }, {} as Record<string, number>)

        const bodegas = Object.keys(stockPorBodega)
        const stocks = Object.values(stockPorBodega)

        chart.setOption({
            backgroundColor: "transparent",
            tooltip: {
                trigger: "axis",
                backgroundColor: theme === "dark" ? "#374151" : "#212842",
                borderColor: theme === "dark" ? "#374151" : "#212842",
                textStyle: {color: "#f0e7d5"},
                axisPointer: {type: "shadow"},
            },
            grid: {left: 120, right: 20, top: 10, bottom: 30},
            xAxis: {
                type: "value",
                axisLine: {show: false},
                axisTick: {show: false},
                splitLine: {lineStyle: {color: theme === "dark" ? "#374151" : "#e9ecef"}},
                axisLabel: {color: theme === "dark" ? "#9ca3af" : "#6c757d"},
            },
            yAxis: {
                type: "category",
                data: bodegas,
                axisLine: {show: false},
                axisTick: {show: false},
                axisLabel: {color: theme === "dark" ? "#9ca3af" : "#6c757d", fontSize: 11},
            },
            series: [
                {
                    type: "bar",
                    data: stocks.map((stock) => ({
                        value: stock,
                        itemStyle: {
                            color: theme === "dark" ? "#0DB8F5" : "#212842",
                        },
                    })),
                    barWidth: "60%",
                    itemStyle: {borderRadius: [0, 4, 4, 0]},
                },
            ],
        })

        const handleResize = () => chart.resize()
        window.addEventListener("resize", handleResize)
        return () => {
            window.removeEventListener("resize", handleResize)
            chart.dispose()
        }
    }, [inventario, theme])

    if (!inventario || inventario.length === 0) {
        return (
            <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                <p>Sin datos para mostrar</p>
            </div>
        )
    }

    return <div ref={chartRef} className="w-full h-[300px]"/>
}

export function EstadoStockChart({inventario}: { inventario: StockItem[] | undefined }) {
    const chartRef = useRef<HTMLDivElement>(null)
    const {theme} = useTheme()

    useEffect(() => {
        if (!chartRef.current || !inventario) return

        const chart = echarts.init(chartRef.current, theme === "dark" ? "dark" : undefined, {renderer: "svg"})

        const sin_stock = inventario.filter((i) => i.estado_stock === 'sin_stock').length
        const critico = inventario.filter((i) => i.estado_stock === 'critico').length
        const bajo = inventario.filter((i) => i.estado_stock === 'bajo').length
        const normal = inventario.filter((i) => i.estado_stock === 'normal').length

        chart.setOption({
            backgroundColor: "transparent",
            tooltip: {
                trigger: "item",
                backgroundColor: theme === "dark" ? "#374151" : "#212842",
                borderColor: theme === "dark" ? "#374151" : "#212842",
                textStyle: {color: "#f0e7d5"},
                formatter: "{b}: {c} productos ({d}%)",
            },
            legend: {
                top: '5%',
                left: 'center',
                textStyle: {color: theme === "dark" ? "#9ca3af" : "#6c757d", fontSize: 11},
            },
            series: [
                {
                    name: 'Estado de Stock',
                    type: 'pie',
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
                        {value: sin_stock, name: "Sin Stock", itemStyle: {color: "#94a3b8"}},
                        {value: critico, name: "Crítico", itemStyle: {color: "#DC2626"}},
                        {value: bajo, name: "Bajo", itemStyle: {color: "#f59e0b"}},
                        {
                            value: normal,
                            name: "Normal",
                            itemStyle: {color: theme === "dark" ? "#0DB8F5" : "#212842"}
                        },
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
    }, [inventario, theme])

    if (!inventario || inventario.length === 0) {
        return (
            <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                <p>Sin datos para mostrar</p>
            </div>
        )
    }

    return <div ref={chartRef} className="w-full h-[300px]"/>
}

interface StockSectionProps {
    compact?: boolean
}

export function StockSection({compact = false}: StockSectionProps) {
    const {data: inventario, isLoading, error} = useStock()
    const router = useRouter()
    const [selectedInventario, setSelectedInventario] = useState<StockItem | null>(null)
    const [modalAjustarStock, setModalAjustarStock] = useState(false)
    const [modalCambiarUbicacion, setModalCambiarUbicacion] = useState(false)
    const [modalReservarStock, setModalReservarStock] = useState(false)

    const getStockStatus = (estado: string) => {
        const estados = {
            'sin_stock': {
                color: "text-slate-600 dark:text-slate-400",
                bg: "bg-slate-500/10",
                label: "Sin Stock",
                icon: "fa-circle-xmark"
            },
            'critico': {
                color: "text-destructive",
                bg: "bg-destructive/10",
                label: "Crítico",
                icon: "fa-circle-exclamation"
            },
            'bajo': {
                color: "text-yellow-600 dark:text-yellow-400",
                bg: "bg-yellow-500/10",
                label: "Bajo",
                icon: "fa-triangle-exclamation"
            },
            'normal': {color: "text-success", bg: "bg-success/10", label: "Normal", icon: "fa-circle-check"}
        }
        return estados[estado as keyof typeof estados] || estados.normal
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
        data: inventario || [],
        itemsPerPage: compact ? 5 : 10,
    })

    const inventario_critico = inventario?.filter((i) => i.estado_stock === 'critico' || i.estado_stock === 'bajo')
    const displayInventario = compact ? inventario_critico?.slice(0, 5) : paginatedData

    if (error) {
    return (
        <div className="bg-card rounded-xl border border-border shadow-sm p-8 text-center">
            <div className="w-12 h-12 bg-destructive/10 rounded-full flex items-center justify-center mx-auto mb-3">
                <i className="fa-solid fa-circle-exclamation text-xl text-destructive"></i>
            </div>
            <p className="text-sm font-medium text-foreground">Error al cargar el stock</p>
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
                        <i className="fa-solid fa-warehouse text-primary text-sm"></i>
                    </div>
                    <div>
                        <h3 className="text-sm font-semibold text-foreground">
                            {compact ? "Stock Crítico por Bodega" : "Stock"}
                        </h3>
                        <p className="text-xs text-muted-foreground mt-0.5">
                            {compact
                                ? "Productos que necesitan reposición"
                                : `${inventario?.length || 0} registros de inventario`}
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
                ) : inventario?.length === 0 ? (
                    <div className="py-16 text-center">
                        <div className="w-14 h-14 bg-muted/60 rounded-full flex items-center justify-center mx-auto mb-4">
                            <i className="fa-solid fa-inbox text-2xl text-muted-foreground/50"></i>
                        </div>
                        <p className="text-sm font-medium text-muted-foreground">No hay inventario registrado</p>
                        <p className="text-xs text-muted-foreground/70 mt-1">Los productos aparecerán aquí cuando realices movimientos de inventario</p>
                    </div>
                ) : (
                    <>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="bg-muted/30 border-b border-border">
                                        <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Código</th>
                                        <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Producto</th>
                                        <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Bodega</th>
                                        <th className="text-center py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Stock</th>
                                        {!compact && (
                                            <th className="text-center py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Reservado</th>
                                        )}
                                        {!compact && (
                                            <th className="py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider text-center w-16">
                                                <i className="fa-solid fa-ellipsis"></i>
                                            </th>
                                        )}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border/60">
                                    {displayInventario?.map((item) => {
                                        const status = getStockStatus(item.estado_stock)
                                        return (
                                            <tr key={item.id} className="hover:bg-muted/20 transition-colors group">
                                                {/* Código */}
                                                <td className="py-3.5 px-6">
                                                    <span className="font-mono text-xs font-semibold text-foreground bg-muted/50 px-2 py-1 rounded-md">
                                                        {item.producto_codigo}
                                                    </span>
                                                </td>

                                                {/* Producto + categoría */}
                                                <td className="py-3.5 px-6">
                                                    <div className="flex flex-col">
                                                        <span className="text-sm font-medium text-foreground leading-snug">
                                                            {item.producto_nombre}
                                                        </span>
                                                        {item.categoria_nombre && (
                                                            <span className="text-xs text-muted-foreground mt-0.5">
                                                                {item.categoria_nombre}
                                                            </span>
                                                        )}
                                                    </div>
                                                </td>

                                                {/* Bodega + código bodega */}
                                                <td className="py-3.5 px-6">
                                                    <div className="flex flex-col">
                                                        <span className="text-sm font-medium text-foreground leading-snug">
                                                            {item.bodega_nombre}
                                                        </span>
                                                        <span className="text-xs font-mono text-muted-foreground mt-0.5">
                                                            {item.bodega_codigo}
                                                        </span>
                                                    </div>
                                                </td>

                                                {/* Stock + estado */}
                                                <td className="py-3.5 px-6">
                                                    <div className="flex flex-col items-center gap-1">
                                                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${status.bg} ${status.color}`}>
                                                            <i className={`fa-solid ${status.icon} text-[9px]`}></i>
                                                            {status.label}
                                                        </span>
                                                        <span className="text-xs font-semibold text-foreground tabular-nums">
                                                            {item.cantidad} {item.unidad_medida}
                                                        </span>
                                                    </div>
                                                </td>

                                                {/* Reservado */}
                                                {!compact && (
                                                    <td className="py-3.5 px-6 text-center">
                                                        {item.stock_reservado > 0 ? (
                                                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-orange-500/10 text-orange-600 dark:text-orange-400">
                                                                <i className="fa-solid fa-lock text-[9px]"></i>
                                                                {item.stock_reservado}
                                                            </span>
                                                        ) : (
                                                            <span className="text-xs text-muted-foreground">—</span>
                                                        )}
                                                    </td>
                                                )}

                                                {/* Acciones */}
                                                {!compact && (
                                                    <td className="py-3.5 px-6 text-center">
                                                        <DropdownMenu>
                                                            <DropdownMenuTrigger asChild>
                                                                <button className="w-7 h-7 inline-flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors opacity-50 group-hover:opacity-100">
                                                                    <i className="fa-solid fa-ellipsis-vertical text-xs"></i>
                                                                </button>
                                                            </DropdownMenuTrigger>
                                                            <DropdownMenuContent align="end" className="w-48">
                                                                <DropdownMenuItem onClick={() => router.push(`/inventario/productos/${item.producto_id}`)}>
                                                                    <i className="fa-solid fa-eye mr-2 text-xs text-muted-foreground"></i>
                                                                    Ver detalles producto
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem onClick={() => router.push(`/inventario/kardex?producto_id=${item.producto_id}&bodega_id=${item.bodega_id}`)}>
                                                                    <i className="fa-solid fa-clock-rotate-left mr-2 text-xs text-muted-foreground"></i>
                                                                    Ver kardex
                                                                </DropdownMenuItem>
                                                                <DropdownMenuSeparator/>
                                                                <DropdownMenuItem onClick={() => router.push(`/inventario/movimientos/nuevo?tipo=entrada&bodega_id=${item.bodega_id}&producto_id=${item.producto_id}`)}>
                                                                    <i className="fa-solid fa-arrow-right-to-bracket mr-2 text-xs text-muted-foreground"></i>
                                                                    Registrar entrada
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem onClick={() => router.push(`/inventario/movimientos/nuevo?tipo=salida&bodega_id=${item.bodega_id}&producto_id=${item.producto_id}`)}>
                                                                    <i className="fa-solid fa-arrow-right-from-bracket mr-2 text-xs text-muted-foreground"></i>
                                                                    Registrar salida
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem onClick={() => router.push(`/inventario/movimientos/nuevo?tipo=transferencia&bodega_origen_id=${item.bodega_id}&producto_id=${item.producto_id}`)}>
                                                                    <i className="fa-solid fa-truck-ramp-box mr-2 text-xs text-muted-foreground"></i>
                                                                    Transferir a bodega
                                                                </DropdownMenuItem>
                                                                <DropdownMenuSeparator/>
                                                                <DropdownMenuItem onClick={() => { setSelectedInventario(item); setModalAjustarStock(true) }}>
                                                                    <i className="fa-solid fa-sliders mr-2 text-xs text-muted-foreground"></i>
                                                                    Ajustar stock
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem onClick={() => { setSelectedInventario(item); setModalCambiarUbicacion(true) }}>
                                                                    <i className="fa-solid fa-location-dot mr-2 text-xs text-muted-foreground"></i>
                                                                    Cambiar ubicación
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem onClick={() => { setSelectedInventario(item); setModalReservarStock(true) }}>
                                                                    <i className="fa-solid fa-lock mr-2 text-xs text-muted-foreground"></i>
                                                                    Reservar stock
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

                        {!compact && inventario && inventario.length > 0 && (
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

            <AjustarStockBodegaModal
                inventario={selectedInventario}
                open={modalAjustarStock}
                onOpenChange={setModalAjustarStock}
            />
            <CambiarUbicacionModal
                inventario={selectedInventario}
                open={modalCambiarUbicacion}
                onOpenChange={setModalCambiarUbicacion}
            />
            <ReservarStockModal
                inventario={selectedInventario}
                open={modalReservarStock}
                onOpenChange={setModalReservarStock}
            />
        </>
    )
}