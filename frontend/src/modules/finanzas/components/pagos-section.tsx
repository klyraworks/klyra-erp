"use client"

import { useEffect, useRef } from "react"
import * as echarts from "echarts"
import { usePagos } from "@/src/core/store"
import { useTheme } from "@/src/core/theme/provider"
import type { Pago } from "@/src/core/api/types"
import {usePagination} from '@/hooks/use-pagination'
import {Pagination} from '@/components/shared/Pagination'


function PagosPorMetodoChart({ pagos }: { pagos: Pago[] | undefined }) {
  const chartRef = useRef<HTMLDivElement>(null)
  const { theme } = useTheme()

  useEffect(() => {
    if (!chartRef.current || !pagos || pagos.length === 0) return

    const chart = echarts.init(chartRef.current, theme === "dark" ? "dark" : undefined, { renderer: "svg" })

    const pagosPorMetodo = pagos.reduce(
      (acc, p) => {
        const metodo = p.metodo || "otro"
        if (!acc[metodo]) {
          acc[metodo] = { count: 0, total: 0 }
        }
        acc[metodo].count += 1
        acc[metodo].total += Number.parseFloat(String(p.monto))
        return acc
      },
      {} as Record<string, { count: number; total: number }>,
    )

    const metodoColors: Record<string, string> = {
      efectivo: "#22c55e",
      transferencia: "#3b82f6",
      tarjeta: "#8b5cf6",
      cheque: "#f59e0b",
      otro: "#6b7280",
    }

    const data = Object.entries(pagosPorMetodo).map(([metodo, info]) => ({
      name: metodo.charAt(0).toUpperCase() + metodo.slice(1),
      value: info.total,
      count: info.count,
      itemStyle: { color: metodoColors[metodo] || "#6b7280" },
    }))

    chart.setOption({
      backgroundColor: "transparent",
      tooltip: {
        trigger: "item",
        backgroundColor: theme === "dark" ? "#374151" : "#212842",
        borderColor: theme === "dark" ? "#374151" : "#212842",
        textStyle: { color: "#f0e7d5" },
        formatter: (params: { name: string; value: number; data: { count: number } }) => {
          return `<div><strong>${params.name}</strong></div>
                  <div>Total: $${params.value.toFixed(2)}</div>
                  <div>Pagos: ${params.data.count}</div>`
        },
      },
      legend: {
        orient: "vertical",
        right: 10,
        top: "center",
        textStyle: { color: theme === "dark" ? "#9ca3af" : "#6c757d", fontSize: 11 },
      },
      series: [
        {
          type: "pie",
          radius: ["40%", "65%"],
          center: ["35%", "50%"],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 4,
            borderColor: theme === "dark" ? "#1f2937" : "#fff",
            borderWidth: 2,
          },
          label: { show: false },
          data: data,
        },
      ],
    })

    const handleResize = () => chart.resize()
    window.addEventListener("resize", handleResize)
    return () => {
      window.removeEventListener("resize", handleResize)
      chart.dispose()
    }
  }, [pagos, theme])

  if (!pagos || pagos.length === 0) {
    return (
      <div className="h-[200px] flex items-center justify-center text-muted-foreground">
        <p>Sin pagos registrados</p>
      </div>
    )
  }

  return <div ref={chartRef} className="w-full h-[200px]" />
}

function PagosPorFechaChart({ pagos }: { pagos: Pago[] | undefined }) {
  const chartRef = useRef<HTMLDivElement>(null)
  const { theme } = useTheme()

  useEffect(() => {
    if (!chartRef.current || !pagos || pagos.length === 0) return

    const chart = echarts.init(chartRef.current, theme === "dark" ? "dark" : undefined, { renderer: "svg" })

    const pagosPorFecha = pagos.reduce(
      (acc, p) => {
        const fecha = p.fecha.split('T')[0] || "Sin fecha"
        if (!acc[fecha]) {
          acc[fecha] = 0
        }
        acc[fecha] += Number.parseFloat(String(p.monto))
        return acc
      },
      {} as Record<string, number>,
    )

    const sortedDates = Object.keys(pagosPorFecha).sort()
    const totales = sortedDates.map((d) => pagosPorFecha[d])

    chart.setOption({
      backgroundColor: "transparent",
      tooltip: {
        trigger: "axis",
        backgroundColor: theme === "dark" ? "#374151" : "#212842",
        borderColor: theme === "dark" ? "#374151" : "#212842",
        textStyle: { color: "#f0e7d5" },
      },
      grid: { left: 60, right: 20, top: 20, bottom: 40 },
      xAxis: {
        type: "category",
        data: sortedDates,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: theme === "dark" ? "#9ca3af" : "#6c757d", fontSize: 10, rotate: 45 },
      },
      yAxis: {
        type: "value",
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: theme === "dark" ? "#374151" : "#e9ecef" } },
        axisLabel: { color: theme === "dark" ? "#9ca3af" : "#6c757d", formatter: "${value}" },
      },
      series: [
        {
          type: "line",
          data: totales,
          smooth: true,
          symbol: "circle",
          symbolSize: 6,
          lineStyle: { color: "#22c55e", width: 2 },
          itemStyle: { color: "#22c55e" },
          areaStyle: {
            color: {
              type: "linear",
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: "rgba(34, 197, 94, 0.3)" },
                { offset: 1, color: "rgba(34, 197, 94, 0)" },
              ],
            },
          },
        },
      ],
    })

    const handleResize = () => chart.resize()
    window.addEventListener("resize", handleResize)
    return () => {
      window.removeEventListener("resize", handleResize)
      chart.dispose()
    }
  }, [pagos, theme])

  if (!pagos || pagos.length === 0) {
    return (
      <div className="h-[200px] flex items-center justify-center text-muted-foreground">
        <p>Sin pagos registrados</p>
      </div>
    )
  }

  return <div ref={chartRef} className="w-full h-[200px]" />
}

