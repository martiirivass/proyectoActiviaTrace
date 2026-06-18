import { http, HttpResponse } from 'msw'

const API_BASE = 'http://localhost:8000/api/v1'

export const finanzasHandlers = [
  // GET /liquidaciones
  http.get(`${API_BASE}/liquidaciones`, ({ request }) => {
    const url = new URL(request.url)
    const cohorteId = url.searchParams.get('cohorte_id')
    const periodo = url.searchParams.get('periodo')

    if (cohorteId === 'coh-1' && periodo === '2026-06') {
      return HttpResponse.json({
        items: [
          {
            id: 'liq-1',
            docente_id: 'doc-1',
            docente_nombre: 'Juan',
            docente_apellido: 'Pérez',
            rol: 'PROFESOR',
            monto_base: 50000,
            monto_plus: 10000,
            total: 60000,
            es_nexo: false,
            excluido_por_factura: false,
            estado: 'Abierta',
            cohorte_id: 'coh-1',
            periodo: '2026-06',
            created_at: '2026-06-01T00:00:00Z',
            updated_at: '2026-06-01T00:00:00Z',
          },
          {
            id: 'liq-2',
            docente_id: 'doc-2',
            docente_nombre: 'María',
            docente_apellido: 'García',
            rol: 'TUTOR',
            monto_base: 30000,
            monto_plus: 5000,
            total: 35000,
            es_nexo: true,
            excluido_por_factura: false,
            estado: 'Cerrada',
            cohorte_id: 'coh-1',
            periodo: '2026-06',
            created_at: '2026-06-01T00:00:00Z',
            updated_at: '2026-06-02T00:00:00Z',
          },
        ],
        kpis: {
          total_facturante: 50000,
          total_no_facturante: 45000,
          cantidad_facturante: 1,
          cantidad_no_facturante: 1,
        },
      })
    }

    return HttpResponse.json({ items: [], kpis: { total_facturante: 0, total_no_facturante: 0, cantidad_facturante: 0, cantidad_no_facturante: 0 } })
  }),

  // POST /liquidaciones/calcular
  http.post(`${API_BASE}/liquidaciones/calcular`, () => {
    return HttpResponse.json({
      items: [],
      kpis: { total_facturante: 0, total_no_facturante: 0, cantidad_facturante: 0, cantidad_no_facturante: 0 },
    })
  }),

  // POST /liquidaciones/:id/cerrar
  http.post(`${API_BASE}/liquidaciones/:id/cerrar`, ({ params }) => {
    if (params.id === 'liq-already-closed') {
      return HttpResponse.json({ detail: 'La liquidación ya está cerrada' }, { status: 409 })
    }
    return new HttpResponse(null, { status: 200 })
  }),

  // GET /liquidaciones/historial
  http.get(`${API_BASE}/liquidaciones/historial`, () => {
    return HttpResponse.json({
      items: [
        { id: 'hist-1', fecha: '2026-06-01T10:00:00Z', usuario: 'Admin', cohorte: '2025', periodo: '2026-06' },
      ],
      total: 1,
      page: 1,
      per_page: 20,
      total_pages: 1,
    })
  }),

  // GET /liquidaciones/exportar
  http.get(`${API_BASE}/liquidaciones/exportar`, () => {
    const csv = 'docente,rol,monto_base,monto_plus,total\nJuan Pérez,PROFESOR,50000,10000,60000'
    return new HttpResponse(csv, {
      headers: { 'Content-Type': 'text/csv' },
    })
  }),

  // GET /grilla-salarial/base
  http.get(`${API_BASE}/grilla-salarial/base`, () => {
    return HttpResponse.json([
      { id: 'sb-1', rol: 'PROFESOR', monto: 50000, desde: '2026-01-01', hasta: null, vigente: true },
      { id: 'sb-2', rol: 'TUTOR', monto: 30000, desde: '2026-01-01', hasta: '2026-06-30', vigente: false },
    ])
  }),

  // POST /grilla-salarial/base
  http.post(`${API_BASE}/grilla-salarial/base`, async ({ request }) => {
    const body = await request.json() as { rol?: string; monto?: number }
    if (body.rol === 'PROFESOR' && body.monto && body.monto > 0) {
      return HttpResponse.json({ id: 'sb-3', ...body, desde: '2026-06-01', hasta: null, vigente: true }, { status: 201 })
    }
    return HttpResponse.json({ detail: 'Error al crear' }, { status: 400 })
  }),

  // PUT /grilla-salarial/base/:id
  http.put(`${API_BASE}/grilla-salarial/base/:id`, () => {
    return HttpResponse.json({ id: 'sb-1', rol: 'PROFESOR', monto: 55000, desde: '2026-01-01', hasta: null, vigente: true })
  }),

  // DELETE /grilla-salarial/base/:id
  http.delete(`${API_BASE}/grilla-salarial/base/:id`, () => {
    return new HttpResponse(null, { status: 204 })
  }),

  // GET /grilla-salarial/plus
  http.get(`${API_BASE}/grilla-salarial/plus`, () => {
    return HttpResponse.json([
      { id: 'sp-1', grupo: 'Antigüedad', rol: 'PROFESOR', descripcion: '5 años', monto: 5000, desde: '2026-01-01', hasta: null, vigente: true },
    ])
  }),

  // POST /grilla-salarial/plus
  http.post(`${API_BASE}/grilla-salarial/plus`, () => {
    return HttpResponse.json({ id: 'sp-2', grupo: 'Nuevo', rol: 'TUTOR', descripcion: 'Test', monto: 3000, desde: '2026-06-01', hasta: null, vigente: true }, { status: 201 })
  }),

  // DELETE /grilla-salarial/plus/:id
  http.delete(`${API_BASE}/grilla-salarial/plus/:id`, () => {
    return new HttpResponse(null, { status: 204 })
  }),

  // GET /facturas
  http.get(`${API_BASE}/facturas`, () => {
    return HttpResponse.json([
      {
        id: 'fac-1',
        docente_id: 'doc-1',
        docente_nombre: 'Juan',
        docente_apellido: 'Pérez',
        periodo: '2026-06',
        detalle: 'Honorarios junio',
        monto: 60000,
        estado: 'Pendiente',
        created_at: '2026-06-01T00:00:00Z',
        updated_at: '2026-06-01T00:00:00Z',
      },
    ])
  }),

  // POST /facturas
  http.post(`${API_BASE}/facturas`, () => {
    return HttpResponse.json({
      id: 'fac-2',
      docente_id: 'doc-3',
      docente_nombre: 'Ana',
      docente_apellido: 'López',
      periodo: '2026-07',
      detalle: 'Honorarios julio',
      monto: 40000,
      estado: 'Pendiente',
      created_at: '2026-07-01T00:00:00Z',
      updated_at: '2026-07-01T00:00:00Z',
    }, { status: 201 })
  }),

  // POST /facturas/:id/abonar
  http.post(`${API_BASE}/facturas/:id/abonar`, ({ params }) => {
    if (params.id === 'fac-already-paid') {
      return HttpResponse.json({ detail: 'La factura ya está abonada' }, { status: 409 })
    }
    return HttpResponse.json({
      id: params.id,
      estado: 'Abonada',
      fecha_abono: '2026-06-15T00:00:00Z',
    })
  }),

  // DELETE /facturas/:id
  http.delete(`${API_BASE}/facturas/:id`, () => {
    return new HttpResponse(null, { status: 204 })
  }),
]
