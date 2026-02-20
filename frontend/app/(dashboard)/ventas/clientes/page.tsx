"use client"

import { Header } from "@/src/shared/components/header"
import { ClientesSection } from "@/src/modules/ventas/components/clientes-section"

export default function ClientesPage() {
  return (
    <>
      <Header title="Gestión de Clientes" breadcrumb={["Klyra", "Ventas", "Clientes"]} />
      <main className="flex-1 overflow-y-auto p-6">
        <ClientesSection />
      </main>
    </>
  )
}
