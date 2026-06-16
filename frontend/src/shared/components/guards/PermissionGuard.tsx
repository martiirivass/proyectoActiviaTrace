import { type ReactNode } from 'react'
import { usePermissions } from '@/shared/hooks/usePermissions'
import { Alert } from '@/shared/components/ui/Alert'

interface PermissionGuardProps {
  requiredPermission: string
  children: ReactNode
  fallback?: ReactNode
}

export function PermissionGuard({
  requiredPermission,
  children,
  fallback,
}: PermissionGuardProps) {
  const { hasPermission } = usePermissions()

  if (hasPermission(requiredPermission)) {
    return <>{children}</>
  }

  if (fallback) {
    return <>{fallback}</>
  }

  return (
    <div className="flex min-h-64 items-center justify-center p-8">
      <Alert
        variant="warning"
        message="No tienes permisos suficientes para acceder a esta sección."
      />
    </div>
  )
}
