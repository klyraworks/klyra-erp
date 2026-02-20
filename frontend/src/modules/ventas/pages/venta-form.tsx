"use client"

import {useState, useMemo} from "react"
import {useStore, useProductos, useClientes, useBodegas} from "@/src/core/store"
import { apiFetch } from "@/src/core/api/client"
import {useTheme} from "@/src/core/theme/provider"
import {mutate} from "swr"
import type {Producto, Cliente} from "@/src/core/api/types"
import Link from "next/link";

// Tipos de identificación del comprador según SRI
const TIPOS_IDENTIFICACION = [
    {codigo: "04", nombre: "RUC"},
    {codigo: "05", nombre: "Cédula"},
    {codigo: "06", nombre: "Pasaporte"},
    {codigo: "07", nombre: "Consumidor Final"},
    {codigo: "08", nombre: "Identificación del Exterior"},
]

// Formas de pago según catálogo SRI
const FORMAS_PAGO = [
    {codigo: "01", nombre: "Sin utilización del sistema financiero"},
    {codigo: "15", nombre: "Compensación de deudas"},
    {codigo: "16", nombre: "Tarjeta de débito"},
    {codigo: "17", nombre: "Dinero electrónico"},
    {codigo: "18", nombre: "Tarjeta prepago"},
    {codigo: "19", nombre: "Tarjeta de crédito"},
    {codigo: "20", nombre: "Otros con utilización del sistema financiero"},
    {codigo: "21", nombre: "Endoso de títulos"},
]

// Tarifas de IVA según SRI
const TARIFAS_IVA = [
    {codigo: "0", nombre: "0%", porcentaje: 0},
    {codigo: "2", nombre: "13%", porcentaje: 13},
    {codigo: "4", nombre: "15%", porcentaje: 15},
    {codigo: "6", nombre: "No Objeto de Impuesto", porcentaje: 0},
    {codigo: "7", nombre: "Exento de IVA", porcentaje: 0},
]

// Tipos de documento
const TIPOS_DOCUMENTO = [
    {codigo: "01", nombre: "Factura"},
    {codigo: "03", nombre: "Liquidación de Compra"},
    {codigo: "04", nombre: "Nota de Crédito"},
    {codigo: "05", nombre: "Nota de Débito"},
]

interface DetalleFactura {
    id: string
    codigoPrincipal: string
    codigoAuxiliar: string
    descripcion: string
    cantidad: number
    precioUnitario: number
    descuento: number
    descuentoPorcentaje: number
    tarifaIva: string
    productoId?: string
}

interface NuevaVentaPageProps {
    onBack: () => void
}

