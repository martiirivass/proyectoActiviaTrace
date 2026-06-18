## Context

El modelo `User` actual (C-02) tiene solo lo mínimo para auth: email, password_hash, nombre, legajo, 2FA. El modelo de datos E4 requiere ~10 campos adicionales, la mayoría PII que debe ir cifrada. Además, el modelo `Asignacion` (E5) es el eje del modelo de autorización — vincula usuario, rol y contexto académico con vigencia.

Este change es CRITICAL porque toca PII y el modelo central de autorización.

## Goals / Non-Goals

**Goals:**
- Extender `User` con todos los campos PII del modelo E4
- PII cifrada con AES-256-GCM via `EncryptedString` TypeDecorator de SQLAlchemy
- Modelo `Asignacion` completo con FKs a Usuario, Materia, Carrera, Cohorte, Dictado (opcionales)
- `Asignacion.responsable_id` para jerarquía docente
- Vigencia `desde/hasta` con `estado_vigencia` derivado (no almacenado)
- ABM usuarios con permiso `usuarios:gestionar`
- CRUD asignaciones con permiso `equipos:asignar`
- Seed de permisos en migration 006

**Non-Goals:**
- No se modifica el flujo de auth/login (el email permanece en texto plano para lookup)
- No se implementa la lógica de "asignación vencida no autoriza" a nivel de middleware (eso va en un change de integración)
- No se implementa el flujo de alta de usuarios (solo el ABM administrativo)
- No se migran datos existentes

## Decisions

### 1. `EncryptedString` como TypeDecorator de SQLAlchemy
| Opción | Veredicto |
|--------|-----------|
| TypeDecorator que encripta/desencripta automáticamente | ✅ Elegido |
| Encriptación manual en service layer | ❌ Riesgo de error humano — olvidar encriptar/desencriptar |
| Almacenar hash + encrypted (searchable encryption) | ❌ Overkill para este dominio |

**Rationale**: El TypeDecorator intercepta `process_bind_param` (encripta al guardar) y `process_result_value` (desencripta al leer). Los campos cifrados se leen/ escriben como `str` en Python pero se almacenan como `text` cifrado en la DB. No es necesario buscar por DNI/CBU, así que no necesitamos hash de búsqueda.

### 2. `estado_vigencia` no se almacena — es derivado
`Asignacion.estado_vigencia` se calcula comparando `desde`, `hasta` con la fecha actual. No se persiste. El servicio expone un helper `is_vigente(asignacion) -> bool`.

### 3. `comisiones` como JSON array
`Asignacion.comisiones` se almacena como `JSON` (PostgreSQL JSONB). Esto permite lista de strings variable sin crear una tabla `comisiones` separada.

### 4. Permisos en seed de migration
`usuarios:gestionar` se asigna a ADMIN. `equipos:asignar` se asigna a ADMIN y COORDINADOR. Se agregan en la migration 006 vía `op.execute` con INSERTs.

### 5. Email NO cifrado
Aunque la KB marca email como `[cifrado]`, el flujo de login requiere buscar por email (`WHERE email = ?`). Cifrarlo rompería el lookup. Decisión: email en texto plano + hash SHA256 del email para búsqueda opcional futura. El email como PII queda mitigado por: (a) cifrado de la DB en reposo, (b) logs sin PII, (c) control de acceso al endpoint.

## Risks / Trade-offs

- **[PII en logs]** Si un desarrollador loggea un objeto User completo, los campos cifrados se ven como ciphertext (seguro), pero los no cifrados (nombre, email) se exponen → Mitigación: Pydantic response schema solo expone lo necesario, nunca el objeto DB directo
- **[Performance]** TypeDecorator agrega overhead de encriptación/desencriptación por campo → Mitigado: AES-256-GCM es rápido (< 1μs por campo), solo aplica a <10 columnas
- **[Clave de encriptación]** Si rota la `ENCRYPTION_KEY`, los datos existentes quedan ilegibles → Mitigado: no implementamos key rotation en este change (non-goal), documentado como deuda técnica
- **[Asignacion vencida]** El sistema actualmente no filtra por vigencia en el middleware de permisos → Mitigado: este change crea el modelo y el helper `is_vigente`, la integración con permisos va en C-09 o posterior
