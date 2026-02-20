"use client"

import { useEffect, useRef } from "react"
import * as echarts from "echarts"
import { useClientes } from "@/src/core/store"
import { useTheme } from "@/src/core/theme/provider"
import type { Cliente } from "@/src/core/api/types"

function CreditoUsadoChart({ clientes }: { clientes: Cliente[] | undefined }) {
  const chartRef = useRef<HTMLDivElement>(null)
  const { theme } = useTheme()

  useEffect(() => {
    if (!chartRef.current || !clientes || clientes.length === 0) return

    const chart = echarts.init(chartRef.current, theme === "dark" ? "dark" : undefined, { renderer: "svg" })

    const clientesConCredito = clientes
      .filter((c) => Number.parseFloat(String(c.limite_credito)) > 0)
      .map((c) => {
        const limite = Number.parseFloat(String(c.limite_credito))
        const disponible = Number.parseFloat(String(c.credito_disponible))
        const usado = limite - disponible
        return {
          nombre: c.razon_social || c.nombre_completo || "N/A",
          limite,
          usado,
          porcentaje: (usado / limite) * 100,
        }
      })
      .sort((a, b) => b.usado - a.usado)
      .slice(0, 8)

    chart.setOption({
      backgroundColor: "transparent",
      tooltip: {
        trigger: "axis",
        backgroundColor: theme === "dark" ? "#374151" : "#212842",
        borderColor: theme === "dark" ? "#374151" : "#212842",
        textStyle: { color: "#f0e7d5" },
        axisPointer: { type: "shadow" },
        formatter: (params: { name: string; value: number }[]) => {
          const p = params[0]
          const cliente = clientesConCredito.find(
            (c) => c.nombre.substring(0, 12) + (c.nombre.length > 12 ? "..." : "") === p.name,
          )
          return `<div><strong>${cliente?.nombre}</strong></div>
                  <div>Usado: $${cliente?.usado.toFixed(2)}</div>
                  <div>Límite: $${cliente?.limite.toFixed(2)}</div>
                  <div>Uso: ${cliente?.porcentaje.toFixed(1)}%</div>`
        },
      },
      grid: { left: 100, right: 20, top: 10, bottom: 30 },
      xAxis: {
        type: "value",
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: theme === "dark" ? "#374151" : "#e9ecef" } },
        axisLabel: { color: theme === "dark" ? "#9ca3af" : "#6c757d", formatter: "${value}" },
      },
      yAxis: {
        type: "category",
        data: clientesConCredito.map((c) => c.nombre.substring(0, 12) + (c.nombre.length > 12 ? "..." : "")),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: theme === "dark" ? "#9ca3af" : "#6c757d", fontSize: 11 },
      },
      series: [
        {
          type: "bar",
          data: clientesConCredito.map((c) => ({
            value: c.usado,
            itemStyle: {
              color:
                c.porcentaje >= 80
                  ? "#dc2626"
                  : c.porcentaje >= 50
                    ? "#f59e0b"
                    : theme === "dark"
                      ? "#60a5fa"
                      : "#212842",
            },
          })),
          barWidth: "60%",
          itemStyle: { borderRadius: [0, 4, 4, 0] },
        },
      ],
    })

    const handleResize = () => chart.resize()
    window.addEventListener("resize", handleResize)
    return () => {
      window.removeEventListener("resize", handleResize)
      chart.dispose()
    }
  }, [clientes, theme])

  if (!clientes || clientes.filter((c) => Number.parseFloat(String(c.limite_credito)) > 0).length === 0) {
    return (
      <div className="h-[250px] flex items-center justify-center text-muted-foreground">
        <p>Sin clientes con crédito</p>
      </div>
    )
  }

  return <div ref={chartRef} className="w-full h-[250px]" />
}

export function ClientesSection() {
  const { data: clientes, isLoading, error } = useClientes()

  if (error) {
    return (
      <div className="bg-card rounded-xl border border-border p-6">
        <div className="text-center text-destructive">
          <i className="fa-solid fa-circle-exclamation text-2xl mb-2"></i>
          <p>Error al cargar clientes</p>
        </div>
      </div>
    )
  }

  return (
    <>
      {clientes && clientes.length > 0 && (
        <div className="bg-card rounded-xl border border-border p-6 mb-6">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
            USO DE CRÉDITO POR CLIENTE
          </h3>
          <CreditoUsadoChart clientes={clientes} />
        </div>
      )}

      <div className="bg-card rounded-xl border border-border p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-muted rounded-lg flex items-center justify-center">
              <i className="fa-solid fa-users text-primary"></i>
            </div>
            <div>
              <h3 className="font-semibold text-foreground">Lista de Clientes</h3>
              <p className="text-sm text-muted-foreground">{clientes?.length || 0} clientes registrados</p>
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-14 bg-muted animate-pulse rounded-lg"></div>
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Cliente</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">RUC</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Límite Crédito</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Disponible</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Usado</th>
                </tr>
              </thead>
              <tbody>
                {clientes?.map((cliente) => {
                  const limite = Number.parseFloat(String(cliente.limite_credito))
                  const disponible = Number.parseFloat(String(cliente.credito_disponible))
                  const usado = limite - disponible
                  return (
                    <tr key={cliente.id} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                      <td className="py-4 px-4 font-medium text-foreground">
                        {cliente.razon_social || cliente.nombre_completo || "N/A"}
                      </td>
                      <td className="py-4 px-4 text-muted-foreground">{cliente.ruc}</td>
                      <td className="py-4 px-4 text-right text-foreground">${limite.toLocaleString()}</td>
                      <td className="py-4 px-4 text-right text-success font-medium">${disponible.toLocaleString()}</td>
                      <td className="py-4 px-4 text-right text-foreground">${usado.toLocaleString()}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  )
}
