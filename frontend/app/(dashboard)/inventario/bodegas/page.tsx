// frontend/app/(dashboard)/inventario/bodegas/page.tsx
"use client"

import {useState} from "react"
import {useRouter} from "next/navigation"
import {Header} from "@/src/shared/components/header"
import {LoadingScreen} from "@/components/ui/loading-screen"
import {BodegasSection} from "@/src/modules/inventario/components/bodegas-section";
import Link from "next/link";

export default function BodegasPage() {
    const router = useRouter()
    const [isNavigating, setIsNavigating] = useState(false)

    const handleAddCategoria = () => {
        setIsNavigating(true)
        router.push("/inventario/bodegas/nuevo")
    }

    if (isNavigating) {
        return <LoadingScreen message="Cargando Bodegas..."/>
    }

    return (
        <>
            <Header
                title="Gestión de Bodegas"
                breadcrumb={["Inventario", "Bodegas"]}
                actions={
                    <Link
                        href="/inventario/bodegas/nuevo"
                        className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
                    >
                        <i className="fa-solid fa-plus"></i>
                        Agregar Bodega
                    </Link>
                }
            />
            <main className="flex-1 overflow-y-auto p-6">
                <BodegasSection/>
            </main>
        </>
    )
}