import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRecovery } from '@/features/auth/hooks/useRecovery'
import { Button } from '@/shared/components/ui/Button'
import { Input } from '@/shared/components/ui/Input'
import { Alert } from '@/shared/components/ui/Alert'
import { useSearchParams } from 'react-router-dom'

const resetSchema = z
  .object({
    password: z
      .string()
      .min(8, 'La contraseña debe tener al menos 8 caracteres'),
    confirmPassword: z.string().min(1, 'Debe confirmar la contraseña'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Las contraseñas no coinciden',
    path: ['confirmPassword'],
  })

type ResetFormData = z.infer<typeof resetSchema>

export function ResetPasswordForm() {
  const { reset } = useRecovery()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetFormData>({
    resolver: zodResolver(resetSchema),
  })

  const onSubmit = (data: ResetFormData) => {
    if (!token) return
    reset.mutate({ token, password: data.password })
  }

  if (!token) {
    return (
      <Alert variant="error" message="Token de recuperación no encontrado.">
        <a
          href="/recuperar"
          className="mt-2 inline-block text-sm text-blue-600 hover:text-blue-800"
        >
          Solicitar nuevo enlace
        </a>
      </Alert>
    )
  }

  if (reset.isSuccess) {
    return (
      <Alert variant="success" message="Contraseña restablecida exitosamente.">
        <a
          href="/login"
          className="mt-2 inline-block text-sm text-blue-600 hover:text-blue-800"
        >
          Ir a iniciar sesión
        </a>
      </Alert>
    )
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5">
      {reset.isError && (
        <Alert
          variant="error"
          message={
            reset.error?.message ?? 'Token inválido o expirado'
          }
        />
      )}

      <p className="text-sm text-gray-600">
        Ingresa tu nueva contraseña.
      </p>

      <Input
        label="Nueva contraseña"
        type="password"
        placeholder="••••••••"
        error={errors.password?.message}
        {...register('password')}
      />

      <Input
        label="Confirmar contraseña"
        type="password"
        placeholder="••••••••"
        error={errors.confirmPassword?.message}
        {...register('confirmPassword')}
      />

      <Button type="submit" loading={reset.isPending} className="w-full">
        Restablecer contraseña
      </Button>
    </form>
  )
}
