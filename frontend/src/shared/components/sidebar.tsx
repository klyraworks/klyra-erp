"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useState, useEffect } from "react"
import { useTheme } from "@/src/core/theme/provider"

// ============================================================================
// TYPES
// ============================================================================

type SubItem = {
  id: string
  label: string
  href: string
  icon: string
}

type MenuItem = {
  id: string
  label: string
  icon: string
  href?: string
  subItems?: SubItem[]
}

type MenuGroup = {
  category: string
  items: MenuItem[]
}

// ============================================================================
// MENU CONFIGURATION
// ============================================================================

const menuItems: MenuGroup[] = [
  {
    category: "Favoritos",
    items: [
      {
        id: "dashboard-module",
        label: "Dashboard",
        icon: "fa-gauge-high",
        href: "/dashboard"
      },
    ],
  },
  {
    category: "Módulos",
    items: [
      {
        id: "inventario-module",
        label: "Inventario",
        icon: "fa-boxes-stacked",
        subItems: [
          { id: "stock", label: "Stock", href: "/inventario/stock", icon: "fa-clipboard-list" },
          { id: "productos-lista", label: "Productos", href: "/inventario/productos", icon: "fa-box" },
          { id: "categorias", label: "Categorías", href: "/inventario/categorias", icon: "fa-tags" },
          { id: "movimientos", label: "Movimientos", href: "/inventario/movimientos", icon: "fa-tags" },
          { id: "bodegas", label: "Bodegas", href: "/inventario/bodegas", icon: "fa-warehouse" },
          { id: "marcas", label: "Marcas", href: "/inventario/marcas", icon: "fa-sliders" },
        ]
      },
      {
        id: "finanzas-module",
        label: "Finanzas",
        icon: "fa-money-bill-trend-up",
        subItems: [
          { id: "cuentas-cobrar", label: "Cuentas por Cobrar", href: "/finanzas/cuentas-cobrar", icon: "fa-hand-holding-dollar" },
          { id: "cuentas-pagar", label: "Cuentas por Pagar", href: "/finanzas/cuentas-pagar", icon: "fa-credit-card" },
          { id: "bancos", label: "Bancos y Cajas", href: "/finanzas/bancos", icon: "fa-building-columns" },
          { id: "ingresos-egresos", label: "Ingresos y Egresos", href: "/finanzas/movimientos", icon: "fa-arrow-right-arrow-left" },
          { id: "reportes-financieros", label: "Reportes Financieros", href: "/finanzas/reportes", icon: "fa-chart-line" },
        ]
      },
      {
        id: "ventas-module",
        label: "Ventas",
        icon: "fa-cart-shopping",
        subItems: [
          { id: "ventas-lista", label: "Lista de Ventas", href: "/ventas", icon: "fa-list" },
          { id: "cotizaciones", label: "Cotizaciones", href: "/ventas/cotizaciones", icon: "fa-file-invoice" },
          { id: "clientes", label: "Clientes", href: "/ventas/clientes", icon: "fa-user-tie" },
          { id: "reportes-ventas", label: "Reportes de Ventas", href: "/ventas/reportes", icon: "fa-chart-bar" },
          { id: "pagos", label: "Pagos", href: "/ventas/pagos", icon: "fa-pay" },
        ]
      },
      {
        id: "compras-module",
        label: "Compras",
        icon: "fa-truck-ramp-box",
        subItems: [
          { id: "compras-lista", label: "Órdenes de Compra", href: "/compras", icon: "fa-file-lines" },
          { id: "nueva-compra", label: "Nueva Compra", href: "/compras/nueva", icon: "fa-cart-plus" },
          { id: "proveedores", label: "Proveedores", href: "/compras/proveedores", icon: "fa-truck" },
          { id: "solicitudes", label: "Solicitudes de Compra", href: "/compras/solicitudes", icon: "fa-clipboard-question" },
          { id: "recepciones", label: "Recepciones", href: "/compras/recepciones", icon: "fa-box-open" },
        ]
      },
      {
        id: "rrhh-module",
        label: "RRHH",
        icon: "fa-users-gear",
        subItems: [
          { id: "empleados", label: "Empleados", href: "/rrhh/empleados", icon: "fa-id-card" },
          { id: "nomina", label: "Nómina", href: "/rrhh/nomina", icon: "fa-money-bill-wave" },
          { id: "asistencia", label: "Asistencia", href: "/rrhh/asistencia", icon: "fa-calendar-check" },
          { id: "vacaciones", label: "Vacaciones y Permisos", href: "/rrhh/vacaciones", icon: "fa-umbrella-beach" },
          { id: "evaluaciones", label: "Evaluaciones", href: "/rrhh/evaluaciones", icon: "fa-star" },
        ]
      },
    ],
  },
]

