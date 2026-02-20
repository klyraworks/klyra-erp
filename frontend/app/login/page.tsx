// app/login/page.tsx
'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { checkAuth } from '@/src/core/api/client'
import { LoginForm } from "@/src/core/auth/login-form"

export default function LoginPage() {
  const router = useRouter()

  useEffect(() => {
    checkAuth().then(result => {
      if (result.authenticated) {
        router.replace('/dashboard')
      }
    })
  }, [router])

  return <LoginForm />
}