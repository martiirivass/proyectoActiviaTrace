import { Spinner } from '@/shared/components/ui/Spinner'
import { Alert } from '@/shared/components/ui/Alert'
import { ComisionCard } from './ComisionCard'
import { useComisiones } from '@/features/academico/hooks/useComisiones'

export function DocenteDashboard() {
  const { data: comisiones, isLoading, isError, refetch } = useComisiones()

  if (isLoading) {
    return (
      <div className="flex min-h-64 items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }

  if (isError) {
    return (
      <Alert
        variant="error"
        message="Error al cargar las comisiones. Intente nuevamente."
      >
        <button
          type="button"
          onClick={() => refetch()}
          className="mt-2 text-sm font-medium text-red-800 underline hover:text-red-900"
        >
          Reintentar
        </button>
      </Alert>
    )
  }

  if (!comisiones || comisiones.length === 0) {
    return (
      <div className="flex min-h-64 items-center justify-center">
        <div className="text-center">
          <p className="text-lg text-gray-500">
            No tienes comisiones asignadas actualmente.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-gray-900">
        Mis Comisiones
      </h1>
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {comisiones.map((c) => (
          <ComisionCard
            key={`${c.materia_id}-${c.cohorte_id}`}
            comision={c}
          />
        ))}
      </div>
    </div>
  )
}
