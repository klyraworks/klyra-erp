"use client"

import {useEffect, useRef, useState} from "react"
import * as echarts from "echarts"
import {useProductos, useStore, viewProducto, getEtiquetaProducto} from "@/src/core/store"
import {useTheme} from "@/src/core/theme/provider"
import type {Producto} from "@/src/core/api/types"
import {usePagination} from '@/hooks/use-pagination'
import {Pagination} from '@/components/shared/Pagination'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import {ProductoDetailModal} from "@/src/modules/inventario/modals/producto-detail-modal"
import {alertas} from "@/components/alerts/alertas-toast"
import {useRouter} from 'next/navigation'
import {DuplicarProductoModal} from "@/src/modules/inventario/modals/duplicar-producto-modal"
import {AgregarImagenModal} from "@/src/modules/inventario/modals/agregar-imagen-modal"
import {InventarioTotalModal} from "@/src/modules/inventario/modals/inventario-total-modal"

function StockDistributionChart({productos}: { productos: Producto[] | undefined }) {
    const chartRef = useRef<HTMLDivElement>(null)
    const {theme} = useTheme()

    useEffect(() => {
        if (!chartRef.current || !productos || productos.length === 0) return

        const chart = echarts.init(chartRef.current, theme === "dark" ? "dark" : undefined, {renderer: "svg"})

        const topProductos = [...productos].sort((a, b) => b.stock - a.stock).slice(0, 10)

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
                data: topProductos.map((p) => p.nombre.substring(0, 15) + (p.nombre.length > 15 ? "..." : "")),
                axisLine: {show: false},
                axisTick: {show: false},
                axisLabel: {color: theme === "dark" ? "#9ca3af" : "#6c757d", fontSize: 11},
            },
            series: [
                {
                    type: "bar",
                    data: topProductos.map((p) => ({
                        value: p.stock,
                        itemStyle: {
                            color: p.stock <= 5 ? "#dc2626" : p.stock <= 15 ? "#f59e0b" : theme === "dark" ? "#0DB8F5" : "#212842",
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
    }, [productos, theme])

    if (!productos || productos.length === 0) {
        return (
            <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                <p>Sin datos para mostrar</p>
            </div>
        )
    }

    return <div ref={chartRef} className="w-full h-[300px]"/>
}

function StockStatusChart({productos}: { productos: Producto[] | undefined }) {
    const chartRef = useRef<HTMLDivElement>(null)
    const {theme} = useTheme()

    useEffect(() => {
        if (!chartRef.current || !productos) return

        const chart = echarts.init(chartRef.current, theme === "dark" ? "dark" : undefined, {renderer: "svg"})

        const critico = productos.filter((p) => p.stock <= 5).length
        const bajo = productos.filter((p) => p.stock > 5 && p.stock <= 15).length
        const normal = productos.filter((p) => p.stock > 15).length

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
                        {value: critico, name: "Crítico (≤5)", itemStyle: {color: "#DC2626"}},
                        {value: bajo, name: "Bajo (6-15)", itemStyle: {color: "#f59e0b"}},
                        {
                            value: normal,
                            name: "Normal (>15)",
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
    }, [productos, theme])

    if (!productos || productos.length === 0) {
        return (
            <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                <p>Sin datos para mostrar</p>
            </div>
        )
    }

    return <div ref={chartRef} className="w-full h-[300px]"/>
}

interface ProductosSectionProps {
    compact?: boolean
}

export function ProductosSection({compact = false}: ProductosSectionProps) {
    const {data: productos, isLoading, error} = useProductos()

    const [selectedProducto, setSelectedProducto] = useState<Producto | null>(null)
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [loading, setLoading] = useState(false)
    const router = useRouter()
    const [modalDuplicar, setModalDuplicar] = useState(false)
    const [modalImagen, setModalImagen] = useState(false)
    const [modalInventarioTotal, setModalInventarioTotal] = useState(false)
    const [productoSeleccionado, setProductoSeleccionado] = useState<Producto | null>(null)

    const handleViewDetails = async (producto: Producto) => {
        setLoading(true)
        setIsModalOpen(true)

        try {
            const productoDetallado = await viewProducto(producto)
            setSelectedProducto(productoDetallado)
        } catch (error) {
            const mensaje = error instanceof Error ? error.message : "Error desconocido"
            alertas.error(mensaje, 'Error al cargar detalles:')
            setSelectedProducto(producto)
        } finally {
            setLoading(false)
        }
    }

    const handleEditProducto = (producto: Producto) => {
        router.push(`/inventario/productos/${producto.id}/editar`)
    }

    const getStockStatus = (stock: number) => {
        if (stock <= 5) return {color: "text-destructive", bg: "bg-destructive/10", label: "Crítico"}
        if (stock <= 15) return {color: "text-yellow-600 dark:text-yellow-400", bg: "bg-yellow-500/10", label: "Bajo"}
        return {color: "text-success", bg: "bg-success/10", label: "Normal"}
    }

    const getProductoTipo = (tipo: string) => {
        if (tipo === "kit") return {color: "text-[#8de4ff]", bg: "bg-[#8de4ff]/10", label: "Kit"}
        if (tipo === "simple") return {color: "text-[#B6D634]", bg: "bg-[#B6D634]/10", label: "Simple"}
        if (tipo === "servicio") return {color: "text-[#989ee3]", bg: "bg-[#989ee3]/10", label: "Servicio"}
        return {color: "text-success", bg: "bg-success/10", label: "Normal"}
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
        data: productos || [],
        itemsPerPage: compact ? 5 : 10, // 5 para compact, 10 para vista completa
    })

    const productos_criticos = productos?.filter((p) => p.stock <= p.stock_minimo);

    const displayProductos = compact ? productos_criticos?.slice(0, 5) : paginatedData

    if (error) {
        return (
            <div className="bg-card rounded-xl border border-border p-6">
                <div className="text-center text-destructive">
                    <i className="fa-solid fa-circle-exclamation text-2xl mb-2"></i>
                    <p>Error al cargar productos</p>
                </div>
            </div>
        )
    }

    return (
        <>
            {!compact && productos && productos.length > 0 && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                    <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">
                            TOP 10 PRODUCTOS POR STOCK
                        </h3>
                        <StockDistributionChart productos={productos}/>
                    </div>
                    <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">
                            ESTADO DE STOCK
                        </h3>
                        <StockStatusChart productos={productos}/>
                    </div>
                </div>
            )}

            <div className="bg-card rounded-xl border border-border shadow-sm">
                <div className="flex items-center justify-between p-6 border-b border-border">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-muted rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-boxes-stacked text-primary text-lg"></i>
                        </div>
                        <div>
                            <h3 className="font-semibold text-foreground">
                                {compact ? "Inventario" : "Gestión de Productos"}
                            </h3>
                            <p className="text-sm text-muted-foreground">
                                {compact ? "Productos con bajo stock" : `${productos?.length || 0} productos registrados`}
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
                    ) : productos?.length === 0 ? (
                        <div className="text-center py-12">
                            <div
                                className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
                                <i className="fa-solid fa-inbox text-3xl text-muted-foreground"></i>
                            </div>
                            <p className="text-muted-foreground font-medium">No hay productos registrados</p>
                            <p className="text-sm text-muted-foreground mt-1">Comienza agregando tu primer producto</p>
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
                                        Stock
                                    </th>
                                    {!compact && (
                                        <th className="text-center py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                            Categoría
                                        </th>
                                    )}
                                    <th className="text-right py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                        Precio
                                    </th>
                                    {!compact && (
                                        <th className="text-center py-3 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                            Acciones
                                        </th>
                                    )}
                                </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                {displayProductos?.map((producto) => {
                                    const status = getStockStatus(producto.stock)
                                    const tipo = getProductoTipo(producto.tipo)
                                    return (
                                        <tr key={producto.id} className="hover:bg-muted/30 transition-colors">
                                            <td className="py-4 px-6">
                                                <div className="flex items-center gap-2">
                                                    <div
                                                        className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">
                                                        <i className="fa-solid fa-barcode text-xs text-primary"></i>
                                                    </div>
                                                    <span className="text-sm font-mono font-medium text-foreground">
                                                        {producto.codigo}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="py-4 px-6">
                                                <div className="flex flex-col">
                                                    <span className="text-sm font-medium text-foreground">
                                                        {producto.nombre}
                                                    </span>
                                                    {producto.descripcion && (
                                                        <span
                                                            className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
                                                            {producto.descripcion}
                                                        </span>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="py-4 px-6">
                                                <div className="flex flex-col items-center gap-1">
                                                    <span
                                                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${status.bg} ${status.color}`}>
                                                        {status.label}
                                                    </span>
                                                    <span className="text-sm font-semibold text-foreground">
                                                        {producto.stock} {producto.unidad_medida}
                                                    </span>
                                                </div>
                                            </td>
                                            {!compact && (
                                                <td className="py-4 px-6">
                                                    <div className="flex flex-col items-center gap-1">
                                                        <span className="text-sm text-foreground">
                                                            {producto.categoria_nombre}
                                                        </span>
                                                        <span className="text-xs text-muted-foreground">
                                                            {tipo.label}
                                                        </span>
                                                    </div>
                                                </td>
                                            )}
                                            <td className="py-4 px-6 text-right text-sm font-medium text-foreground">
                                                ${Number.parseFloat(String(producto.precio_venta)).toFixed(2)}
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
                                                                <DropdownMenuItem
                                                                    onClick={() => handleViewDetails(producto)}>
                                                                    <i className="fa-solid fa-eye mr-2 text-sm"></i>
                                                                    Ver detalles
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem
                                                                    onClick={() => handleEditProducto(producto)}>
                                                                    <i className="fa-solid fa-pen-to-square mr-2 text-sm"></i>
                                                                    Editar
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem onClick={() => {
                                                                    setProductoSeleccionado(producto)
                                                                    setModalDuplicar(true)
                                                                }}>
                                                                    <i className="fa-solid fa-copy mr-2 text-sm"></i>
                                                                    Duplicar producto
                                                                </DropdownMenuItem>
                                                                <DropdownMenuSeparator/>
                                                                <DropdownMenuItem onClick={() => {
                                                                    setProductoSeleccionado(producto)
                                                                    setModalInventarioTotal(true)
                                                                }}>
                                                                    <i className="fa-solid fa-boxes-stacked mr-2 text-sm"></i>
                                                                    Ver inventario total
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem>
                                                                    <i className="fa-solid fa-clock-rotate-left mr-2 text-sm"></i>
                                                                    Historial
                                                                </DropdownMenuItem>
                                                                <DropdownMenuSeparator/>
                                                                <DropdownMenuItem onClick={() => {
                                                                    setProductoSeleccionado(producto)
                                                                    setModalImagen(true)
                                                                }}>
                                                                    <i className="fa-solid fa-image mr-2 text-sm"></i>
                                                                    Agregar imagen
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem onClick={async () => {
                                                                    try {
                                                                        const etiqueta = await getEtiquetaProducto(producto.id)
                                                                        console.log('Etiqueta:', etiqueta)
                                                                        alertas.info('Función de impresión pendiente de implementar', 'Info')
                                                                    } catch (error: any) {
                                                                        alertas.error(error.message, 'Error')
                                                                    }
                                                                }}>
                                                                    <i className="fa-solid fa-barcode mr-2 text-sm"></i>
                                                                    Imprimir etiqueta
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
                                    )
                                })}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {!compact && productos && productos.length > 0 && (
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

            <ProductoDetailModal
                producto={selectedProducto}
                open={isModalOpen}
                onOpenChange={setIsModalOpen}
            />
            <DuplicarProductoModal
                producto={productoSeleccionado}
                open={modalDuplicar}
                onOpenChange={setModalDuplicar}
            />
            <AgregarImagenModal
                producto={productoSeleccionado}
                open={modalImagen}
                onOpenChange={setModalImagen}
            />
            <InventarioTotalModal
                producto={productoSeleccionado}
                open={modalInventarioTotal}
                onOpenChange={setModalInventarioTotal}
            />
        </>
    )
}
