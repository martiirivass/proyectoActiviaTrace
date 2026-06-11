## Context

El módulo de **Encuentros y Guardias** cubre la Épica 6 del producto. Los docentes necesitan planificar encuentros sincrónicos (recurrentes o puntuales), registrar su realización, y compartir grabaciones. Los tutores necesitan registrar guardias de atención. La coordinación necesita visibilidad transversal de ambos dominios.

Actualmente el backend tiene una arquitectura consolidada:
- FastAPI con routers → services → repositories (TenantScopedRepository)
- SQLAlchemy 2.0 async con modelos que heredan de `SoftDeleteMixin` y usan UUID PK
- Pydantic v2 schemas con `ConfigDict(extra='forbid')`
- Permisos finos via `require_permission(codename)` 
- Auditoría via `AuditService.log(...)` con códigos en `audit_codes.py`
- Tests con base de datos real (sin mocks de DB)

Este change sigue el patrón establecido. Governance level: MEDIO — implementación con checkpoints.

## Goals / Non-Goals

**Goals:**
- Modelar SlotEncuentro, InstanciaEncuentro y Guardia con soft delete y tenant scope
- Implementar creación de slots recurrentes (generación de N instancias) y únicos
- Permitir edición individual de instancias (estado, meet_url, video_url, comentario)
- Generar bloque HTML embebible con cronograma de encuentros
- Vista admin transversal de encuentros para COORDINADOR/ADMIN
- Registro de guardias por TUTOR con consulta global y export para COORDINADOR/ADMIN
- Proteger todo el módulo con permiso `encuentros:gestionar`
- Auditoría de todas las operaciones del módulo

**Non-Goals:**
- Integración con calendarios externos (Google Calendar, iCal) — queda para iteración futura
- Notificaciones automáticas al crear/modificar encuentros — se puede agregar vía worker existente
- Reprogramación inteligente (corrimiento de series) — la edición es manual por instancia
- Frontend de este módulo (se implementa en C-22/C-23)
- Eliminación física de datos (soft delete solamente, como en todo el sistema)

## Decisions

### D1: Slot recurrente como entidad separada de las instancias
- **Opción A (elegida)**: `SlotEncuentro` como plantilla → genera N `InstanciaEncuentro` hijas. Cada instancia tiene estado propio (RN-14). El slot no tiene estado.
- **Opción B**: Una sola tabla `Encuentro` con campo `recurrencia` como JSON.
- **Razón**: La opción A refleja fielmente el modelo de dominio (RN-13/RN-14). Permite que cada instancia evolucione independientemente sin afectar las demás. La opción B mezcla conceptos y complica consultas como "todas las instancias de un slot" o "instancias programadas para hoy".

### D2: Generación de instancias en el service (no en el modelo ni en DB trigger)
- **Opción A (elegida)**: El service `EncuentroService.crear_slot()` recibe los datos, crea el `SlotEncuentro`, calcula las fechas y hace bulk insert de las instancias.
- **Opción B**: Trigger de base de datos o función PostgreSQL.
- **Razón**: La lógica de generación de fechas (día_semana + fecha_inicio + cant_semanas) es regla de negocio, debe estar testeable y visible en el service. Un trigger la oculta y dificulta el testeo. El service es explícito y mantenible.

### D3: `cant_semanas = 0` como indicador de encuentro único
- **Opción A (elegida)**: Si `cant_semanas == 0` se ignora `dia_semana` y `fecha_inicio`, y se usa `fecha_unica`.
- **Opción B**: Campo booleano `es_unico` separado.
- **Razón**: El modelo de datos en la KB ya define esta semántica (E9: `cant_semanas: entero — cuántas instancias genera (0 si es fecha única)`). Simplifica la validación y es consistente con el dominio.

### D4: `hora` como `Time` nativo de PostgreSQL (no string)
- **Opción A (elegida)**: Columna `hora` de tipo `Time(timezone=False)` en ambas tablas.
- **Opción B**: String en formato "HH:MM".
- **Razón**: PostgreSQL tiene tipo `TIME` nativo que permite ordenamiento, comparación y validación automática. Pydantic lo serializa como string "HH:MM:SS" en la respuesta, que es el formato esperado.

