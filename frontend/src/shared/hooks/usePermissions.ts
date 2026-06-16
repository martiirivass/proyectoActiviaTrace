import { useAuth } from './useAuth'

export function usePermissions(): {
  hasPermission: (permission: string) => boolean
  hasAnyPermission: (permissions: string[]) => boolean
  permissions: string[]
} {
  const { permissions } = useAuth()

  const hasPermission = (permission: string): boolean => {
    return permissions.includes(permission)
  }

  const hasAnyPermission = (required: string[]): boolean => {
    return required.some((p) => permissions.includes(p))
  }

  return { hasPermission, hasAnyPermission, permissions }
}
