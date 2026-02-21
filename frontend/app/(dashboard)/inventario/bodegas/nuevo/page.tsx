// frontend/app/(dashboard)/inventario/bodegas/nuevo/page.tsx
"use client"

import Link from "next/link"
import {Header} from "@/src/shared/components/header"
import {BodegaForm} from "@/src/modules/inventario/forms/bodega-form"
import {useRef} from "react";

export default function NuevaBodegaRoute() {
    const formRef = useRef<HTMLFormElement>(null!)
    return (
        <>
            <Header
                title="Nueva Bodega"
                breadcrumb={["Inventario", "Bodegas", "Nuevo"]}
                actions={
                    <div className="flex items-center gap-2">
                        <Link
                            href="/inventario/bodegas"
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
                            <span className="hidden sm:inline">Crear Bodega</span>
                        </button>
                    </div>
                }
            />
            <main className="flex-1 overflow-y-auto p-6">
                <div className="max-w-7xl mx-auto">
                    <BodegaForm mode="create" formRef={formRef}/>
                </div>
            </main>
        </>
    )
}
