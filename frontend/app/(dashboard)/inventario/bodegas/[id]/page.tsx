"use client"

import { useParams, useRouter } from "next/navigation"
import { useStore, viewProducto } from "@/src/core/store"
import { Header } from "@/src/shared/components/header"
import { LoadingScreen } from "@/components/ui/loading-screen"
import { useEffect, useState } from "react"
import { Producto } from "@/src/core/api/types"

export default function ProductoDetallePage() {
  const params = useParams()
  const router = useRouter()
  const productoId = params.id as string
  const [producto, setProducto] = useState<Producto | null>(null)
  const [loading, setLoading] = useState(true)


  if (loading) {
    return <LoadingScreen message="Cargando producto..." />
  }

  if (!producto) {
    return <div>Producto no encontrado</div>
  }

  return (
    <>
      <Header
        title={producto.nombre}
        breadcrumb={["Inventario", "Productos", producto.nombre]}
        actions={
          <button
            onClick={() => router.push(`/inventario/productos/${producto.id}/editar`)}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            <i className="fa-solid fa-pen"></i>
            Editar
          </button>
        }
      />
      <main className="flex-1 overflow-y-auto p-6">
        {/* Aquí va el contenido del detalle del producto */}
        <div className="bg-card rounded-xl border border-border p-6">
          <h2 className="text-xl font-bold mb-4">{producto.nombre}</h2>
          <p className="text-muted-foreground">{producto.descripcion}</p>
          {/* Más detalles... */}
        </div>
      </main>
    </>
  )
}