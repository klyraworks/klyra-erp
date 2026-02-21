// app/(dashboard)/movimientos/nuevo/page.tsx

"use client"

import {useSearchParams} from "next/navigation"
import {Header} from "@/src/shared/components/header"
import {MovimientoForm} from "@/src/modules/inventario/forms/movimiento-form"
import Link from "next/link";
import {BodegaForm} from "@/src/modules/inventario/forms/bodega-form";
import {useRef} from "react";

export default function NuevoMovimientoPage() {
    const searchParams = useSearchParams()

    // Obtener parámetros de la URL
    const tipo = (searchParams.get('tipo') || 'entrada') as 'entrada' | 'salida' | 'transferencia'
    const bodegaId = searchParams.get('bodega_id') || undefined
    const bodegaOrigenId = searchParams.get('bodega_origen_id') || undefined
    const productoId = searchParams.get('producto_id') || undefined
    const formRef = useRef<HTMLFormElement>(null!)

    // Determinar título y breadcrumb según tipo
    const getTitulo = () => {
        switch (tipo) {
            case 'entrada':
                return 'Registrar Entrada'
            case 'salida':
                return 'Registrar Salida'
            case 'transferencia':
                return 'Registrar Transferencia'
            default:
                return 'Nuevo Movimiento'
        }
    }

    const getIcono = () => {
        switch (tipo) {
            case 'entrada':
                return 'fa-arrow-right-to-bracket'
            case 'salida':
                return 'fa-arrow-right-from-bracket'
            case 'transferencia':
                return 'fa-truck-ramp-box'
            default:
                return 'fa-boxes-stacked'
        }
    }

    return (<>
            <Header
                title={getTitulo()}
                breadcrumb={["Inventario", "Movimientos", getTitulo()]}
                actions={
                <div className="flex items-center gap-2">
                    <Link
                        href="/inventario/productos"
                        className="flex items-center gap-2 px-4 py-2 bg-muted text-foreground rounded-lg text-sm font-medium hover:bg-muted/80 transition-colors"
                    >
                        <i className="fa-solid fa-arrow-left"></i>
                        <span className="hidden sm:inline">Volver</span>
                    </Link>
                    <button
                        onClick={() => formRef.current?.requestSubmit()}
                        className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm"
                    >
                        <i className="fa-solid fa-save"></i>
                        <span className="hidden sm:inline">Crear Movimiento</span>
                    </button>
                </div>
                }
            />
            <main className="flex-1 overflow-y-auto p-6">
                <div className="max-w-7xl mx-auto">
                <MovimientoForm
                    tipo={tipo}
                    bodegaIdInicial={bodegaId || bodegaOrigenId}
                    productoIdInicial={productoId}
                    formRef={formRef}
                />
                </div>
            </main>
        </>
    )
}