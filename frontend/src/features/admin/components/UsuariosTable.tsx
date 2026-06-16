import type { Usuario, PaginatedResponse } from '@/features/admin/types'
import { Button } from '@/shared/components/ui/Button'

interface UsuariosTableProps {
  data: PaginatedResponse<Usuario> | undefined
  onEdit: (item: Usuario) => void
  onDelete: (id: string) => void
  onPageChange: (page: number) => void
}

export function UsuariosTable({ data, onEdit, onDelete, onPageChange }: UsuariosTableProps) {
  if (!data || data.items.length === 0) {
    return <p className="py-8 text-center text-gray-500">No hay usuarios registrados</p>
  }

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Email</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Nombre</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Apellido</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">DNI</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Roles</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Regional</th>
              <th className="px-4 py-3 text-center font-medium text-gray-600">Facturador</th>
              <th className="px-4 py-3 text-center font-medium text-gray-600">Estado</th>
              <th className="px-4 py-3 text-center font-medium text-gray-600" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.items.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50">
                <td className="px-4 py-3">{user.email}</td>
                <td className="px-4 py-3">{user.nombre}</td>
                <td className="px-4 py-3">{user.apellido}</td>
                <td className="px-4 py-3">{user.dni}</td>
                <td className="px-4 py-3">{user.roles.join(', ')}</td>
                <td className="px-4 py-3">{user.regional ?? '—'}</td>
                <td className="px-4 py-3 text-center">{user.facturador ? 'Sí' : 'No'}</td>
                <td className="px-4 py-3 text-center">
                  <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                    user.activo ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                  }`}>
                    {user.activo ? 'Activo' : 'Inactivo'}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  <div className="flex justify-center gap-2">
                    <Button variant="ghost" size="sm" onClick={() => onEdit(user)}>Editar</Button>
                    <Button variant="ghost" size="sm" onClick={() => onDelete(user.id)}>Eliminar</Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Página {data.page} de {data.total_pages} ({data.total} registros)
          </p>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" disabled={data.page <= 1} onClick={() => onPageChange(data.page - 1)}>
              Anterior
            </Button>
            <Button variant="secondary" size="sm" disabled={data.page >= data.total_pages} onClick={() => onPageChange(data.page + 1)}>
              Siguiente
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
