// frontend/src/shared/components/auth-guard.tsx
"use client"

import type React from "react"
import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useStore } from "@/src/core/store"
import { LoadingScreen } from "@/components/ui/loading-screen"

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useStore()
  const router = useRouter()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    // Marcar como montado en el cliente
    setMounted(true)
  }, [])

  useEffect(() => {
    // Solo redirigir después de que el componente esté montado
    if (mounted && !isAuthenticated) {
      router.push("/")
    }
  }, [mounted, isAuthenticated, router])

  // Durante SSR y primera hidratación, siempre mostrar loading
  if (!mounted) {
    return <LoadingScreen message="Verificando autenticación..." />
  }

  // Después de montar, mostrar loading si no está autenticado
  if (!isAuthenticated) {
    return <LoadingScreen message="Redirigiendo..." />
  }

  return <>{children}</>
}