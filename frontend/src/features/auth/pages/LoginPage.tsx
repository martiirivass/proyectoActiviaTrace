import { LoginForm } from '@/features/auth/components/LoginForm'
import { Card } from '@/shared/components/ui/Card'

export default function LoginPage() {
  return (
    <div className="flex min-h-svh items-center justify-center bg-gray-50 px-4">
      <Card
        className="w-full max-w-md"
        header={<h1 className="text-xl font-semibold text-gray-900">Iniciar sesión</h1>}
      >
        <LoginForm />
      </Card>
    </div>
  )
}
