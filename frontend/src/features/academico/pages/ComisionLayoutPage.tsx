import { useEffect } from 'react'
import { Outlet, useParams, useNavigate } from 'react-router-dom'
import { ComisionTabs } from '@/features/academico/components/ComisionTabs'
import { useComisiones } from '@/features/academico/hooks/useComisiones'
import { Spinner } from '@/shared/components/ui/Spinner'
import { Alert } from '@/shared/components/ui/Alert'

export default function ComisionLayoutPage() {
  const { materiaId, cohorteId } = useParams<{
    materiaId: string
    cohorteId: string
  }>()
  const navigate = useNavigate()
  const { data: comisiones, isLoading, isError } = useComisiones()

  const comision = comisiones?.find(
    (c) => c.materia_id === materiaId && c.cohorte_id === cohorteId,
  )

  useEffect(() => {
    if (!isLoading && !comision) return
  }, [isLoading, comision])

  if (isLoading) {
    return (
      <div className="flex min-h-64 items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }

  if (isError || !comision) {
    return (
      <Alert variant="error" message="Comisión no encontrada.">
        <button
          type="button"
          onClick={() => navigate('/dashboard')}
          className="mt-2 text-sm font-medium underline"
        >
          Volver al dashboard
        </button>
      </Alert>
    )
  }

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-xl font-bold text-gray-900">
          {comision.materia_nombre}
        </h1>
        <p className="text-sm text-gray-500">
          Cohorte: {comision.cohorte_nombre}
        </p>
      </div>
      <ComisionTabs />
      <Outlet />
    </div>
  )
}
