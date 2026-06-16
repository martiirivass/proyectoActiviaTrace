import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '@/shared/hooks/useAuth'
import { Button } from '@/shared/components/ui/Button'

interface NavItem {
  label: string
  to: string
  requiredPermission?: string
}

interface NavSection {
  label: string
  items: NavItem[]
}

const defaultNavItems: NavItem[] = [
  { label: 'Dashboard', to: '/dashboard' },
  { label: 'Estructura Académica', to: '/estructura', requiredPermission: 'academica:read' },
  { label: 'Usuarios', to: '/usuarios', requiredPermission: 'usuarios:read' },
  { label: 'Auditoría', to: '/auditoria', requiredPermission: 'auditoria:read' },
]

const finanzasNavItems: NavItem[] = [
  { label: 'Liquidaciones', to: '/finanzas/liquidaciones', requiredPermission: 'liquidaciones:ver' },
  { label: 'Grilla Salarial', to: '/finanzas/grilla-salarial', requiredPermission: 'grilla-salarial:ver' },
  { label: 'Facturas', to: '/finanzas/facturas', requiredPermission: 'facturas:gestionar' },
]

const adminNavItems: NavItem[] = [
  { label: 'Estructura', to: '/admin/estructura', requiredPermission: 'estructura:gestionar' },
  { label: 'Usuarios', to: '/admin/usuarios', requiredPermission: 'usuarios:read' },
  { label: 'Auditoría', to: '/admin/auditoria', requiredPermission: 'auditoria:read' },
]

export function AppLayout() {
  const { user, logout, permissions } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const visibleDefaultItems = defaultNavItems.filter(
    (item) =>
      !item.requiredPermission || permissions.includes(item.requiredPermission),
  )

  const visibleFinanzasItems = finanzasNavItems.filter(
    (item) =>
      !item.requiredPermission || permissions.includes(item.requiredPermission),
  )

  const visibleAdminItems = adminNavItems.filter(
    (item) =>
      !item.requiredPermission || permissions.includes(item.requiredPermission),
  )

  const displayName =
    user?.nombre && user?.apellido
      ? `${user.nombre} ${user.apellido}`
      : user?.email ?? ''

  return (
    <div className="flex min-h-svh bg-gray-50">
      {/* Sidebar */}
      <aside
        className={`flex flex-col border-r border-gray-200 bg-white transition-all duration-200 ${
          sidebarOpen ? 'w-64' : 'w-16'
        }`}
      >
        {/* Sidebar header */}
        <div className="flex h-16 items-center justify-between border-b border-gray-200 px-4">
          {sidebarOpen && (
            <span className="text-lg font-bold text-gray-900">activia-trace</span>
          )}
          <button
            type="button"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="rounded-md p-1.5 text-gray-500 hover:bg-gray-100"
            aria-label={sidebarOpen ? 'Colapsar menú' : 'Expandir menú'}
          >
            {sidebarOpen ? '◀' : '▶'}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 overflow-y-auto p-3">
          {visibleDefaultItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-100'
                } ${!sidebarOpen ? 'justify-center' : ''}`
              }
              title={item.label}
            >
              <span className="text-lg">{getNavIcon(item.label)}</span>
              {sidebarOpen && <span>{item.label}</span>}
            </NavLink>
          ))}

          {sidebarOpen && visibleFinanzasItems.length > 0 && (
            <p className="mt-4 px-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
              Finanzas
            </p>
          )}
          {visibleFinanzasItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-100'
                } ${!sidebarOpen ? 'justify-center' : ''}`
              }
              title={item.label}
            >
              <span className="text-lg">{getNavIcon(item.label)}</span>
              {sidebarOpen && <span>{item.label}</span>}
            </NavLink>
          ))}

          {sidebarOpen && visibleAdminItems.length > 0 && (
            <p className="mt-4 px-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
              Admin
            </p>
          )}
          {visibleAdminItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-100'
                } ${!sidebarOpen ? 'justify-center' : ''}`
              }
              title={item.label}
            >
              <span className="text-lg">{getNavIcon(item.label)}</span>
              {sidebarOpen && <span>{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Sidebar footer */}
        {sidebarOpen && (
          <div className="border-t border-gray-200 p-4 text-xs text-gray-500">
            v0.1.0
          </div>
        )}
      </aside>

      {/* Main content */}
      <div className="flex flex-1 flex-col">
        {/* Header */}
        <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6">
          <div />
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-700">{displayName}</span>
            <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
              {user?.roles?.join(', ')}
            </span>
            <Button variant="ghost" size="sm" onClick={logout}>
              Cerrar sesión
            </Button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

function getNavIcon(label: string): string {
  const icons: Record<string, string> = {
    Dashboard: '📊',
    Liquidaciones: '💰',
    'Grilla Salarial': '📊',
    Facturas: '🧾',
    Estructura: '🏛',
    Usuarios: '👥',
    Auditoría: '📋',
    'Estructura Académica': '🏛',
  }
  return icons[label] ?? '•'
}
