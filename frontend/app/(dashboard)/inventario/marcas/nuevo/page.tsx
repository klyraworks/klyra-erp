"use client"

import { useRef } from "react"
import Link from "next/link"
import { Header } from "@/src/shared/components/header"
import { MarcaForm } from "@/src/modules/inventario/forms/marca-form"

export default function NuevaMarcaRoute() {
    const formRef = useRef<HTMLFormElement>(null!)

    return (
        <>
            <Header
                title="Nueva Marca"
                breadcrumb={["Inventario", "Marcas", "Crear"]}
                actions={
                    <div className="flex items-center gap-2">
                        <Link
                            href="/inventario/marcas"
                            className="flex items-center gap-2 px-4 py-2 border border-border rounded-lg text-sm font-medium text-foreground hover:bg-muted transition-colors"
                        >
                            <i className="fa-solid fa-arrow-left"></i>
                            <span className="hidden sm:inline">Volver</span>
                        </Link>
                        <button
                            onClick={() => formRef.current?.requestSubmit()}
                            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm"
                        >
                            <i className="fa-solid fa-save"></i>
                            <span className="hidden sm:inline">Crear Marca</span>
                        </button>
                    </div>
                }
            />
            <main className="flex-1 overflow-y-auto p-6">
                <div className="max-w-7xl mx-auto">
                    <MarcaForm mode="create" formRef={formRef} />
                </div>
            </main>
        </>
    )
}