// components/alerts/alertas-toast.tsx
import toast from 'react-hot-toast'
import { useEffect, useState } from 'react'

// Iconos por tipo
const ICONS = {
  success: (
    <div className="flex-shrink-0">
      <div className="w-10 h-10 rounded-lg bg-green-500/10 border border-green-500/20 flex items-center justify-center">
        <i className="fa-solid fa-check text-green-600 dark:text-green-400 text-lg"></i>
      </div>
    </div>
  ),
  error: (
    <div className="flex-shrink-0">
      <div className="w-10 h-10 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center">
        <i className="fa-solid fa-xmark text-red-600 dark:text-red-400 text-lg"></i>
      </div>
    </div>
  ),
  warning: (
    <div className="flex-shrink-0">
      <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
        <i className="fa-solid fa-triangle-exclamation text-amber-600 dark:text-amber-400 text-lg"></i>
      </div>
    </div>
  ),
  info: (
    <div className="flex-shrink-0">
      <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
        <i className="fa-solid fa-circle-info text-blue-600 dark:text-blue-400 text-lg"></i>
      </div>
    </div>
  ),
  loading: (
    <div className="flex-shrink-0">
      <div className="w-10 h-10 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center">
        <i className="fa-solid fa-spinner fa-spin text-primary text-lg"></i>
      </div>
    </div>
  ),
}

// Opciones comunes
const commonOptions = {
  position: 'top-right' as const,
  duration: 1500,
}

const CustomToast = ({
  t,
  icon,
  title,
  message,
  accentColor,
  duration,
}: {
  t: any
  icon: React.ReactNode
  title?: string
  message: string
  accentColor: string
  duration?: number
}) => {
  const [progress, setProgress] = useState(100)

  useEffect(() => {
    if (!duration || duration === Infinity) return

    const startTime = Date.now()
    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime
      const remaining = Math.max(0, 100 - (elapsed / duration) * 100)
      setProgress(remaining)

      if (remaining === 0) {
        clearInterval(interval)
      }
    }, 16)

    return () => clearInterval(interval)
  }, [duration])

  const handleDismiss = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    toast.dismiss(t.id)
  }

  return (
    <div
      className={`${
        t.visible ? 'animate-in slide-in-from-right-full' : 'animate-out slide-out-to-right-full'
      } max-w-md w-full bg-white dark:bg-neutral-900 shadow-lg rounded-xl border border-neutral-200 dark:border-neutral-800 pointer-events-auto overflow-hidden`}
    >
      <div className="p-4">
        <div className="flex items-start gap-3">
          {icon}
          <div className="flex-1 min-w-0">
            {title && (
              <p className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
                {title}
              </p>
            )}
            <p className="text-sm text-neutral-600 dark:text-neutral-400 whitespace-pre-line">
              {message}
            </p>
          </div>
          <button
            onClick={handleDismiss}
            type="button"
            className="flex-shrink-0 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 transition-colors p-1 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800"
            aria-label="Cerrar notificación"
          >
            <i className="fa-solid fa-xmark text-sm"></i>
          </button>
        </div>
      </div>

      {/* Barra de progreso */}
      {duration && duration !== Infinity && (
        <div className="h-1 bg-neutral-100 dark:bg-neutral-800 overflow-hidden">
          <div
            className="h-full transition-all duration-75 ease-linear"
            style={{
              width: `${progress}%`,
              backgroundColor: accentColor,
            }}
          />
        </div>
      )}
    </div>
  )
}

