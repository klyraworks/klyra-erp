"use client"

import {useState} from "react"
import {useRouter} from "next/navigation"
import {Header} from "@/src/shared/components/header"
import {StockSection} from "@/src/modules/inventario/components/stock-section"
import {LoadingScreen} from "@/components/ui/loading-screen"
import Link from "next/link"

export default function ProductosPage() {
    const router = useRouter()
    const [isNavigating, setIsNavigating] = useState(false)

    const handleCrearEntrada = () => {
        setIsNavigating(true)
        router.push("/inventario/movimientos/nuevo")
    }
    const handleProductos = () => {
        setIsNavigating(true)
        router.push("/inventario/productos")
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
                    <div className={"flex gap-2"}>
                        <Link
                            href={"/inventario/productos"}
                            className="flex items-center gap-2 px-4 py-2 bg-success/80 rounded-lg text-sm font-medium hover:bg-success/40 transition-colors"
                        >
                            <i className="fa-solid fa-share"></i>
                            Productos
                        </Link>
                        <button
                            onClick={handleCrearEntrada}
                            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
                        >
                            <i className="fa-solid fa-plus"></i>
                            Crear Entrada
                        </button>
                    </div>
                }
            />
            <main className="flex-1 overflow-y-auto p-6">
                <StockSection/>
            </main>
        </>
    )
}