interface PagosSectionProps {
  compact?: boolean
}

export function PagosSection({compact = false}: PagosSectionProps) {
  const { data: pagos, isLoading, error } = usePagos()


  const getMetodoIcon = (metodo: string) => {
    switch (metodo?.toLowerCase()) {
      case "efectivo":
        return "fa-money-bill-wave"
      case "transferencia":
        return "fa-building-columns"
      case "tarjeta":
        return "fa-credit-card"
      case "cheque":
        return "fa-money-check"
      default:
        return "fa-receipt"
    }
  }

  if (error) {
    return (
      <div className="bg-card rounded-xl border border-border p-6">
        <div className="text-center text-destructive">
          <i className="fa-solid fa-circle-exclamation text-2xl mb-2"></i>
          <p>Error al cargar pagos</p>
        </div>
      </div>
    )
  }

  const {
        paginatedData,
        currentPage,
        totalPages,
        goToPage,
        nextPage,
        prevPage,
        hasNextPage,
        hasPrevPage,
        startIndex,
        endIndex,
        totalItems,
    } = usePagination({
        data: pagos || [],
        itemsPerPage: compact ? 5 : 10, // 5 para compact, 10 para vista completa
    })

  const displayPagos = compact ? pagos?.slice(0, 5) : paginatedData



  return (
    <>
      {pagos && pagos.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="bg-card rounded-xl border border-border p-6">
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
              PAGOS POR MÉTODO
            </h3>
            <PagosPorMetodoChart pagos={pagos} />
          </div>
          <div className="bg-card rounded-xl border border-border p-6">
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
              TENDENCIA DE PAGOS
            </h3>
            <PagosPorFechaChart pagos={pagos} />
          </div>
        </div>
      )}

      <div className="bg-card rounded-xl border border-border p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-muted rounded-lg flex items-center justify-center">
              <i className="fa-solid fa-money-check-dollar text-primary"></i>
            </div>
            <div>
              <h3 className="font-semibold text-foreground">Historial de Pagos</h3>
              <p className="text-sm text-muted-foreground">{pagos?.length || 0} pagos registrados</p>
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-14 bg-muted animate-pulse rounded-lg"></div>
            ))}
          </div>
        ) : pagos?.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <i className="fa-solid fa-inbox text-3xl mb-2"></i>
            <p>No hay pagos registrados</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Venta</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Fecha</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Método</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Monto</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Referencia</th>
                </tr>
              </thead>
              <tbody>
                {displayPagos?.map((pago) => (
                  <tr key={pago.id} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                    <td className="py-4 px-4 font-medium text-foreground">{pago.venta?.numero || "-"}</td>
                    <td className="py-4 px-4 text-muted-foreground">{pago.fecha_local.split('T')[0] || "-"}</td>
                    <td className="py-4 px-4">
                      <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-muted text-sm">
                        <i className={`fa-solid ${getMetodoIcon(pago.metodo)} text-primary`}></i>
                        {pago.metodo?.charAt(0).toUpperCase() + pago.metodo?.slice(1) || "N/A"}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-right text-success font-semibold">
                      ${Number.parseFloat(String(pago.monto)).toFixed(2)}
                    </td>
                    <td className="py-4 px-4 text-muted-foreground">{pago.referencia || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!compact && (
                <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    onPageChange={goToPage}
                    onNext={nextPage}
                    onPrev={prevPage}
                    hasNextPage={hasNextPage}
                    hasPrevPage={hasPrevPage}
                    startIndex={startIndex}
                    endIndex={endIndex}
                    totalItems={totalItems}
                />
            )}
          </div>
        )}
      </div>
    </>
  )
}
