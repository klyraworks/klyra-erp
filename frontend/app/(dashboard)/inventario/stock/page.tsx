"use client"

import {useState} from "react"
import {useRouter} from "next/navigation"
import {Header} from "@/src/shared/components/header"
import {StockSection} from "@/src/modules/inventario/components/stock-section"
import {StatsDrawer, DrawerChartCard} from "@/src/shared/components/stats-drawer"
import {StockPorBodegaChart, EstadoStockChart} from "@/src/modules/inventario/components/stock-section"
import {LoadingScreen} from "@/components/ui/loading-screen"
import Link from "next/link"
import {useStock} from "@/src/core/store";

export default function ProductosPage() {
    const router = useRouter()
    const [isNavigating, setIsNavigating] = useState(false)
    const [statsOpen, setStatsOpen] = useState(false)

    const {data: inventario, isLoading, error} = useStock()

    const handleCrearEntrada = () => {
        setIsNavigating(true)
        router.push("/inventario/movimientos/nuevo")
    }

    if (isNavigating) {
        return <LoadingScreen message="Cargando productos..."/>
    }

    return (
        <>
            <Header
                title="Gestión de Productos en Inventario"
                breadcrumb={["Inventario", "Productos"]}
                actions={
                    <div className="flex gap-2">
                        <button
                            onClick={handleCrearEntrada}
                            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors whitespace-nowrap"
                        >
                            <i className="fa-solid fa-plus"></i>
                            Crear Entrada
                        </button>
                        <Link
                            href="/inventario/productos"
                            className="flex items-center gap-2 px-4 py-2 bg-success/80 rounded-lg text-sm font-medium hover:bg-success/40 transition-colors whitespace-nowrap"
                        >
                            <i className="fa-solid fa-share"></i>
                            Productos
                        </Link>
                        <button
                            onClick={() => setStatsOpen(true)}
                            className="flex items-center gap-2 px-4 py-2 border border-border rounded-lg text-sm font-medium text-foreground hover:bg-muted transition-colors whitespace-nowrap"
                        >
                            <i className="fa-solid fa-chart-bar"></i>
                            <span >Estadísticas</span>
                        </button>
                    </div>
                }
            />

            <main className="flex-1 overflow-y-auto p-6">
                <StockSection/>
            </main>

            <StatsDrawer
                open={statsOpen}
                onClose={() => setStatsOpen(false)}
                title="Estadísticas de Stock"
            >
                <DrawerChartCard title="Stock por Bodega" icon="fa-warehouse">
                    <StockPorBodegaChart inventario={inventario}/>
                </DrawerChartCard>
                <DrawerChartCard title="Estado de Inventario" icon="fa-circle-half-stroke">
                    <EstadoStockChart inventario={inventario}/>
                </DrawerChartCard>
            </StatsDrawer>
        </>
    )
}