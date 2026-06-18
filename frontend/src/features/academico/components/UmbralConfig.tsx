import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Button } from '@/shared/components/ui/Button'
import { Spinner } from '@/shared/components/ui/Spinner'
import { Alert } from '@/shared/components/ui/Alert'
import { UmbralSlider } from './UmbralSlider'
import {
  useUmbral,
  useUpdateUmbral,
  useRecalcularUmbral,
} from '@/features/academico/hooks/useUmbral'

export function UmbralConfig() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const { data: umbral, isLoading, isError, refetch } = useUmbral(materiaId ?? '')
  const updateMutation = useUpdateUmbral()
  const recalcularMutation = useRecalcularUmbral()

  const [umbralPct, setUmbralPct] = useState(60)
  const [valoresTextuales, setValoresTextuales] = useState<string[]>([])
  const [nuevoValor, setNuevoValor] = useState('')
  const [sliderError, setSliderError] = useState<string | null>(null)

  useEffect(() => {
    if (umbral) {
      setUmbralPct(umbral.umbral_pct)
      setValoresTextuales(umbral.valores_aprobatorios)
    }
  }, [umbral])

  const handleSave = () => {
    if (umbralPct < 0 || umbralPct > 100) {
      setSliderError('El umbral debe estar entre 0 y 100')
      return
    }
    if (!materiaId) return
    setSliderError(null)
    updateMutation.mutate({
      materia_id: materiaId,
      umbral_pct: umbralPct,
      valores_aprobatorios: valoresTextuales,
    })
  }

  const handleRecalcular = () => {
    if (!materiaId) return
    recalcularMutation.mutate(materiaId)
  }

  const agregarValor = () => {
    const trimmed = nuevoValor.trim()
    if (trimmed && !valoresTextuales.includes(trimmed)) {
      setValoresTextuales([...valoresTextuales, trimmed])
      setNuevoValor('')
    }
  }

  const eliminarValor = (valor: string) => {
    setValoresTextuales(valoresTextuales.filter((v) => v !== valor))
  }

  if (isLoading) {
    return (
      <div className="flex min-h-64 items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }

  if (isError) {
    return (
      <Alert variant="error" message="Error al cargar la configuración del umbral.">
        <button
          type="button"
          onClick={() => refetch()}
          className="mt-2 text-sm font-medium underline"
        >
          Reintentar
        </button>
      </Alert>
    )
  }

  return (
    <div className="max-w-lg space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">
        Configuración de umbral
      </h2>

      <UmbralSlider
        value={umbralPct}
        onChange={(v) => {
          setUmbralPct(v)
          setSliderError(null)
        }}
        error={sliderError}
      />

      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-700">
          Valores textuales aprobatorios
        </label>
        <div className="flex flex-wrap gap-2">
          {valoresTextuales.map((v) => (
            <span
              key={v}
              className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-3 py-1 text-sm text-blue-800"
            >
              {v}
              <button
                type="button"
                onClick={() => eliminarValor(v)}
                className="ml-1 text-blue-600 hover:text-blue-800"
                aria-label={`Eliminar ${v}`}
              >
                ✕
              </button>
            </span>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={nuevoValor}
            onChange={(e) => setNuevoValor(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') agregarValor()
            }}
            placeholder="Ej: Satisfactorio"
            className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
          <Button variant="secondary" size="sm" onClick={agregarValor}>
            Agregar
          </Button>
        </div>
      </div>

      <div className="flex gap-3">
        <Button onClick={handleSave} loading={updateMutation.isPending}>
          Guardar
        </Button>
        <Button
          variant="secondary"
          onClick={handleRecalcular}
          loading={recalcularMutation.isPending}
        >
          Recalcular aprobados
        </Button>
      </div>

      {updateMutation.isSuccess && (
        <Alert variant="success" message="Umbral actualizado correctamente." />
      )}
      {updateMutation.isError && (
        <Alert
          variant="error"
          message={updateMutation.error?.message ?? 'Error al guardar el umbral.'}
        />
      )}
      {recalcularMutation.isSuccess && (
        <Alert
          variant="success"
          message="Cálculo de aprobados actualizado."
        />
      )}
    </div>
  )
}
