// frontend/src/shared/components/stats-drawer.tsx

"use client"

import { useEffect, useRef } from "react"

interface StatsDrawerProps {
    open: boolean
    onClose: () => void
    title?: string
    children: React.ReactNode
}

export function StatsDrawer({ open, onClose, title = "Estadísticas", children }: StatsDrawerProps) {
    const drawerRef = useRef<HTMLDivElement>(null)

    // Cerrar con Escape
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && open) onClose()
        }
        document.addEventListener('keydown', handleKeyDown)
        return () => document.removeEventListener('keydown', handleKeyDown)
    }, [open, onClose])

    // Bloquear scroll del body cuando está abierto
    useEffect(() => {
        document.body.style.overflow = open ? 'hidden' : ''
        return () => { document.body.style.overflow = '' }
    }, [open])

    return (
        <>
            {/* Overlay */}
            <div
                className={`fixed inset-0 bg-black/40 z-40 transition-opacity duration-300 ${open ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}
                onClick={onClose}
            />

            {/* Drawer */}
            <div
                ref={drawerRef}
                className={`fixed top-0 right-0 h-full w-full sm:w-[420px] bg-card border-l border-border shadow-2xl z-50 flex flex-col transition-transform duration-300 ease-in-out ${open ? 'translate-x-0' : 'translate-x-full'}`}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-border flex-shrink-0">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-chart-bar text-primary text-sm"></i>
                        </div>
                        <h2 className="text-sm font-semibold text-foreground">{title}</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="w-8 h-8 flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors"
                    >
                        <i className="fa-solid fa-xmark text-sm"></i>
                    </button>
                </div>

                {/* Contenido scrolleable */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {children}
                </div>
            </div>
        </>
    )
}

// Sub-componente para cada chart dentro del drawer
interface DrawerChartCardProps {
    title: string
    icon?: string
    children: React.ReactNode
}

export function DrawerChartCard({ title, icon = "fa-chart-simple", children }: DrawerChartCardProps) {
    return (
        <div className="bg-background rounded-xl border border-border p-4">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
                <i className={`fa-solid ${icon} text-primary text-[10px]`}></i>
                {title}
            </h3>
            {children}
        </div>
    )
}