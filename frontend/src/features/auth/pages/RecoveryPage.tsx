import { Link } from 'react-router-dom'
import { RecoveryForm } from '@/features/auth/components/RecoveryForm'
import { Card } from '@/shared/components/ui/Card'

export default function RecoveryPage() {
  return (
    <div className="flex min-h-svh items-center justify-center bg-gray-50 px-4">
      <Card
        className="w-full max-w-md"
        header={<h1 className="text-xl font-semibold text-gray-900">Recuperar contraseña</h1>}
      >
        <RecoveryForm />
        <p className="mt-4 text-center text-sm text-gray-600">
          <Link to="/login" className="text-blue-600 hover:text-blue-800">
            Volver al inicio de sesión
          </Link>
        </p>
      </Card>
    </div>
  )
}
