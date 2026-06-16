import { useState } from 'react'
import { Button } from '@/shared/components/ui/Button'
import { Input } from '@/shared/components/ui/Input'

interface FiltrosUsuariosProps {
  onFilter: (search: string, rol: string, activo: boolean | undefined) => void
}

export function FiltrosUsuarios({ onFilter }: FiltrosUsuariosProps) {
  const [search, setSearch] = useState('')
  const [rol, setRol] = useState('')
  const [activo, setActivo] = useState<string>('true')

  const handleFilter = () => {
    onFilter(
      search,
      rol,
      activo === '' ? undefined : activo === 'true',
    )
  }

  return (
    <div className="flex flex-wrap items-end gap-4 rounded-lg border border-gray-200 bg-white p-4">
      <Input
        label="Buscar (email, nombre, apellido, DNI)"
        placeholder="Buscar..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-gray-700">Rol</label>
        <select
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={rol}
          onChange={(e) => setRol(e.target.value)}
        >
          <option value="">Todos</option>
          <option value="ALUMNO">ALUMNO</option>
          <option value="TUTOR">TUTOR</option>
          <option value="PROFESOR">PROFESOR</option>
          <option value="COORDINADOR">COORDINADOR</option>
          <option value="NEXO">NEXO</option>
          <option value="ADMIN">ADMIN</option>
          <option value="FINANZAS">FINANZAS</option>
        </select>
      </div>
      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-gray-700">Estado</label>
        <select
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={activo}
          onChange={(e) => setActivo(e.target.value)}
        >
          <option value="true">Activos</option>
          <option value="false">Inactivos</option>
          <option value="">Todos</option>
        </select>
      </div>
      <Button onClick={handleFilter}>Filtrar</Button>
    </div>
  )
}
