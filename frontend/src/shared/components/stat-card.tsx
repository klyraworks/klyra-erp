"use client"

interface StatCardProps {
  title: string
  value: string | number
  icon: string
  change?: {
    value: number
    label: string
  }
  subtitle: string
}

export function StatCard({ title, value, icon, change, subtitle }: StatCardProps) {
  return (
    <div className="bg-card rounded-xl border border-border p-4 flex items-start justify-between mb-3">
      <div>
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{title}</p>
        <p className="text-2xl font-bold text-foreground my-3">{value}</p>
        <p className="text-xs text-muted-foreground">{subtitle}</p>
      </div>
      <div className="flex items-start justify-between mb-4 align-right">
        <div
          className={`w-10 h-10 bg-primary rounded-lg flex items-center justify-center`}
        >
          <i className={`fa-solid ${icon} text-primary-foreground`}></i>
        </div>
        {change && (
          <span
            className={`text-xs font-medium px-2 py-1 rounded-full ${change.value >= 0 ? "bg-success/10 text-success" : "bg-destructive/10 text-destructive"}`}
          >
            {change.value >= 0 ? "+" : ""}
            {change.value}% {change.label}
          </span>
        )}
      </div>
    </div>
  )
}
