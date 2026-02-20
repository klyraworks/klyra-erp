// frontend/app/(dashboard)/inventario/bodegas/nuevo/page.tsx
"use client"

import Link from "next/link"
import { Header } from "@/src/shared/components/header"
import { BodegaForm } from "@/src/modules/inventario/forms/bodega-form"

export default function NuevaBodegaRoute() {
  return (
    <>
      <Header
        title="Nueva Bodega"
        breadcrumb={["Inventario", "Bodegas", "Nuevo"]}
        actions={
          <Link
            href="/inventario/bodegas"
            className="flex items-center gap-2 px-4 py-2 bg-muted text-muted-foreground rounded-lg text-sm font-medium hover:bg-muted/80 transition-colors"
          >
            <i className="fa-solid fa-arrow-left"></i>
            Volver
          </Link>
        }
      />
      <main className="flex-1 overflow-y-auto p-6">
          <BodegaForm mode="create" />
      </main>
    </>
  )
}
