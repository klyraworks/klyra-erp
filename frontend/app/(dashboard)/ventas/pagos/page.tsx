"use client"

import { Header } from "@/src/shared/components/header"
import { PagosSection } from "@/src/modules/finanzas/components/pagos-section"

export default function PagosPage() {
  return (
    <>
      <Header title="Gestión de Pagos" breadcrumb={["Klyra", "Finanzas", "Pagos"]} />
      <main className="flex-1 overflow-y-auto p-6">
        <PagosSection />
      </main>
    </>
  )
}
