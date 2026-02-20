"use client"

import { useState } from "react"
import { Header } from "@/src/shared/components/header"
import { useStore } from "@/src/core/store"

export default function ConfiguracionPage() {
  const { apiUrl, setApiUrl } = useStore()
  const [activeTab, setActiveTab] = useState<"empresa" | "facturacion" | "sistema" | "api">("empresa")

  // Mock empresa data
  const [empresaData, setEmpresaData] = useState({
    ruc: "0992123456001",
    razonSocial: "Empresa Demo S.A.",
    nombreComercial: "Klyra Demo",
    direccionMatriz: "Av. Principal 123, Guayaquil",
    telefono: "+593 4 123 4567",
    email: "contacto@empresa.com",
    obligadoContabilidad: true,
    regimenMicroempresa: false,
    agenteRetencion: "001",
  })

  // Facturación config
  const [facturacionData, setFacturacionData] = useState({
    ambiente: "pruebas",
    tipoEmision: "normal",
    establecimiento: "001",
    puntoEmision: "001",
    secuencialFactura: 1,
    secuencialNotaCredito: 1,
    secuencialNotaDebito: 1,
    secuencialRetencion: 1,
    secuencialGuiaRemision: 1,
    certificadoP12: "",
    claveCertificado: "",
  })

  // Sistema config
  const [sistemaData, setSistemaData] = useState({
    moneda: "USD",
    decimalesPrecio: 2,
    decimalesCantidad: 2,
    ivaDefault: 15,
    permitirStockNegativo: false,
    requiereAprobacion: true,
    diasCreditoDefault: 30,
  })

  const [tempApiUrl, setTempApiUrl] = useState(apiUrl)

  const tabs = [
    { id: "empresa", label: "Datos Empresa", icon: "fa-building" },
    { id: "facturacion", label: "Facturación SRI", icon: "fa-file-invoice" },
    { id: "sistema", label: "Sistema", icon: "fa-sliders" },
    { id: "api", label: "Conexión API", icon: "fa-plug" },
  ]

  return (
    <>
      <Header title="Configuración" breadcrumb={["Klyra", "Configuración"]} />
      <main className="flex-1 overflow-y-auto p-6">
        <div className="max-w-5xl mx-auto">
          {/* Tabs */}
          <div className="bg-card rounded-xl border border-border overflow-hidden">
            {/* Tab Headers */}
            <div className="flex border-b border-border overflow-x-auto">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as typeof activeTab)}
                  className={`flex items-center gap-2 px-6 py-4 text-sm font-medium transition-colors relative whitespace-nowrap ${
                    activeTab === tab.id ? "text-primary" : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <i className={`fa-solid ${tab.icon}`}></i>
                  {tab.label}
                  {activeTab === tab.id && <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary"></span>}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="p-6">
              {/* Empresa Tab */}
              {activeTab === "empresa" && (
                <div className="space-y-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                      <i className="fa-solid fa-building text-primary text-xl"></i>
                    </div>
                    <div>
                      <h3 className="font-semibold text-foreground">Información de la Empresa</h3>
                      <p className="text-sm text-muted-foreground">Datos fiscales y de contacto</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        <i className="fa-solid fa-id-card mr-2 text-muted-foreground"></i>
                        RUC
                      </label>
                      <input
                        type="text"
                        value={empresaData.ruc}
                        onChange={(e) => setEmpresaData({ ...empresaData, ruc: e.target.value })}
                        className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                        maxLength={13}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        <i className="fa-solid fa-building mr-2 text-muted-foreground"></i>
                        Razón Social
                      </label>
                      <input
                        type="text"
                        value={empresaData.razonSocial}
                        onChange={(e) => setEmpresaData({ ...empresaData, razonSocial: e.target.value })}
                        className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        <i className="fa-solid fa-store mr-2 text-muted-foreground"></i>
                        Nombre Comercial
                      </label>
                      <input
                        type="text"
                        value={empresaData.nombreComercial}
                        onChange={(e) => setEmpresaData({ ...empresaData, nombreComercial: e.target.value })}
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
                        value={empresaData.telefono}
                        onChange={(e) => setEmpresaData({ ...empresaData, telefono: e.target.value })}
                        className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                      />
                    </div>
                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-foreground mb-2">
                        <i className="fa-solid fa-location-dot mr-2 text-muted-foreground"></i>
                        Dirección Matriz
                      </label>
                      <input
                        type="text"
                        value={empresaData.direccionMatriz}
                        onChange={(e) => setEmpresaData({ ...empresaData, direccionMatriz: e.target.value })}
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
                        value={empresaData.email}
                        onChange={(e) => setEmpresaData({ ...empresaData, email: e.target.value })}
                        className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        <i className="fa-solid fa-hashtag mr-2 text-muted-foreground"></i>
                        Resolución Agente Retención
                      </label>
                      <input
                        type="text"
                        value={empresaData.agenteRetencion}
                        onChange={(e) => setEmpresaData({ ...empresaData, agenteRetencion: e.target.value })}
                        placeholder="Ej: NAC-DNCRASC20-00000001"
                        className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                      />
                    </div>
                  </div>

                  {/* Checkboxes */}
                  <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border">
                    <label className="flex items-center gap-3 p-4 bg-muted rounded-xl cursor-pointer">
                      <input
                        type="checkbox"
                        checked={empresaData.obligadoContabilidad}
                        onChange={(e) => setEmpresaData({ ...empresaData, obligadoContabilidad: e.target.checked })}
                        className="w-5 h-5 rounded border-border text-primary focus:ring-primary/30"
                      />
                      <div>
                        <p className="text-sm font-medium text-foreground">Obligado a llevar contabilidad</p>
                        <p className="text-xs text-muted-foreground">Según normativa SRI</p>
                      </div>
                    </label>
                    <label className="flex items-center gap-3 p-4 bg-muted rounded-xl cursor-pointer">
                      <input
                        type="checkbox"
                        checked={empresaData.regimenMicroempresa}
                        onChange={(e) => setEmpresaData({ ...empresaData, regimenMicroempresa: e.target.checked })}
                        className="w-5 h-5 rounded border-border text-primary focus:ring-primary/30"
                      />
                      <div>
                        <p className="text-sm font-medium text-foreground">Régimen Microempresa</p>
                        <p className="text-xs text-muted-foreground">RIMPE - Negocio Popular</p>
                      </div>
                    </label>
                  </div>

                  <div className="flex justify-end gap-3 pt-4 border-t border-border">
                    <button className="px-6 py-2.5 bg-primary text-primary-foreground rounded-xl text-sm font-medium hover:bg-primary/90 transition-colors flex items-center gap-2">
                      <i className="fa-solid fa-check"></i>
                      Guardar Cambios
                    </button>
                  </div>
                </div>
              )}

              {/* Facturación Tab */}
              {activeTab === "facturacion" && (
                <div className="space-y-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                      <i className="fa-solid fa-file-invoice text-primary text-xl"></i>
                    </div>
                    <div>
                      <h3 className="font-semibold text-foreground">Configuración de Facturación Electrónica</h3>
                      <p className="text-sm text-muted-foreground">Parámetros SRI Ecuador</p>
                    </div>
                  </div>

                  {/* Ambiente */}
                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        <i className="fa-solid fa-cloud mr-2 text-muted-foreground"></i>
                        Ambiente
                      </label>
                      <select
                        value={facturacionData.ambiente}
                        onChange={(e) => setFacturacionData({ ...facturacionData, ambiente: e.target.value })}
                        className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                      >
                        <option value="pruebas">Pruebas (1)</option>
                        <option value="produccion">Producción (2)</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        <i className="fa-solid fa-paper-plane mr-2 text-muted-foreground"></i>
                        Tipo de Emisión
                      </label>
                      <select
                        value={facturacionData.tipoEmision}
                        onChange={(e) => setFacturacionData({ ...facturacionData, tipoEmision: e.target.value })}
                        className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                      >
                        <option value="normal">Normal (1)</option>
                        <option value="contingencia">Contingencia (2)</option>
                      </select>
                    </div>
                  </div>

                  {/* Secuenciales */}
                  <div className="space-y-4 pt-4 border-t border-border">
                    <h4 className="font-medium text-foreground flex items-center gap-2">
                      <i className="fa-solid fa-list-ol text-muted-foreground"></i>
                      Secuenciales por Tipo de Documento
                    </h4>
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">Establecimiento</label>
                        <input
                          type="text"
                          value={facturacionData.establecimiento}
                          onChange={(e) => setFacturacionData({ ...facturacionData, establecimiento: e.target.value })}
                          maxLength={3}
                          className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">Punto Emisión</label>
                        <input
                          type="text"
                          value={facturacionData.puntoEmision}
                          onChange={(e) => setFacturacionData({ ...facturacionData, puntoEmision: e.target.value })}
                          maxLength={3}
                          className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">Sec. Factura</label>
                        <input
                          type="number"
                          value={facturacionData.secuencialFactura}
                          onChange={(e) =>
                            setFacturacionData({
                              ...facturacionData,
                              secuencialFactura: Number.parseInt(e.target.value),
                            })
                          }
                          min={1}
                          className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">Sec. Nota Crédito</label>
                        <input
                          type="number"
                          value={facturacionData.secuencialNotaCredito}
                          onChange={(e) =>
                            setFacturacionData({
                              ...facturacionData,
                              secuencialNotaCredito: Number.parseInt(e.target.value),
                            })
                          }
                          min={1}
                          className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">Sec. Retención</label>
                        <input
                          type="number"
                          value={facturacionData.secuencialRetencion}
                          onChange={(e) =>
                            setFacturacionData({
                              ...facturacionData,
                              secuencialRetencion: Number.parseInt(e.target.value),
                            })
                          }
                          min={1}
                          className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">Sec. Guía Remisión</label>
                        <input
                          type="number"
                          value={facturacionData.secuencialGuiaRemision}
                          onChange={(e) =>
                            setFacturacionData({
                              ...facturacionData,
                              secuencialGuiaRemision: Number.parseInt(e.target.value),
                            })
                          }
                          min={1}
                          className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Certificado Digital */}
                  <div className="space-y-4 pt-4 border-t border-border">
                    <h4 className="font-medium text-foreground flex items-center gap-2">
                      <i className="fa-solid fa-certificate text-muted-foreground"></i>
                      Certificado Digital (Firma Electrónica)
                    </h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">Archivo .p12</label>
                        <div className="flex gap-2">
                          <input
                            type="text"
                            value={facturacionData.certificadoP12}
                            readOnly
                            placeholder="Seleccionar archivo..."
                            className="flex-1 px-4 py-3 bg-muted border border-border rounded-xl text-sm"
                          />
                          <button className="px-4 py-3 bg-secondary text-secondary-foreground rounded-xl text-sm font-medium hover:bg-secondary/80 transition-colors">
                            <i className="fa-solid fa-upload"></i>
                          </button>
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">Clave del Certificado</label>
                        <input
                          type="password"
                          value={facturacionData.claveCertificado}
                          onChange={(e) => setFacturacionData({ ...facturacionData, claveCertificado: e.target.value })}
                          placeholder="Contraseña del .p12"
                          className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-end gap-3 pt-4 border-t border-border">
                    <button className="px-6 py-2.5 bg-primary text-primary-foreground rounded-xl text-sm font-medium hover:bg-primary/90 transition-colors flex items-center gap-2">
                      <i className="fa-solid fa-check"></i>
                      Guardar Configuración
                    </button>
                  </div>
                </div>
              )}

              {/* Sistema Tab */}
              {activeTab === "sistema" && (
                <div className="space-y-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                      <i className="fa-solid fa-sliders text-primary text-xl"></i>
                    </div>
                    <div>
                      <h3 className="font-semibold text-foreground">Configuración del Sistema</h3>
                      <p className="text-sm text-muted-foreground">Parámetros generales de operación</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        <i className="fa-solid fa-dollar-sign mr-2 text-muted-foreground"></i>
                        Moneda
                      </label>
                      <select
                        value={sistemaData.moneda}
                        onChange={(e) => setSistemaData({ ...sistemaData, moneda: e.target.value })}
                        className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                      >
                        <option value="USD">Dólar Estadounidense (USD)</option>
                        <option value="EUR">Euro (EUR)</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        <i className="fa-solid fa-percent mr-2 text-muted-foreground"></i>
                        IVA por Defecto (%)
                      </label>
                      <select
                        value={sistemaData.ivaDefault}
                        onChange={(e) =>
                          setSistemaData({ ...sistemaData, ivaDefault: Number.parseInt(e.target.value) })
                        }
                        className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                      >
                        <option value={0}>0%</option>
                        <option value={13}>13%</option>
                        <option value={15}>15%</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        <i className="fa-solid fa-hashtag mr-2 text-muted-foreground"></i>
                        Decimales en Precios
                      </label>
                      <select
                        value={sistemaData.decimalesPrecio}
                        onChange={(e) =>
                          setSistemaData({ ...sistemaData, decimalesPrecio: Number.parseInt(e.target.value) })
                        }
                        className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                      >
                        <option value={2}>2 decimales</option>
                        <option value={3}>3 decimales</option>
                        <option value={4}>4 decimales</option>
                        <option value={6}>6 decimales</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        <i className="fa-solid fa-calendar-days mr-2 text-muted-foreground"></i>
                        Días de Crédito por Defecto
                      </label>
                      <input
                        type="number"
                        value={sistemaData.diasCreditoDefault}
                        onChange={(e) =>
                          setSistemaData({ ...sistemaData, diasCreditoDefault: Number.parseInt(e.target.value) })
                        }
                        min={0}
                        className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                      />
                    </div>
                  </div>

                  {/* Toggles */}
                  <div className="space-y-3 pt-4 border-t border-border">
                    <div className="flex items-center justify-between p-4 bg-muted rounded-xl">
                      <div>
                        <p className="text-sm font-medium text-foreground">Permitir stock negativo</p>
                        <p className="text-xs text-muted-foreground">Permite vender productos sin stock disponible</p>
                      </div>
                      <button
                        onClick={() =>
                          setSistemaData({ ...sistemaData, permitirStockNegativo: !sistemaData.permitirStockNegativo })
                        }
                        className={`w-12 h-6 rounded-full p-0.5 transition-colors ${
                          sistemaData.permitirStockNegativo ? "bg-primary" : "bg-border"
                        }`}
                      >
                        <div
                          className={`w-5 h-5 rounded-full bg-white transition-transform ${
                            sistemaData.permitirStockNegativo ? "translate-x-6" : "translate-x-0"
                          }`}
                        />
                      </button>
                    </div>
                    <div className="flex items-center justify-between p-4 bg-muted rounded-xl">
                      <div>
                        <p className="text-sm font-medium text-foreground">Requiere aprobación de ventas</p>
                        <p className="text-xs text-muted-foreground">
                          Las ventas deben ser aprobadas antes de procesarse
                        </p>
                      </div>
                      <button
                        onClick={() =>
                          setSistemaData({ ...sistemaData, requiereAprobacion: !sistemaData.requiereAprobacion })
                        }
                        className={`w-12 h-6 rounded-full p-0.5 transition-colors ${
                          sistemaData.requiereAprobacion ? "bg-primary" : "bg-border"
                        }`}
                      >
                        <div
                          className={`w-5 h-5 rounded-full bg-white transition-transform ${
                            sistemaData.requiereAprobacion ? "translate-x-6" : "translate-x-0"
                          }`}
                        />
                      </button>
                    </div>
                  </div>

                  <div className="flex justify-end gap-3 pt-4 border-t border-border">
                    <button className="px-6 py-2.5 bg-primary text-primary-foreground rounded-xl text-sm font-medium hover:bg-primary/90 transition-colors flex items-center gap-2">
                      <i className="fa-solid fa-check"></i>
                      Guardar Configuración
                    </button>
                  </div>
                </div>
              )}

              {/* API Tab */}
              {activeTab === "api" && (
                <div className="space-y-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                      <i className="fa-solid fa-plug text-primary text-xl"></i>
                    </div>
                    <div>
                      <h3 className="font-semibold text-foreground">Conexión API Backend</h3>
                      <p className="text-sm text-muted-foreground">Configuración de conexión con Django REST</p>
                    </div>
                  </div>

                  <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl flex items-start gap-3">
                    <i className="fa-solid fa-circle-info text-blue-500 mt-0.5"></i>
                    <div>
                      <p className="text-sm font-medium text-foreground">URL del API</p>
                      <p className="text-sm text-muted-foreground">
                        Ingresa la URL base de tu servidor Django. Ejemplo: http://localhost:8000
                      </p>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      <i className="fa-solid fa-link mr-2 text-muted-foreground"></i>
                      URL del API Backend
                    </label>
                    <input
                      type="url"
                      value={tempApiUrl}
                      onChange={(e) => setTempApiUrl(e.target.value)}
                      placeholder="http://localhost:8000"
                      className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                    />
                  </div>

                  {/* Connection Status */}
                  <div className="p-4 bg-muted rounded-xl">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-green-500/10 text-green-600 rounded-lg flex items-center justify-center">
                          <i className="fa-solid fa-server"></i>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-foreground">Estado de Conexión</p>
                          <p className="text-xs text-muted-foreground">Verificar conectividad con el backend</p>
                        </div>
                      </div>
                      <button className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg text-sm font-medium hover:bg-secondary/80 transition-colors flex items-center gap-2">
                        <i className="fa-solid fa-rotate"></i>
                        Probar Conexión
                      </button>
                    </div>
                  </div>

                  {/* Endpoints Info */}
                  <div className="space-y-3 pt-4 border-t border-border">
                    <h4 className="font-medium text-foreground flex items-center gap-2">
                      <i className="fa-solid fa-code text-muted-foreground"></i>
                      Endpoints Configurados
                    </h4>
                    <div className="grid grid-cols-2 gap-3">
                      {[
                        { endpoint: "/api/auth/login/", desc: "Autenticación" },
                        { endpoint: "/api/ventas/", desc: "Gestión de ventas" },
                        { endpoint: "/api/productos/", desc: "Catálogo de productos" },
                        { endpoint: "/api/clientes/", desc: "Gestión de clientes" },
                        { endpoint: "/api/pagos/", desc: "Registro de pagos" },
                        { endpoint: "/api/movimientos-inventario/", desc: "Movimientos de inventario" },
                      ].map((item) => (
                        <div key={item.endpoint} className="p-3 bg-muted rounded-lg">
                          <code className="text-xs text-primary font-mono">{item.endpoint}</code>
                          <p className="text-xs text-muted-foreground mt-1">{item.desc}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="flex justify-end gap-3 pt-4 border-t border-border">
                    <button
                      onClick={() => {
                        setApiUrl(tempApiUrl)
                      }}
                      className="px-6 py-2.5 bg-primary text-primary-foreground rounded-xl text-sm font-medium hover:bg-primary/90 transition-colors flex items-center gap-2"
                    >
                      <i className="fa-solid fa-check"></i>
                      Guardar URL
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
