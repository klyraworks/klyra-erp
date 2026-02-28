// app/(dashboard)/productos/[id]/editar/page.tsx

"use client"

import {useParams} from "next/navigation"
import {useStore, viewProducto} from "@/src/core/store"
import {Header} from "@/src/shared/components/header"
import {ProductoForm} from "@/src/modules/inventario/forms/producto-form"
import {LoadingScreen} from "@/components/ui/loading-screen"
import {useEffect, useRef, useState} from "react"
import {Producto} from "@/src/core/api/types"
import {alertas} from "@/components/alerts/alertas-toast"
import Link from "next/link";

export default function EditarProductoPage() {
    const params = useParams()
    const productoId = params.id as string
    const [producto, setProducto] = useState<Producto | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(false)
    const formRef = useRef<HTMLFormElement>(null!)

    useEffect(() => {
        async function loadProducto() {
            try {
                setLoading(true)
                const data = await viewProducto({id: productoId} as Producto)
                setProducto(data)
                setError(false)
            } catch (err) {
                console.warn('Error al cargar producto:', err)
                setError(true)
                alertas.error('No se pudo cargar el producto', 'Error')
            } finally {
                setLoading(false)
            }
        }

        if (productoId) {
            loadProducto()
        }
    }, [productoId])

    if (loading) {
        return <LoadingScreen message="Cargando datos del producto..."/>
    }

    if (error || !producto) {
        return (
            <>
                <Header
                    title="Error"
                    breadcrumb={["Inventario", "Productos", "Error"]}
                />
                <main className="flex-1 overflow-y-auto p-6">
                    <div className="bg-card rounded-xl border border-border p-6 text-center">
                        <i className="fa-solid fa-circle-exclamation text-4xl text-destructive mb-4"></i>
                        <p className="text-destructive font-medium">Producto no encontrado</p>
                        <p className="text-sm text-muted-foreground mt-2">
                            El producto que buscas no existe o no tienes permisos para verlo
                        </p>
                    </div>
                </main>
            </>
        )
    }

    return (
        <>
            <Header
                title="Editar Producto"
                breadcrumb={["Inventario", "Productos", "Editar", producto.nombre]}
                actions={
                    <div className="flex items-center gap-2">
                        <Link
                            href="/inventario/productos"
                            className="flex items-center gap-2 px-4 py-2 bg-muted text-muted-foreground rounded-lg text-sm font-medium hover:bg-muted/80 transition-colors"
                        >
                            <i className="fa-solid fa-arrow-left"></i>
                            Volver
                        </Link>
                        <button
                            onClick={() => formRef.current?.requestSubmit()}
                            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm"
                        >
                            <i className="fa-solid fa-save"></i>
                            <span className="hidden sm:inline">Crear Producto</span>
                        </button>
                    </div>
                }
            />
            <main className="flex-1 overflow-y-auto p-6">
                <div className="max-w-7xl mx-auto">
                    <ProductoForm mode="edit" producto={producto} formRef={formRef}/>
                </div>
            </main>
        </>
    )
}