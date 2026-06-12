## Context

El módulo de avisos (F3.5) agrega un tablón institucional al sistema, donde COORDINADOR y ADMIN publican notificaciones segmentadas. Todos los roles pueden ver los avisos que les corresponden según su alcance, rol y ventana de vigencia, y confirmar lectura cuando el aviso lo requiera (acknowledgment).

Se implementa como módulo nuevo dentro de la arquitectura existente: modelos → repository → schemas → service → router, siguiendo las convenciones de C-01/C-04/C-06/C-07.

### Estado actual
- Ya existe el permiso `avisos:publicar` en la matriz de roles (COORDINADOR, ADMIN)
- Ya existen los modelos `Materia` (C-06) y `Usuario` (C-07) como FKs del Aviso
- Ya existe `AuditLog` (C-05) para registrar acciones
- No hay código de avisos implementado aún

## Goals / Non-Goals

**Goals:**
- CRUD completo de avisos institucionales con alcance, severidad, vigencia y estado activo/inactivo
- Filtrado automático de visibilidad según alcance (global, materia, cohorte, rol), ventana temporal y estado activo
- Confirmación de lectura (acknowledgment) por usuario, con contadores derivados
- Métricas por aviso: total de destinatarios, vistos (ack existente), confirmados (ack con confirmado_at)
- Endpoints RESTful bajo `/api/v1/avisos/`
- Tests de filtrado, vigencia, ack y contadores

**Non-Goals:**
- Notificaciones push o en tiempo real (el usuario ve los avisos al consultar)
- Envío de emails al publicar un aviso
- Avisos programados (se crean con vigencia y el sistema filtra al consultar)
- Mensajería interna entre usuarios (eso es C-20)
- Personalización de severidad por tenant (severidad fija: Info, Advertencia, Critico)

## Decisions

1. **Contadores derivados, no denormalizados** — Los contadores de vistos/confirmados se calculan como `COUNT(*)` sobre `AcknowledgmentAviso`. No se almacenan en `Aviso`. Esto evita inconsistencias y es barato para el volumen esperado (decenas de avisos activos).

2. **Filtrado de visibilidad en service, no en query** — El service recibe el usuario autenticado (roles, tenant, materias asociadas) y construye el filtro dinámico en el repository. El repository recibe parámetros ya resueltos (ej. `materia_ids: list[uuid.UUID]` del usuario). Esto mantiene la lógica de negocio fuera del repository.

3. **Enum de alcance** — `AlcanceAviso(Global | PorMateria | PorCohorte | PorRol)` en lugar de tabla separada. Es un catálogo fijo de 4 valores, no administrable.

4. **Severidad como enum** — `SeveridadAviso(Info | Advertencia | Critico)`. No afecta comportamiento del sistema en esta versión (solo visual).

5. **Acknowledgment con usuario_id único por aviso** — Se usa `unique constraint (aviso_id, usuario_id)` en `AcknowledgmentAviso`. Si ya existe un ack, el segundo POST devuelve 409 Conflict.

6. **Migración separada** — Una sola migración Alembic para crear ambas tablas (`aviso` y `acknowledgment_aviso`), con índices en tenant_id, vigencia, y unique constraint de ack.

## Risks / Trade-offs

- [Riesgo] Volumen alto de avisos + ack por alumno: si hay 1000 alumnos y 50 avisos activos, el filtrado sigue siendo barato (< 100 ms) porque se indexa por tenant + vigencia + alcance.
- [Riesgo] Alcance `PorRol` con múltiples roles seleccionables: se almacena como un solo enum, no como array. Si en el futuro se necesita multi-rol por aviso, habrá que migrar a tabla puente o JSONB.
- [Riesgo] Cuerpo de aviso como texto enriquecido: se almacena como `TEXT` plano por ahora. Si se requiere HTML/markdown, se agrega campo extra en migración futura.