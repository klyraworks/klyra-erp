"use client"

import {useState} from "react"
import {Header} from "@/src/shared/components/header"

export default function PerfilPage() {
    const [activeTab, setActiveTab] = useState<"general" | "seguridad" | "notificaciones">("general")

    // Mock user data - esto se conectará a la API
    const [userData, setUserData] = useState({
        nombre: "Admin",
        apellido: "Usuario",
        email: "admin@klyra.ec",
        telefono: "+593 99 123 4567",
        cargo: "Administrador",
        departamento: "Sistemas",
        fechaIngreso: "2024-01-15",
        avatar: "",
    })

    const [passwords, setPasswords] = useState({
        actual: "",
        nueva: "",
        confirmar: "",
    })

    const [notificaciones, setNotificaciones] = useState({
        emailVentas: true,
        emailInventario: true,
        emailPagos: false,
        pushVentas: true,
        pushInventario: false,
        pushPagos: true,
    })

    const tabs = [
        {id: "general", label: "Información General", icon: "fa-user"},
        {id: "seguridad", label: "Seguridad", icon: "fa-shield-halved"},
        {id: "notificaciones", label: "Notificaciones", icon: "fa-bell"},
    ]

    return (
        <>
            <Header title="Mi Perfil" breadcrumb={["Klyra", "Perfil"]}/>
            <main className="flex-1 overflow-y-auto p-6">
                <div className="max-w-4xl mx-auto">
                    {/* Profile Header */}
                    <div className="bg-card rounded-xl border border-border p-6 mb-6">
                        <div className="flex items-start gap-6">
                            {/* Avatar */}
                            <div className="relative">
                                <div
                                    className="w-24 h-24 rounded-2xl bg-primary flex items-center justify-center text-primary-foreground text-3xl font-bold">
                                    {userData.nombre.charAt(0)}
                                    {userData.apellido.charAt(0)}
                                </div>
                                <button
                                    className="absolute -bottom-2 -right-2 w-8 h-8 bg-card border border-border rounded-lg flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">
                                    <i className="fa-solid fa-camera text-sm"></i>
                                </button>
                            </div>

                            {/* Info */}
                            <div className="flex-1">
                                <h2 className="text-xl font-bold text-foreground">
                                    {userData.nombre} {userData.apellido}
                                </h2>
                                <p className="text-muted-foreground">
                                    {userData.cargo} - {userData.departamento}
                                </p>
                                <div className="flex items-center gap-4 mt-3 text-sm text-muted-foreground">
                  <span className="flex items-center gap-2">
                    <i className="fa-solid fa-envelope"></i>
                      {userData.email}
                  </span>
                                    <span className="flex items-center gap-2">
                    <i className="fa-solid fa-phone"></i>
                                        {userData.telefono}
                  </span>
                                </div>
                            </div>

                            {/* Status Badge */}
                            <div
                                className="flex items-center gap-2 px-3 py-1.5 bg-green-500/10 text-green-600 rounded-lg text-sm font-medium">
                                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                                Activo
                            </div>
                        </div>
                    </div>

                    {/* Tabs */}
                    <div className="bg-card rounded-xl border border-border overflow-hidden">
                        {/* Tab Headers */}
                        <div className="flex border-b border-border">
                            {tabs.map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id as typeof activeTab)}
                                    className={`flex items-center gap-2 px-6 py-4 text-sm font-medium transition-colors relative ${
                                        activeTab === tab.id ? "text-primary" : "text-muted-foreground hover:text-foreground"
                                    }`}
                                >
                                    <i className={`fa-solid ${tab.icon}`}></i>
                                    {tab.label}
                                    {activeTab === tab.id &&
                                        <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary"></span>}
                                </button>
                            ))}
                        </div>

                        {/* Tab Content */}
                        <div className="p-6">
                            {/* General Tab */}
                            {activeTab === "general" && (
                                <div className="space-y-6">
                                    <div className="grid grid-cols-2 gap-6">
                                        <div>
                                            <label className="block text-sm font-medium text-foreground mb-2">
                                                <i className="fa-solid fa-user mr-2 text-muted-foreground"></i>
                                                Nombre
                                            </label>
                                            <input
                                                type="text"
                                                value={userData.nombre}
                                                onChange={(e) => setUserData({...userData, nombre: e.target.value})}
                                                className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-foreground mb-2">
                                                <i className="fa-solid fa-user mr-2 text-muted-foreground"></i>
                                                Apellido
                                            </label>
                                            <input
                                                type="text"
                                                value={userData.apellido}
                                                onChange={(e) => setUserData({...userData, apellido: e.target.value})}
                                                className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-foreground mb-2">
                                                <i className="fa-solid fa-envelope mr-2 text-muted-foreground"></i>
                                                Correo Electrónico
                                            </label>
                                            <input
                                                type="email"
                                                value={userData.email}
                                                onChange={(e) => setUserData({...userData, email: e.target.value})}
                                                className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-foreground mb-2">
                                                <i className="fa-solid fa-phone mr-2 text-muted-foreground"></i>
                                                Teléfono
                                            </label>
                                            <input
                                                type="tel"
                                                value={userData.telefono}
                                                onChange={(e) => setUserData({...userData, telefono: e.target.value})}
                                                className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-foreground mb-2">
                                                <i className="fa-solid fa-briefcase mr-2 text-muted-foreground"></i>
                                                Cargo
                                            </label>
                                            <input
                                                type="text"
                                                value={userData.cargo}
                                                disabled
                                                className="w-full px-4 py-3 bg-muted/50 border border-border rounded-xl text-sm text-muted-foreground cursor-not-allowed"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-foreground mb-2">
                                                <i className="fa-solid fa-building mr-2 text-muted-foreground"></i>
                                                Departamento
                                            </label>
                                            <input
                                                type="text"
                                                value={userData.departamento}
                                                disabled
                                                className="w-full px-4 py-3 bg-muted/50 border border-border rounded-xl text-sm text-muted-foreground cursor-not-allowed"
                                            />
                                        </div>
                                    </div>

                                    <div className="flex justify-end gap-3 pt-4 border-t border-border">
                                        <button
                                            className="px-4 py-2.5 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
                                            Cancelar
                                        </button>
                                        <button
                                            className="px-6 py-2.5 bg-primary text-primary-foreground rounded-xl text-sm font-medium hover:bg-primary/90 transition-colors flex items-center gap-2">
                                            <i className="fa-solid fa-check"></i>
                                            Guardar Cambios
                                        </button>
                                    </div>
                                </div>
                            )}

                            {/* Security Tab */}
                            {activeTab === "seguridad" && (
                                <div className="space-y-6">
                                    <div
                                        className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-start gap-3">
                                        <i className="fa-solid fa-triangle-exclamation text-amber-500 mt-0.5"></i>
                                        <div>
                                            <p className="text-sm font-medium text-foreground">Seguridad de la
                                                cuenta</p>
                                            <p className="text-sm text-muted-foreground">
                                                Te recomendamos cambiar tu contraseña periódicamente para mantener tu
                                                cuenta segura.
                                            </p>
                                        </div>
                                    </div>

                                    <div className="space-y-4">
                                        <h3 className="font-semibold text-foreground flex items-center gap-2">
                                            <i className="fa-solid fa-key text-muted-foreground"></i>
                                            Cambiar Contraseña
                                        </h3>

                                        <div>
                                            <label className="block text-sm font-medium text-foreground mb-2">Contraseña
                                                Actual</label>
                                            <input
                                                type="password"
                                                value={passwords.actual}
                                                onChange={(e) => setPasswords({...passwords, actual: e.target.value})}
                                                placeholder="Ingresa tu contraseña actual"
                                                className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                                            />
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <label className="block text-sm font-medium text-foreground mb-2">Nueva
                                                    Contraseña</label>
                                                <input
                                                    type="password"
                                                    value={passwords.nueva}
                                                    onChange={(e) => setPasswords({
                                                        ...passwords,
                                                        nueva: e.target.value
                                                    })}
                                                    placeholder="Mínimo 8 caracteres"
                                                    className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-foreground mb-2">Confirmar
                                                    Contraseña</label>
                                                <input
                                                    type="password"
                                                    value={passwords.confirmar}
                                                    onChange={(e) => setPasswords({
                                                        ...passwords,
                                                        confirmar: e.target.value
                                                    })}
                                                    placeholder="Repite la nueva contraseña"
                                                    className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    {/* Session Info */}
                                    <div className="space-y-4 pt-4 border-t border-border">
                                        <h3 className="font-semibold text-foreground flex items-center gap-2">
                                            <i className="fa-solid fa-clock-rotate-left text-muted-foreground"></i>
                                            Sesiones Activas
                                        </h3>

                                        <div className="space-y-3">
                                            <div className="flex items-center justify-between p-4 bg-muted rounded-xl">
                                                <div className="flex items-center gap-3">
                                                    <div
                                                        className="w-10 h-10 bg-green-500/10 text-green-600 rounded-lg flex items-center justify-center">
                                                        <i className="fa-solid fa-desktop"></i>
                                                    </div>
                                                    <div>
                                                        <p className="text-sm font-medium text-foreground">Este
                                                            dispositivo</p>
                                                        <p className="text-xs text-muted-foreground">Chrome en Windows -
                                                            Activo ahora</p>
                                                    </div>
                                                </div>
                                                <span
                                                    className="px-2 py-1 bg-green-500/10 text-green-600 text-xs font-medium rounded-lg">
                          Actual
                        </span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex justify-end gap-3 pt-4 border-t border-border">
                                        <button
                                            className="px-4 py-2.5 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
                                            Cancelar
                                        </button>
                                        <button
                                            className="px-6 py-2.5 bg-primary text-primary-foreground rounded-xl text-sm font-medium hover:bg-primary/90 transition-colors flex items-center gap-2">
                                            <i className="fa-solid fa-lock"></i>
                                            Actualizar Contraseña
                                        </button>
                                    </div>
                                </div>
                            )}

                            {/* Notifications Tab */}
                            {activeTab === "notificaciones" && (
                                <div className="space-y-6">
                                    {/* Email Notifications */}
                                    <div className="space-y-4">
                                        <h3 className="font-semibold text-foreground flex items-center gap-2">
                                            <i className="fa-solid fa-envelope text-muted-foreground"></i>
                                            Notificaciones por Correo
                                        </h3>

                                        <div className="space-y-3">
                                            {[
                                                {
                                                    key: "emailVentas",
                                                    label: "Nuevas ventas",
                                                    desc: "Recibe un correo cuando se registre una nueva venta",
                                                },
                                                {
                                                    key: "emailInventario",
                                                    label: "Alertas de inventario",
                                                    desc: "Notificaciones cuando el stock esté bajo",
                                                },
                                                {
                                                    key: "emailPagos",
                                                    label: "Pagos recibidos",
                                                    desc: "Confirmación de pagos registrados"
                                                },
                                            ].map((item) => (
                                                <div key={item.key}
                                                     className="flex items-center justify-between p-4 bg-muted rounded-xl">
                                                    <div>
                                                        <p className="text-sm font-medium text-foreground">{item.label}</p>
                                                        <p className="text-xs text-muted-foreground">{item.desc}</p>
                                                    </div>
                                                    <button
                                                        onClick={() =>
                                                            setNotificaciones({
                                                                ...notificaciones,
                                                                [item.key]: !notificaciones[item.key as keyof typeof notificaciones],
                                                            })
                                                        }
                                                        className={`w-12 h-6 rounded-full p-0.5 transition-colors ${
                                                            notificaciones[item.key as keyof typeof notificaciones] ? "bg-primary" : "bg-border"
                                                        }`}
                                                    >
                                                        <div
                                                            className={`w-5 h-5 rounded-full bg-white transition-transform ${
                                                                notificaciones[item.key as keyof typeof notificaciones]
                                                                    ? "translate-x-6"
                                                                    : "translate-x-0"
                                                            }`}
                                                        />
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Push Notifications */}
                                    <div className="space-y-4 pt-4 border-t border-border">
                                        <h3 className="font-semibold text-foreground flex items-center gap-2">
                                            <i className="fa-solid fa-bell text-muted-foreground"></i>
                                            Notificaciones Push
                                        </h3>

                                        <div className="space-y-3">
                                            {[
                                                {
                                                    key: "pushVentas",
                                                    label: "Nuevas ventas",
                                                    desc: "Alertas instantáneas de ventas"
                                                },
                                                {
                                                    key: "pushInventario",
                                                    label: "Alertas de inventario",
                                                    desc: "Notificaciones de stock crítico",
                                                },
                                                {
                                                    key: "pushPagos",
                                                    label: "Pagos recibidos",
                                                    desc: "Alertas de pagos entrantes"
                                                },
                                            ].map((item) => (
                                                <div key={item.key}
                                                     className="flex items-center justify-between p-4 bg-muted rounded-xl">
                                                    <div>
                                                        <p className="text-sm font-medium text-foreground">{item.label}</p>
                                                        <p className="text-xs text-muted-foreground">{item.desc}</p>
                                                    </div>
                                                    <button
                                                        onClick={() =>
                                                            setNotificaciones({
                                                                ...notificaciones,
                                                                [item.key]: !notificaciones[item.key as keyof typeof notificaciones],
                                                            })
                                                        }
                                                        className={`w-12 h-6 rounded-full p-0.5 transition-colors ${
                                                            notificaciones[item.key as keyof typeof notificaciones] ? "bg-primary" : "bg-border"
                                                        }`}
                                                    >
                                                        <div
                                                            className={`w-5 h-5 rounded-full bg-white transition-transform ${
                                                                notificaciones[item.key as keyof typeof notificaciones]
                                                                    ? "translate-x-6"
                                                                    : "translate-x-0"
                                                            }`}
                                                        />
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="flex justify-end gap-3 pt-4 border-t border-border">
                                        <button
                                            className="px-6 py-2.5 bg-primary text-primary-foreground rounded-xl text-sm font-medium hover:bg-primary/90 transition-colors flex items-center gap-2">
                                            <i className="fa-solid fa-check"></i>
                                            Guardar Preferencias
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </>
    )
}
