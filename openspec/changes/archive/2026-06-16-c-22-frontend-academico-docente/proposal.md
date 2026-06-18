## Why

El backend de activia-trace ya expone todas las APIs necesarias para que el rol PROFESOR (y TUTOR) gestione sus comisiones: importación de calificaciones, umbral, análisis de atrasados, ranking, notas finales, reportes, exportación de TPs sin corregir, comunicaciones masivas con preview y tracking, y monitoreo de seguimiento. Sin embargo, el frontend actual solo tiene el shell y auth (C-21). No existe ninguna interfaz para que el docente opere estos casos de uso. Este cambio implementa todas las vistas del módulo académico-docente, transformando el shell en una herramienta funcional para el perfil PROFESOR.

## What Changes

1. **Dashboard del docente** (`/dashboard`): resumen de comisiones asignadas con métricas clave (alumnos totales, atrasados, actividades pendientes de corrección).
2. **Gestión de comisión** (`/comision/:materiaId/:cohorteId`): layout con tabs que agrupa todas las vistas de una comisión.
3. **Importación de calificaciones** con flujo completo: subida de archivo → preview con detección de actividades → selección de actividades a incluir → confirmación → resumen de resultado.
4. **Configuración de umbral**: slider/input numérico con validación 0-100, values textuales aprobatorios, botón de recalcular aprobados.
5. **Vista de atrasados**: tabla filtrable con búsqueda, indicación de causa (nota_bajo_umbral / actividad_faltante).
6. **Ranking de actividades**: tabla ordenable con posición, nombre, aprobadas/total, porcentaje.
7. **Notas finales**: tabla con promedio general por alumno, detalle de actividades individuales.
8. **Reportes rápidos**: métricas consolidadas con distribución gráfica básica (barras simples).
9. **Exportar TPs sin corregir**: botón de descarga CSV con indicador de progreso.
10. **Comunicación a atrasados**: formulario de redacción + preview → envío individual o masivo + tabla de tracking de estados (Pendiente, Enviando, Enviado, Error, Cancelado) con actualización en tiempo real.
11. **Monitor de seguimiento** (`/monitor`): vista con filtros (alumno, comisión, regional, actividad) y métricas por alumno.
12. **Tests**: import flow, tabla de atrasados, preview de comunicación, tracking de estados.

## Capabilities

### New Capabilities
- `docente-dashboard`: Dashboard del docente con resumen de comisiones, métricas y acceso rápido a cada comisión.
- `comision-gestion`: Layout de tabs para navegar entre las vistas de una comisión (calificaciones, umbral, atrasados, ranking, notas, reportes, comunicaciones).
- `calificaciones-import-ui`: Flujo de importación de calificaciones con subida de archivo, preview, selección de actividades y confirmación.
- `umbral-config-ui`: Configuración del umbral de aprobación con slider/input numérico y valores textuales aprobatorios.
- `atrasados-vista`: Visualización de alumnos atrasados con filtros y desglose por actividad.
- `ranking-vista`: Ranking descendente de actividades aprobadas por alumno.
- `notas-finales-vista`: Notas finales agrupadas con promedio general y detalle de actividades.
- `reportes-rapidos-vista`: Reportes consolidados con métricas y distribución de aprobación.
- `exportar-tps-ui`: Exportación de TPs sin corregir en formato CSV descargable.
- `comunicaciones-profesor`: Redacción, preview, envío (individual/masivo) y tracking de comunicaciones a alumnos atrasados.
- `monitor-seguimiento-ui`: Monitor de seguimiento con filtros y métricas por alumno (TUTOR/PROFESOR).

### Modified Capabilities
*(Ninguna — primer cambio frontend de dominio)*

## Impact

- **Nuevo feature module**: `frontend/src/features/academico/` con su estructura de components, hooks, services, types, pages.
- **Modificaciones en router**: nuevas rutas protegidas bajo el AuthLayout existente en `router/index.tsx`.
- **Modificaciones en AppLayout**: nuevos items de menú dinámicos para el perfil PROFESOR.
- **Sin impacto en backend**: solo consume endpoints existentes de C-10, C-11, C-12.
- **Dependencias de frontend**: ninguna nueva — React Hook Form, TanStack Query, Axios ya instalados.
- **Datos mockeados opcionalmente**: se pueden usar mocks de API (MSW) durante desarrollo para endpoints que aún no estén deployados.