// Funciones de alerta
export const alertas = {
  success: (message: string, title?: string, options = {}) => {
    const duration = (options as any).duration || commonOptions.duration
    toast.custom(
      (t) => (
        <CustomToast
          t={t}
          icon={ICONS.success}
          title={title}
          message={message}
          accentColor="rgb(34, 197, 94)"
          duration={duration}
        />
      ),
      { ...commonOptions, ...options }
    )
  },

  error: (message: string, title?: string, options = {}) => {
    const duration = (options as any).duration || 1500
    toast.custom(
      (t) => (
        <CustomToast
          t={t}
          icon={ICONS.error}
          title={title}
          message={message}
          accentColor="rgb(239, 68, 68)"
          duration={duration}
        />
      ),
      { ...commonOptions, duration: 1500, ...options }
    )
  },

  warning: (message: string, title?: string, options = {}) => {
    const duration = (options as any).duration || commonOptions.duration
    toast.custom(
      (t) => (
        <CustomToast
          t={t}
          icon={ICONS.warning}
          title={title}
          message={message}
          accentColor="rgb(245, 158, 11)"
          duration={duration}
        />
      ),
      { ...commonOptions, ...options }
    )
  },

  info: (message: string, title?: string, options = {}) => {
    const duration = (options as any).duration || commonOptions.duration
    toast.custom(
      (t) => (
        <CustomToast
          t={t}
          icon={ICONS.info}
          title={title}
          message={message}
          accentColor="rgb(59, 130, 246)"
          duration={duration}
        />
      ),
      { ...commonOptions, ...options }
    )
  },

  loading: (message: string, title?: string, options = {}) => {
    return toast.custom(
      (t) => (
        <CustomToast
          t={t}
          icon={ICONS.loading}
          title={title}
          message={message}
          accentColor="hsl(var(--primary))"
          duration={Infinity}
        />
      ),
      { ...commonOptions, duration: Infinity, ...options }
    )
  },

  confirm: (message: string, onConfirm: () => void, options?: {
              title?: string
              onCancel?: () => void
              confirmLabel?: string
              cancelLabel?: string
              variant?: 'danger' | 'warning' | 'primary'
            }) => {
    toast.custom(
        (t) => (
            <ConfirmToast
                t={t}
                title={options?.title}
                message={message}
                onConfirm={onConfirm}
                onCancel={options?.onCancel}
                confirmLabel={options?.confirmLabel}
                cancelLabel={options?.cancelLabel}
                variant={options?.variant ?? 'danger'}
            />
        ),
        {...commonOptions, duration: Infinity}
    )
  },

  promise: <T,>(
    promise: Promise<T>,
    messages: {
      loading: string
      success: string | ((data: T) => string)
      error: string | ((error: any) => string)
    },
    titles?: {
      loading?: string
      success?: string
      error?: string
    },
    options = {}
  ) => {
    const loadingToast = alertas.loading(messages.loading, titles?.loading)

    promise
      .then((data) => {
        toast.dismiss(loadingToast)
        const successMsg = typeof messages.success === 'function'
          ? messages.success(data)
          : messages.success
        alertas.success(successMsg, titles?.success)
        return data
      })
      .catch((error) => {
        toast.dismiss(loadingToast)
        const errorMsg = typeof messages.error === 'function'
          ? messages.error(error)
          : messages.error
        alertas.error(errorMsg, titles?.error)
        throw error
      })

    return promise
  },

  dismiss: (toastId?: string) => {
    toast.dismiss(toastId)
  },

  dismissAll: () => {
    toast.dismiss()
  },
}

// Componente de confirmación
const ConfirmToast = ({
  t,
  title,
  message,
  onConfirm,
  onCancel,
  confirmLabel = 'Confirmar',
  cancelLabel = 'Cancelar',
  variant = 'danger',
}: {
  t: any
  title?: string
  message: string
  onConfirm: () => void
  onCancel?: () => void
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'danger' | 'warning' | 'primary'
}) => {
  const variantStyles = {
    danger: {
      icon: <i className="fa-solid fa-triangle-exclamation text-red-600 dark:text-red-400 text-lg"></i>,
      bg: 'bg-red-500/10 border-red-500/20',
      btn: 'bg-red-600 hover:bg-red-700 text-white',
    },
    warning: {
      icon: <i className="fa-solid fa-triangle-exclamation text-amber-600 dark:text-amber-400 text-lg"></i>,
      bg: 'bg-amber-500/10 border-amber-500/20',
      btn: 'bg-amber-500 hover:bg-amber-600 text-white',
    },
    primary: {
      icon: <i className="fa-solid fa-circle-question text-blue-600 dark:text-blue-400 text-lg"></i>,
      bg: 'bg-blue-500/10 border-blue-500/20',
      btn: 'bg-blue-600 hover:bg-blue-700 text-white',
    },
  }

  const styles = variantStyles[variant]

  const handleConfirm = () => {
    toast.dismiss(t.id)
    onConfirm()
  }

  const handleCancel = () => {
    toast.dismiss(t.id)
    onCancel?.()
  }

  return (
    <div
      className={`${
        t.visible ? 'animate-in slide-in-from-right-full' : 'animate-out slide-out-to-right-full'
      } max-w-md w-full bg-white dark:bg-neutral-900 shadow-lg rounded-xl border border-neutral-200 dark:border-neutral-800 pointer-events-auto overflow-hidden`}
    >
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0">
            <div className={`w-10 h-10 rounded-lg border flex items-center justify-center ${styles.bg}`}>
              {styles.icon}
            </div>
          </div>
          <div className="flex-1 min-w-0">
            {title && (
              <p className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
                {title}
              </p>
            )}
            <p className="text-sm text-neutral-600 dark:text-neutral-400 whitespace-pre-line">
              {message}
            </p>
            <div className="flex gap-2 mt-3">
              <button
                type="button"
                onClick={handleConfirm}
                className={`text-xs font-medium px-3 py-1.5 rounded-lg transition-colors ${styles.btn}`}
              >
                {confirmLabel}
              </button>
              <button
                type="button"
                onClick={handleCancel}
                className="text-xs font-medium px-3 py-1.5 rounded-lg border border-neutral-200 dark:border-neutral-700 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
              >
                {cancelLabel}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}