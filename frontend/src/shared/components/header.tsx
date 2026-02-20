"use client"

import type React from "react"

import {useState} from "react"
import {useRouter} from "next/navigation"
import {useStore} from "@/src/core/store"
import {logout} from "@/src/core/api/client"

interface HeaderProps {
    title: string
    breadcrumb?: string[]
    actions?: React.ReactNode
}

export function Header({title, breadcrumb = [], actions}: HeaderProps) {

    const router = useRouter()
    const [showDropdown, setShowDropdown] = useState(false)
    const [showMobileMenu, setShowMobileMenu] = useState(false)
    const [showMobileActions, setShowMobileActions] = useState(false)

    const handleLogout = () => {
        logout()
        router.push("/")
    }

    return (
        <>
            <header className="px-4 sm:px-6 my-4">
                {/* Top Row: Breadcrumb */}
                {breadcrumb.length > 0 && (
                    <div className="hidden md:flex items-center gap-2 text-xs lg:text-sm text-muted-foreground mb-2">
                        {breadcrumb.map((item, index) => (
                            <span key={index} className="flex items-center gap-2">
                {index > 0 && <i className="fa-solid fa-chevron-right text-[10px]"></i>}
                                <span className="truncate max-w-[100px] lg:max-w-[150px] xl:max-w-none" title={item}>
                  {item}
                </span>
              </span>
                        ))}
                    </div>
                )}

                {/* Main Row */}
                <div className="flex items-center justify-between gap-4 pb-3 border-b lg:border-0 lg:pb-0">
                    {/* Left: Title */}
                    <div className="flex-1 min-w-0">
                        <h1 className="text-base sm:text-lg lg:text-xl font-semibold text-foreground truncate">
                            {title}
                        </h1>
                    </div>

                    {/* Right: Utility Bar */}
                    <div className="flex items-center gap-2 flex-shrink-0">
                        {/* Search - Icon only below xl */}
                        <button
                            className="xl:hidden w-9 h-9 flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors">
                            <i className="fa-solid fa-magnifying-glass text-sm"></i>
                        </button>

                        {/* Search - Full input on xl+ */}
                        <div className="relative hidden xl:block">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                <i className="fa-solid fa-magnifying-glass text-sm"></i>
              </span>
                            <input
                                type="text"
                                placeholder="Buscar..."
                                className="w-48 xl:w-64 pl-9 pr-4 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                            />
                        </div>

                        {/* Notifications */}
                        <button
                            className="relative w-9 h-9 flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors">
                            <i className="fa-solid fa-bell text-sm"></i>
                            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-destructive rounded-full"></span>
                        </button>

                        {/* User Menu - Desktop */}
                        <div className="relative hidden lg:block">
                            <button
                                onClick={() => setShowDropdown(!showDropdown)}
                                className="flex items-center gap-2 px-2 py-2 rounded-lg hover:bg-muted transition-colors"
                            >
                                <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                                    <i className="fa-solid fa-user text-primary text-sm"></i>
                                </div>
                                <div className="text-left hidden 2xl:block">
                                    <p className="text-sm font-medium text-foreground">Admin</p>
                                    <p className="text-xs text-muted-foreground">Administrador</p>
                                </div>
                                <i className="fa-solid fa-chevron-down text-xs text-muted-foreground"></i>
                            </button>

                            {showDropdown && (
                                <>
                                    <div className="fixed inset-0 z-40" onClick={() => setShowDropdown(false)}/>
                                    <div
                                        className="absolute right-0 top-full mt-2 w-48 bg-card border border-border rounded-xl shadow-lg z-50 py-2">
                                        <button
                                            className="w-full px-4 py-2 text-left text-sm text-muted-foreground hover:text-foreground hover:bg-muted flex items-center gap-3">
                                            <i className="fa-solid fa-user-gear"></i>
                                            Mi Perfil
                                        </button>
                                        <button
                                            className="w-full px-4 py-2 text-left text-sm text-muted-foreground hover:bg-muted flex items-center gap-3">
                                            <i className="fa-solid fa-gear"></i>
                                            Configuración
                                        </button>
                                        <hr className="my-2 border-border"/>
                                        <button
                                            onClick={handleLogout}
                                            className="w-full px-4 py-2 text-left text-sm text-destructive hover:bg-destructive/10 flex items-center gap-3"
                                        >
                                            <i className="fa-solid fa-right-from-bracket"></i>
                                            Cerrar Sesión
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>

                        {/* User Avatar - Mobile */}
                        <button
                            onClick={() => setShowMobileMenu(!showMobileMenu)}
                            className="lg:hidden w-9 h-9 bg-primary/10 rounded-full flex items-center justify-center"
                        >
                            <i className="fa-solid fa-user text-primary text-sm"></i>
                        </button>
                    </div>
                </div>

                {/* Actions Row - Below main header, full width */}
                {actions && (
                    <div className={"border-y flex justify-end pb-3"}>
                        <div className="hidden lg:flex items-center gap-2 mt-3 flex-wrap">
                            {actions}
                        </div>
                    </div>
                )}
            </header>

            {/* Mobile Actions FAB */}
            {actions && (
                <>
                    <button
                        onClick={() => setShowMobileActions(!showMobileActions)}
                        className="lg:hidden fixed top-20 right-6 z-50 w-14 h-14 bg-primary text-primary-foreground rounded-full flex items-center justify-center shadow-lg hover:scale-110 transition-all"
                    >
                        <i
                            className={`fa-solid ${showMobileActions ? "fa-times" : "fa-plus"} text-lg transition-transform ${showMobileActions ? "rotate-45" : ""}`}
                        ></i>
                    </button>

                    {/* Actions Menu */}
                    <div
                        className={`lg:hidden fixed top-36 right-6 z-40 flex flex-col gap-2 transition-all duration-300 ${
                            showMobileActions ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-4 pointer-events-none"
                        }`}
                    >
                        {actions}
                    </div>

                    {/* Overlay */}
                    {showMobileActions && (
                        <div
                            className="lg:hidden fixed inset-0 bg-black/20 z-30 transition-opacity"
                            onClick={() => setShowMobileActions(false)}
                        />
                    )}
                </>
            )}

            {/* Mobile Bottom Menu */}
            {showMobileMenu && (
                <>
                    <div
                        className="lg:hidden fixed inset-0 bg-black/50 z-40 animate-in fade-in duration-200"
                        onClick={() => setShowMobileMenu(false)}
                    />
                    <div
                        className="lg:hidden fixed bottom-0 left-0 right-0 bg-card border-t border-border rounded-t-2xl z-50 p-4 space-y-2 animate-in slide-in-from-bottom duration-300">
                        {/* User Info */}
                        <div className="flex items-center gap-3 px-3 py-2 mb-2">
                            <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                                <i className="fa-solid fa-user text-primary"></i>
                            </div>
                            <div>
                                <p className="text-sm font-medium text-foreground">Admin</p>
                                <p className="text-xs text-muted-foreground">Administrador</p>
                            </div>
                        </div>

                        {/* Menu Items */}
                        <button
                            className="w-full px-3 py-2.5 text-left text-sm text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg flex items-center gap-3 transition-colors">
                            <i className="fa-solid fa-user-gear w-5"></i>
                            Mi Perfil
                        </button>
                        <button
                            className="w-full px-3 py-2.5 text-left text-sm text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg flex items-center gap-3 transition-colors">
                            <i className="fa-solid fa-gear w-5"></i>
                            Configuración
                        </button>
                        <button
                            onClick={handleLogout}
                            className="w-full px-3 py-2.5 text-left text-sm text-destructive hover:bg-destructive/10 rounded-lg flex items-center gap-3 transition-colors"
                        >
                            <i className="fa-solid fa-right-from-bracket w-5"></i>
                            Cerrar Sesión
                        </button>
                    </div>
                </>
            )}
        </>
    )
}