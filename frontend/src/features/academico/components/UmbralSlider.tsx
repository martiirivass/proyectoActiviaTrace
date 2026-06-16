interface UmbralSliderProps {
  value: number
  onChange: (value: number) => void
  error?: string | null
}

export function UmbralSlider({ value, onChange, error }: UmbralSliderProps) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-gray-700">
        Umbral de aprobación: {value}%
      </label>
      <div className="flex items-center gap-4">
        <input
          type="range"
          min={0}
          max={100}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="flex-1 accent-blue-600"
          aria-label="Umbral de aprobación"
        />
        <input
          type="number"
          min={0}
          max={100}
          value={value}
          onChange={(e) => {
            const v = Number(e.target.value)
            if (v >= 0 && v <= 100) onChange(v)
          }}
          className="w-20 rounded-md border border-gray-300 px-3 py-2 text-center text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Valor numérico del umbral"
        />
      </div>
      {error && (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
      {!error && (value < 0 || value > 100) && (
        <p className="text-sm text-red-600" role="alert">
          El umbral debe estar entre 0 y 100
        </p>
      )}
    </div>
  )
}
