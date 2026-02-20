// components/ProtectedRoute.tsx
'use client'

import React, { useEffect, useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { checkAuth } from '@/src/core/api/client'
import { useStore } from '@/src/core/store'
import {LoadingScreen} from "@/components/ui/loading-screen";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const { setAuth } = useStore()
  const [loading, setLoading] = useState(true)
  const [authenticated, setAuthenticated] = useState(false)
  const hasChecked = useRef(false) // ← Evitar múltiples llamadas

  useEffect(() => {
    if (hasChecked.current) return // ← Si ya verificó, salir

    const verify = async () => {
      hasChecked.current = true // ← Marcar como verificado

      const result = await checkAuth()

      if (result.authenticated && result.user && result.empleado && result.empresa) {
        setAuth(result.user, result.empleado, result.empresa)
        setAuthenticated(true)
      } else {
        router.push('/login')
      }

      setLoading(false)
    }

    verify()
  }, []) // ← Dependencias vacías, solo ejecutar una vez

  if (loading) {
    return <LoadingScreen message="Verificando autenticación..." />
  }

  if (!authenticated) {
    return null
  }

  return <>{children}</>
}