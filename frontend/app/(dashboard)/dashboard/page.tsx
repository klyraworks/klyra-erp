// app/dashboard/page.tsx
"use client"

import { Header } from "@/src/shared/components/header"
import { StatCard } from "@/src/shared/components/stat-card"
import { useVentas, useProductos, usePagos } from "@/src/core/store"
import { VentasSection } from "@/src/modules/ventas/components/ventas-section"
import { ProductosSection } from "@/src/modules/inventario/components/productos-section"

export default function DashboardPage() {
  const { data: ventas } = useVentas()
  const { data: productos } = useProductos()
  const { data: pagos } = usePagos()

  const totalVentas = ventas.reduce((sum, v) => sum + Number.parseFloat(String(v.total)), 0)
  const ventasPendientes = ventas.filter((v) => v.estado === "pendiente" || v.estado === "borrador").length
  const productosStock = productos.filter((p) => p.stock <= 5).length
  const totalPagos = pagos.reduce((sum, p) => sum + Number.parseFloat(String(p.monto)), 0)

  return (
    <>
      <Header title="Dashboard" breadcrumb={["Klyra", "Dashboard"]} />
      <main className="flex-1 overflow-y-auto p-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <StatCard
              title="Total Ventas"
              value={`$${totalVentas.toFixed(2)}`}
              icon="fa-dollar-sign"
              subtitle="Descripción"/>
          <StatCard
              title="Ventas Pendientes"
              value={ventasPendientes}
              icon="fa-clock"
              subtitle="Descripción"
          />
          <StatCard
            title="Stock Crítico"
            value={productosStock}
            icon="fa-triangle-exclamation"
            subtitle="Descripción"/>
          <StatCard
            title="Total Cobrado"
            value={`$${totalPagos.toFixed(2)}`}
            icon="fa-money-bill-wave"
            subtitle="Descripción"
          />
        </div>

        {/* Recent Data */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <VentasSection compact />
          <ProductosSection compact />
        </div>
      </main>
    </>
  )
}
