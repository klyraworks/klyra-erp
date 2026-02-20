"use client"

import { Header } from "@/src/shared/components/header"
import { MovimientosSection } from "@/src/modules/inventario/components/movimientos-section"

export default function MovimientosPage() {
  return (
    <>
      <Header title="Movimientos de Inventario" breadcrumb={["Klyra", "Inventario", "Movimientos"]} />
      <main className="flex-1 overflow-y-auto p-6">
        <MovimientosSection />
      </main>
    </>
  )
}
