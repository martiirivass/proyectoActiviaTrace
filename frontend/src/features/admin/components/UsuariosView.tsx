import { useState, useCallback } from 'react'
import { FiltrosUsuarios } from './FiltrosUsuarios'
import { UsuariosTable } from './UsuariosTable'
import { UsuarioFormModal } from './UsuarioFormModal'
import { ConfirmDeleteModal } from '@/features/finanzas/components/ConfirmDeleteModal'
import { useUsuarios, useCreateUsuario, useUpdateUsuario, useDeleteUsuario } from '@/features/admin/hooks/useUsuarios'
import type { Usuario, UsuarioFormData } from '@/features/admin/types'
import { Spinner } from '@/shared/components/ui/Spinner'
import { Alert } from '@/shared/components/ui/Alert'
import { Button } from '@/shared/components/ui/Button'

export function UsuariosView() {
  const [filtros, setFiltros] = useState<{ search?: string; rol?: string; activo?: boolean }>({ activo: true })
  const [page, setPage] = useState(1)
  const { data, isLoading, error } = useUsuarios({ ...filtros, page, per_page: 20 })
  const createMutation = useCreateUsuario()
  const updateMutation = useUpdateUsuario()
  const deleteMutation = useDeleteUsuario()

  const [showForm, setShowForm] = useState(false)
  const [editingUsuario, setEditingUsuario] = useState<Usuario | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const handleFilter = useCallback((search: string, rol: string, activo: boolean | undefined) => {
    const f: { search?: string; rol?: string; activo?: boolean } = {}
    if (search) f.search = search
    if (rol) f.rol = rol
    if (activo !== undefined) f.activo = activo
    setFiltros(f)
    setPage(1)
  }, [])

  const handleSave = (formData: UsuarioFormData) => {
    if (editingUsuario) {
      updateMutation.mutate({ id: editingUsuario.id, data: formData }, {
        onSuccess: () => { setShowForm(false); setEditingUsuario(null) },
      })
    } else {
      createMutation.mutate(formData, {
        onSuccess: () => { setShowForm(false); setEditingUsuario(null) },
      })
    }
  }

  const handleConfirmDelete = useCallback(() => {
    if (!deletingId) return
    deleteMutation.mutate(deletingId, { onSuccess: () => setDeletingId(null) })
  }, [deletingId, deleteMutation])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Usuarios</h1>
        <Button onClick={() => { setEditingUsuario(null); setShowForm(true) }}>
          Nuevo Usuario
        </Button>
      </div>

      <FiltrosUsuarios onFilter={handleFilter} />

      {isLoading && <div className="flex justify-center py-8"><Spinner /></div>}
      {error && <Alert variant="error" message="Error al cargar usuarios" />}

      {!isLoading && !error && (
        <UsuariosTable
          data={data}
          onEdit={(item) => { setEditingUsuario(item); setShowForm(true) }}
          onDelete={(id) => setDeletingId(id)}
          onPageChange={(p) => setPage(p)}
        />
      )}

      {showForm && (
        <UsuarioFormModal
          item={editingUsuario}
          onSave={handleSave}
          onClose={() => { setShowForm(false); setEditingUsuario(null) }}
          loading={createMutation.isPending || updateMutation.isPending}
        />
      )}

      {deletingId && (
        <ConfirmDeleteModal
          message="¿Estás seguro de eliminar este usuario? Se realizará un soft delete."
          onConfirm={handleConfirmDelete}
          onCancel={() => setDeletingId(null)}
          loading={deleteMutation.isPending}
        />
      )}
    </div>
  )
}
