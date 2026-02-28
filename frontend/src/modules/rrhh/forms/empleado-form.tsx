// frontend/src/modules/rrhh/forms/empleado-form.tsx

"use client"

import {useState, useEffect} from "react"
import {useRouter} from "next/navigation"
import {mutate} from "swr"
import {alertas} from "@/components/alerts/alertas-toast"
import {apiFetch, ApiError} from "@/src/core/api/client"
import {Empleado, RolBasico, Departamento, BuscarResponse, Puesto, Ciudad} from "@/src/core/api/types"
import {Select} from "@/components/select/select-klyra"
import {CheckboxKlyra} from "@/components/ui/checkbox-klyra"
import React from "react"

interface EmpleadoFormProps {
    mode: "create" | "edit"
    empleado?: Empleado | null
    formRef?: React.RefObject<HTMLFormElement>
}

export function EmpleadoForm({mode, empleado, formRef}: EmpleadoFormProps) {
    const router = useRouter()
    const isEditMode = mode === "edit"

    const [loading, setLoading] = useState(false)

    const [persona, setPersona] = useState({
        nombre1: "",
        nombre2: "",
        apellido1: "",
        apellido2: "",
        cedula: "",
        pasaporte: "",
        email: "",
        telefono: "",
        ciudad_id: null as number | null,
        fecha_nacimiento: "",
    })

    const [laboral, setLaboral] = useState({
        salario: "",
        fecha_contratacion: "",
        estado: "activo",
        puesto_id: null as string | null,
        rol_id: null as string | null,
        departamento_id: null as string | null,
    })

    const [crearAcceso, setCrearAcceso] = useState(true)

    // Roles
    const [roles, setRoles] = useState<RolBasico[]>([])
    const [rolInicial, setRolInicial] = useState<RolBasico | null>(null)
    const [loadingRoles, setLoadingRoles] = useState(false)

    // Departamentos
    const [departamentos, setDepartamentos] = useState<Departamento[]>([])
    const [departamentoInicial, setDepartamentoInicial] = useState<Departamento | null>(null)
    const [loadingDepartamentos, setLoadingDepartamentos] = useState(false)

    // Puestos
    const [puestos, setPuestos] = useState<Puesto[]>([])
    const [puestoInicial, setPuestoInicial] = useState<Puesto | null>(null)
    const [loadingPuestos, setLoadingPuestos] = useState(false)

    // Ciudades
    const [ciudades, setCiudades] = useState<Ciudad[]>([])
    const [ciudadInicial, setCiudadInicial] = useState<Ciudad | null>(null)
    const [loadingCiudades, setLoadingCiudades] = useState(false)

    useEffect(() => {
        if (isEditMode && empleado) {
            setPersona({
                nombre1: empleado.persona.nombre1 ?? "",
                nombre2: empleado.persona.nombre2 ?? "",
                apellido1: empleado.persona.apellido1 ?? "",
                apellido2: empleado.persona.apellido2 ?? "",
                cedula: empleado.persona.cedula ?? "",
                pasaporte: empleado.persona.pasaporte ?? "",
                email: empleado.persona.email ?? "",
                telefono: empleado.persona.telefono ?? "",
                ciudad_id: empleado.persona.ciudad?.id ?? null,
                fecha_nacimiento: empleado.persona.fecha_nacimiento ?? "",
            })
            setLaboral({
                puesto_id: empleado.puesto?.id ?? null,
                salario: empleado.salario ? String(empleado.salario) : "",
                fecha_contratacion: empleado.fecha_contratacion ?? "",
                estado: empleado.estado ?? "activo",
                rol_id: empleado.rol?.id ?? null,
                departamento_id: empleado.departamento?.id ?? null,
            })
        }
    }, [isEditMode, empleado])

    // Cargar rol inicial en modo edición
    useEffect(() => {
        async function loadRolInicial() {
            if (!isEditMode || !empleado?.rol?.id) return
            try {
                const data = await apiFetch<BuscarResponse<RolBasico>>(
                    `/api/seguridad/roles/${encodeURIComponent(empleado.rol.id)}/`
                )
                console.log("Rol inicial:", data)
                const rol = data ?? null
                setRolInicial(rol)
                setRoles(rol ? [rol] : [])
            } catch (err) {
                console.warn("Error cargando rol inicial:", err)
            }
        }

        loadRolInicial()
    }, [isEditMode, empleado])
    useEffect(() => {
    }, [empleado])

    // Cargar departamento inicial en modo edición
    useEffect(() => {
        async function loadDepartamentoInicial() {
            if (!isEditMode || !empleado?.departamento?.id) return
            try {
                const data = await apiFetch<BuscarResponse<Departamento>>(
                    `/api/rrhh/departamentos/${encodeURIComponent(empleado.departamento.id)}/`
                )
                const dep = data ?? null
                setDepartamentoInicial(dep)
                setDepartamentos(dep ? [dep] : [])
            } catch (err) {
                console.warn("Error cargando departamento inicial:", err)
            }
        }

        loadDepartamentoInicial()
    }, [isEditMode, empleado])
    console.log("Empleado:", empleado)

    // Cargar puesto inicial en modo edición
    useEffect(() => {
        async function loadPuestoInicial() {
            if (!isEditMode || !empleado?.puesto) return
            try {
                const query = empleado.puesto?.id
                const data = await apiFetch<BuscarResponse<Puesto>>(
                    `/api/rrhh/puestos/${encodeURIComponent(query)}/`
                )
                const pue = data ?? null
                setPuestoInicial(pue)
                setPuestos(pue ? [pue] : [])
            } catch (err) {
                console.warn("Error cargando puesto inicial:", err)
            }
        }

        loadPuestoInicial()
    }, [isEditMode, empleado])

    // Cargar ciudad inicial en modo edición
    useEffect(() => {
        async function loadCiudadInicial() {
            console.log("Ciudad empleado:", empleado?.persona.ciudad?.id)
            if (!isEditMode || !empleado?.persona.ciudad) return
            try {
                const data = await apiFetch<BuscarResponse<Ciudad>>(
                    `/api/core/ciudades/${encodeURIComponent(empleado.persona.ciudad?.id)}/`
                )
                console.log("Ciudad inicial:", data)
                const ciu = data ?? null
                setCiudadInicial(ciu)
                setCiudades(ciu ? [ciu] : [])
            } catch (err) {
                console.warn("Error cargando ciudad inicial:", err)
            }
        }

        loadCiudadInicial()
    }, [isEditMode, empleado])

    const buscarRoles = async (query: string) => {
        if (query.trim() === "") {
            setRoles(rolInicial ? [rolInicial] : [])
            return
        }
        setLoadingRoles(true)
        try {
            const data = await apiFetch<BuscarResponse<RolBasico>>(
                `/api/seguridad/roles/buscar/?q=${encodeURIComponent(query)}`
            )
            setRoles(data.results)
        } catch (err) {
            if (err instanceof ApiError) alertas.error(err.mensaje, err.titulo)
            else alertas.error("Error al buscar roles", "Error")
        } finally {
            setLoadingRoles(false)
        }
    }

    const buscarDepartamentos = async (query: string) => {
        if (query.trim() === "") {
            setDepartamentos(departamentoInicial ? [departamentoInicial] : [])
            return
        }
        setLoadingDepartamentos(true)
        try {
            const data = await apiFetch<BuscarResponse<Departamento>>(
                `/api/rrhh/departamentos/buscar/?q=${encodeURIComponent(query)}`
            )
            setDepartamentos(data.results)
        } catch (err) {
            if (err instanceof ApiError) alertas.error(err.mensaje, err.titulo)
            else alertas.error("Error al buscar departamentos", "Error")
        } finally {
            setLoadingDepartamentos(false)
        }
    }

    const buscarPuestos = async (query: string) => {
        if (query.trim() === "") {
            setPuestos(puestoInicial ? [puestoInicial] : [])
            return
        }
        setLoadingPuestos(true)
        try {
            const data = await apiFetch<BuscarResponse<Puesto>>(
                `/api/rrhh/puestos/buscar/?q=${encodeURIComponent(query)}`
            )
            setPuestos(data.results)
        } catch (err) {
            if (err instanceof ApiError) alertas.error(err.mensaje, err.titulo)
            else alertas.error("Error al buscar puestos", "Error")
        } finally {
            setLoadingPuestos(false)
        }
    }

    const buscarCiudades = async (query: string) => {
        if (query.trim() === "") {
            setCiudades(ciudadInicial ? [ciudadInicial] : [])
            return
        }
        setLoadingCiudades(true)
        try {
            const data = await apiFetch<BuscarResponse<Ciudad>>(
                `/api/core/ciudades/?search=${encodeURIComponent(query)}`
            )
            setCiudades(data.results)
        } catch (err) {
            if (err instanceof ApiError) alertas.error(err.mensaje, err.titulo)
            else alertas.error("Error al buscar ciudades", "Error")
        } finally {
            setLoadingCiudades(false)
        }
    }

    const handlePersonaChange = (field: string, value: string | number | null) => {
        setPersona(prev => ({...prev, [field]: value}))
    }

    const handleLaboralChange = (field: string, value: unknown) => {
        setLaboral(prev => ({...prev, [field]: value}))
    }

    const validarFormulario = (): boolean => {
        if (!persona.nombre1.trim()) {
            alertas.warning("El primer nombre es requerido", "Campo requerido")
            return false
        }
        if (!persona.apellido1.trim()) {
            alertas.warning("El primer apellido es requerido", "Campo requerido")
            return false
        }
        if (!persona.cedula.trim() && !persona.pasaporte.trim()) {
            alertas.warning("Se requiere cédula o pasaporte", "Campo requerido")
            return false
        }
        if (!persona.email.trim()) {
            alertas.warning("El email es requerido", "Campo requerido")
            return false
        }
        if (!laboral.salario || parseFloat(laboral.salario) <= 0) {
            alertas.warning("El salario debe ser mayor a cero", "Campo requerido")
            return false
        }
        if (!laboral.fecha_contratacion) {
            alertas.warning("La fecha de contratación es requerida", "Campo requerido")
            return false
        }
        return true
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        e.stopPropagation()
        if (loading) return
        if (!validarFormulario()) return
        setLoading(true)
        try {
            const payload: Record<string, unknown> = isEditMode
                ? {
                    persona: {
                        nombre1: persona.nombre1.trim(),
                        nombre2: persona.nombre2.trim() || null,
                        apellido1: persona.apellido1.trim(),
                        apellido2: persona.apellido2.trim() || null,
                        cedula: persona.cedula.trim() || null,
                        pasaporte: persona.pasaporte.trim() || null,
                        email: persona.email.trim(),
                        telefono: persona.telefono.trim() || null,
                        ciudad_id: persona.ciudad_id,
                        fecha_nacimiento: persona.fecha_nacimiento || null,
                    },
                    puesto_id: laboral.puesto_id,
                    salario: parseFloat(laboral.salario),
                    fecha_contratacion: laboral.fecha_contratacion,
                    estado: laboral.estado,
                    rol_id: laboral.rol_id,
                    departamento_id: laboral.departamento_id,
                }
                : {
                    persona: {
                        nombre1: persona.nombre1.trim(),
                        nombre2: persona.nombre2.trim() || null,
                        apellido1: persona.apellido1.trim(),
                        apellido2: persona.apellido2.trim() || null,
                        cedula: persona.cedula.trim() || null,
                        pasaporte: persona.pasaporte.trim() || null,
                        email: persona.email.trim(),
                        telefono: persona.telefono.trim() || null,
                        ciudad_id: persona.ciudad_id,
                        fecha_nacimiento: persona.fecha_nacimiento || null,
                    },
                    puesto_id: laboral.puesto_id,
                    salario: parseFloat(laboral.salario),
                    fecha_contratacion: laboral.fecha_contratacion,
                    estado: laboral.estado,
                    rol_id: laboral.rol_id,
                    departamento_id: laboral.departamento_id,
                    crear_acceso: crearAcceso,
                }

            console.log("Payload:", payload)

            await apiFetch(
                isEditMode ? `/api/seguridad/empleados/${empleado?.id}/` : `/api/seguridad/empleados/`,
                {method: isEditMode ? "PATCH" : "POST", body: JSON.stringify(payload)}
            )
            alertas.success(
                isEditMode ? "Empleado actualizado exitosamente" : "Empleado creado exitosamente",
                isEditMode ? "Empleado Actualizado" : "Empleado Creado"
            )
            await mutate(["/api/seguridad/empleados/"])
            setTimeout(() => router.push("/rrhh/empleados"), 1500)
        } catch (err) {
            if (err instanceof ApiError) alertas.error(err.mensaje, err.titulo)
            else alertas.error("Error desconocido al guardar", isEditMode ? "Error al Actualizar" : "Error al Crear")
        } finally {
            setLoading(false)
        }
    }

    return (
        <form ref={formRef} onSubmit={handleSubmit}
              className={`grid grid-cols-1 gap-6 ${!isEditMode ? "lg:grid-cols-3" : ""}`}>
            {/* Columna principal */}
            <div className="lg:col-span-2 space-y-6">

                {/* Datos Personales */}
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-id-card text-primary text-lg"></i>
                        </div>
                        <h2 className="text-sm font-semibold text-foreground">Datos Personales</h2>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Primer nombre <span className="text-destructive">*</span>
                            </label>
                            <input
                                type="text"
                                value={persona.nombre1}
                                onChange={(e) => handlePersonaChange("nombre1", e.target.value)}
                                placeholder="Ej: Carlos"
                                className="px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                            />
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Segundo nombre
                            </label>
                            <input
                                type="text"
                                value={persona.nombre2}
                                onChange={(e) => handlePersonaChange("nombre2", e.target.value)}
                                placeholder="Ej: Andrés"
                                className="px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                            />
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Primer apellido <span className="text-destructive">*</span>
                            </label>
                            <input
                                type="text"
                                value={persona.apellido1}
                                onChange={(e) => handlePersonaChange("apellido1", e.target.value)}
                                placeholder="Ej: Mendoza"
                                className="px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                            />
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Segundo apellido
                            </label>
                            <input
                                type="text"
                                value={persona.apellido2}
                                onChange={(e) => handlePersonaChange("apellido2", e.target.value)}
                                placeholder="Ej: Pérez"
                                className="px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                            />
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Cédula
                            </label>
                            <input
                                type="text"
                                value={persona.cedula}
                                onChange={(e) => handlePersonaChange("cedula", e.target.value)}
                                placeholder="1234567890"
                                maxLength={10}
                                className="px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                            />
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Pasaporte
                            </label>
                            <input
                                type="text"
                                value={persona.pasaporte}
                                onChange={(e) => handlePersonaChange("pasaporte", e.target.value)}
                                placeholder="Ej: AB123456"
                                className="px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                            />
                        </div>

                        <div className="flex flex-col gap-1.5 sm:col-span-2">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Email <span className="text-destructive">*</span>
                            </label>
                            <input
                                type="email"
                                value={persona.email}
                                onChange={(e) => handlePersonaChange("email", e.target.value)}
                                placeholder="correo@empresa.com"
                                className="px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                            />
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Teléfono
                            </label>
                            <input
                                type="text"
                                value={persona.telefono}
                                onChange={(e) => handlePersonaChange("telefono", e.target.value)}
                                placeholder="0991234567"
                                className="px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                            />
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Fecha de nacimiento
                            </label>
                            <input
                                type="date"
                                value={persona.fecha_nacimiento}
                                onChange={(e) => handlePersonaChange("fecha_nacimiento", e.target.value)}
                                className="px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                            />
                        </div>

                        <div className="flex flex-col gap-1.5 sm:col-span-2">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Ciudad
                            </label>
                            <Select
                                options={(ciudades ?? []).map(c => ({
                                    value: c.id,
                                    label: c.name,
                                    description: `${c.region?.name}, ${c.pais?.name}`,
                                    icon: "fas fa-city"
                                }))}
                                value={persona.ciudad_id || ""}
                                onChange={(value) => handlePersonaChange("ciudad_id", value || null)}
                                onSearch={buscarCiudades}
                                searchable
                                placeholder="Buscar ciudades..."
                                loading={loadingCiudades}
                                className="w-full"
                            />
                        </div>
                    </div>
                </div>

                {/* Datos Laborales */}
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-briefcase text-primary text-lg"></i>
                        </div>
                        <h2 className="text-sm font-semibold text-foreground">Datos Laborales</h2>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Puesto
                            </label>
                            <Select
                                options={puestos.map(p => ({
                                    value: p.id,
                                    label: p.nombre,
                                    icon: "fas fa-shield"
                                }))}
                                value={laboral.puesto_id || ""}
                                onChange={(value) => handleLaboralChange("puesto_id", value || null)}
                                onSearch={buscarPuestos}
                                searchable
                                placeholder="Buscar puestos..."
                                loading={loadingPuestos}
                                className="w-full"
                            />
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Salario <span className="text-destructive">*</span>
                            </label>
                            <input
                                type="number"
                                value={laboral.salario}
                                onChange={(e) => handleLaboralChange("salario", e.target.value)}
                                placeholder="0.00"
                                min="0"
                                step="0.01"
                                className="px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                            />
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Fecha de contratación <span className="text-destructive">*</span>
                            </label>
                            <input
                                type="date"
                                value={laboral.fecha_contratacion}
                                onChange={(e) => handleLaboralChange("fecha_contratacion", e.target.value)}
                                className="px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                            />
                        </div>

                        {isEditMode && (
                            <div className="flex flex-col gap-1.5">
                                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                    Estado
                                </label>
                                <select
                                    value={laboral.estado}
                                    onChange={(e) => handleLaboralChange("estado", e.target.value)}
                                    className="px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                >
                                    <option value="activo">Activo</option>
                                    <option value="inactivo">Inactivo</option>
                                </select>
                            </div>
                        )}

                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Rol
                            </label>
                            <Select
                                options={(roles ?? []).map(r => ({
                                    value: r.id,
                                    label: r.nombre,
                                    icon: "fas fa-shield-halved"
                                }))}
                                value={laboral.rol_id || ""}
                                onChange={(value) => handleLaboralChange("rol_id", value || null)}
                                onSearch={buscarRoles}
                                searchable
                                placeholder="Buscar rol..."
                                loading={loadingRoles}
                                className="w-full"
                            />
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Departamento
                            </label>
                            <Select
                                options={departamentos.map(d => ({
                                    value: d.id,
                                    label: d.nombre,
                                    description: d.codigo,
                                    icon: "fas fa-building"
                                }))}
                                value={laboral.departamento_id || ""}
                                onChange={(value) => handleLaboralChange("departamento_id", value || null)}
                                onSearch={buscarDepartamentos}
                                searchable
                                placeholder="Buscar departamento..."
                                loading={loadingDepartamentos}
                                className="w-full"
                            />
                        </div>
                    </div>
                </div>

                {/* Información de solo lectura — modo edición */}
                {isEditMode && empleado && (
                    <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                        <div className="flex items-center gap-3 mb-4 pb-4 border-b border-border">
                            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                                <i className="fa-solid fa-circle-info text-muted-foreground text-lg"></i>
                            </div>
                            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Información</h2>
                        </div>
                        <div className="space-y-1">
                            <div className="flex items-center justify-between py-2 border-b border-border">
                                <span className="text-xs text-muted-foreground flex items-center gap-2">
                                    <i className="fa-solid fa-barcode"></i>Código
                                </span>
                                <span
                                    className="font-mono text-xs font-semibold text-foreground bg-muted/50 px-2 py-1 rounded-md">
                                    {empleado.codigo}
                                </span>
                            </div>
                            <div className="flex items-center justify-between py-2 border-b border-border">
                                <span className="text-xs text-muted-foreground flex items-center gap-2">
                                    <i className="fa-solid fa-at"></i>Username
                                </span>
                                <span className="font-mono text-xs text-foreground">
                                    {empleado.username ??
                                        <span className="italic text-muted-foreground/60">Sin acceso</span>}
                                </span>
                            </div>
                            <div className="flex items-center justify-between py-2 border-b border-border">
                                <span className="text-xs text-muted-foreground flex items-center gap-2">
                                    <i className="fa-solid fa-user-md"></i>Cuenta
                                </span>
                                {empleado.cuenta_activada ? (
                                    <span
                                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                                        <i className="fa-solid fa-circle-check text-[9px]"></i>Activada
                                    </span>
                                ) : empleado.tiene_acceso ? (
                                    <span
                                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-yellow-500/10 text-yellow-600 dark:text-yellow-400">
                                        <i className="fa-solid fa-clock text-[9px]"></i>Pendiente
                                    </span>
                                ) : (
                                    <span
                                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-muted/60 text-muted-foreground">
                                        <i className="fa-solid fa-user-slash text-[9px]"></i>Sin acceso
                                    </span>
                                )}
                            </div>
                            <div className="flex items-center justify-between py-2">
                                <span className="text-xs text-muted-foreground flex items-center gap-2">
                                    <i className="fa-solid fa-calendar"></i>Contratado
                                </span>
                                <span className="text-xs font-medium text-foreground">
                                    {new Date(empleado.fecha_contratacion).toLocaleDateString("es-EC", {
                                        day: "2-digit", month: "short", year: "numeric"
                                    })}
                                </span>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Columna lateral */}
            {/* Acceso al sistema — solo en creación */}
            {!isEditMode && (
                <div className="space-y-6">
                    <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                                <i className="fa-solid fa-key text-primary text-lg"></i>
                            </div>
                            <h2 className="text-sm font-semibold text-foreground">Acceso al Sistema</h2>
                        </div>

                        <div>
                            <CheckboxKlyra
                                checked={crearAcceso}
                                onChange={setCrearAcceso}
                                label="Crear cuenta de acceso"
                                className={"w-full justify-center mb-2"}
                            />
                            <p className="text-xs text-muted-foreground">
                                Se enviará un email de activación al empleado para que defina su contraseña.
                            </p>
                        </div>

                        {crearAcceso && (
                            <div
                                className="mt-4 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                                <div className="flex gap-2">
                                    <i className="fa-solid fa-circle-info text-blue-500 text-xs mt-0.5 shrink-0"></i>
                                    <p className="text-xs text-blue-600 dark:text-blue-400">
                                        El username se generará automáticamente. El link de activación expira en 48
                                        horas.
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </form>
    )
}