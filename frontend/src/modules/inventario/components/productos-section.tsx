"use client"

import {useEffect, useRef, useState} from "react"
import * as echarts from "echarts"
import {useProductos, viewProducto, getEtiquetaProducto} from "@/src/core/store"
import {useTheme} from "@/src/core/theme/provider"
import type {Producto} from "@/src/core/api/types"
import {usePagination} from "@/hooks/use-pagination"
import {Pagination} from "@/components/shared/Pagination"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {ProductoDetailModal} from "@/src/modules/inventario/modals/producto-detail-modal"
import {DuplicarProductoModal} from "@/src/modules/inventario/modals/duplicar-producto-modal"
import {AgregarImagenModal} from "@/src/modules/inventario/modals/agregar-imagen-modal"
import {InventarioTotalModal} from "@/src/modules/inventario/modals/inventario-total-modal"
import {alertas} from "@/components/alerts/alertas-toast"
import {ApiError} from "@/src/core/api/client"
import {useRouter} from "next/navigation"


// ============================================================
// HELPERS — fuera del componente para evitar recreación
// ============================================================

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


// ============================================================
// CHARTS
// ============================================================

export function StockDistributionChart({productos}: { productos: Producto[] | undefined }) {
    const chartRef = useRef<HTMLDivElement>(null)
    const {theme} = useTheme()

    useEffect(() => {
        if (!chartRef.current || !productos || productos.length === 0) return

        const chart = echarts.init(chartRef.current, theme === "dark" ? "dark" : undefined, {renderer: "svg"})
        const topProductos = [...productos]
            .sort((a, b) => (b.stock_total ?? 0) - (a.stock_total ?? 0))
            .slice(0, 10)

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
                data: topProductos.map((p) =>
                    p.nombre.length > 15 ? p.nombre.substring(0, 15) + "..." : p.nombre
                ),
                axisLine: {show: false},
                axisTick: {show: false},
                axisLabel: {color: theme === "dark" ? "#9ca3af" : "#6c757d", fontSize: 11},
            },
            series: [{
                type: "bar",
                data: topProductos.map((p) => {
                    const stock = p.stock_total ?? 0
                    return {
                        value: stock,
                        itemStyle: {
                            color: stock <= 5 ? "#dc2626" : stock <= 15 ? "#f59e0b" : theme === "dark" ? "#0DB8F5" : "#212842",
                        },
                    }
                }),
                barWidth: "60%",
                itemStyle: {borderRadius: [0, 4, 4, 0]},
            }],
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

export function StockStatusChart({productos}: { productos: Producto[] | undefined }) {
    const chartRef = useRef<HTMLDivElement>(null)
    const {theme} = useTheme()

    useEffect(() => {
        if (!chartRef.current || !productos) return

        const chart = echarts.init(chartRef.current, theme === "dark" ? "dark" : undefined, {renderer: "svg"})

        const critico = productos.filter((p) => (p.stock_total ?? 0) <= 5).length
        const bajo = productos.filter((p) => (p.stock_total ?? 0) > 5 && (p.stock_total ?? 0) <= 15).length
        const normal = productos.filter((p) => (p.stock_total ?? 0) > 15).length

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
                top: "5%",
                left: "center",
                textStyle: {color: theme === "dark" ? "#9ca3af" : "#6c757d", fontSize: 11},
            },
            series: [{
                name: "Estado de Stock",
                type: "pie",
                radius: ["40%", "70%"],
                top: "5%",
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
                    {value: normal, name: "Normal (>15)", itemStyle: {color: theme === "dark" ? "#0DB8F5" : "#212842"}},
                ],
                emphasis: {label: {show: true, fontSize: 10, fontWeight: "bold"}},
                label: {show: false, position: "center"},
                labelLine: {show: false},
            }],
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


// ============================================================
// PRODUCTOS SECTION
// ============================================================

interface ProductosSectionProps {
    compact?: boolean
}

export function ProductosSection({compact = false}: ProductosSectionProps) {
    const {data: productos, isLoading, error} = useProductos()
    const router = useRouter()

    const [selectedProducto, setSelectedProducto] = useState<Producto | null>(null)
    const [productoSeleccionado, setProductoSeleccionado] = useState<Producto | null>(null)
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [modalDuplicar, setModalDuplicar] = useState(false)
    const [modalImagen, setModalImagen] = useState(false)
    const [modalInventarioTotal, setModalInventarioTotal] = useState(false)
    const [loadingDetalle, setLoadingDetalle] = useState(false)

    // Productos bajo stock mínimo — para modo compact
    const productosCriticos = productos?.filter(
        (p) => (p.stock_total ?? 0) <= p.stock_minimo
    )

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
        itemsPerPage: compact ? 5 : 10,
    })

    const displayProductos = compact ? productosCriticos?.slice(0, 5) : paginatedData

    const handleViewDetails = async (producto: Producto) => {
        setLoadingDetalle(true)
        setIsModalOpen(true)
        try {
            const productoDetallado = await viewProducto(producto)
            setSelectedProducto(productoDetallado)
        } catch (err) {
            if (err instanceof ApiError) {
                alertas.error(err.mensaje, err.titulo)
            } else {
                alertas.error('Error al cargar detalles', 'Error')
            }
            setSelectedProducto(producto) // fallback al producto básico
        } finally {
            setLoadingDetalle(false)
        }
    }

    const handleEtiqueta = async (id: string) => {
        try {
            await getEtiquetaProducto(id)
            alertas.info('Función de impresión pendiente de implementar', 'Info')
        } catch (err) {
            if (err instanceof ApiError) {
                alertas.error(err.mensaje, err.titulo)
            } else {
                alertas.error('Error al obtener etiqueta', 'Error')
            }
        }
    }

    if (error) {
        return (
            <div className="bg-card rounded-xl border border-border shadow-sm p-8 text-center">
                <div className="w-12 h-12 bg-destructive/10 rounded-full flex items-center justify-center mx-auto mb-3">
                    <i className="fa-solid fa-circle-exclamation text-xl text-destructive"></i>
                </div>
                <p className="text-sm font-medium text-foreground">Error al cargar productos</p>
                <p className="text-xs text-muted-foreground mt-1">Intenta recargar la página</p>
            </div>
        )
    }

    return (
        <>
            <div className="bg-card rounded-xl border border-border shadow-sm">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-boxes-stacked text-primary text-sm"></i>
                        </div>
                        <div>
                            <h3 className="text-sm font-semibold text-foreground">
                                {compact ? "Inventario" : "Gestión de Productos"}
                            </h3>
                            <p className="text-xs text-muted-foreground mt-0.5">
                                {compact
                                    ? "Productos con bajo stock"
                                    : `${productos?.length ?? 0} productos registrados`}
                            </p>
                        </div>
                    </div>
                </div>

                <div className="p-0">
                    {isLoading ? (
                        <div className="p-6 space-y-3">
                            {[1, 2, 3, 4].map((i) => (
                                <div key={i} className="h-12 bg-muted/40 animate-pulse rounded-lg"/>
                            ))}
                        </div>

                    ) : !productos?.length ? (
                        <div className="py-16 text-center">
                            <div
                                className="w-14 h-14 bg-muted/60 rounded-full flex items-center justify-center mx-auto mb-4">
                                <i className="fa-solid fa-inbox text-2xl text-muted-foreground/50"></i>
                            </div>
                            <p className="text-sm font-medium text-muted-foreground">No hay productos registrados</p>
                            <p className="text-xs text-muted-foreground/70 mt-1">Comienza agregando tu primer
                                producto</p>
                        </div>

                    ) : (
                        <>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                    <tr className="bg-muted/30 border-b border-border">
                                        <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Código</th>
                                        <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Producto</th>
                                        <th className="text-center py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Stock</th>
                                        {!compact && (
                                            <th className="text-left py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Categoría</th>
                                        )}
                                        <th className="text-right py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Precio</th>
                                        {!compact && (
                                            <th className="py-2.5 px-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider text-center w-16">
                                                <i className="fa-solid fa-ellipsis"></i>
                                            </th>
                                        )}
                                    </tr>
                                    </thead>
                                    <tbody className="divide-y divide-border/60">
                                    {displayProductos?.map((producto) => {
                                        const stock = producto.stock_total ?? 0
                                        const status = getStockStatus(stock)
                                        const tipo = getProductoTipo(producto.tipo)

                                        return (
                                            <tr key={producto.id} className="hover:bg-muted/20 transition-colors group">
                                                {/* Código */}
                                                <td className="py-3.5 px-6">
                                                    <span
                                                        className="font-mono text-xs font-semibold text-foreground bg-muted/50 px-2 py-1 rounded-md">
                                                        {producto.codigo}
                                                    </span>
                                                </td>

                                                {/* Nombre + descripción */}
                                                <td className="py-3.5 px-6">
                                                    <div className="flex flex-col">
                                                        <span
                                                            className="text-sm font-medium text-foreground leading-snug">
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

                                                {/* Stock */}
                                                <td className="py-3.5 px-6">
                                                    <div className="flex flex-col items-center gap-1">
                                                        <span
                                                            className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${status.bg} ${status.color}`}>
                                                            {status.label}
                                                        </span>
                                                        <span
                                                            className="text-xs font-semibold text-foreground tabular-nums">
                                                            {stock} {producto.unidad_medida?.abreviatura ?? ''}
                                                        </span>
                                                    </div>
                                                </td>

                                                {/* Categoría + tipo */}
                                                {!compact && (
                                                    <td className="py-3.5 px-6">
                                                        <div className="flex flex-col">
                                                            <span className="text-sm text-foreground leading-snug">
                                                                {producto.categoria?.nombre ?? '—'}
                                                            </span>
                                                            <span className={`text-xs mt-0.5 ${tipo.color}`}>
                                                                {tipo.label}
                                                            </span>
                                                        </div>
                                                    </td>
                                                )}

                                                {/* Precio */}
                                                <td className="py-3.5 px-6 text-right">
                                                    <span
                                                        className="text-sm font-semibold text-foreground tabular-nums">
                                                        ${Number(producto.precio_venta).toFixed(2)}
                                                    </span>
                                                </td>

                                                {/* Acciones */}
                                                {!compact && (
                                                    <td className="py-3.5 px-6 text-center">
                                                        <DropdownMenu>
                                                            <DropdownMenuTrigger asChild>
                                                                <button
                                                                    className="w-7 h-7 inline-flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors opacity-50 group-hover:opacity-100">
                                                                    <i className="fa-solid fa-ellipsis-vertical text-xs"></i>
                                                                </button>
                                                            </DropdownMenuTrigger>
                                                            <DropdownMenuContent align="end" className="w-48">
                                                                <DropdownMenuItem
                                                                    onClick={() => handleViewDetails(producto)}>
                                                                    <i className="fa-solid fa-eye mr-2 text-xs text-muted-foreground"></i>
                                                                    Ver detalles
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem
                                                                    onClick={() => router.push(`/inventario/productos/${producto.id}/editar`)}>
                                                                    <i className="fa-solid fa-pen-to-square mr-2 text-xs text-muted-foreground"></i>
                                                                    Editar
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem onClick={() => {
                                                                    setProductoSeleccionado(producto);
                                                                    setModalDuplicar(true)
                                                                }}>
                                                                    <i className="fa-solid fa-copy mr-2 text-xs text-muted-foreground"></i>
                                                                    Duplicar producto
                                                                </DropdownMenuItem>
                                                                <DropdownMenuSeparator/>
                                                                <DropdownMenuItem onClick={() => {
                                                                    setProductoSeleccionado(producto);
                                                                    setModalInventarioTotal(true)
                                                                }}>
                                                                    <i className="fa-solid fa-boxes-stacked mr-2 text-xs text-muted-foreground"></i>
                                                                    Ver inventario total
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem>
                                                                    <i className="fa-solid fa-clock-rotate-left mr-2 text-xs text-muted-foreground"></i>
                                                                    Historial
                                                                </DropdownMenuItem>
                                                                <DropdownMenuSeparator/>
                                                                <DropdownMenuItem onClick={() => {
                                                                    setProductoSeleccionado(producto);
                                                                    setModalImagen(true)
                                                                }}>
                                                                    <i className="fa-solid fa-image mr-2 text-xs text-muted-foreground"></i>
                                                                    Agregar imagen
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem
                                                                    onClick={() => handleEtiqueta(producto.id)}>
                                                                    <i className="fa-solid fa-barcode mr-2 text-xs text-muted-foreground"></i>
                                                                    Imprimir etiqueta
                                                                </DropdownMenuItem>
                                                                <DropdownMenuSeparator/>
                                                                <DropdownMenuItem
                                                                    className="text-destructive focus:text-destructive">
                                                                    <i className="fa-solid fa-ban mr-2 text-xs"></i>
                                                                    Desactivar
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

                            {!compact && (productos?.length ?? 0) > 0 && (
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

            {/* Modales */}
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