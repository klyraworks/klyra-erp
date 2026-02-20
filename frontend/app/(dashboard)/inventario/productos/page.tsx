"use client"

import {useState} from "react"
import {useRouter} from "next/navigation"
import {Header} from "@/src/shared/components/header"
import {ProductosSection} from "@/src/modules/inventario/components/productos-section"
import {LoadingScreen} from "@/components/ui/loading-screen"

export default function ProductosPage() {
    const router = useRouter()
    const [isNavigating, setIsNavigating] = useState(false)

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
                            onClick={handleStock}
                            className="flex items-center gap-2 px-4 py-2 bg-success/80 rounded-lg text-sm font-medium hover:bg-success/40 transition-colors"
                        >
                            <i className="fa-solid fa-share"></i>
                            Stock
                        </button>
                        <button
                            onClick={handleAddProducto}
                            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
                        >
                            <i className="fa-solid fa-plus"></i>
                            Agregar Producto
                        </button>
                    </div>
                }
            />
            <main className="flex-1 overflow-y-auto p-6">
                <ProductosSection/>
            </main>
        </>
    )
}