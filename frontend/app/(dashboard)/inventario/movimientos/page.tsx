"use client"

import { Header } from "@/src/shared/components/header"
import { MovimientosSection } from "@/src/modules/inventario/components/movimientos-section"
import {DrawerChartCard, StatsDrawer} from "@/src/shared/components/stats-drawer";
import {MovimientosPorTipoChart, MovimientosPorFechaChart} from "@/src/modules/inventario/components/movimientos-section";
import {useState} from "react";
import {useMovimientos} from "@/src/core/store";
import {useRouter} from "next/navigation";

export default function MovimientosPage() {
    const router = useRouter()
    const [isNavigating, setIsNavigating] = useState(false)
    const [statsOpen, setStatsOpen] = useState(false)
    const {data: movimientos, isLoading, error} = useMovimientos()


    const handleAddProducto = () => {
        setIsNavigating(true)
        router.push("/inventario/movimientos/nuevo")
    }
  return (
    <>
      <Header
          title="Movimientos de Inventario"
          breadcrumb={["Klyra", "Inventario", "Movimientos"]}
          actions={
              <div className={"flex gap-2"}>
                  <button
                      onClick={handleAddProducto}
                      className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
                  >
                      <i className="fa-solid fa-plus"></i>
                      Crear Movimiento
                  </button>
                  <button
                      onClick={() => setStatsOpen(true)}
                      className="flex items-center gap-2 px-4 py-2 border border-border rounded-lg text-sm font-medium text-foreground hover:bg-muted transition-colors whitespace-nowrap"
                  >
                      <i className="fa-solid fa-chart-bar"></i>
                      <span>Estadísticas</span>
                  </button>
              </div>

          }
      />
      <main className="flex-1 overflow-y-auto p-6">
        <MovimientosSection />
      </main>

        <StatsDrawer
            open={statsOpen}
            onClose={() => setStatsOpen(false)}
            title="Estadísticas de Stock"
        >
            <DrawerChartCard title="Stock por Bodega" icon="fa-warehouse">
                <MovimientosPorTipoChart movimientos={movimientos}/>
            </DrawerChartCard>
            <DrawerChartCard title="Estado de Inventario" icon="fa-circle-half-stroke">
                <MovimientosPorFechaChart movimientos={movimientos}/>
            </DrawerChartCard>
        </StatsDrawer>
    </>
  )
}
