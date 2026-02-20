"use client"

import type React from "react"
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { Sidebar } from "@/src/shared/components/sidebar"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ProtectedRoute>
      <div className="flex h-screen bg-background">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">{children}</div>
      </div>
    </ProtectedRoute>
  )
}
