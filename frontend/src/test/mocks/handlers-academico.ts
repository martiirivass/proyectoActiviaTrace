import { http, HttpResponse } from 'msw'

const API_BASE = 'http://localhost:8000/api/v1'

export const academicoHandlers = [
  // GET /materias/mis-comisiones
  http.get(`${API_BASE}/materias/mis-comisiones`, () => {
    return HttpResponse.json([
      {
        materia_id: 'mat-1',
        cohorte_id: 'coh-1',
        materia_nombre: 'Matemática I',
        cohorte_nombre: '2025',
        alumnos_count: 30,
        atrasados_count: 5,
        pendientes_count: 3,
      },
      {
        materia_id: 'mat-2',
        cohorte_id: 'coh-2',
        materia_nombre: 'Lengua II',
        cohorte_nombre: '2025',
        alumnos_count: 25,
        atrasados_count: 0,
        pendientes_count: 1,
      },
    ])
  }),

  // POST /calificaciones/preview
  http.post(`${API_BASE}/calificaciones/preview`, () => {
    return HttpResponse.json({
      actividades_detectadas: [
        { id: 'act-1', nombre: 'TP1', tipo: 'numerica' },
        { id: 'act-2', nombre: 'TP2', tipo: 'numerica' },
      ],
      alumnos: [
        {
          alumno: { id: 'al-1', legajo: '123', nombre: 'Juan', apellido: 'Pérez', email: 'juan@test.com' },
          valores: { TP1: 8, TP2: 7 },
        },
        {
          alumno: { id: 'al-2', legajo: '124', nombre: 'María', apellido: 'García', email: 'maria@test.com' },
          valores: { TP1: 6, TP2: null },
        },
      ],
      metadatos_columnas: ['nombre', 'apellido', 'email'],
    })
  }),

  // POST /calificaciones/importar
  http.post(`${API_BASE}/calificaciones/importar`, () => {
    return HttpResponse.json({
      registros_creados: 4,
      resumen: { ok: true },
    })
  }),

  // GET /umbral
  http.get(`${API_BASE}/umbral`, () => {
    return HttpResponse.json({
      umbral_pct: 60,
      valores_aprobatorios: ['Satisfactorio', 'Supera lo esperado'],
    })
  }),

  // PATCH /umbral
  http.patch(`${API_BASE}/umbral`, () => {
    return HttpResponse.json({
      umbral_pct: 70,
      valores_aprobatorios: ['Supera lo esperado'],
    })
  }),

  // POST /umbral/recalcular
  http.post(`${API_BASE}/umbral/recalcular`, () => {
    return new HttpResponse(null, { status: 200 })
  }),

  // GET /analisis/atrasados
  http.get(`${API_BASE}/analisis/atrasados`, ({ request }) => {
    const url = new URL(request.url)
    const busqueda = url.searchParams.get('busqueda')

    let data = [
      {
        alumno: { id: 'al-1', legajo: '123', nombre: 'Juan', apellido: 'Pérez', email: 'juan@test.com' },
        actividad: 'TP2',
        causa: 'nota_bajo_umbral',
      },
      {
        alumno: { id: 'al-2', legajo: '124', nombre: 'María', apellido: 'García', email: 'maria@test.com' },
        actividad: 'TP1',
        causa: 'actividad_faltante',
      },
    ]

    if (busqueda) {
      data = data.filter(
        (e) =>
          e.alumno.nombre.toLowerCase().includes(busqueda.toLowerCase()) ||
          e.alumno.apellido.toLowerCase().includes(busqueda.toLowerCase()),
      )
    }

    return HttpResponse.json(data)
  }),

  // GET /analisis/ranking
  http.get(`${API_BASE}/analisis/ranking`, () => {
    return HttpResponse.json([
      { posicion: 1, alumno: { id: 'al-1', legajo: '123', nombre: 'Juan', apellido: 'Pérez', email: 'juan@test.com' }, email: 'juan@test.com', comision: '2025', aprobadas: 5, total: 6, porcentaje: 83 },
      { posicion: 2, alumno: { id: 'al-2', legajo: '124', nombre: 'María', apellido: 'García', email: 'maria@test.com' }, email: 'maria@test.com', comision: '2025', aprobadas: 3, total: 6, porcentaje: 50 },
    ])
  }),

  // GET /notas-finales
  http.get(`${API_BASE}/notas-finales`, () => {
    return HttpResponse.json([
      {
        alumno: { id: 'al-1', legajo: '123', nombre: 'Juan', apellido: 'Pérez', email: 'juan@test.com' },
        email: 'juan@test.com',
        comision: '2025',
        actividades_consideradas: 6,
        nota_final: 7.5,
        actividades: [
          { nombre: 'TP1', nota: 8 },
          { nombre: 'TP2', nota: 7 },
        ],
      },
    ])
  }),

  // GET /analisis/reportes-rapidos
  http.get(`${API_BASE}/analisis/reportes-rapidos`, () => {
    return HttpResponse.json({
      alumnos_total: 30,
      actividades_total: 6,
      promedio_general: 7.2,
      aprobados: 20,
      desaprobados: 10,
      pct_aprobacion: 67,
      distribucion_actividades: [
        { nombre: 'TP1', alumnos_con_nota: 28, promedio: 7.5, aprobados: 22, desaprobados: 6 },
        { nombre: 'TP2', alumnos_con_nota: 25, promedio: 6.8, aprobados: 18, desaprobados: 7 },
      ],
    })
  }),

  // GET /analisis/exportar-tps
  http.get(`${API_BASE}/analisis/exportar-tps`, () => {
    const csv = 'alumno,actividad,fecha_finalizacion\nJuan Pérez,TP1,\nMaría García,TP2,2025-03-01'
    return new HttpResponse(csv, {
      headers: { 'Content-Type': 'text/csv' },
    })
  }),

  // POST /comunicaciones/preview
  http.post(`${API_BASE}/comunicaciones/preview`, () => {
    return HttpResponse.json({
      preview_html: '<p>Contenido de prueba</p>',
      cantidad_destinatarios: 2,
    })
  }),

  // POST /comunicaciones/enviar
  http.post(`${API_BASE}/comunicaciones/enviar`, () => {
    return HttpResponse.json({
      lote_id: 'lote-1',
      total_mensajes: 1,
      mensaje_id: 'msg-1',
    })
  }),

  // POST /comunicaciones/enviar-lote
  http.post(`${API_BASE}/comunicaciones/enviar-lote`, () => {
    return HttpResponse.json({
      lote_id: 'lote-2',
      total_mensajes: 3,
    })
  }),

  // GET /comunicaciones/lote/:loteId
  http.get(`${API_BASE}/comunicaciones/lote/:loteId`, () => {
    return HttpResponse.json({
      lote: { id: 'lote-1' },
      mensajes: [
        { id: 'msg-1', destinatario: 'juan@test.com', asunto: 'Test', estado: 'enviado', fecha_envio: '2025-03-01T10:00:00Z' },
        { id: 'msg-2', destinatario: 'maria@test.com', asunto: 'Test', estado: 'pendiente', fecha_envio: null },
      ],
      distribucion: { pendiente: 1, enviando: 0, enviado: 1, error: 0, cancelado: 0 },
    })
  }),

  // GET /comunicaciones/materia/:materiaId
  http.get(`${API_BASE}/comunicaciones/materia/:materiaId`, () => {
    return HttpResponse.json({
      comunicaciones: [
        { id: 'msg-1', destinatario: 'juan@test.com', asunto: 'Aviso importante', estado: 'enviado', fecha_envio: '2025-03-01T10:00:00Z' },
        { id: 'msg-2', destinatario: 'maria@test.com', asunto: 'Recordatorio', estado: 'pendiente', fecha_envio: null },
      ],
      distribucion: { pendiente: 1, enviando: 0, enviado: 1, error: 0, cancelado: 0 },
    })
  }),

  // GET /analisis/monitor-seguimiento
  http.get(`${API_BASE}/analisis/monitor-seguimiento`, () => {
    return HttpResponse.json([
      {
        alumno: { id: 'al-1', legajo: '123', nombre: 'Juan', apellido: 'Pérez', email: 'juan@test.com' },
        email: 'juan@test.com',
        comision: '2025',
        regional: 'CABA',
        total: 6,
        aprobadas: 5,
        desaprobadas: 1,
        pendientes: 0,
        porcentaje: 83,
      },
      {
        alumno: { id: 'al-2', legajo: '124', nombre: 'María', apellido: 'García', email: 'maria@test.com' },
        email: 'maria@test.com',
        comision: '2025',
        regional: 'GBA',
        total: 6,
        aprobadas: 3,
        desaprobadas: 2,
        pendientes: 1,
        porcentaje: 50,
      },
    ])
  }),
]
