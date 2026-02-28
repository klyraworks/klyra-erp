"use client"

import Link from "next/link"
import {Header} from "@/src/shared/components/header"
import {ProductoForm} from "@/src/modules/inventario/forms/producto-form"
import {BodegaForm} from "@/src/modules/inventario/forms/bodega-form";
import {useRef} from "react";

export default function NuevoProductoRoute() {
    const formRef = useRef<HTMLFormElement>(null!)
    return (
        <>
            <Header
                title="Nuevo Producto"
                breadcrumb={["Inventario", "Productos", "Nuevo"]}
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
                    <ProductoForm mode="create" formRef={formRef}/>
                </div>
            </main>
        </>
    )
}
