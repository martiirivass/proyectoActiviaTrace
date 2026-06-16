import { ResetPasswordForm } from '@/features/auth/components/ResetPasswordForm'
import { Card } from '@/shared/components/ui/Card'

export default function ResetPasswordPage() {
  return (
    <div className="flex min-h-svh items-center justify-center bg-gray-50 px-4">
      <Card
        className="w-full max-w-md"
        header={<h1 className="text-xl font-semibold text-gray-900">Restablecer contraseña</h1>}
      >
        <ResetPasswordForm />
      </Card>
    </div>
  )
}
