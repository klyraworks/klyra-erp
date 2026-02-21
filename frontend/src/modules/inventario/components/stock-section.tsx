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
            <div className="bg-card rounded-xl border border-border p-6">
                <div className="text-center text-destructive">
                    <i className="fa-solid fa-circle-exclamation text-2xl mb-2"></i>
                    <p>Error al cargar el stock</p>
                </div>
            </div>
        )
    }

    return (
        <>
            <div className="bg-card rounded-xl border border-border shadow-sm">
                <div className="flex items-center justify-between p-6 border-b border-border">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-muted rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-warehouse text-primary text-lg"></i>
                        </div>
                        <div>
                            <h3 className="font-semibold text-foreground">
                                {compact ? "Stock Crítico por Bodega" : "Stock"}
                            </h3>
                            <p className="text-sm text-muted-foreground">
                                {compact
                                    ? "Productos que necesitan reposición"
                                    : `${inventario?.length || 0} registros de inventario`}
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
                    ) : inventario?.length === 0 ? (
                        <div className="text-center py-12">
                            <div
                                className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
                                <i className="fa-solid fa-inbox text-3xl text-muted-foreground"></i>
                            </div>
                            <p className="text-muted-foreground font-medium">No hay inventario registrado</p>
                            <p className="text-sm text-muted-foreground mt-1">Los productos aparecerán aquí cuando
                                realices movimientos de inventario</p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto -mx-6">
                            <table className="w-full">
                                <thead>
                                <tr className="border-b border-border">
                                    <th className="text-left py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                        Código
                                    </th>
                                    <th className="text-left py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                        Producto
                                    </th>
                                    <th className="text-center py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                        Bodega
                                    </th>
                                    <th className="text-center py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                        Stock
                                    </th>
                                    {!compact && (
                                        <th className="text-center py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                            Reservado
                                        </th>
                                    )}
                                    {!compact && (
                                        <th className="text-center py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                            Acciones
                                        </th>
                                    )}
                                </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                {displayInventario?.map((item) => {
                                    const status = getStockStatus(item.estado_stock)
                                    return (
                                        <tr key={item.id} className="hover:bg-muted/30 transition-colors">
                                            <td className="py-4 px-6">
                                                <div className="flex items-center gap-2">
                                                    <div
                                                        className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">
                                                        <i className="fa-solid fa-barcode text-xs text-primary"></i>
                                                    </div>
                                                    <span className="text-sm font-mono font-medium text-foreground">
                                                        {item.producto_codigo}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="py-4 px-6">
                                                <div className="flex flex-col">
                                                    <span className="text-sm font-medium text-foreground">
                                                        {item.producto_nombre}
                                                    </span>
                                                    {item.categoria_nombre && (
                                                        <span
                                                            className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
                                                            {item.categoria_nombre}
                                                        </span>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="py-4 px-6">
                                                <div className="flex flex-col items-center gap-1">
                                                    <span className="text-sm font-medium text-foreground">
                                                        {item.bodega_nombre}
                                                    </span>
                                                    <span className="text-xs font-mono text-muted-foreground">
                                                        {item.bodega_codigo}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="py-4 px-6">
                                                <div className="flex flex-col items-center gap-1">
                                                    <span
                                                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${status.bg} ${status.color}`}>
                                                        {status.label}
                                                    </span>
                                                    <span className="text-sm font-semibold text-foreground">
                                                        {item.cantidad} {item.unidad_medida}
                                                    </span>
                                                </div>
                                            </td>
                                            {!compact && (
                                                <td className="py-4 px-6 text-center">
                                                    {item.stock_reservado > 0 ? (
                                                        <span
                                                            className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-orange-500/10 text-orange-600 dark:text-orange-400">
                                                            <i className="fa-solid fa-lock text-[10px] mr-1"></i>
                                                            {item.stock_reservado}
                                                        </span>
                                                    ) : (
                                                        <span className="text-xs text-muted-foreground">—</span>
                                                    )}
                                                </td>
                                            )}
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
                                                                <DropdownMenuItem onClick={() => {
                                                                    router.push(`/inventario/productos/${item.producto_id}`)
                                                                }}>
                                                                    <i className="fa-solid fa-eye mr-2 text-sm"></i>
                                                                    Ver detalles producto
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem onClick={() => {
                                                                    router.push(`/inventario/kardex?producto_id=${item.producto_id}&bodega_id=${item.bodega_id}`)
                                                                }}>
                                                                    <i className="fa-solid fa-clock-rotate-left mr-2 text-sm"></i>
                                                                    Ver kardex
                                                                </DropdownMenuItem>
                                                                <DropdownMenuSeparator/>
                                                                <DropdownMenuItem onClick={() => {
                                                                    router.push(`/inventario/movimientos/nuevo?tipo=entrada&bodega_id=${item.bodega_id}&producto_id=${item.producto_id}`)
                                                                }}>
                                                                    <i className="fa-solid fa-arrow-right-to-bracket mr-2 text-sm"></i>
                                                                    Registrar entrada
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem onClick={() => {
                                                                    router.push(`/inventario/movimientos/nuevo?tipo=salida&bodega_id=${item.bodega_id}&producto_id=${item.producto_id}`)
                                                                }}>
                                                                    <i className="fa-solid fa-arrow-right-from-bracket mr-2 text-sm"></i>
                                                                    Registrar salida
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem onClick={() => {
                                                                    router.push(`/inventario/movimientos/nuevo?tipo=transferencia&bodega_origen_id=${item.bodega_id}&producto_id=${item.producto_id}`)
                                                                }}>
                                                                    <i className="fa-solid fa-truck-ramp-box mr-2 text-sm"></i>
                                                                    Transferir a bodega
                                                                </DropdownMenuItem>
                                                                <DropdownMenuSeparator/>
                                                                <DropdownMenuItem onClick={() => {
                                                                    setSelectedInventario(item)
                                                                    setModalAjustarStock(true)
                                                                }}>
                                                                    <i className="fa-solid fa-sliders mr-2 text-sm"></i>
                                                                    Ajustar stock
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem onClick={() => {
                                                                    setSelectedInventario(item)
                                                                    setModalCambiarUbicacion(true)
                                                                }}>
                                                                    <i className="fa-solid fa-location-dot mr-2 text-sm"></i>
                                                                    Cambiar ubicación
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem onClick={() => {
                                                                    setSelectedInventario(item)
                                                                    setModalReservarStock(true)
                                                                }}>
                                                                    <i className="fa-solid fa-lock mr-2 text-sm"></i>
                                                                    Reservar stock
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

                    {!compact && inventario && inventario.length > 0 && (
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