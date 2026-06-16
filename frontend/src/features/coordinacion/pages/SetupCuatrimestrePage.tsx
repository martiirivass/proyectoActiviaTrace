import { useState } from 'react'
import { Card } from '@/shared/components/ui/Card'
import { Button } from '@/shared/components/ui/Button'
import { Alert } from '@/shared/components/ui/Alert'
import {
  useCreateCohorte,
  useClonarEquipoSetup,
  useAsignacionMasivaSetup,
  useUploadPrograma,
  useCargarFechas,
  usePublicarAvisoSetup,
} from '@/features/coordinacion/hooks/useSetup'

interface WizardState {
  step: number
  cohorte: {
    identifier: string
    name: string
    vigencia_desde: string
    vigencia_hasta: string
  }
  clone: {
    origen_materia_id: string
    origen_carrera_id: string
    origen_cohorte_id: string
  }
  asignaciones: string
  programas: Array<{ materia_id: string; file: File | null; filename: string }>
  fechas: Array<{ materia_id: string; fecha: string; descripcion: string }>
  aviso: { titulo: string; contenido: string }
}

const initialState: WizardState = {
  step: 1,
  cohorte: { identifier: '', name: '', vigencia_desde: '', vigencia_hasta: '' },
  clone: { origen_materia_id: '', origen_carrera_id: '', origen_cohorte_id: '' },
  asignaciones: '',
  programas: [{ materia_id: '', file: null, filename: '' }],
  fechas: [{ materia_id: '', fecha: '', descripcion: '' }],
  aviso: { titulo: '', contenido: '' },
}

