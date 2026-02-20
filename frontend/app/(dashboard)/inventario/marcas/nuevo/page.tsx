"use client"

import Link from "next/link"
import {Header} from "@/src/shared/components/header"
import {MarcaForm} from "@/src/modules/inventario/forms/marca-form"

export default function NuevaMarcaRoute() {
    return (
        <>
            <Header
                title="Nueva Marca"
                breadcrumb={["Inventario", "Marcas", "Crear"]}
                actions={
                    <Link
                        href="/inventario/marcas"
                        className="flex items-center gap-2 px-4 py-2 bg-muted text-foreground rounded-lg text-sm font-medium hover:bg-muted/80 transition-colors"
                    >
                        <i className="fa-solid fa-arrow-left"></i>
                        <span className="hidden sm:inline">Volver</span>
                    </Link>
                }
            />
            <main className="flex-1 overflow-y-auto p-6">
                <div className="max-w-7xl mx-auto">
                    <MarcaForm mode="create"/>
                </div>
            </main>
        </>
    )
}