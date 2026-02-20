"use client"

import Link from "next/link"
import { Header } from "@/src/shared/components/header"
import { VentasSection } from "@/src/modules/ventas/components/ventas-section"

export default function VentasPage() {
  return (
    <>
      <Header
        title="Gestión de Ventas"
        breadcrumb={["Klyra", "Ventas"]}
        actions={
          <Link
            href="/ventas/add-venta"
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            <i className="fa-solid fa-plus"></i>
            Nueva Venta
          </Link>
        }
      />
      <main className="flex-1 overflow-y-auto p-6">
        <VentasSection />
      </main>
    </>
  )
}
