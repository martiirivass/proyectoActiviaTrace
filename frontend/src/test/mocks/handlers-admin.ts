import { http, HttpResponse } from 'msw'

const API_BASE = 'http://localhost:8000/api/v1'

export const adminHandlers = [
  // GET /admin/carreras
  http.get(`${API_BASE}/admin/carreras`, () => {
    return HttpResponse.json([
      { id: 'car-1', codigo: 'ING-INFO', nombre: 'Ingeniería Informática', activo: true, created_at: '2025-01-01T00:00:00Z', updated_at: '2025-01-01T00:00:00Z' },
      { id: 'car-2', codigo: 'LIC-MAT', nombre: 'Licenciatura en Matemática', activo: true, created_at: '2025-01-01T00:00:00Z', updated_at: '2025-01-01T00:00:00Z' },
    ])
  }),

  // POST /admin/carreras
  http.post(`${API_BASE}/admin/carreras`, async ({ request }) => {
    const body = await request.json() as { codigo?: string }
    if (body.codigo === 'DUPLICADO') {
      return HttpResponse.json({ detail: 'El código ya existe en el tenant' }, { status: 409 })
    }
    return HttpResponse.json({ id: 'car-3', ...body, activo: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() }, { status: 201 })
  }),

  // PUT /admin/carreras/:id
  http.put(`${API_BASE}/admin/carreras/:id`, () => {
    return HttpResponse.json({ id: 'car-1', codigo: 'ING-INFO', nombre: 'Ingeniería Informática (editada)', activo: true, created_at: '2025-01-01T00:00:00Z', updated_at: new Date().toISOString() })
  }),

  // DELETE /admin/carreras/:id
  http.delete(`${API_BASE}/admin/carreras/:id`, () => {
    return new HttpResponse(null, { status: 204 })
  }),

  // GET /admin/cohortes
  http.get(`${API_BASE}/admin/cohortes`, ({ request }) => {
    const url = new URL(request.url)
    const carreraId = url.searchParams.get('carrera_id')

    const cohortes = [
      { id: 'coh-1', carrera_id: 'car-1', carrera_nombre: 'Ingeniería Informática', nombre: '2025', anio: 2025, activo: true, created_at: '2025-01-01T00:00:00Z', updated_at: '2025-01-01T00:00:00Z' },
      { id: 'coh-2', carrera_id: 'car-1', carrera_nombre: 'Ingeniería Informática', nombre: '2026', anio: 2026, activo: true, created_at: '2025-01-01T00:00:00Z', updated_at: '2025-01-01T00:00:00Z' },
    ]

    if (carreraId) {
      return HttpResponse.json(cohortes.filter((c) => c.carrera_id === carreraId))
    }
    return HttpResponse.json(cohortes)
  }),

  // POST /admin/cohortes
  http.post(`${API_BASE}/admin/cohortes`, () => {
    return HttpResponse.json({ id: 'coh-3', carrera_id: 'car-1', carrera_nombre: 'Ingeniería Informática', nombre: '2027', anio: 2027, activo: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() }, { status: 201 })
  }),

  // GET /admin/materias
  http.get(`${API_BASE}/admin/materias`, () => {
    return HttpResponse.json([
      { id: 'mat-1', codigo: 'MAT-101', nombre: 'Matemática I', activo: true, created_at: '2025-01-01T00:00:00Z', updated_at: '2025-01-01T00:00:00Z' },
      { id: 'mat-2', codigo: 'PROG-101', nombre: 'Programación I', activo: true, created_at: '2025-01-01T00:00:00Z', updated_at: '2025-01-01T00:00:00Z' },
    ])
  }),

  // POST /admin/materias
  http.post(`${API_BASE}/admin/materias`, () => {
    return HttpResponse.json({ id: 'mat-3', codigo: 'FIS-101', nombre: 'Física I', activo: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() }, { status: 201 })
  }),

  // GET /admin/dictados
  http.get(`${API_BASE}/admin/dictados`, () => {
    return HttpResponse.json([
      { id: 'dic-1', materia_id: 'mat-1', materia_nombre: 'Matemática I', materia_codigo: 'MAT-101', carrera_id: 'car-1', carrera_nombre: 'Ingeniería Informática', cohorte_id: 'coh-1', cohorte_nombre: '2025', nombre: 'Matemática I - 2025', created_at: '2025-01-01T00:00:00Z', updated_at: '2025-01-01T00:00:00Z' },
    ])
  }),

  // POST /admin/dictados
  http.post(`${API_BASE}/admin/dictados`, () => {
    return HttpResponse.json({ id: 'dic-2', materia_id: 'mat-2', materia_nombre: 'Programación I', materia_codigo: 'PROG-101', carrera_id: 'car-1', carrera_nombre: 'Ingeniería Informática', cohorte_id: 'coh-2', cohorte_nombre: '2026', nombre: 'Programación I - 2026', created_at: new Date().toISOString(), updated_at: new Date().toISOString() }, { status: 201 })
  }),

  // GET /admin/usuarios
  http.get(`${API_BASE}/admin/usuarios`, () => {
    return HttpResponse.json({
      items: [
        { id: 'user-1', email: 'test@example.com', nombre: 'Test', apellido: 'User', dni: '12345678', roles: ['ADMIN'], regional: 'CABA', facturador: false, activo: true, created_at: '2025-01-01T00:00:00Z', updated_at: '2025-01-01T00:00:00Z' },
        { id: 'user-2', email: 'juan@example.com', nombre: 'Juan', apellido: 'Pérez', dni: '87654321', roles: ['PROFESOR'], regional: 'GBA', facturador: true, activo: true, created_at: '2025-01-01T00:00:00Z', updated_at: '2025-01-01T00:00:00Z' },
      ],
      total: 2,
      page: 1,
      per_page: 20,
      total_pages: 1,
    })
  }),

  // POST /admin/usuarios
  http.post(`${API_BASE}/admin/usuarios`, async ({ request }) => {
    const body = await request.json() as { email?: string }
    if (body.email === 'dup@example.com') {
      return HttpResponse.json({ detail: 'El email ya existe en el tenant' }, { status: 409 })
    }
    return HttpResponse.json({ id: 'user-3', ...body, roles: ['TUTOR'], activo: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() }, { status: 201 })
  }),

  // PUT /admin/usuarios/:id
  http.put(`${API_BASE}/admin/usuarios/:id`, () => {
    return HttpResponse.json({ id: 'user-1', email: 'updated@example.com', nombre: 'Updated', apellido: 'User', dni: '12345678', roles: ['ADMIN'], activo: true, created_at: '2025-01-01T00:00:00Z', updated_at: new Date().toISOString() })
  }),

  // DELETE /admin/usuarios/:id
  http.delete(`${API_BASE}/admin/usuarios/:id`, () => {
    return new HttpResponse(null, { status: 204 })
  }),

  // GET /audit/dashboard
  http.get(`${API_BASE}/audit/dashboard`, () => {
    return HttpResponse.json({
      acciones_por_dia: [
        { fecha: '2026-06-01', total: 15 },
        { fecha: '2026-06-02', total: 22 },
        { fecha: '2026-06-03', total: 8 },
      ],
      comunicaciones_por_docente: [
        { docente: 'Juan Pérez', pendientes: 2, enviando: 0, enviados: 10, error: 1, cancelados: 0, total: 13 },
      ],
      interacciones_por_docente_materia: [
        { docente: 'Juan Pérez', materia: 'Matemática I', total_acciones: 25, desglose: { CALIFICACIONES_IMPORTAR: 5, COMUNICACION_ENVIAR: 20 } },
      ],
      ultimas_acciones: [
        { id: 'aud-1', fecha_hora: '2026-06-03T15:00:00Z', actor: 'Admin', actor_id: 'user-1', accion: 'LIQUIDACION_CALCULAR', materia: '', detalle: 'Cálculo de liquidaciones para período 2026-06', ip: '192.168.1.1' },
        { id: 'aud-2', fecha_hora: '2026-06-03T14:00:00Z', actor: 'Juan Pérez', actor_id: 'user-2', accion: 'CALIFICACIONES_IMPORTAR', materia: 'Matemática I', detalle: 'Importación de calificaciones TP1', ip: '192.168.1.2' },
      ],
    })
  }),

  // GET /audit/log
  http.get(`${API_BASE}/audit/log`, () => {
    return HttpResponse.json({
      items: [
        { id: 'aud-1', fecha_hora: '2026-06-03T15:00:00Z', actor: 'Admin', actor_id: 'user-1', accion: 'LIQUIDACION_CALCULAR', materia: '', detalle: 'Cálculo de liquidaciones para período 2026-06', ip: '192.168.1.1', metadata: { cohorte: '2025' } },
        { id: 'aud-2', fecha_hora: '2026-06-03T14:00:00Z', actor: 'Juan Pérez', actor_id: 'user-2', accion: 'CALIFICACIONES_IMPORTAR', materia: 'Matemática I', detalle: 'Importación de calificaciones TP1', ip: '192.168.1.2' },
      ],
      total: 2,
      page: 1,
      per_page: 50,
      total_pages: 1,
    })
  }),
]
