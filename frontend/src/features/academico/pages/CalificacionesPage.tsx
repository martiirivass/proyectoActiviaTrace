import { ImportWizard } from '@/features/academico/components/ImportWizard/ImportWizard'

export default function CalificacionesPage() {
  return (
    <div>
      <h2 className="mb-4 text-lg font-semibold text-gray-900">
        Importar calificaciones
      </h2>
      <ImportWizard />
    </div>
  )
}
