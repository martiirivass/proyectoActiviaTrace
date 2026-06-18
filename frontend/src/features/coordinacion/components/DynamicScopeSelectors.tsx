import type { AlcanceAviso } from '@/features/coordinacion/types'

interface DynamicScopeSelectorsProps {
  alcance: AlcanceAviso
  scopeId: string
  onScopeIdChange: (value: string) => void
}

export function DynamicScopeSelectors({
  alcance,
  scopeId,
  onScopeIdChange,
}: DynamicScopeSelectorsProps) {
  if (alcance === 'Global') {
    return <p className="text-sm text-gray-500">El aviso será visible para todos los usuarios</p>
  }

  const label =
    alcance === 'PorMateria'
      ? 'Seleccionar Materia'
      : alcance === 'PorCohorte'
        ? 'Seleccionar Cohorte'
        : 'Seleccionar Rol'

  const placeholder =
    alcance === 'PorMateria'
      ? 'ID de materia'
      : alcance === 'PorCohorte'
        ? 'ID de cohorte'
        : 'Nombre del rol'

  return (
    <div>
      <label className="text-sm font-medium text-gray-700">{label}</label>
      <input
        className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        value={scopeId}
        onChange={(e) => onScopeIdChange(e.target.value)}
        placeholder={placeholder}
      />
    </div>
  )
}
