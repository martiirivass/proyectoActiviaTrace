import { useRef, type ChangeEvent } from 'react'
import { Button } from '@/shared/components/ui/Button'

const ALLOWED_EXTENSIONS = ['.xlsx', '.csv']

interface UploadStepProps {
  onFileSelected: (file: File) => void
  isLoading: boolean
  error: string | null
}

export function UploadStep({ onFileSelected, isLoading, error }: UploadStepProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      onFileSelected(file)
      return
    }
    onFileSelected(file)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase()
      if (!ALLOWED_EXTENSIONS.includes(ext)) return
      onFileSelected(file)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  return (
    <div className="space-y-4">
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-300 p-12 transition-colors hover:border-blue-400 hover:bg-blue-50"
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click()
        }}
      >
        <p className="text-lg text-gray-600">
          Arrastrá tu archivo aquí o hacé clic para seleccionar
        </p>
        <p className="mt-1 text-sm text-gray-400">
          Formatos soportados: .xlsx, .csv
        </p>
        <input
          ref={inputRef}
          type="file"
          accept=".xlsx,.csv"
          className="hidden"
          onChange={handleFileChange}
        />
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-700" role="alert">
          {error}
        </div>
      )}

      {isLoading && (
        <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
          Procesando archivo...
        </div>
      )}
    </div>
  )
}
