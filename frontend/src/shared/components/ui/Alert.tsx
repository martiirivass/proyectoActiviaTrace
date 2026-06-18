import { type ReactNode } from 'react'

type AlertVariant = 'error' | 'success' | 'warning' | 'info'

interface AlertProps {
  variant?: AlertVariant
  message: string
  onDismiss?: () => void
  children?: ReactNode
}

const variantStyles: Record<AlertVariant, string> = {
  error: 'bg-red-50 border-red-300 text-red-800',
  success: 'bg-green-50 border-green-300 text-green-800',
  warning: 'bg-yellow-50 border-yellow-300 text-yellow-800',
  info: 'bg-blue-50 border-blue-300 text-blue-800',
}

export function Alert({
  variant = 'error',
  message,
  onDismiss,
  children,
}: AlertProps) {
  return (
    <div
      className={`flex items-start gap-3 rounded-md border p-4 text-sm ${variantStyles[variant]}`}
      role="alert"
    >
      <div className="flex-1">
        <p>{message}</p>
        {children}
      </div>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="ml-auto cursor-pointer text-current opacity-70 hover:opacity-100"
          aria-label="Cerrar"
        >
          ✕
        </button>
      )}
    </div>
  )
}
