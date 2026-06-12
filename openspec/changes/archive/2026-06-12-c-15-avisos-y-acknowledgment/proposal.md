## Why

Actualmente el sistema no dispone de un módulo de comunicación institucional. Los COORDINADORES y ADMIN no tienen forma de publicar avisos dirigidos a segmentos específicos de usuarios (por materia, por cohorte, por rol, o globales). Los ALUMNOS y docentes no tienen un tablón central donde consultar novedades, advertencias o información crítica. Esto obliga a usar canales externos (email, WhatsApp) sin control de visibilidad ni trazabilidad de lectura. Implementar el tablón de avisos cierra esa brecha con segmentación por audiencia, ventana de vigencia, priorización y confirmación de lectura obligatoria para avisos críticos.

## What Changes

- **Nuevos modelos**: `Aviso` (alcance Global/PorMateria/PorCohorte/PorRol, severidad Info/Advertencia/Crítico, ventana de vigencia inicio/fin, orden de prioridad, requiere_ack) y `AcknowledgmentAviso` (aviso_id + usuario_id + confirmado_at), ambos con soft delete y tenant scope.
- **Endpoints `/api/v1/avisos/*`**: CRUD completo para COORDINADOR/ADMIN, visualización filtrada para todos los roles según su alcance, confirmación de lectura (ack), y estadísticas de confirmación para gestión.
- **Permisos nuevos**: `avisos:publicar` (COORDINADOR, ADMIN) para CRUD de avisos; `avisos:ver` (ALL roles) para visualización.
- **Auditoría**: acciones `AVISO_CREAR`, `AVISO_EDITAR`, `AVISO_ELIMINAR`, `AVISO_ACK` en audit log.
- **Filtrado por alcance**: al listar avisos, el sistema filtra automáticamente según el tenant del usuario, su rol, sus asignaciones (materias/cohortes), y la ventana de vigencia del aviso (RN-18/19/20).
- **Contadores derivados**: las estadísticas de visualización/confirmación se calculan desde la tabla `AcknowledgmentAviso`, nunca se almacenan desnormalizadas.
- **Migración Alembic**: creación de tablas `aviso` y `acknowledgment_aviso`.

## Capabilities

### New Capabilities
- `avisos-crud`: gestión completa de avisos — creación con alcance, severidad, contexto (materia/cohorte), rol destino, ventana de vigencia, orden y requerimiento de ack; edición, eliminación suave.
- `avisos-visualizacion`: listado de avisos activos para el usuario autenticado, filtrado automáticamente por rol, alcance, contexto académico y ventana de vigencia; ordenado por prioridad.
- `avisos-acknowledgment`: confirmación de lectura por parte del usuario destino; el sistema registra quién, cuándo y si el aviso requiere ack; contadores derivados.
- `avisos-stats`: estadísticas de confirmación por aviso (totales de vistas, acknowledges) para COORDINADOR/ADMIN con permiso `avisos:publicar`.

### Modified Capabilities
<!-- Ninguna — son capabilities nuevas, no hay modificaciones sobre capabilities existentes -->

## Impact

- **Backend**: 2 nuevos modelos (`Aviso`, `AcknowledgmentAviso`), 2 nuevos repositorios (`aviso_repository.py`, `acknowledgment_repository.py`), 1 nuevo service (`aviso_service.py`), 1 nuevo router (`avisos.py`), schemas Pydantic para cada endpoint, códigos de auditoría nuevos.
- **Base de datos**: migración Alembic con 2 tablas nuevas. Sin cambios en tablas existentes.
- **Permisos**: nuevos permisos `avisos:publicar` y `avisos:ver` en la matriz de roles. `avisos:publicar` asignado a COORDINADOR y ADMIN; `avisos:ver` asignado a ALL roles (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS).
- **API**: nuevo namespace `/api/v1/avisos/` con endpoints CRUD + ack + stats.
- **Dependencias**: C-06 (estructura académica) completo para vincular avisos a materias y cohortes.
