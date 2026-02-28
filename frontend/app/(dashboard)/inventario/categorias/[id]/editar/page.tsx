// app/(dashboard)/categorias/[id]/editar/page.tsx

"use client"

import {useParams} from "next/navigation"
import {Header} from "@/src/shared/components/header"
import {CategoriaForm} from "@/src/modules/inventario/forms/categoria-form"
import {LoadingScreen} from "@/components/ui/loading-screen"
import {useEffect, useRef, useState} from "react"
import {alertas} from "@/components/alerts/alertas-toast"
import Link from "next/link"
import {Categoria} from "@/src/core/api/types"
import { apiFetch, ApiError } from "@/src/core/api/client"

export default function EditarCategoriaPage() {
    const params = useParams()
    const categoriaId = params.id as string
    const [categoria, setCategoria] = useState<Categoria | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(false)
    const formRef = useRef<HTMLFormElement>(null!)

    useEffect(() => {
        async function loadCategoria() {
            try {
                setLoading(true)

                const data = await apiFetch<Categoria>(`/api/categorias/${categoriaId}/`)
                setCategoria(data)
                setError(false)
            } catch (err) {
                setError(true)
                if (err instanceof ApiError) {
                    alertas.error(err.mensaje, err.titulo)
                } else {
                    alertas.error('No se pudo cargar la categoría', 'Error')
                }
            } finally {
                setLoading(false)
            }
        }

        if (categoriaId) {
            loadCategoria()
        }
    }, [categoriaId])

    if (loading) {
        return <LoadingScreen message="Cargando datos de la categoría..."/>
    }

    if (error || !categoria) {
        return (
            <>
                <Header
                    title="Error"
                    breadcrumb={["Inventario", "Categorías", "Error"]}
                />
                <main className="flex-1 overflow-y-auto p-6">
                    <div className="max-w-2xl mx-auto">
                        <div className="bg-card rounded-xl border border-border shadow-sm p-8 text-center">
                            <div
                                className="w-16 h-16 bg-red-100 dark:bg-red-950/20 rounded-full flex items-center justify-center mx-auto mb-4">
                                <i className="fa-solid fa-circle-exclamation text-3xl text-red-600 dark:text-red-400"></i>
                            </div>
                            <h3 className="text-lg font-semibold text-foreground mb-2">Categoría no encontrada</h3>
                            <p className="text-sm text-muted-foreground mb-6">
                                La categoría que buscas no existe o no tienes permisos para acceder a ella
                            </p>
                            <Link
                                href="/inventario/categorias"
                                className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
                            >
                                <i className="fa-solid fa-arrow-left"></i>
                                Volver
                            </Link>
                        </div>
                    </div>
                </main>
            </>
        )
    }

    return (
        <>
            <Header
                title="Editar Categoría"
                breadcrumb={["Inventario", "Categorías", "Editar", categoria.nombre]}
                actions={
                    <div className="flex items-center gap-2">
                        {categoria.subcategorias_count !== undefined && categoria.subcategorias_count > 0 && (
                            <div
                                className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-purple-100 dark:bg-purple-950/20 text-purple-800 dark:text-purple-300 rounded-lg text-xs font-medium">
                                <i className="fa-solid fa-sitemap"></i>
                                {categoria.subcategorias_count} subcategoría{categoria.subcategorias_count !== 1 ? 's' : ''}
                            </div>
                        )}
                        {categoria.productos_count !== undefined && categoria.productos_count > 0 && (
                            <div
                                className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-blue-100 dark:bg-blue-950/20 text-blue-800 dark:text-blue-300 rounded-lg text-xs font-medium">
                                <i className="fa-solid fa-box"></i>
                                {categoria.productos_count} producto{categoria.productos_count !== 1 ? 's' : ''}
                            </div>
                        )}
                        <Link
                            href="/inventario/categorias"
                            className="flex items-center gap-2 px-4 py-2 bg-muted text-foreground rounded-lg text-sm font-medium hover:bg-muted/80 transition-colors"
                        >
                            <i className="fa-solid fa-arrow-left"></i>
                            <span className="hidden sm:inline">Volver</span>
                        </Link>
                        <button
                            onClick={() => formRef.current?.requestSubmit()}
                            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm"
                        >
                            <i className="fa-solid fa-save"></i>
                            <span className="hidden sm:inline">Crear Categoría</span>
                        </button>
                    </div>
                }
            />
            <main className="flex-1 overflow-y-auto p-6">
                <div className="max-w-7xl mx-auto">
                    {/* Información contextual */}
                    <div
                        className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
                        <div className="flex items-start gap-3">
                            <i className="fa-solid fa-info-circle text-blue-600 dark:text-blue-400 mt-0.5"></i>
                            <div className="flex-1">
                                <p className="text-sm font-medium text-blue-800 dark:text-blue-300 mb-1">
                                    Editando categoría: {categoria.codigo}
                                </p>
                                <div className="text-xs text-blue-700 dark:text-blue-400 space-y-1">
                                    {categoria.ruta_completa && (
                                        <p>
                                            <strong>Ruta:</strong> {categoria.ruta_completa}
                                        </p>
                                    )}
                                    {categoria.subcategorias_count !== undefined && categoria.subcategorias_count > 0 && (
                                        <p className="text-yellow-700 dark:text-yellow-400">
                                            <i className="fa-solid fa-warning mr-1"></i>
                                            Esta categoría
                                            tiene {categoria.subcategorias_count} subcategoría{categoria.subcategorias_count !== 1 ? 's' : ''}.
                                            Los cambios en la jerarquía afectarán sus niveles.
                                        </p>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>

                    <CategoriaForm mode="edit" categoria={categoria} formRef={formRef}/>
                </div>
            </main>
        </>
    )
}