export function NuevaVentaPage({onBack}: NuevaVentaPageProps) {
    const {data: productos} = useProductos()
    const {data: clientes} = useClientes()
    const {data: bodegas} = useBodegas()

    const [loading, setLoading] = useState(false)
    const [searchProducto, setSearchProducto] = useState("")
    const [showProductoDropdown, setShowProductoDropdown] = useState<string | null>(null)
    const [searchCliente, setSearchCliente] = useState("")
    const [showClienteDropdown, setShowClienteDropdown] = useState(false)

    // Datos del documento
    const [tipoDocumento, setTipoDocumento] = useState("01")
    const [puntoEmision, setPuntoEmision] = useState("001")
    const [establecimiento, setEstablecimiento] = useState("001")
    const [secuencial, setSecuencial] = useState("")
    const [fechaEmision, setFechaEmision] = useState(new Date().toISOString().split("T")[0])

    // Datos del comprador
    const [tipoIdentificacion, setTipoIdentificacion] = useState("07")
    const [identificacion, setIdentificacion] = useState("9999999999999")
    const [razonSocial, setRazonSocial] = useState("CONSUMIDOR FINAL")
    const [direccion, setDireccion] = useState("")
    const [telefono, setTelefono] = useState("")
    const [email, setEmail] = useState("")
    const [clienteId, setClienteId] = useState<string | null>(null)

    // Datos de pago
    const [formaPago, setFormaPago] = useState("01")
    const [plazo, setPlazo] = useState(0)
    const [unidadTiempo, setUnidadTiempo] = useState("dias")
    const [tipoPago, setTipoPago] = useState<"contado" | "credito">("contado")

    // Datos adicionales
    const [observaciones, setObservaciones] = useState("")
    const [bodegaId, setBodegaId] = useState("")
    const [vendedor, setVendedor] = useState("")

    // Totales globales
    const [propina, setPropina] = useState(0)
    const [descuentoGlobal, setDescuentoGlobal] = useState(0)
    const [descuentoGlobalPorcentaje, setDescuentoGlobalPorcentaje] = useState(0)

    // Detalles de la factura
    const [detalles, setDetalles] = useState<DetalleFactura[]>([
        {
            id: `temp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            codigoPrincipal: "",
            codigoAuxiliar: "",
            descripcion: "",
            cantidad: 1,
            precioUnitario: 0,
            descuento: 0,
            descuentoPorcentaje: 0,
            tarifaIva: "2",
        },
    ])

    // Cálculos
    const calculos = useMemo(() => {
        let subtotalSinImpuestos = 0
        let totalDescuentos = 0
        let subtotal0 = 0
        let subtotal13 = 0
        let subtotal15 = 0
        let subtotalNoObjeto = 0
        let subtotalExento = 0
        let iva13 = 0
        let iva15 = 0

        detalles.forEach((detalle) => {
            const subtotalLinea = detalle.cantidad * detalle.precioUnitario
            const descuentoLinea = detalle.descuento || (subtotalLinea * detalle.descuentoPorcentaje) / 100
            const baseImponible = subtotalLinea - descuentoLinea

            subtotalSinImpuestos += baseImponible
            totalDescuentos += descuentoLinea

            const tarifa = TARIFAS_IVA.find((t) => t.codigo === detalle.tarifaIva)
            if (tarifa) {
                switch (detalle.tarifaIva) {
                    case "0":
                        subtotal0 += baseImponible
                        break
                    case "2":
                        subtotal13 += baseImponible
                        iva13 += baseImponible * 0.13
                        break
                    case "4":
                        subtotal15 += baseImponible
                        iva15 += baseImponible * 0.15
                        break
                    case "6":
                        subtotalNoObjeto += baseImponible
                        break
                    case "7":
                        subtotalExento += baseImponible
                        break
                }
            }
        })

        // Aplicar descuento global
        const factorDescuento =
            descuentoGlobal > 0
                ? (subtotalSinImpuestos - descuentoGlobal) / subtotalSinImpuestos
                : descuentoGlobalPorcentaje > 0
                    ? 1 - descuentoGlobalPorcentaje / 100
                    : 1

        if (factorDescuento < 1) {
            subtotal0 *= factorDescuento
            subtotal13 *= factorDescuento
            subtotal15 *= factorDescuento
            subtotalNoObjeto *= factorDescuento
            subtotalExento *= factorDescuento
            iva13 = subtotal13 * 0.13
            iva15 = subtotal15 * 0.15
            totalDescuentos += descuentoGlobal || (subtotalSinImpuestos * descuentoGlobalPorcentaje) / 100
            subtotalSinImpuestos *= factorDescuento
        }

        const totalIva = iva13 + iva15
        const total = subtotalSinImpuestos + totalIva + propina

        return {
            subtotalSinImpuestos,
            totalDescuentos,
            subtotal0,
            subtotal13,
            subtotal15,
            subtotalNoObjeto,
            subtotalExento,
            iva13,
            iva15,
            totalIva,
            propina,
            total,
        }
    }, [detalles, propina, descuentoGlobal, descuentoGlobalPorcentaje])

    // Generar clave de acceso (simulada - 49 dígitos)
    const claveAcceso = useMemo(() => {
        const fecha = fechaEmision.replace(/-/g, "").split("").reverse().join("")
        const tipoDoc = tipoDocumento.padStart(2, "0")
        const ruc = "1792123456001" // RUC del emisor (debería venir de config)
        const ambiente = "1" // 1=Pruebas, 2=Producción
        const serie = `${establecimiento}${puntoEmision}`
        const seq = (secuencial || "000000001").padStart(9, "0")
        const codigoNumerico = Math.random().toString().slice(2, 10)
        const tipoEmision = "1"

        const base = `${fecha}${tipoDoc}${ruc}${ambiente}${serie}${seq}${codigoNumerico}${tipoEmision}`
        // Aquí iría el cálculo del dígito verificador módulo 11
        const digitoVerificador = "7"

        return base + digitoVerificador
    }, [fechaEmision, tipoDocumento, establecimiento, puntoEmision, secuencial])

    // Agregar línea de detalle
    const agregarLinea = () => {
        setDetalles([
            ...detalles,
            {
                id: `temp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                codigoPrincipal: "",
                codigoAuxiliar: "",
                descripcion: "",
                cantidad: 1,
                precioUnitario: 0,
                descuento: 0,
                descuentoPorcentaje: 0,
                tarifaIva: "2",
            },
        ])
    }

    // Eliminar línea de detalle
    const eliminarLinea = (id: string) => {
        if (detalles.length > 1) {
            setDetalles(detalles.filter((d) => d.id !== id))
        }
    }

    // Duplicar línea
    const duplicarLinea = (detalle: DetalleFactura) => {
        const newDetalle = {...detalle, id: `temp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`}
        const index = detalles.findIndex((d) => d.id === detalle.id)
        const newDetalles = [...detalles]
        newDetalles.splice(index + 1, 0, newDetalle)
        setDetalles(newDetalles)
    }

    // Actualizar línea de detalle
    const actualizarLinea = (id: string, campo: keyof DetalleFactura, valor: any) => {
        setDetalles(
            detalles.map((d) => {
                if (d.id === id) {
                    const updated = {...d, [campo]: valor}

                    // Si cambia el descuento fijo, resetear porcentaje
                    if (campo === "descuento" && valor > 0) {
                        updated.descuentoPorcentaje = 0
                    }
                    // Si cambia el porcentaje, resetear descuento fijo
                    if (campo === "descuentoPorcentaje" && valor > 0) {
                        updated.descuento = 0
                    }

                    return updated
                }
                return d
            }),
        )
    }

    // Seleccionar producto
    const seleccionarProducto = (detalleId: string, producto: Producto) => {
        setDetalles(
            detalles.map((d) => {
                if (d.id === detalleId) {
                    return {
                        ...d,
                        productoId: producto.id,
                        codigoPrincipal: producto.codigo,
                        descripcion: producto.nombre,
                        precioUnitario: Number(producto.precio_venta) || 0, // Convert precio_venta to number before assigning
                    }
                }
                return d
            }),
        )
        setShowProductoDropdown(null)
        setSearchProducto("")
    }

    // Seleccionar cliente
    const seleccionarCliente = (cliente: Cliente) => {
        setClienteId(cliente.id)
        setIdentificacion(cliente.ruc)
        setRazonSocial(cliente.razon_social || cliente.nombre_completo || "")
        setDireccion(cliente.direccion || "")
        setTelefono(cliente.telefono || "")
        setEmail(cliente.email || "")
        setTipoIdentificacion(cliente.ruc.length === 13 ? "04" : "05")
        setShowClienteDropdown(false)
        setSearchCliente("")
    }

    // Limpiar cliente
    const limpiarCliente = () => {
        setClienteId(null)
        setIdentificacion("9999999999999")
        setRazonSocial("CONSUMIDOR FINAL")
        setDireccion("")
        setTelefono("")
        setEmail("")
        setTipoIdentificacion("07")
    }

    // Filtrar productos
    const productosFiltrados = useMemo(() => {
        if (!productos || !searchProducto) return []
        const search = searchProducto.toLowerCase()
        return productos
            .filter((p) => p.codigo.toLowerCase().includes(search) || p.nombre.toLowerCase().includes(search))
            .slice(0, 10)
    }, [productos, searchProducto])

    // Filtrar clientes
    const clientesFiltrados = useMemo(() => {
        if (!clientes || !searchCliente) return []
        const search = searchCliente.toLowerCase()
        return clientes
            .filter(
                (c) =>
                    c.ruc.toLowerCase().includes(search) ||
                    (c.razon_social || "").toLowerCase().includes(search) ||
                    (c.nombre_completo || "").toLowerCase().includes(search),
            )
            .slice(0, 10)
    }, [clientes, searchCliente])

    // Enviar venta
    const handleSubmit = async (accion: "borrador" | "emitir") => {
        // Validaciones
        if (detalles.some((d) => !d.descripcion || d.cantidad <= 0 || d.precioUnitario <= 0)) {
            alert("Complete todos los detalles de los productos")
            return
        }

        if (tipoIdentificacion !== "07" && !identificacion) {
            alert("Ingrese la identificación del comprador")
            return
        }

        setLoading(true)
        try {
            const payload = {
                tipo_documento: tipoDocumento,
                establecimiento,
                punto_emision: puntoEmision,
                secuencial,
                fecha_emision: fechaEmision,
                clave_acceso: claveAcceso,

                // Comprador
                tipo_identificacion_comprador: tipoIdentificacion,
                identificacion_comprador: identificacion,
                razon_social_comprador: razonSocial,
                direccion_comprador: direccion,
                telefono_comprador: telefono,
                email_comprador: email,
                cliente: clienteId,

                // Pago
                forma_pago: formaPago,
                plazo,
                unidad_tiempo: unidadTiempo,
                tipo_pago: tipoPago,

                // Adicionales
                observaciones,
                bodega: bodegaId || undefined,
                vendedor,

                // Totales
                propina,
                descuento_global: descuentoGlobal || (calculos.subtotalSinImpuestos * descuentoGlobalPorcentaje) / 100,

                // Detalles
                detalles_data: detalles.map((d) => ({
                    codigo_principal: d.codigoPrincipal,
                    codigo_auxiliar: d.codigoAuxiliar,
                    descripcion: d.descripcion,
                    cantidad: d.cantidad,
                    precio_unitario: d.precioUnitario,
                    descuento: d.descuento || (d.cantidad * d.precioUnitario * d.descuentoPorcentaje) / 100,
                    tarifa_iva: d.tarifaIva,
                    producto: d.productoId,
                })),

                // Acción
                workflow: accion === "emitir" ? "rapido" : "normal",
                estado: accion === "borrador" ? "borrador" : undefined,
            }

            await apiFetch("/api/ventas/", {
                method: "POST",
                body: JSON.stringify(payload),
            })

            mutate(["/api/ventas/"])
            alert(accion === "emitir" ? "Factura emitida exitosamente" : "Borrador guardado")
            onBack()
        } catch (err) {
            alert("Error: " + (err as Error).message)
        } finally {
            setLoading(false)
        }
    }

    // Buscar producto por código de barras (Enter en el campo)
    const buscarPorCodigo = (detalleId: string, codigo: string) => {
        const producto = productos?.find((p) => p.codigo.toLowerCase() === codigo.toLowerCase())
        if (producto) {
            seleccionarProducto(detalleId, producto)
        }
    }

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <div className="bg-card border-b border-border sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-4 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <Link
                                href="/ventas"
                                className="flex items-center gap-2 px-4 py-2 bg-muted text-muted-foreground rounded-lg text-sm font-medium hover:bg-muted/80 transition-colors"
                            >
                                <i className="fa-solid fa-arrow-left"></i>
                            </Link>
                            <div>
                                <h1 className="text-xl font-bold text-foreground">Nueva Factura</h1>
                                <p className="text-sm text-muted-foreground">Emisión de comprobante electrónico</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-3">
                            <button
                                onClick={() => handleSubmit("borrador")}
                                disabled={loading}
                                className="flex items-center gap-2 px-4 py-2 border border-border rounded-lg text-sm font-medium text-foreground hover:bg-muted transition-colors disabled:opacity-50"
                            >
                                <i className="fa-solid fa-floppy-disk"></i>
                                Guardar Borrador
                            </button>
                            <button
                                onClick={() => handleSubmit("emitir")}
                                disabled={loading}
                                className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
                            >
                                <i className="fa-solid fa-paper-plane"></i>
                                Emitir Factura
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto py-6">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Columna principal */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Datos del documento */}
                        <div className="bg-card rounded-xl border border-border p-6">
                            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
                                <i className="fa-solid fa-file-invoice"></i>
                                Datos del Documento
                            </h2>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                        <i className="fa-solid fa-file-alt mr-1"></i>
                                        Tipo
                                    </label>
                                    <select
                                        value={tipoDocumento}
                                        onChange={(e) => setTipoDocumento(e.target.value)}
                                        className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                    >
                                        {TIPOS_DOCUMENTO.map((tipo) => (
                                            <option key={tipo.codigo} value={tipo.codigo}>
                                                {tipo.nombre}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                        <i className="fa-solid fa-building mr-1"></i>
                                        Establecimiento
                                    </label>
                                    <input
                                        type="text"
                                        value={establecimiento}
                                        onChange={(e) => setEstablecimiento(e.target.value.replace(/\D/g, "").slice(0, 3))}
                                        maxLength={3}
                                        className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                        placeholder="001"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                        <i className="fa-solid fa-cash-register mr-1"></i>
                                        Pto. Emisión
                                    </label>
                                    <input
                                        type="text"
                                        value={puntoEmision}
                                        onChange={(e) => setPuntoEmision(e.target.value.replace(/\D/g, "").slice(0, 3))}
                                        maxLength={3}
                                        className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                        placeholder="001"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                        <i className="fa-solid fa-hashtag mr-1"></i>
                                        Secuencial
                                    </label>
                                    <input
                                        type="text"
                                        value={secuencial}
                                        onChange={(e) => setSecuencial(e.target.value.replace(/\D/g, "").slice(0, 9))}
                                        maxLength={9}
                                        className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                        placeholder="Auto"
                                    />
                                </div>
                            </div>
                            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                        <i className="fa-solid fa-calendar mr-1"></i>
                                        Fecha de Emisión
                                    </label>
                                    <input
                                        type="date"
                                        value={fechaEmision}
                                        onChange={(e) => setFechaEmision(e.target.value)}
                                        className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                        <i className="fa-solid fa-key mr-1"></i>
                                        Clave de Acceso (49 dígitos)
                                    </label>
                                    <input
                                        type="text"
                                        value={claveAcceso}
                                        readOnly
                                        className="w-full px-3 py-2 bg-muted border border-border rounded-lg text-xs font-mono text-muted-foreground"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Datos del comprador */}
                        <div className="bg-card rounded-xl border border-border p-6">
                            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
                                <i className="fa-solid fa-user"></i>
                                Datos del Comprador
                            </h2>

                            {/* Buscador de cliente */}
                            <div className="mb-4 relative">
                                <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                    <i className="fa-solid fa-search mr-1"></i>
                                    Buscar Cliente Existente
                                </label>
                                <div className="relative">
                                    <input
                                        type="text"
                                        value={searchCliente}
                                        onChange={(e) => {
                                            setSearchCliente(e.target.value)
                                            setShowClienteDropdown(true)
                                        }}
                                        onFocus={() => setShowClienteDropdown(true)}
                                        className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 pr-20"
                                        placeholder="Buscar por RUC, cédula o nombre..."
                                    />
                                    {clienteId && (
                                        <button
                                            onClick={limpiarCliente}
                                            className="absolute right-2 top-1/2 -translate-y-1/2 px-2 py-1 text-xs text-destructive hover:bg-destructive/10 rounded"
                                        >
                                            <i className="fa-solid fa-times mr-1"></i>
                                            Limpiar
                                        </button>
                                    )}
                                </div>
                                {showClienteDropdown && clientesFiltrados.length > 0 && (
                                    <div
                                        className="absolute z-20 w-full mt-1 bg-card border border-border rounded-lg shadow-lg max-h-60 overflow-y-auto">
                                        {clientesFiltrados.map((cliente) => (
                                            <button
                                                key={cliente.id}
                                                onClick={() => seleccionarCliente(cliente)}
                                                className="w-full px-4 py-2 text-left text-sm hover:bg-muted transition-colors flex items-center justify-between"
                                            >
                                                <div>
                          <span className="font-medium text-foreground">
                            {cliente.razon_social || cliente.nombre_completo}
                          </span>
                                                    <span className="text-muted-foreground ml-2">({cliente.ruc})</span>
                                                </div>
                                                {/* CHANGE> Convert credito_disponible to number */}
                                                <span className="text-xs text-muted-foreground">
                          Crédito: ${Number(cliente.credito_disponible || 0).toFixed(2)}
                        </span>
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>

                            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                        <i className="fa-solid fa-id-card mr-1"></i>
                                        Tipo Identificación
                                    </label>
                                    <select
                                        value={tipoIdentificacion}
                                        onChange={(e) => setTipoIdentificacion(e.target.value)}
                                        className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                    >
                                        {TIPOS_IDENTIFICACION.map((tipo) => (
                                            <option key={tipo.codigo} value={tipo.codigo}>
                                                {tipo.nombre}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <div className="col-span-2">
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                        <i className="fa-solid fa-fingerprint mr-1"></i>
                                        Identificación
                                    </label>
                                    <input
                                        type="text"
                                        value={identificacion}
                                        onChange={(e) => setIdentificacion(e.target.value)}
                                        disabled={tipoIdentificacion === "07"}
                                        className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 disabled:bg-muted disabled:text-muted-foreground"
                                        placeholder="RUC / Cédula / Pasaporte"
                                    />
                                </div>
                            </div>

                            <div className="mt-4">
                                <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                    <i className="fa-solid fa-building mr-1"></i>
                                    Razón Social / Nombre
                                </label>
                                <input
                                    type="text"
                                    value={razonSocial}
                                    onChange={(e) => setRazonSocial(e.target.value.toUpperCase())}
                                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                    placeholder="Nombre o razón social del comprador"
                                />
                            </div>

                            <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                        <i className="fa-solid fa-location-dot mr-1"></i>
                                        Dirección
                                    </label>
                                    <input
                                        type="text"
                                        value={direccion}
                                        onChange={(e) => setDireccion(e.target.value)}
                                        className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                        placeholder="Dirección del comprador"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                        <i className="fa-solid fa-phone mr-1"></i>
                                        Teléfono
                                    </label>
                                    <input
                                        type="text"
                                        value={telefono}
                                        onChange={(e) => setTelefono(e.target.value)}
                                        className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                        placeholder="Teléfono"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                        <i className="fa-solid fa-envelope mr-1"></i>
                                        Email
                                    </label>
                                    <input
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                        placeholder=" correo@ejemplo.com"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Detalles de la factura */}
                        <div className="bg-card rounded-xl border border-border p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                                    <i className="fa-solid fa-list"></i>
                                    Detalle de Productos / Servicios
                                </h2>
                                <button
                                    onClick={agregarLinea}
                                    className="flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary rounded-lg text-sm font-medium hover:bg-primary/20 transition-colors"
                                >
                                    <i className="fa-solid fa-plus"></i>
                                    Agregar Línea
                                </button>
                            </div>

                            <div className="space-y-4">
                                {detalles.map((detalle, index) => (
                                    <div key={detalle.id}
                                         className="p-4 bg-muted/30 rounded-lg border border-border/50">
                                        <div className="flex items-center justify-between mb-3">
                                            <span
                                                className="text-xs font-medium text-muted-foreground">Línea {index + 1}</span>
                                            <div className="flex items-center gap-1">
                                                <button
                                                    onClick={() => duplicarLinea(detalle)}
                                                    className="p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded transition-colors"
                                                    title="Duplicar línea"
                                                >
                                                    <i className="fa-solid fa-copy text-sm"></i>
                                                </button>
                                                {detalles.length > 1 && (
                                                    <button
                                                        onClick={() => eliminarLinea(detalle.id)}
                                                        className="p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded transition-colors"
                                                        title="Eliminar línea"
                                                    >
                                                        <i className="fa-solid fa-trash text-sm"></i>
                                                    </button>
                                                )}
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-12 gap-3">
                                            {/* Código y búsqueda */}
                                            <div className="col-span-12 md:col-span-3 relative">
                                                <label className="block text-xs font-medium text-muted-foreground mb-1">
                                                    <i className="fa-solid fa-barcode mr-1"></i>
                                                    Código / Producto
                                                </label>
                                                <input
                                                    type="text"
                                                    value={detalle.codigoPrincipal || searchProducto}
                                                    onChange={(e) => {
                                                        if (detalle.productoId) {
                                                            actualizarLinea(detalle.id, "codigoPrincipal", e.target.value)
                                                        } else {
                                                            setSearchProducto(e.target.value)
                                                            setShowProductoDropdown(detalle.id)
                                                        }
                                                    }}
                                                    onKeyDown={(e) => {
                                                        if (e.key === "Enter" && !detalle.productoId) {
                                                            buscarPorCodigo(detalle.id, searchProducto)
                                                        }
                                                    }}
                                                    onFocus={() => {
                                                        if (!detalle.productoId) {
                                                            setShowProductoDropdown(detalle.id)
                                                        }
                                                    }}
                                                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                                    placeholder="Buscar o escanear..."
                                                />
                                                {showProductoDropdown === detalle.id && productosFiltrados.length > 0 && (
                                                    <div
                                                        className="absolute z-20 w-full mt-1 bg-card border border-border rounded-lg shadow-lg max-h-48 overflow-y-auto">
                                                        {productosFiltrados.map((producto) => (
                                                            <button
                                                                key={producto.id}
                                                                onClick={() => seleccionarProducto(detalle.id, producto)}
                                                                className="w-full px-3 py-2 text-left text-sm hover:bg-muted transition-colors"
                                                            >
                                                                <div className="flex justify-between">
                                                                    <span
                                                                        className="font-medium text-foreground">{producto.nombre}</span>
                                                                    {/* CHANGE> Convert precio_venta to number */}
                                                                    <span
                                                                        className="text-primary">${Number(producto.precio_venta || 0).toFixed(2)}</span>
                                                                </div>
                                                                <div className="text-xs text-muted-foreground">
                                                                    {producto.codigo} • Stock: {producto.stock}
                                                                </div>
                                                            </button>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>

                                            {/* Descripción */}
                                            <div className="col-span-12 md:col-span-5">
                                                <label className="block text-xs font-medium text-muted-foreground mb-1">
                                                    <i className="fa-solid fa-align-left mr-1"></i>
                                                    Descripción
                                                </label>
                                                <input
                                                    type="text"
                                                    value={detalle.descripcion}
                                                    onChange={(e) => actualizarLinea(detalle.id, "descripcion", e.target.value)}
                                                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                                    placeholder="Descripción del producto o servicio"
                                                />
                                            </div>

                                            {/* Cantidad */}
                                            <div className="col-span-4 md:col-span-2">
                                                <label className="block text-xs font-medium text-muted-foreground mb-1">
                                                    <i className="fa-solid fa-hashtag mr-1"></i>
                                                    Cantidad
                                                </label>
                                                <input
                                                    type="number"
                                                    value={detalle.cantidad}
                                                    onChange={(e) =>
                                                        actualizarLinea(detalle.id, "cantidad", Number.parseFloat(e.target.value) || 0)
                                                    }
                                                    min="0"
                                                    step="0.01"
                                                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                                />
                                            </div>

                                            {/* Precio unitario */}
                                            <div className="col-span-4 md:col-span-2">
                                                <label className="block text-xs font-medium text-muted-foreground mb-1">
                                                    <i className="fa-solid fa-dollar-sign mr-1"></i>
                                                    P. Unitario
                                                </label>
                                                <input
                                                    type="number"
                                                    value={detalle.precioUnitario}
                                                    onChange={(e) =>
                                                        actualizarLinea(detalle.id, "precioUnitario", Number.parseFloat(e.target.value) || 0)
                                                    }
                                                    min="0"
                                                    step="0.01"
                                                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                                />
                                            </div>

                                            {/* Código auxiliar */}
                                            <div className="col-span-4 md:col-span-2">
                                                <label className="block text-xs font-medium text-muted-foreground mb-1">
                                                    <i className="fa-solid fa-qrcode mr-1"></i>
                                                    Cód. Auxiliar
                                                </label>
                                                <input
                                                    type="text"
                                                    value={detalle.codigoAuxiliar}
                                                    onChange={(e) => actualizarLinea(detalle.id, "codigoAuxiliar", e.target.value)}
                                                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                                    placeholder="Opcional"
                                                />
                                            </div>

                                            {/* Descuento */}
                                            <div className="col-span-4 md:col-span-2">
                                                <label className="block text-xs font-medium text-muted-foreground mb-1">
                                                    <i className="fa-solid fa-tag mr-1"></i>
                                                    Descuento $
                                                </label>
                                                <input
                                                    type="number"
                                                    value={detalle.descuento}
                                                    onChange={(e) =>
                                                        actualizarLinea(detalle.id, "descuento", Number.parseFloat(e.target.value) || 0)
                                                    }
                                                    min="0"
                                                    step="0.01"
                                                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                                />
                                            </div>

                                            {/* Descuento % */}
                                            <div className="col-span-4 md:col-span-2">
                                                <label className="block text-xs font-medium text-muted-foreground mb-1">
                                                    <i className="fa-solid fa-percent mr-1"></i>
                                                    Desc. %
                                                </label>
                                                <input
                                                    type="number"
                                                    value={detalle.descuentoPorcentaje}
                                                    onChange={(e) =>
                                                        actualizarLinea(detalle.id, "descuentoPorcentaje", Number.parseFloat(e.target.value) || 0)
                                                    }
                                                    min="0"
                                                    max="100"
                                                    step="0.01"
                                                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                                />
                                            </div>

                                            {/* Tarifa IVA */}
                                            <div className="col-span-4 md:col-span-2">
                                                <label className="block text-xs font-medium text-muted-foreground mb-1">
                                                    <i className="fa-solid fa-scale-balanced mr-1"></i>
                                                    IVA
                                                </label>
                                                <select
                                                    value={detalle.tarifaIva}
                                                    onChange={(e) => actualizarLinea(detalle.id, "tarifaIva", e.target.value)}
                                                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                                >
                                                    {TARIFAS_IVA.map((tarifa) => (
                                                        <option key={tarifa.codigo} value={tarifa.codigo}>
                                                            {tarifa.nombre}
                                                        </option>
                                                    ))}
                                                </select>
                                            </div>

                                            {/* Subtotal línea */}
                                            <div className="col-span-4 md:col-span-2">
                                                <label className="block text-xs font-medium text-muted-foreground mb-1">
                                                    <i className="fa-solid fa-calculator mr-1"></i>
                                                    Subtotal
                                                </label>
                                                <div
                                                    className="px-3 py-2 bg-muted border border-border rounded-lg text-sm font-medium text-foreground">
                                                    $
                                                    {(
                                                        detalle.cantidad * detalle.precioUnitario -
                                                        (detalle.descuento ||
                                                            (detalle.cantidad * detalle.precioUnitario * detalle.descuentoPorcentaje) / 100)
                                                    ).toFixed(2)}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Columna lateral */}
                    <div className="space-y-6">
                        {/* Forma de pago */}
                        <div className="bg-card rounded-xl border border-border p-6">
                            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
                                <i className="fa-solid fa-credit-card"></i>
                                Forma de Pago
                            </h2>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">Tipo de
                                        Pago</label>
                                    <div className="grid grid-cols-2 gap-2">
                                        <button
                                            onClick={() => setTipoPago("contado")}
                                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                                                tipoPago === "contado"
                                                    ? "bg-primary text-primary-foreground"
                                                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                                            }`}
                                        >
                                            <i className="fa-solid fa-money-bill mr-2"></i>
                                            Contado
                                        </button>
                                        <button
                                            onClick={() => setTipoPago("credito")}
                                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                                                tipoPago === "credito"
                                                    ? "bg-primary text-primary-foreground"
                                                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                                            }`}
                                        >
                                            <i className="fa-solid fa-clock mr-2"></i>
                                            Crédito
                                        </button>
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                        <i className="fa-solid fa-wallet mr-1"></i>
                                        Forma de Pago (SRI)
                                    </label>
                                    <select
                                        value={formaPago}
                                        onChange={(e) => setFormaPago(e.target.value)}
                                        className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                    >
                                        {FORMAS_PAGO.map((forma) => (
                                            <option key={forma.codigo} value={forma.codigo}>
                                                {forma.codigo} - {forma.nombre}
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                {tipoPago === "credito" && (
                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                                <i className="fa-solid fa-hourglass-half mr-1"></i>
                                                Plazo
                                            </label>
                                            <input
                                                type="number"
                                                value={plazo}
                                                onChange={(e) => setPlazo(Number.parseInt(e.target.value) || 0)}
                                                min="0"
                                                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                            />
                                        </div>
                                        <div>
                                            <label
                                                className="block text-xs font-medium text-muted-foreground mb-1.5">Unidad</label>
                                            <select
                                                value={unidadTiempo}
                                                onChange={(e) => setUnidadTiempo(e.target.value)}
                                                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                            >
                                                <option value="dias">Días</option>
                                                <option value="meses">Meses</option>
                                            </select>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Descuento global */}
                        <div className="bg-card rounded-xl border border-border p-6">
                            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
                                <i className="fa-solid fa-tags"></i>
                                Descuento Global
                            </h2>
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">Monto
                                        $</label>
                                    <input
                                        type="number"
                                        value={descuentoGlobal}
                                        onChange={(e) => {
                                            setDescuentoGlobal(Number.parseFloat(e.target.value) || 0)
                                            setDescuentoGlobalPorcentaje(0)
                                        }}
                                        min="0"
                                        step="0.01"
                                        className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">Porcentaje
                                        %</label>
                                    <input
                                        type="number"
                                        value={descuentoGlobalPorcentaje}
                                        onChange={(e) => {
                                            setDescuentoGlobalPorcentaje(Number.parseFloat(e.target.value) || 0)
                                            setDescuentoGlobal(0)
                                        }}
                                        min="0"
                                        max="100"
                                        step="0.01"
                                        className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Información adicional */}
                        <div className="bg-card rounded-xl border border-border p-6">
                            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
                                <i className="fa-solid fa-circle-info"></i>
                                Información Adicional
                            </h2>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                        <i className="fa-solid fa-warehouse mr-1"></i>
                                        Bodega
                                    </label>
                                    <select
                                        value={bodegaId}
                                        onChange={(e) => setBodegaId(e.target.value)}
                                        className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                    >
                                        <option value="">Seleccionar bodega</option>
                                        {bodegas?.map((bodega) => (
                                            <option key={bodega.id} value={bodega.id}>
                                                {bodega.nombre}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                        <i className="fa-solid fa-user-tie mr-1"></i>
                                        Vendedor
                                    </label>
                                    <input
                                        type="text"
                                        value={vendedor}
                                        onChange={(e) => setVendedor(e.target.value)}
                                        className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                        placeholder="Nombre del vendedor"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                        <i className="fa-solid fa-comment mr-1"></i>
                                        Observaciones
                                    </label>
                                    <textarea
                                        value={observaciones}
                                        onChange={(e) => setObservaciones(e.target.value)}
                                        rows={3}
                                        className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 resize-none"
                                        placeholder="Notas adicionales..."
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Totales */}
                        <div className="bg-card rounded-xl border border-border p-6">
                            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
                                <i className="fa-solid fa-receipt"></i>
                                Resumen de Totales
                            </h2>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between text-muted-foreground">
                                    <span>Subtotal 0%:</span>
                                    <span>${calculos.subtotal0.toFixed(2)}</span>
                                </div>
                                <div className="flex justify-between text-muted-foreground">
                                    <span>Subtotal 13%:</span>
                                    <span>${calculos.subtotal13.toFixed(2)}</span>
                                </div>
                                {calculos.subtotal15 > 0 && (
                                    <div className="flex justify-between text-muted-foreground">
                                        <span>Subtotal 15%:</span>
                                        <span>${calculos.subtotal15.toFixed(2)}</span>
                                    </div>
                                )}
                                {calculos.subtotalNoObjeto > 0 && (
                                    <div className="flex justify-between text-muted-foreground">
                                        <span>No Objeto IVA:</span>
                                        <span>${calculos.subtotalNoObjeto.toFixed(2)}</span>
                                    </div>
                                )}
                                {calculos.subtotalExento > 0 && (
                                    <div className="flex justify-between text-muted-foreground">
                                        <span>Exento IVA:</span>
                                        <span>${calculos.subtotalExento.toFixed(2)}</span>
                                    </div>
                                )}
                                <div className="flex justify-between text-muted-foreground">
                                    <span>Subtotal sin impuestos:</span>
                                    <span>${calculos.subtotalSinImpuestos.toFixed(2)}</span>
                                </div>
                                {calculos.totalDescuentos > 0 && (
                                    <div className="flex justify-between text-destructive">
                                        <span>Total Descuentos:</span>
                                        <span>-${calculos.totalDescuentos.toFixed(2)}</span>
                                    </div>
                                )}
                                <div className="flex justify-between text-muted-foreground">
                                    <span>IVA 13%:</span>
                                    <span>${calculos.iva13.toFixed(2)}</span>
                                </div>
                                {calculos.iva15 > 0 && (
                                    <div className="flex justify-between text-muted-foreground">
                                        <span>IVA 15%:</span>
                                        <span>${calculos.iva15.toFixed(2)}</span>
                                    </div>
                                )}
                                {propina > 0 && (
                                    <div className="flex justify-between text-muted-foreground">
                                        <span>Propina:</span>
                                        <span>${propina.toFixed(2)}</span>
                                    </div>
                                )}
                                <div className="pt-3 mt-3 border-t border-border">
                                    <div className="flex justify-between text-lg font-bold text-foreground">
                                        <span>TOTAL:</span>
                                        <span className="text-primary">${calculos.total.toFixed(2)}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Propina */}
                            <div className="mt-4 pt-4 border-t border-border">
                                <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                    <i className="fa-solid fa-hand-holding-dollar mr-1"></i>
                                    Propina
                                </label>
                                <input
                                    type="number"
                                    value={propina}
                                    onChange={(e) => setPropina(Number.parseFloat(e.target.value) || 0)}
                                    min="0"
                                    step="0.01"
                                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                                />
                            </div>
                        </div>

                        {/* Acciones móvil */}
                        <div className="lg:hidden flex flex-col gap-3">
                            <button
                                onClick={() => handleSubmit("borrador")}
                                disabled={loading}
                                className="w-full flex items-center justify-center gap-2 px-4 py-3 border border-border rounded-lg text-sm font-medium text-foreground hover:bg-muted transition-colors disabled:opacity-50"
                            >
                                <i className="fa-solid fa-floppy-disk"></i>
                                Guardar Borrador
                            </button>
                            <button
                                onClick={() => handleSubmit("emitir")}
                                disabled={loading}
                                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
                            >
                                <i className="fa-solid fa-paper-plane"></i>
                                Emitir Factura
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
