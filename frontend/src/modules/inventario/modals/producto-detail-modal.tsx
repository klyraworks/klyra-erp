// frontend/src/inventario/modals/producto-detail-modal.tsx

import {Dialog, DialogContent, DialogHeader, DialogTitle} from "@/components/ui/dialog"
import {Badge} from "@/components/ui/badge"
import type {Producto} from "@/src/core/api/types"
import { mutate } from "swr"

interface ProductoDetailModalProps {
    producto: Producto | null
    open: boolean
    onOpenChange: (open: boolean) => void
}

export function ProductoDetailModal({producto, open, onOpenChange}: ProductoDetailModalProps) {
    if (!producto) return null

    const getStockStatus = (stockEstado?: string) => {
        if (stockEstado === 'agotado') return {
            color: "text-destructive",
            bg: "bg-destructive/10",
            label: "Agotado",
            icon: "fa-circle-xmark"
        }
        if (stockEstado === 'bajo') return {
            color: "text-yellow-600 dark:text-yellow-400",
            bg: "bg-yellow-500/10",
            label: "Stock Bajo",
            icon: "fa-triangle-exclamation"
        }
        if (stockEstado === 'medio') return {
            color: "text-blue-600 dark:text-blue-400",
            bg: "bg-blue-500/10",
            label: "Stock Medio",
            icon: "fa-circle-half-stroke"
        }
        return {
            color: "text-success",
            bg: "bg-success/10",
            label: "Stock Normal",
            icon: "fa-circle-check"
        }
    }

    const getProductoTipo = (tipo: string) => {
        if (tipo === "kit") return {
            color: "text-[#8de4ff]",
            bg: "bg-[#8de4ff]/10",
            label: producto.tipo_display || "Kit",
            icon: "fa-box-open"
        }
        if (tipo === "simple") return {
            color: "text-[#B6D634]",
            bg: "bg-[#B6D634]/10",
            label: producto.tipo_display || "Producto Simple",
            icon: "fa-box"
        }
        if (tipo === "servicio") return {
            color: "text-[#989ee3]",
            bg: "bg-[#989ee3]/10",
            label: producto.tipo_display || "Servicio",
            icon: "fa-handshake"
        }
        return {
            color: "text-success",
            bg: "bg-success/10",
            label: "Normal",
            icon: "fa-box"
        }
    }

    const status = getStockStatus(producto.stock_estado)
    const tipo = getProductoTipo(producto.tipo)
    const componentes = producto.componentes_detalle ?? []

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="!max-w-6xl max-h-[90vh] overflow-y-auto p-0">
                {/* Header Sticky */}
                <DialogHeader className="sticky top-0 px-4 sm:px-6 pt-4 sm:pt-6 pb-4 border-b">
                    <DialogTitle className="flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4">
                        <div
                            className="w-12 h-12 sm:w-14 sm:h-14 bg-muted rounded flex items-center justify-center flex-shrink-0">
                            {producto.imagen ? (
                                <img src={producto.imagen} alt={producto.nombre}
                                     className="w-full h-full object-cover rounded"/>
                            ) : (
                                <i className="fa-solid fa-box text-muted-foreground text-lg sm:text-xl"></i>
                            )}
                        </div>
                        <div className="flex-1 min-w-0 w-full sm:w-auto">
                            <h2 className="text-base sm:text-lg font-semibold leading-tight mb-2">{producto.nombre}</h2>
                            <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
                            <span
                                className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${tipo.bg} ${tipo.color}`}>
                              <i className={`fa-solid ${tipo.icon} mr-1 sm:mr-1.5 text-[10px]`}></i>
                              <span className="hidden sm:inline">{tipo.label}</span>
                              <span className="sm:hidden">{tipo.label.split(' ')[0]}</span>
                            </span>
                                <Badge variant={producto.is_active ? "default" : "destructive"} className="text-xs">
                                    {producto.estado || (producto.is_active ? "Activo" : "Inactivo")}
                                </Badge>
                                <span
                                    className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${status.bg} ${status.color}`}>
                                    <i className={`fa-solid ${status.icon} mr-1 sm:mr-1.5 text-[10px]`}></i>{status.label}
                                </span>
                            </div>
                        </div>
                    </DialogTitle>
                </DialogHeader>

                <div className="px-4 sm:px-6 pb-4 sm:pb-6 space-y-3 sm:space-y-4">
                    {/* Códigos - Mobile: Stack, Desktop: Table */}
                    <div className="border rounded-lg overflow-hidden">
                        <table className="w-full text-xs sm:text-sm">
                            <tbody>
                            <tr className="border-b bg-muted/30">
                                <td className="px-3 sm:px-4 py-2 sm:py-2.5 font-medium text-muted-foreground">
                                    <i className="fa-solid fa-hashtag mr-1.5 sm:mr-2 text-xs"></i>
                                    <span className="hidden sm:inline">Código</span>
                                    <span className="sm:hidden">Cód.</span>
                                </td>
                                <td className="px-3 sm:px-4 py-2 sm:py-2.5 font-mono text-xs sm:text-sm">{producto.codigo}</td>
                            </tr>
                            {producto.codigo_barras && (
                                <tr className="border-b bg-muted/30">
                                    <td className="px-3 sm:px-4 py-2 sm:py-2.5 font-medium text-muted-foreground">
                                        <i className="fa-solid fa-barcode mr-1.5 sm:mr-2 text-xs"></i>
                                        <span className="hidden sm:inline">Código de Barras</span>
                                        <span className="sm:hidden">Barras</span>
                                    </td>
                                    <td className="px-3 sm:px-4 py-2 sm:py-2.5 font-mono text-xs sm:text-sm">{producto.codigo_barras}</td>
                                </tr>
                            )}
                            {producto.descripcion && (
                                <tr>
                                    <td className="px-3 sm:px-4 py-2 sm:py-2.5 font-medium text-muted-foreground align-top">
                                        <i className="fa-solid fa-align-left mr-1.5 sm:mr-2 text-xs"></i>
                                        <span className="hidden sm:inline">Descripción</span>
                                        <span className="sm:hidden">Desc.</span>
                                    </td>
                                    <td className="px-3 sm:px-4 py-2 sm:py-2.5 text-xs sm:text-sm">{producto.descripcion}</td>
                                </tr>
                            )}
                            </tbody>
                        </table>
                    </div>

                    {/* Precios y Stock - Mobile: Stack, Desktop: Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
                        {/* Precios */}
                        <div className="border rounded-lg overflow-hidden">
                            <div className="bg-muted/50 px-3 sm:px-4 py-2 border-b">
                                <h3 className="text-[10px] sm:text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                    <i className="fa-solid fa-dollar-sign mr-1.5 sm:mr-2"></i>Precios
                                </h3>
                            </div>
                            <table className="w-full text-xs sm:text-sm">
                                <tbody>
                                <tr className="border-b">
                                    <td className="px-3 sm:px-4 py-2 sm:py-3 font-medium text-muted-foreground">
                                        <span className="hidden sm:inline">Precio de Compra</span>
                                        <span className="sm:hidden">Compra</span>
                                    </td>
                                    <td className="px-3 sm:px-4 py-2 sm:py-3 text-right font-semibold tabular-nums">
                                        ${Number.parseFloat(String(producto.precio_compra)).toFixed(2)}
                                    </td>
                                </tr>
                                <tr className="border-b bg-success/5">
                                    <td className="px-3 sm:px-4 py-2 sm:py-3 font-medium text-success/90">
                                        <span className="hidden sm:inline">Precio de Venta</span>
                                        <span className="sm:hidden">Venta</span>
                                        {producto.iva && (
                                            <span
                                                className="ml-1.5 sm:ml-2 text-[10px] bg-success/20 px-1 sm:px-1.5 py-0.5 rounded">IVA</span>
                                        )}
                                    </td>
                                    <td className="px-3 sm:px-4 py-2 sm:py-3 text-right font-bold text-success tabular-nums">
                                        ${Number.parseFloat(String(producto.precio_venta)).toFixed(2)}
                                    </td>
                                </tr>
                                {producto.margen_ganancia && (
                                    <tr className="bg-primary/5">
                                        <td className="px-3 sm:px-4 py-2 sm:py-3 font-medium text-primary text-xs sm:text-sm">
                                            <i className="fa-solid fa-chart-line mr-1.5 sm:mr-2 text-xs"></i>
                                            <span className="hidden sm:inline">Margen de Ganancia</span>
                                            <span className="sm:hidden">Margen</span>
                                        </td>
                                        <td className="px-3 sm:px-4 py-2 sm:py-3 text-right">
                                            <div className="font-bold text-primary tabular-nums text-sm sm:text-base">
                                                {producto.margen_ganancia.porcentaje.toFixed(2)}%
                                            </div>
                                            <div className="text-[10px] sm:text-xs text-muted-foreground tabular-nums">
                                                ${producto.margen_ganancia.monto.toFixed(2)}
                                            </div>
                                        </td>
                                    </tr>
                                )}
                                </tbody>
                            </table>
                        </div>

                        {/* Stock */}
                        <div className="border rounded-lg overflow-hidden">
                            <div className="bg-muted/50 px-3 sm:px-4 py-2 border-b">
                                <h3 className="text-[10px] sm:text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                    <i className="fa-solid fa-warehouse mr-1.5 sm:mr-2"></i>Inventario
                                </h3>
                            </div>
                            <table className="w-full text-xs sm:text-sm">
                                <tbody>
                                <tr className={`border-b ${status.bg}`}>
                                    <td className="px-3 sm:px-4 py-2 sm:py-3 font-medium"
                                        style={{color: 'inherit', opacity: 0.9}}>
                                        <span className="hidden sm:inline">Stock Actual</span>
                                        <span className="sm:hidden">Actual</span>
                                    </td>
                                    <td className="px-3 sm:px-4 py-2 sm:py-3 text-right font-bold tabular-nums">
                                        {producto.stock}
                                        {producto.unidad_medida_detalle && (
                                            <span className="ml-1.5 sm:ml-2 text-xs font-medium text-muted-foreground">
                          {producto.unidad_medida_detalle.abreviatura}
                        </span>
                                        )}
                                    </td>
                                </tr>
                                <tr className="border-b">
                                    <td className="px-3 sm:px-4 py-2 sm:py-3 font-medium text-muted-foreground">
                                        <span className="hidden sm:inline">Stock Mínimo</span>
                                        <span className="sm:hidden">Mínimo</span>
                                    </td>
                                    <td className="px-3 sm:px-4 py-2 sm:py-3 text-right font-semibold tabular-nums">
                                        {producto.stock_minimo}
                                        {producto.unidad_medida_detalle && (
                                            <span className="ml-1.5 sm:ml-2 text-xs font-medium text-muted-foreground">
                          {producto.unidad_medida_detalle.abreviatura}
                        </span>
                                        )}
                                    </td>
                                </tr>
                                <tr>
                                    <td className="px-3 sm:px-4 py-2 sm:py-3 font-medium text-muted-foreground">Estado</td>
                                    <td className="px-3 sm:px-4 py-2 sm:py-3 text-right">
                      <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${status.bg} ${status.color}`}>
                        <i className={`fa-solid ${status.icon} mr-1 sm:mr-1.5 text-[10px]`}></i>
                          {status.label}
                      </span>
                                    </td>
                                </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Clasificación - Mobile optimized */}
                    <div className="border rounded-lg overflow-hidden">
                        <div className="bg-muted/50 px-3 sm:px-4 py-2 border-b">
                            <h3 className="text-[10px] sm:text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                <i className="fa-solid fa-layer-group mr-1.5 sm:mr-2"></i>Clasificación
                            </h3>
                        </div>
                        <table className="w-full text-xs sm:text-sm">
                            <tbody>
                            {producto.categoria_detalle && (
                                <tr className="border-b">
                                    <td className="px-3 sm:px-4 py-2 sm:py-2.5 font-medium text-muted-foreground w-24 sm:w-32">
                                        <i className="fa-solid fa-diagram-project mr-1.5 sm:mr-2 text-xs"></i>
                                        <span className="hidden sm:inline">Categoría</span>
                                        <span className="sm:hidden">Cat.</span>
                                    </td>
                                    <td className="px-3 sm:px-4 py-2 sm:py-2.5">
                                        <div className="font-medium">{producto.categoria_detalle.nombre}</div>
                                        {producto.categoria_detalle.ruta_completa && (
                                            <div
                                                className="text-[10px] sm:text-xs text-muted-foreground mt-0.5 hidden sm:block">
                                                {producto.categoria_detalle.ruta_completa}
                                            </div>
                                        )}
                                    </td>
                                </tr>
                            )}
                            {producto.marca_detalle && (
                                <tr className="border-b">
                                    <td className="px-3 sm:px-4 py-2 sm:py-2.5 font-medium text-muted-foreground">
                                        <i className="fa-solid fa-tag mr-1.5 sm:mr-2 text-xs"></i>Marca
                                    </td>
                                    <td className="px-3 sm:px-4 py-2 sm:py-2.5">
                                        <div className="font-medium">{producto.marca_detalle.nombre}</div>
                                        {producto.marca_detalle.pais_origen && (
                                            <div className="text-[10px] sm:text-xs text-muted-foreground mt-0.5">
                                                {producto.marca_detalle.pais_origen}
                                            </div>
                                        )}
                                    </td>
                                </tr>
                            )}
                            {producto.unidad_medida_detalle && (
                                <tr className="border-b">
                                    <td className="px-3 sm:px-4 py-2 sm:py-2.5 font-medium text-muted-foreground">
                                        <i className="fa-solid fa-ruler mr-1.5 sm:mr-2 text-xs"></i>
                                        <span className="hidden sm:inline">Unidad</span>
                                        <span className="sm:hidden">Und.</span>
                                    </td>
                                    <td className="px-3 sm:px-4 py-2 sm:py-2.5">
                                        <span className="font-medium">{producto.unidad_medida_detalle.nombre}</span>
                                        <span className="text-xs text-muted-foreground ml-1.5 sm:ml-2 font-mono">
                        ({producto.unidad_medida_detalle.abreviatura})
                      </span>
                                    </td>
                                </tr>
                            )}
                            {producto.peso && (
                                <tr className="border-b">
                                    <td className="px-3 sm:px-4 py-2 sm:py-2.5 font-medium text-muted-foreground">
                                        <i className="fa-solid fa-weight-hanging mr-1.5 sm:mr-2 text-xs"></i>Peso
                                    </td>
                                    <td className="px-3 sm:px-4 py-2 sm:py-2.5">
                                        <span
                                            className="font-medium tabular-nums">{Number(producto.peso).toFixed(2)} kg</span>
                                    </td>
                                </tr>
                            )}
                            {producto.es_perecedero && (
                                <tr>
                                    <td className="px-3 sm:px-4 py-2 sm:py-2.5 font-medium text-muted-foreground">
                                        <i className="fa-solid fa-apple-whole mr-1.5 sm:mr-2 text-xs"></i>
                                        <span className="hidden sm:inline">Perecedero</span>
                                        <span className="sm:hidden">Perec.</span>
                                    </td>
                                    <td className="px-3 sm:px-4 py-2 sm:py-2.5">
                      <span className="inline-flex items-center gap-1.5 font-medium text-xs sm:text-sm">
                        <i className="fa-solid fa-check-circle text-success text-xs"></i>
                          {producto.dias_vida_util ? `${producto.dias_vida_util} días` : 'Sí'}
                      </span>
                                    </td>
                                </tr>
                            )}
                            </tbody>
                        </table>
                    </div>

                    {/* Componentes del Kit - Mobile: Vertical cards, Desktop: Table */}
                    {producto.es_kit && componentes.length > 0 && (
                        <div className="border rounded-lg overflow-hidden">
                            <div className="bg-muted/50 px-3 sm:px-4 py-2 border-b flex items-center justify-between">
                                <h3 className="text-[10px] sm:text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                    <i className="fa-solid fa-box-open mr-1.5 sm:mr-2"></i>Componentes
                                </h3>
                                {producto.total_componentes && (
                                    <Badge variant="secondary" className="text-[10px]">
                                        {producto.total_componentes}
                                    </Badge>
                                )}
                            </div>

                            {/* Mobile: Cards */}
                            <div className="sm:hidden divide-y">
                                {componentes.map((componente) => (
                                    <div key={componente.id} className="px-3 py-2.5 space-y-1">
                                        <div className="flex items-center justify-between">
                                            <span className="font-medium text-xs">{componente.componente_nombre}</span>
                                            <span
                                                className="font-semibold text-xs tabular-nums">×{componente.cantidad}</span>
                                        </div>
                                        {componente.observaciones && (
                                            <p className="text-[10px] text-muted-foreground">{componente.observaciones}</p>
                                        )}
                                        {componente.es_opcional && (
                                            <Badge variant="outline" className="text-[9px] h-4">Opcional</Badge>
                                        )}
                                    </div>
                                ))}
                            </div>

                            {/* Desktop: Table */}
                            <table className="w-full text-xs sm:text-sm hidden sm:table">
                                <thead>
                                <tr className="border-b bg-muted/20">
                                    <th className="px-4 py-2 text-left font-medium text-muted-foreground text-xs">Componente</th>
                                    <th className="px-4 py-2 text-left font-medium text-muted-foreground text-xs">Observaciones</th>
                                    <th className="px-4 py-2 text-center font-medium text-muted-foreground text-xs w-20">Cantidad</th>
                                    <th className="px-4 py-2 text-center font-medium text-muted-foreground text-xs w-20">Tipo</th>
                                </tr>
                                </thead>
                                <tbody>
                                {componentes.map((componente, idx) => (
                                    <tr key={componente.id}
                                        className={idx !== componentes.length - 1 ? "border-b" : ""}>
                                        <td className="px-4 py-2.5 font-medium">{componente.componente_nombre}</td>
                                        <td className="px-4 py-2.5 text-muted-foreground text-xs">
                                            {componente.observaciones || '—'}
                                        </td>
                                        <td className="px-4 py-2.5 text-center font-semibold tabular-nums">×{componente.cantidad}</td>
                                        <td className="px-4 py-2.5 text-center">
                                            {componente.es_opcional ? (
                                                <Badge variant="outline" className="text-[10px]">Opcional</Badge>
                                            ) : (
                                                <span className="text-xs text-muted-foreground">Requerido</span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                                </tbody>
                            </table>
                            {producto.costo_componentes && (
                                <div
                                    className="bg-primary/5 border-t-2 px-3 sm:px-4 py-2.5 sm:py-3 flex items-center justify-between">
                                    <span className="font-semibold text-xs sm:text-sm">Costo Total</span>
                                    <span className="font-bold text-primary tabular-nums text-sm sm:text-base">

                                    </span>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Fechas - Mobile: Stack, Desktop: Row */}
                    {(producto.created_at || producto.updated_at) && (
                        <div className="border rounded-lg overflow-hidden">
                            <table className="w-full text-xs sm:text-sm">
                                <tbody>
                                <tr className="flex flex-col sm:table-row">
                                    {producto.created_at && (
                                        <>
                                            <td className="px-3 sm:px-4 py-2 font-medium text-muted-foreground bg-muted/20 border-b sm:border-b-0 sm:border-r sm:w-1/4">
                                                <i className="fa-solid fa-calendar-plus mr-1.5 sm:mr-2 text-xs"></i>
                                                <span className="hidden sm:inline">Fecha de Creación</span>
                                                <span className="sm:hidden">Creado</span>
                                            </td>
                                            <td className="px-3 sm:px-4 py-2 bg-muted/20 border-b sm:border-b-0 text-xs">
                                                {new Date(producto.created_at).toLocaleDateString('es-ES', {
                                                    year: 'numeric',
                                                    month: 'short',
                                                    day: 'numeric',
                                                    hour: '2-digit',
                                                    minute: '2-digit'
                                                })}
                                            </td>
                                        </>
                                    )}
                                    {producto.updated_at && (
                                        <>
                                            <td className="px-3 sm:px-4 py-2 font-medium text-muted-foreground border-b sm:border-b-0 sm:border-l sm:w-1/4">
                                                <i className="fa-solid fa-calendar-check mr-1.5 sm:mr-2 text-xs"></i>
                                                <span className="hidden sm:inline">Última Actualización</span>
                                                <span className="sm:hidden">Actualizado</span>
                                            </td>
                                            <td className="px-3 sm:px-4 py-2 text-xs">
                                                {new Date(producto.updated_at).toLocaleDateString('es-ES', {
                                                    year: 'numeric',
                                                    month: 'short',
                                                    day: 'numeric',
                                                    hour: '2-digit',
                                                    minute: '2-digit'
                                                })}
                                            </td>
                                        </>
                                    )}
                                </tr>
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    )
}