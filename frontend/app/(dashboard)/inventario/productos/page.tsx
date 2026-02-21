"use client"

import {useState} from "react"
import {useRouter} from "next/navigation"
import {Header} from "@/src/shared/components/header"
import {ProductosSection, StockStatusChart, StockDistributionChart} from "@/src/modules/inventario/components/productos-section"
import {LoadingScreen} from "@/components/ui/loading-screen"
import {useProductos, useStock} from "@/src/core/store";
import {DrawerChartCard, StatsDrawer} from "@/src/shared/components/stats-drawer";

export default function ProductosPage() {
    const router = useRouter()
    const [isNavigating, setIsNavigating] = useState(false)
    const [statsOpen, setStatsOpen] = useState(false)

    const {data: productos, isLoading, error} = useProductos()

    const handleAddProducto = () => {
        setIsNavigating(true)
        router.push("/inventario/productos/nuevo")
    }
    const handleStock = () => {
        setIsNavigating(true)
        router.push("/inventario/stock")
    }

    if (isNavigating) {
        return <LoadingScreen message="Cargando productos en inventario..."/>
    }

    return (
        <>
            <Header
                title="Gestión de Productos"
                breadcrumb={["Inventario", "Productos"]}
                actions={
                    <div className={"flex gap-2"}>
                        <button
                            onClick={handleAddProducto}
                            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
                        >
                            <i className="fa-solid fa-plus"></i>
                            Agregar Producto
                        </button>
                        <button
                            onClick={handleStock}
                            className="flex items-center gap-2 px-4 py-2 bg-success/80 rounded-lg text-sm font-medium hover:bg-success/40 transition-colors"
                        >
                            <i className="fa-solid fa-share"></i>
                            Stock
                        </button>
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
                <ProductosSection/>
            </main>

            <StatsDrawer
                open={statsOpen}
                onClose={() => setStatsOpen(false)}
                title="Estadísticas de Stock"
            >
                <DrawerChartCard title="Stock por Bodega" icon="fa-warehouse">
                    <StockStatusChart productos={productos}/>
                </DrawerChartCard>
                <DrawerChartCard title="Estado de Inventario" icon="fa-circle-half-stroke">
                    <StockDistributionChart productos={productos}/>
                </DrawerChartCard>
            </StatsDrawer>
        </>
    )
}