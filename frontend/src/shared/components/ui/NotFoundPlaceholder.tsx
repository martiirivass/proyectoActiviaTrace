export function NotFoundPlaceholder() {
  return (
    <div className="flex min-h-svh items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900">404</h1>
        <p className="mt-2 text-gray-600">Página no encontrada</p>
        <a
          href="/login"
          className="mt-4 inline-block text-blue-600 hover:text-blue-800"
        >
          Volver al inicio
        </a>
      </div>
    </div>
  )
}
