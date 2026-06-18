import { AtrasadosTable } from '@/features/academico/components/AtrasadosTable'

export default function AtrasadosPage() {
  return (
    <div>
      <h2 className="mb-4 text-lg font-semibold text-gray-900">
        Alumnos atrasados
      </h2>
      <AtrasadosTable />
    </div>
  )
}
