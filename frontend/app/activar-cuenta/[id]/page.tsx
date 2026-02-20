// app/activar-cuenta/page.tsx
'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { checkAuth } from '@/src/core/api/client'
import { ActivarCuentaForm } from "@/src/modules/seguridad/forms/activar-cuenta-form"

export default function ActivarCuentaPage() {
  return <ActivarCuentaForm />
}