// ============================================================================
// COMPONENT
// ============================================================================

export function Sidebar() {
  const { theme, toggleTheme } = useTheme()
  const pathname = usePathname()
  const [isOpen, setIsOpen] = useState(false)
  const [expandedItems, setExpandedItems] = useState<Record<string, boolean>>({})

  // Auto-expandir el dropdown correcto basado en la ruta actual
  useEffect(() => {
    const newExpandedState: Record<string, boolean> = {}

    menuItems.forEach((group) => {
      group.items.forEach((item) => {
        if (item.subItems) {
          // Verificar si algún subitem coincide con la ruta actual
          const hasActiveChild = item.subItems.some((sub) =>
            isRouteActive(sub.href)
          )
          newExpandedState[item.id] = hasActiveChild
        }
      })
    })

    setExpandedItems(newExpandedState)
  }, [pathname])

  // ============================================================================
  // HELPER FUNCTIONS
  // ============================================================================

  /**
   * Determina si una ruta está activa
   * Maneja casos especiales como dashboard y rutas anidadas
   */
  const isRouteActive = (href: string): boolean => {
    // Dashboard es un caso especial - solo activo en coincidencia exacta
    if (href === "/dashboard") {
      return pathname === "/dashboard"
    }

    // Coincidencia exacta
    if (pathname === href) {
      return true
    }

    // Verificar si es una subruta (termina con / después del href)
    return pathname.startsWith(href + "/")
  }

  /**
   * Determina si algún hijo del módulo está activo
   */
  const hasActiveChild = (item: MenuItem): boolean => {
    if (!item.subItems) return false
    return item.subItems.some((sub) => isRouteActive(sub.href))
  }

  /**
   * Determina si un subitem específico debe marcarse como activo
   * Evita que múltiples items se marquen cuando uno es prefijo del otro
   */
  const isSubItemActive = (subItem: SubItem, allSubItems: SubItem[]): boolean => {
    // Primero verificar si hay una ruta más específica que coincida
    const moreSpecificMatch = allSubItems.find((other) =>
      other.href !== subItem.href &&
      other.href.startsWith(subItem.href) &&
      isRouteActive(other.href)
    )

    // Si hay una ruta más específica activa, este item NO debe marcarse
    if (moreSpecificMatch) {
      return false
    }

    // De lo contrario, verificar si esta ruta está activa
    return isRouteActive(subItem.href)
  }

  /**
   * Toggle de un dropdown
   * Cierra otros dropdowns cuando se abre uno nuevo
   */
  const toggleDropdown = (itemId: string) => {
    setExpandedItems((prev) => {
      const isCurrentlyExpanded = prev[itemId]

      // Si se está abriendo (estaba cerrado), cerrar todos los demás primero
      if (!isCurrentlyExpanded) {
        const newState: Record<string, boolean> = {}
        Object.keys(prev).forEach((key) => {
          newState[key] = false
        })
        newState[itemId] = true
        return newState
      }

      // Si se está cerrando, solo cerrar este
      return {
        ...prev,
        [itemId]: false
      }
    })
  }

  /**
   * Cierra el sidebar mobile
   */
  const closeSidebar = () => {
    setIsOpen(false)
  }

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="lg:hidden fixed bottom-6 right-6 z-50 w-14 h-14 bg-primary text-primary-foreground rounded-full flex items-center justify-center shadow-lg hover:scale-110 transition-transform"
        aria-label={isOpen ? "Cerrar menú" : "Abrir menú"}
      >
        <i className={`fa-solid ${isOpen ? "fa-times" : "fa-bars"} text-lg`}></i>
      </button>

      {/* Overlay */}
      {isOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={closeSidebar}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-40
          w-64 bg-card border-r border-border h-screen flex flex-col
          transition-transform duration-300 ease-in-out
          ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
      >
        {/* Logo */}
        <div className="p-6 border-b border-border">
          <Link
            href="/dashboard"
            className="flex items-center gap-3 group"
            onClick={closeSidebar}
          >
            <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center group-hover:scale-105 transition-transform">
              <span className="text-lg font-bold text-primary-foreground">K</span>
            </div>
            <div>
              <h1 className="font-bold text-foreground">Klyra</h1>
              <p className="text-xs text-muted-foreground">Sistema ERP</p>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 overflow-y-auto">
          {menuItems.map((group) => (
            <div key={group.category} className="mb-6">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3 px-3">
                {group.category}
              </h3>
              <ul className="space-y-1">
                {group.items.map((item) => (
                  <li key={item.id}>
                    {item.subItems ? (
                      // Item con submódulos (dropdown)
                      <div>
                        <button
                          onClick={() => toggleDropdown(item.id)}
                          className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                            hasActiveChild(item)
                              ? "text-primary"
                              : "text-muted-foreground hover:text-foreground hover:bg-muted"
                          }`}
                          aria-expanded={expandedItems[item.id]}
                        >
                          <span className="flex items-center gap-3">
                            <i className={`fa-solid ${item.icon} w-5 text-center`}></i>
                            {item.label}
                          </span>
                          <i className={`fa-solid fa-chevron-down text-xs transition-transform duration-300 ${
                            expandedItems[item.id] ? "rotate-180" : ""
                          }`}></i>
                        </button>

                        {/* Submódulos con animación */}
                        <div
                          className={`grid transition-all duration-300 ease-in-out ${
                            expandedItems[item.id] 
                              ? "grid-rows-[1fr] opacity-100 mt-1" 
                              : "grid-rows-[0fr] opacity-0"
                          }`}
                        >
                          <div className="overflow-hidden">
                            <ul className="ml-8 space-y-1 pb-1">
                              {item.subItems.map((subItem) => {
                                const isActive = isSubItemActive(subItem, item.subItems!)

                                return (
                                  <li key={subItem.id}>
                                    <Link
                                      href={subItem.href}
                                      onClick={closeSidebar}
                                      className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all duration-200 ${
                                        isActive
                                          ? "bg-primary text-primary-foreground font-medium shadow-sm"
                                          : "text-muted-foreground hover:text-foreground hover:bg-muted hover:translate-x-1"
                                      }`}
                                    >
                                      <i className={`fa-solid ${subItem.icon} w-4 text-center text-xs`}></i>
                                      {subItem.label}
                                    </Link>
                                  </li>
                                )
                              })}
                            </ul>
                          </div>
                        </div>
                      </div>
                    ) : (
                      // Item sin submódulos (link directo)
                      <Link
                        href={item.href!}
                        onClick={closeSidebar}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                          isRouteActive(item.href!)
                            ? "bg-primary text-primary-foreground shadow-sm"
                            : "text-muted-foreground hover:text-foreground hover:bg-muted hover:translate-x-1"
                        }`}
                      >
                        <i className={`fa-solid ${item.icon} w-5 text-center`}></i>
                        {item.label}
                      </Link>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>

        {/* Theme Toggle & Footer */}
        <div className="p-4 border-t border-border">
          <button
            onClick={toggleTheme}
            className="w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-all duration-200"
            aria-label={`Cambiar a modo ${theme === "dark" ? "claro" : "oscuro"}`}
          >
            <span className="flex items-center gap-3">
              <i className={`fa-solid ${theme === "dark" ? "fa-moon" : "fa-sun"} w-5 text-center`}></i>
              {theme === "dark" ? "Modo Oscuro" : "Modo Claro"}
            </span>
            <div
              className={`w-10 h-5 rounded-full p-0.5 transition-colors duration-300 ${
                theme === "dark" ? "bg-primary" : "bg-muted"
              }`}
            >
              <div
                className={`w-4 h-4 rounded-full bg-white transition-transform duration-300 ${
                  theme === "dark" ? "translate-x-5" : "translate-x-0"
                }`}
              />
            </div>
          </button>
        </div>
      </aside>
    </>
  )
}