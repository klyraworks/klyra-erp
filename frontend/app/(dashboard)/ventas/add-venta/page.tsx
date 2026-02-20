"use client"

import Link from "next/link"
import { Header } from "@/src/shared/components/header"
import { NuevaVentaPage } from "@/src/modules/ventas/pages/venta-form"

export default function NuevaVentaRoute() {
  return (
    <>
      <Header
        title="Nueva Venta / Factura"
        breadcrumb={["Klyra", "Ventas", "Nueva"]}
        actions={
          <Link
            href="/ventas"
            className="flex items-center gap-2 px-4 py-2 bg-muted text-muted-foreground rounded-lg text-sm font-medium hover:bg-muted/80 transition-colors"
          >
            <i className="fa-solid fa-arrow-left"></i>
            Volver
          </Link>
        }
      />
      <main className="flex-1 overflow-y-auto p-6">
        <NuevaVentaPage onBack={() => "/ventas"} />
      </main>
    </>
  )
}
