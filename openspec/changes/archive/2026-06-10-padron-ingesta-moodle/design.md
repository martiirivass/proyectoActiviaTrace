## Context

El padrón de alumnos es la base sobre la que operan calificaciones, atrasos y comunicaciones. Actualmente la plataforma no tiene modelo de alumnos por materia×cohorte. C-09 introduce los modelos `VersionPadron` y `EntradaPadron` con versionado (una versión activa por materia×cohorte), import desde archivo con preview/confirm, integración con Moodle Web Services (sync nocturna + on-demand), y operación de vaciado de materia.

El diseño sigue los patrones establecidos en C-01..C-08 (Models → Repositories → Services → Integrations → Routers), con TenantScopedRepository, SoftDeleteMixin y cifrado AES-256 para PII (email).

## Goals / Non-Goals

**Goals:**
- Modelo `VersionPadron` (tenant_id, materia_id, cohorte_id, cargado_por, cargado_at, activa) con soft delete
- Modelo `EntradaPadron` (version_id, usuario_id nullable, nombre, apellidos, email cifrado, comision, regional) con soft delete
- Regla de versionado: al activar una nueva versión, la anterior se desactiva automáticamente
- Import de `.xlsx`/`.csv` con preview (F1.3) y confirmación en dos pasos (F1.4)
- Integración Moodle Web Services (`integrations/moodle_ws.py`): sync usuarios/actividades, endpoint on-demand, schedule nocturno
- Fallback manual (xlsx/csv) cuando Moodle no expone WS
- Vaciar datos de materia (F1.5, RN-04): soft delete de todas las versiones y entradas de una materia
- Audit `PADRON_CARGAR` en preview y confirm
- Endpoints protegidos con `padron:importar` y `padron:vaciar`
- Migration Alembic con índices, FKs y unique constraint

**Non-Goals:**
- No se implementa import de calificaciones (C-10)
- No se implementa detección de atrasos (C-10+)
- No se implementa sincronización bidireccional con Moodle (solo lectura desde trace)
- No se implementa autenticación federada con Moodle SSO (ADR-001)
- No se implementa vista frontend de padrón (C-21+)

## Decisions

### 1. Versionado en dos tablas separadas (VersionPadron + EntradaPadron)
| Opción | Veredicto |
|--------|-----------|
| Dos tablas: VersionPadron (metadata) + EntradaPadron (filas) | ✅ Elegido |
| Tabla única con `version` como atributo de fila | ❌ Mezcla metadata con datos, dificulta queries de versión activa |

**Rationale**: El modelo E6 de la KB define explícitamente esta separación. La metadata de versión (quién cargó, cuándo, activa) es una entidad distinta de las entradas individuales. Además, permite que las `Calificacion` (C-10) referencien a `EntradaPadron` directamente, independientemente de la versión.

### 2. Activación explícita (no automática en import)
| Opción | Veredicto |
|--------|-----------|
| Preview → Confirm (dos pasos): preview devuelve datos parseados, confirm crea versión activa | ✅ Elegido |
| Import directo en un solo paso | ❌ No permite revisión previa del usuario (F1.3 exige preview) |

**Rationale**: F1.3 requiere vista previa antes de confirmar. El flujo es: (1) subir archivo → preview con datos parseados → (2) confirmar → se crea VersionPadron activa + EntradaPadron. La preview no persiste nada, solo parsea y valida.

### 3. Moodle WS como módulo de integración aislado
| Opción | Veredicto |
|--------|-----------|
| Cliente Moodle WS en `backend/app/integrations/moodle_ws.py` | ✅ Elegido |
| Lógica de Moodle embebida en servicios de padrón | ❌ Mezcla responsabilidades, viola Clean Architecture |

**Rationale**: El cliente Moodle WS es un módulo independiente con sus propios errores, reintentos y schedule. El PadronService lo invoca pero no conoce sus detalles internos. Esto permite testear con mock y cambiar el cliente sin tocar lógica de negocio.

### 4. Almacenamiento temporario de preview en memoria (no en DB)
La preview del archivo subido se procesa en memoria y se devuelve como respuesta. No se persiste nada hasta el confirm. Esto evita tablas temporales y registros huérfanos.

### 5. Soft delete en ambas entidades
`VersionPadron` y `EntradaPadron` heredan `SoftDeleteMixin`. Al "vaciar materia" se hace soft delete de todas las versiones y entradas de esa materia. Al activar una nueva versión, la anterior se desactiva (campo `activa = False`) pero no se borra.

### 6. PII (email) cifrado con AES-256
El campo `email` en `EntradaPadron` se almacena cifrado, consistente con el tratamiento de PII en `Usuario`. El cifrado/descifrado se maneja a nivel de repository/schema.

### 7. Repositorio único PadronRepository
| Opción | Veredicto |
|--------|-----------|
| Repositorio único `PadronRepository` con métodos para ambas entidades | ✅ Elegido |
| Dos repos: `VersionPadronRepository` + `EntradaPadronRepository` | ❌ Sobredivisión: siempre se opera sobre versiones y sus entradas juntos |

**Rationale**: Las operaciones de padrón siempre involucran VersionPadron y EntradaPadron de forma transaccional (preview no persiste, confirm crea ambas, vaciar afecta ambas). Un repositorio único simplifica la lógica transaccional.

## Risks / Trade-offs

- **[Volumen]** Una materia con muchos alumnos puede tener archivos xlsx grandes → mitigado: procesamiento streaming con openpyxl (no carga todo en memoria)
- **[Moodle WS timeout]** Sync nocturna puede fallar si Moodle está caído → mitigado: cola de reintentos con backoff exponencial, error → 502 con logging
- **[Cifrado]** Email cifrado impide búsqueda directa por email → mitigado: el repositorio expone método `find_by_email` que cifra el término de búsqueda y compara contra el campo cifrado (simétrica, misma clave)
- **[Versionado concurrente]** Dos usuarios podrían activar versiones simultáneamente → mitigado: la activación es una operación transaccional con lock optimista (verificar activa = False antes de activar)
