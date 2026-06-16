import { NavLink } from 'react-router-dom'

const tabs = [
  { label: 'Calificaciones', path: 'calificaciones' },
  { label: 'Umbral', path: 'umbral' },
  { label: 'Atrasados', path: 'atrasados' },
  { label: 'Ranking', path: 'ranking' },
  { label: 'Notas Finales', path: 'notas' },
  { label: 'Reportes', path: 'reportes' },
  { label: 'Comunicaciones', path: 'comunicaciones' },
]

export function ComisionTabs() {
  return (
    <nav className="mb-6 flex flex-wrap gap-1 border-b border-gray-200">
      {tabs.map((tab) => (
        <NavLink
          key={tab.path}
          to={tab.path}
          end
          className={({ isActive }) =>
            `px-4 py-2 text-sm font-medium transition-colors ${
              isActive
                ? 'border-b-2 border-blue-600 text-blue-700'
                : 'text-gray-600 hover:text-gray-900'
            }`
          }
        >
          {tab.label}
        </NavLink>
      ))}
    </nav>
  )
}