export default function SetupCuatrimestrePage() {
  const [state, setState] = useState<WizardState>(initialState)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const createCohorte = useCreateCohorte()
  const cloneEquipo = useClonarEquipoSetup()
  const asignacionMasiva = useAsignacionMasivaSetup()
  const uploadPrograma = useUploadPrograma()
  const cargarFechas = useCargarFechas()
  const publicarAviso = usePublicarAvisoSetup()

  const update = (partial: Partial<WizardState>) =>
    setState((s) => ({ ...s, ...partial }))

  const isLastStep = state.step === 7

  const nextStep = () => {
    if (state.step < 7) update({ step: state.step + 1 })
  }

  const prevStep = () => {
    if (state.step > 1) update({ step: state.step - 1 })
  }

  const handleFinish = async () => {
    setSubmitting(true)
    setError(null)
    try {
      const cohorteResult = await createCohorte.mutateAsync(state.cohorte)

      if (state.clone.origen_materia_id) {
        await cloneEquipo.mutateAsync({
          ...state.clone,
          destino_cohorte_id: cohorteResult.id,
        })
      }

      if (state.asignaciones.trim()) {
        const ids = state.asignaciones.split(',').map((s) => s.trim()).filter(Boolean)
        await asignacionMasiva.mutateAsync({
          docentes_ids: ids,
          materia_id: '',
          carrera_id: '',
          cohorte_id: cohorteResult.id,
          rol: 'PROFESOR',
          vigencia_desde: state.cohorte.vigencia_desde,
          vigencia_hasta: state.cohorte.vigencia_hasta,
        })
      }

      for (const prog of state.programas) {
        if (prog.file) {
          await uploadPrograma.mutateAsync({
            materia_id: prog.materia_id,
            cohorte_id: cohorteResult.id,
            file: prog.file,
          })
        }
      }

      if (state.fechas.some((f) => f.fecha)) {
        const fechasValidas = state.fechas.filter((f) => f.fecha)
        await cargarFechas.mutateAsync(
          fechasValidas.map((f) => ({
            materia_id: f.materia_id,
            fecha: f.fecha,
            descripcion: f.descripcion,
          })),
        )
      }

      if (state.aviso.titulo) {
        await publicarAviso.mutateAsync({
          titulo: state.aviso.titulo,
          contenido: state.aviso.contenido,
          alcance: 'PorCohorte',
          scope_id: cohorteResult.id,
          severidad: 'baja',
          vigencia_inicio: state.cohorte.vigencia_desde,
          vigencia_fin: state.cohorte.vigencia_hasta,
          orden: 0,
          requiere_ack: false,
        })
      }

      setSuccess(true)
    } catch {
      setError('Error al ejecutar el setup. Revise los datos e intente nuevamente.')
    } finally {
      setSubmitting(false)
    }
  }

  if (success) {
    return (
      <div className="mx-auto max-w-2xl py-12">
        <Alert
          variant="success"
          message="Setup de cuatrimestre completado exitosamente."
        >
          <Button
            className="mt-4"
            onClick={() => {
              setState(initialState)
              setSuccess(false)
            }}
          >
            Nuevo Setup
          </Button>
        </Alert>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">
          Setup de Cuatrimestre
        </h2>
        <span className="text-sm text-gray-500">
          Paso {state.step} de 7
        </span>
      </div>

      <div className="flex gap-1">
        {[1, 2, 3, 4, 5, 6, 7].map((s) => (
          <div
            key={s}
            className={`h-2 flex-1 rounded-full ${
              s <= state.step ? 'bg-blue-600' : 'bg-gray-200'
            }`}
          />
        ))}
      </div>

      {error && <Alert variant="error" message={error} onDismiss={() => setError(null)} />}

      <Card>
        {state.step === 1 && (
          <div className="space-y-4">
            <h3 className="text-base font-medium text-gray-800">
              Paso 1: Crear Cohortes
            </h3>
            <div>
              <label className="text-sm font-medium text-gray-700">Identificador</label>
              <input
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={state.cohorte.identifier}
                onChange={(e) =>
                  update({ cohorte: { ...state.cohorte, identifier: e.target.value } })
                }
                placeholder="Ej: 2026-2C"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Nombre</label>
              <input
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={state.cohorte.name}
                onChange={(e) =>
                  update({ cohorte: { ...state.cohorte, name: e.target.value } })
                }
                placeholder="Ej: Segundo Cuatrimestre 2026"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700">Vigencia desde</label>
                <input
                  type="date"
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  value={state.cohorte.vigencia_desde}
                  onChange={(e) =>
                    update({ cohorte: { ...state.cohorte, vigencia_desde: e.target.value } })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Vigencia hasta</label>
                <input
                  type="date"
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  value={state.cohorte.vigencia_hasta}
                  onChange={(e) =>
                    update({ cohorte: { ...state.cohorte, vigencia_hasta: e.target.value } })
                  }
                />
              </div>
            </div>
          </div>
        )}

        {state.step === 2 && (
          <div className="space-y-4">
            <h3 className="text-base font-medium text-gray-800">
              Paso 2: Clonar Equipo Docente
            </h3>
            <p className="text-sm text-gray-600">
              Selecciona el equipo origen para clonar las asignaciones al nuevo período.
            </p>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700">Materia ID (origen)</label>
                <input
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  value={state.clone.origen_materia_id}
                  onChange={(e) =>
                    update({ clone: { ...state.clone, origen_materia_id: e.target.value } })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Carrera ID (origen)</label>
                <input
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  value={state.clone.origen_carrera_id}
                  onChange={(e) =>
                    update({ clone: { ...state.clone, origen_carrera_id: e.target.value } })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Cohorte ID (origen)</label>
                <input
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  value={state.clone.origen_cohorte_id}
                  onChange={(e) =>
                    update({ clone: { ...state.clone, origen_cohorte_id: e.target.value } })
                  }
                />
              </div>
            </div>
          </div>
        )}

        {state.step === 3 && (
          <div className="space-y-4">
            <h3 className="text-base font-medium text-gray-800">
              Paso 3: Ajustar Asignaciones
            </h3>
            <p className="text-sm text-gray-600">
              Ingresa IDs de docentes para asignaciones faltantes (separados por coma).
            </p>
            <div>
              <label className="text-sm font-medium text-gray-700">IDs de Docentes</label>
              <textarea
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                rows={3}
                value={state.asignaciones}
                onChange={(e) => update({ asignaciones: e.target.value })}
                placeholder="docente-id-1, docente-id-2, ..."
              />
            </div>
          </div>
        )}

        {state.step === 4 && (
          <div className="space-y-4">
            <h3 className="text-base font-medium text-gray-800">
              Paso 4: Cargar Programas
            </h3>
            <p className="text-sm text-gray-600">
              Sube los programas por materia y cohorte.
            </p>
            {state.programas.map((prog, idx) => (
              <div key={idx} className="flex items-end gap-2">
                <div className="flex-1">
                  <label className="text-sm font-medium text-gray-700">Materia ID</label>
                  <input
                    className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                    value={prog.materia_id}
                    onChange={(e) => {
                      const updated = [...state.programas]
                      updated[idx] = { ...updated[idx], materia_id: e.target.value }
                      update({ programas: updated })
                    }}
                  />
                </div>
                <div className="flex-1">
                  <label className="text-sm font-medium text-gray-700">Archivo</label>
                  <input
                    type="file"
                    className="mt-1 w-full text-sm"
                    onChange={(e) => {
                      const file = e.target.files?.[0] ?? null
                      const updated = [...state.programas]
                      updated[idx] = { ...updated[idx], file, filename: file?.name ?? '' }
                      update({ programas: updated })
                    }}
                  />
                </div>
                {state.programas.length > 1 && (
                  <Button
                    type="button"
                    variant="danger"
                    size="sm"
                    onClick={() => {
                      const updated = state.programas.filter((_, i) => i !== idx)
                      update({ programas: updated.length ? updated : [{ materia_id: '', file: null, filename: '' }] })
                    }}
                  >
                    ×
                  </Button>
                )}
              </div>
            ))}
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() =>
                update({
                  programas: [...state.programas, { materia_id: '', file: null, filename: '' }],
                })
              }
            >
              + Agregar Programa
            </Button>
          </div>
        )}

        {state.step === 5 && (
          <div className="space-y-4">
            <h3 className="text-base font-medium text-gray-800">
              Paso 5: Cargar Fechas de Evaluaciones
            </h3>
            {state.fechas.map((f, idx) => (
              <div key={idx} className="flex gap-2">
                <div className="flex-1">
                  <label className="text-sm font-medium text-gray-700">Materia ID</label>
                  <input
                    className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                    value={f.materia_id}
                    onChange={(e) => {
                      const updated = [...state.fechas]
                      updated[idx] = { ...updated[idx], materia_id: e.target.value }
                      update({ fechas: updated })
                    }}
                  />
                </div>
                <div className="flex-1">
                  <label className="text-sm font-medium text-gray-700">Fecha</label>
                  <input
                    type="date"
                    className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                    value={f.fecha}
                    onChange={(e) => {
                      const updated = [...state.fechas]
                      updated[idx] = { ...updated[idx], fecha: e.target.value }
                      update({ fechas: updated })
                    }}
                  />
                </div>
                <div className="flex-1">
                  <label className="text-sm font-medium text-gray-700">Descripción</label>
                  <input
                    className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                    value={f.descripcion}
                    onChange={(e) => {
                      const updated = [...state.fechas]
                      updated[idx] = { ...updated[idx], descripcion: e.target.value }
                      update({ fechas: updated })
                    }}
                    placeholder="Ej: Parcial 1"
                  />
                </div>
                {state.fechas.length > 1 && (
                  <Button
                    type="button"
                    variant="danger"
                    size="sm"
                    className="mt-6"
                    onClick={() => {
                      const updated = state.fechas.filter((_, i) => i !== idx)
                      update({ fechas: updated.length ? updated : [{ materia_id: '', fecha: '', descripcion: '' }] })
                    }}
                  >
                    ×
                  </Button>
                )}
              </div>
            ))}
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() =>
                update({
                  fechas: [...state.fechas, { materia_id: '', fecha: '', descripcion: '' }],
                })
              }
            >
              + Agregar Fecha
            </Button>
          </div>
        )}

        {state.step === 6 && (
          <div className="space-y-4">
            <h3 className="text-base font-medium text-gray-800">
              Paso 6: Publicar Aviso de Bienvenida
            </h3>
            <p className="text-sm text-gray-600">
              Crea un aviso de bienvenida que será scoped a la nueva cohorte.
            </p>
            <div>
              <label className="text-sm font-medium text-gray-700">Título</label>
              <input
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={state.aviso.titulo}
                onChange={(e) => update({ aviso: { ...state.aviso, titulo: e.target.value } })}
                placeholder="Ej: ¡Bienvenidos al nuevo cuatrimestre!"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Contenido</label>
              <textarea
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                rows={4}
                value={state.aviso.contenido}
                onChange={(e) => update({ aviso: { ...state.aviso, contenido: e.target.value } })}
                placeholder="Mensaje de bienvenida..."
              />
            </div>
          </div>
        )}

        {state.step === 7 && (
          <div className="space-y-4">
            <h3 className="text-base font-medium text-gray-800">Confirmación</h3>
            <p className="text-sm text-gray-600">
              Revisa el resumen antes de aplicar todos los cambios.
            </p>
            <div className="rounded-md bg-gray-50 p-4 text-sm space-y-2">
              <p><strong>Cohorte:</strong> {state.cohorte.identifier} — {state.cohorte.name}</p>
              <p><strong>Vigencia:</strong> {state.cohorte.vigencia_desde} → {state.cohorte.vigencia_hasta}</p>
              {state.clone.origen_materia_id && (
                <p><strong>Clonar desde:</strong> Mat {state.clone.origen_materia_id} / Carr {state.clone.origen_carrera_id} / Coh {state.clone.origen_cohorte_id}</p>
              )}
              {state.asignaciones && <p><strong>Asignaciones masivas:</strong> {state.asignaciones}</p>}
              <p><strong>Programas a cargar:</strong> {state.programas.filter((p) => p.file).length}</p>
              <p><strong>Fechas de evaluación:</strong> {state.fechas.filter((f) => f.fecha).length}</p>
              {state.aviso.titulo && <p><strong>Aviso:</strong> {state.aviso.titulo}</p>}
            </div>
          </div>
        )}
      </Card>

      <div className="flex justify-between">
        <Button
          variant="secondary"
          onClick={prevStep}
          disabled={state.step === 1}
        >
          Anterior
        </Button>
        {isLastStep ? (
          <Button onClick={handleFinish} loading={submitting}>
            Finalizar
          </Button>
        ) : (
          <Button onClick={nextStep}>Siguiente</Button>
        )}
      </div>
    </div>
  )
}
