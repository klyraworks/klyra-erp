"use client"

import Link from "next/link"
import { Header } from "@/src/shared/components/header"
import { ProductoForm } from "@/src/modules/inventario/forms/producto-form"

export default function NuevoProductoRoute() {
  return (
    <>
      <Header
        title="Nuevo Producto"
        breadcrumb={["Klyra", "Inventario", "Productos", "Nuevo"]}
        actions={
          <Link
            href="/inventario/productos"
            className="flex items-center gap-2 px-4 py-2 bg-muted text-muted-foreground rounded-lg text-sm font-medium hover:bg-muted/80 transition-colors"
          >
            <i className="fa-solid fa-arrow-left"></i>
            Volver
          </Link>
        }
      />
      <main className="flex-1 overflow-y-auto p-6">
          <ProductoForm mode="create" />
      </main>
    </>
  )
}
