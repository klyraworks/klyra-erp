"use client"

import Link from "next/link"
import { Header } from "@/src/shared/components/header"
import { CategoriaForm } from "@/src/modules/inventario/forms/categoria-form"

export default function NuevaCategoriaRoute() {
  return (
    <>
      <Header
        title="Nueva Categoría"
        breadcrumb={["Inventario", "Categorías", "Nuevo"]}
        actions={
          <Link
            href="/inventario/categorias"
            className="flex items-center gap-2 px-4 py-2 bg-muted text-muted-foreground rounded-lg text-sm font-medium hover:bg-muted/80 transition-colors"
          >
            <i className="fa-solid fa-arrow-left"></i>
            Volver
          </Link>
        }
      />
      <main className="flex-1 overflow-y-auto p-6">
          <CategoriaForm mode="create" />
      </main>
    </>
  )
}