### D5: Permiso único `encuentros:gestionar` para todo el módulo
- **Opción A (elegida)**: Un solo permiso que cubre slots, instancias y guardias. Se asigna a PROFESOR, TUTOR, COORDINADOR y ADMIN con capacidades diferenciadas por lógica del service.
- **Opción B**: Permisos separados (`encuentros:crear`, `encuentros:editar`, `guardias:registrar`, etc.).
- **Razón**: Simplicidad inicial. Las diferencias de capacidad se resuelven por rol en el service (e.g., TUTOR solo puede crear guardias, no slots; COORDINADOR puede ver todo el tenant). Si en el futuro se necesita granularidad más fina, se puede migrar a permisos separados. El guard `encuentros:gestionar` unifica la protección.

### D6: Export HTML como endpoint GET que devuelve texto plano
- **Opción A (elegida)**: `GET /api/v1/encuentros/{materia_id}/exportar-html` devuelve `text/html` con el bloque formateado.
- **Opción B**: Endpoint POST que devuelve JSON con el HTML como string.
- **Razón**: El contenido HTML se copia y pega en el LMS. Un GET con `text/html` permite vista previa directa en navegador y es más natural para el flujo de copiado. El response será `Response(content=html, media_type="text/html")`.

### D7: Guardias con `creada_at` como timestamp (no herencia de TimestampMixin)
- **Opción A (elegida)**: Campo `creada_at` con `server_default=func.now()` igual que en otros modelos, pero sin `updated_at` ni soft delete — las guardias no se modifican una vez creadas (solo cambia estado).
- **Opción B**: Full SoftDeleteMixin + TimestampMixin.
- **Razón**: Una guardia es un registro de evento, no una entidad mutable. Una vez registrada, solo cambia su estado (Pendiente→Realizada/Cancelada). El soft delete no aplica semánticamente. La ausencia de `updated_at` es intencional (el único cambio posible lo indicamos vía estado). Sin embargo, usamos soft delete por consistencia con el resto del sistema.

**Corrección D7**: Usamos SoftDeleteMixin para mantener consistencia transversal con el resto del modelo. La regla de negocio de inmutabilidad se aplica en el service (no permitir DELETE, solo transicionar estado).

## Risks / Trade-offs

| Riesgo | Mitigación |
|--------|-----------|
| [R1] Generación de instancias recurrentes con `cant_semanas` grande (ej: 52) podría ser slow si se hace instancia por instancia | Usar bulk insert con SQLAlchemy `add_all()`. Para 52 instancias es trivial, pero si se escala se puede optimizar con `insert()` bulk. |
| [R2] Slot recurrente sin fecha de fin explícita (solo `cant_semanas`) — si se necesita modificar la serie, no hay mecanismo de "extender" | Por ahora el docente puede crear un nuevo slot. En futura iteración se puede agregar endpoint PATCH de slot para modificar `vig_hasta`. |
| [R3] Export HTML genera markup plano sin estilos — el LMS destino puede no renderizarlo correctamente | El HTML generado usa `<table>` simple con clases básicas. Cada institución puede adaptar el template. Se documenta la estructura. |
| [R4] Permiso único `encuentros:gestionar` puede ser demasiado amplio para TUTOR (solo debería registrar guardias, no ver slots) | El service valida por rol: TUTOR no tiene acceso a endpoints de encuentros. Si hay confusión, se migra a `guardias:registrar` separado. |

## Migration Plan

1. Agregar código de auditoría `ENCUENTRO_CREAR`, `ENCUENTRO_EDITAR`, `GUARDIA_REGISTRAR` en `audit_codes.py`
2. Agregar permiso `encuentros:gestionar` en el seeder de permisos
3. Crear migración Alembic con tablas `slot_encuentro`, `instancia_encuentro`, `guardia`
4. Implementar modelos → repositorios → services → routers → schemas
5. Escribir tests
6. Registrar los routers en `app/api/v1/__init__.py`

**Rollback**: `alembic downgrade -1` elimina las 3 tablas. El permiso `encuentros:gestionar` queda en la tabla de permisos pero sin uso, no afecta otras funcionalidades.

## Open Questions

- **Q1**: La KB menciona `reprogramado` como posible estado en RN-14, pero E10 solo lista `Programado|Realizado|Cancelado`. Se usan los 3 estados del modelo E10 (Programado/Realizado/Cancelado). Si se necesita "Reprogramado", se agrega en iteración futura.
- **Q2**: El export HTML ¿debe incluir solo instancias Programadas y Realizadas, o también Canceladas? Decisión inicial: solo Programadas y Realizadas. Las canceladas se omiten del bloque.
- **Q3**: La guardia tiene `comentarios` como texto libre. ¿Debe tener límite de caracteres? Se definen 500 chars como máximo en el schema Pydantic.
