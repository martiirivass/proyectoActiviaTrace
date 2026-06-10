## ADDED Requirements

### Requirement: Sincronizar padrón desde Moodle Web Services
El sistema SHALL integrarse con Moodle Web Services para sincronizar usuarios y actividades del LMS.

#### Scenario: Sync on-demand exitosa
- **WHEN** se envía POST `/api/v1/padron/sync-moodle` con `materia_id` y `cohorte_id` válidos
- **THEN** retorna 202 indicando que la sincronización fue encolada
- **AND** el sistema consulta el Web Service `core_user_get_users` de Moodle
- **AND** mapea los usuarios obtenidos a entradas de padrón
- **AND** crea una nueva `VersionPadron` activa con los datos sincronizados

#### Scenario: Sync nocturna automática
- **WHEN** se ejecuta el schedule nocturno de sincronización
- **THEN** el sistema procesa todas las materias con integración Moodle habilitada
- **AND** actualiza los padrones de cada materia×cohorte

#### Scenario: Moodle WS retorna error
- **WHEN** el Web Service de Moodle retorna un error (timeout, conexión rechazada, HTTP error)
- **THEN** el sistema retorna 502 Bad Gateway
- **AND** el error se registra con el detalle del código y mensaje de Moodle
- **AND** el sistema programa un reintento automático con backoff exponencial

#### Scenario: Fallback a importación manual
- **WHEN** la materia no tiene integración Moodle configurada
- **THEN** el endpoint `/api/v1/padron/sync-moodle` retorna 400 indicando que no hay integración
- **AND** el usuario debe usar importación manual por archivo

### Requirement: Configuración de integración Moodle
El sistema SHALL permitir configurar por materia si la integración con Moodle Web Services está habilitada.

#### Scenario: Materia con integración Moodle habilitada
- **WHEN** una materia tiene `moodle_integration_enabled: true`
- **THEN** el endpoint de sync on-demand está disponible
- **AND** la sync nocturna incluye esa materia

#### Scenario: Materia sin integración Moodle
- **WHEN** una materia no tiene integración Moodle configurada
- **THEN** solo está disponible la importación manual por archivo
