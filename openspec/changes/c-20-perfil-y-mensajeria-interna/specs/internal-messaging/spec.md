## ADDED Requirements

### Requirement: System stores messages in a `mensajes` table

The system SHALL have a `Mensaje` model mapped to table `mensajes` with:
- `id`: UUID primary key
- `tenant_id`: UUID foreign key to `tenants.id`, NOT NULL, indexed
- `hilo_id`: UUID NOT NULL, indexed — shared across messages in the same thread
- `remitente_id`: UUID foreign key to `users.id`, NOT NULL
- `destinatario_id`: UUID foreign key to `users.id`, NOT NULL
- `asunto`: String(200), NOT NULL
- `cuerpo`: Text, NOT NULL
- `leido`: Boolean, default False, NOT NULL
- `created_at`: DateTime with timezone, server default now
- `updated_at`: DateTime with timezone, on update now

The model SHALL inherit from `SoftDeleteMixin` and `Base`.

The `hilo_id` SHALL be generated with `uuid.uuid4()` for the first message in a thread. Subsequent replies reuse the same `hilo_id`.

#### Scenario: create mensajes table

- **WHEN** the migration runs
- **THEN** the `mensajes` table exists with columns: `id`, `tenant_id`, `hilo_id`, `remitente_id`, `destinatario_id`, `asunto`, `cuerpo`, `leido`, `is_deleted`, `deleted_at`, `created_at`, `updated_at`

### Requirement: Authenticated user can send a new message

The system SHALL provide `POST /api/v1/inbox` for any authenticated user to send a new message to another user in the same tenant.

Request body (`MensajeCreateRequest`): `destinatario_id` (UUID, required), `asunto` (String, max 200), `cuerpo` (String).

The system SHALL generate a new `hilo_id` for each new message. The same `hilo_id` SHALL be used for subsequent replies.

The system SHALL verify that `destinatario_id` exists and belongs to the same tenant before creating the message.

#### Scenario: send message to valid user

- **WHEN** an authenticated user sends `POST /api/v1/inbox` with `destinatario_id`, `asunto`, and `cuerpo` to a valid user in the same tenant
- **THEN** the system creates the message and returns 201 with `MensajeResponse`

#### Scenario: send message to non-existent user

- **WHEN** an authenticated user sends `POST /api/v1/inbox` with a `destinatario_id` that does not exist
- **THEN** the system returns 404

#### Scenario: send message to user in different tenant

- **WHEN** an authenticated user sends `POST /api/v1/inbox` with a `destinatario_id` from a different tenant
- **THEN** the system returns 404 (no cross-tenant messaging)

#### Scenario: send message without auth

- **WHEN** an unauthenticated request sends `POST /api/v1/inbox`
- **THEN** the system returns 401

### Requirement: Authenticated user can list inbox threads

The system SHALL provide `GET /api/v1/inbox` for any authenticated user to list their message threads (hilos).

Each item in the response SHALL be a thread summary containing: `hilo_id`, `remitente_id`, `remitente_nombre`, `asunto` (from last message), `ultimo_mensaje` (preview of last message body), `ultima_fecha`, `no_leidos` (count of unread messages in that thread).

Results SHALL be ordered by most recent message first. Support `offset` and `limit` query params for pagination.

#### Scenario: list threads with messages

- **WHEN** an authenticated user sends `GET /api/v1/inbox`
- **THEN** the system returns 200 with a list of hilos where the user is either sender or recipient, ordered by most recent message first

#### Scenario: list threads with pagination

- **WHEN** an authenticated user sends `GET /api/v1/inbox?offset=0&limit=10`
- **THEN** the system returns 200 with at most 10 threads

#### Scenario: list threads when inbox is empty

- **WHEN** an authenticated user with no messages sends `GET /api/v1/inbox`
- **THEN** the system returns 200 with an empty list

### Requirement: Authenticated user can read a thread

The system SHALL provide `GET /api/v1/inbox/{hilo_id}` for any authenticated user to read all messages in a thread.

The system SHALL verify that the authenticated user is either `remitente_id` or `destinatario_id` of at least one message in the hilo before returning data.

After reading, the system SHALL mark ALL messages in that hilo where the user is the `destinatario_id` as `leido = True`.

Each message in the response SHALL include: `id`, `hilo_id`, `remitente_id`, `destinatario_id`, `asunto`, `cuerpo`, `leido`, `created_at`.

#### Scenario: read own thread

- **WHEN** an authenticated user sends `GET /api/v1/inbox/{hilo_id}` for a thread where they are sender or recipient
- **THEN** the system returns 200 with all messages in the thread ordered by `created_at` ASC, and marks unread messages as read

#### Scenario: read thread from another user

- **WHEN** an authenticated user sends `GET /api/v1/inbox/{hilo_id}` for a thread where they are NEITHER sender NOR recipient
- **THEN** the system returns 404

#### Scenario: read non-existent thread

- **WHEN** an authenticated user sends `GET /api/v1/inbox/{hilo_id}` with a non-existent `hilo_id`
- **THEN** the system returns 404

### Requirement: Authenticated user can respond to a thread

The system SHALL provide `POST /api/v1/inbox/{hilo_id}/responder` for any authenticated user to reply within an existing thread.

Request body (`MensajeResponderRequest`): `cuerpo` (String).

The system SHALL verify that the authenticated user is either `remitente_id` or `destinatario_id` of at least one message in the hilo before allowing the response.

The new message SHALL reuse the same `hilo_id` and SHALL swap sender/recipient roles (if user A was recipient, the response makes user A the sender).

#### Scenario: respond to own thread

- **WHEN** an authenticated user sends `POST /api/v1/inbox/{hilo_id}/responder` with `cuerpo` for a thread they have access to
- **THEN** the system creates the reply with the same `hilo_id`, swaps sender/recipient roles, and returns 201 with `MensajeResponse`

#### Scenario: respond to thread without access

- **WHEN** an authenticated user sends `POST /api/v1/inbox/{hilo_id}/responder` for a thread they do NOT have access to
- **THEN** the system returns 404

#### Scenario: respond to non-existent thread

- **WHEN** an authenticated user sends `POST /api/v1/inbox/{hilo_id}/responder` for a non-existent `hilo_id`
- **THEN** the system returns 404

### Requirement: System tracks unread message count

The system SHALL provide a method `count_no_leidos(tenant_id, user_id)` that returns the count of messages where `destinatario_id = user_id` AND `leido = False`.

#### Scenario: count unread after receiving message

- **WHEN** user A sends a message to user B
- **THEN** user B's unread count increments by 1
