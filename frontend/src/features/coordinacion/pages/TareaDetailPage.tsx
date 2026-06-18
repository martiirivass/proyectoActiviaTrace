import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card } from '@/shared/components/ui/Card'
import { Button } from '@/shared/components/ui/Button'
import { Spinner } from '@/shared/components/ui/Spinner'
import { TareaDelegarModal } from '@/features/coordinacion/components/TareaDelegarModal'
import {
  useTarea,
  useCambiarEstadoTarea,
  useComentariosTarea,
  useAgregarComentario,
} from '@/features/coordinacion/hooks/useTareas'
import type { TareaEstado } from '@/features/coordinacion/types'

export default function TareaDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: tarea, isLoading } = useTarea(id)
  const { data: comentarios } = useComentariosTarea(id)
  const changeEstado = useCambiarEstadoTarea()
  const addComment = useAgregarComentario()
  const [delegarOpen, setDelegarOpen] = useState(false)
  const [commentText, setCommentText] = useState('')

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Spinner />
      </div>
    )
  }

  if (!tarea) {
    return (
      <div className="py-8 text-center text-gray-500">
        Tarea no encontrada
        <br />
        <button
          type="button"
          className="mt-2 text-blue-600 hover:text-blue-800"
          onClick={() => navigate('/dashboard/coordinacion/tareas')}
        >
          Volver a tareas
        </button>
      </div>
    )
  }

  const estadosDisponibles: TareaEstado[] =
    tarea.estado === 'pendiente'
      ? ['en_curso', 'cancelada']
      : tarea.estado === 'en_curso'
        ? ['completada', 'cancelada']
        : []

  const handleSubmitComment = (e: React.FormEvent) => {
    e.preventDefault()
    if (!commentText.trim() || !id) return
    addComment.mutate(
      { tarea_id: id, contenido: commentText },
      { onSuccess: () => setCommentText('') },
    )
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">{tarea.titulo}</h2>
        <Button variant="secondary" size="sm" onClick={() => navigate('/dashboard/coordinacion/tareas')}>
          Volver
        </Button>
      </div>

      <Card>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">Estado:</span>{' '}
              <span className="text-gray-900">{tarea.estado}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Asignado a:</span>{' '}
              <span className="text-gray-900">{tarea.asignado_nombre}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Asignador:</span>{' '}
              <span className="text-gray-900">{tarea.asignador_nombre}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Materia:</span>{' '}
              <span className="text-gray-900">{tarea.materia_nombre ?? '—'}</span>
            </div>
          </div>
          <div className="border-t border-gray-200 pt-3">
            <p className="text-sm text-gray-700">{tarea.descripcion}</p>
          </div>
        </div>
      </Card>

      <div className="flex gap-2">
        {estadosDisponibles.map((estado) => (
          <Button
            key={estado}
            size="sm"
            variant="secondary"
            loading={changeEstado.isPending}
            onClick={() => id && changeEstado.mutate({ id, data: { estado } })}
          >
            Marcar como {estado}
          </Button>
        ))}
        <Button size="sm" variant="secondary" onClick={() => setDelegarOpen(true)}>
          Delegar
        </Button>
      </div>

      <Card header={<span className="font-medium text-gray-900">Comentarios</span>}>
        <div className="max-h-64 space-y-3 overflow-y-auto">
          {comentarios?.map((c) => (
            <div key={c.id} className="rounded-md bg-gray-50 p-3">
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span className="font-medium">{c.autor_nombre}</span>
                <span>{new Date(c.created_at).toLocaleString()}</span>
              </div>
              <p className="mt-1 text-sm text-gray-700">{c.contenido}</p>
            </div>
          ))}
          {(!comentarios || comentarios.length === 0) && (
            <p className="text-center text-sm text-gray-400">Sin comentarios</p>
          )}
        </div>
        <form onSubmit={handleSubmitComment} className="mt-3 flex gap-2">
          <input
            className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm"
            value={commentText}
            onChange={(e) => setCommentText(e.target.value)}
            placeholder="Escribir comentario..."
          />
          <Button type="submit" size="sm" loading={addComment.isPending}>
            Enviar
          </Button>
        </form>
      </Card>

      {delegarOpen && id && (
        <TareaDelegarModal tareaId={id} onClose={() => setDelegarOpen(false)} />
      )}
    </div>
  )
}
