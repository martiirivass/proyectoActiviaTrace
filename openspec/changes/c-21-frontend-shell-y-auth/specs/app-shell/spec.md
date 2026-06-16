## ADDED Requirements

### Requirement: AuthGuard protects authenticated routes

The system SHALL provide an `AuthGuard` component that checks for a valid session before rendering protected content. If no session exists, it redirects to `/login`.

#### Scenario: Authenticated user accesses protected route
- **WHEN** a user with a valid session navigates to a protected route
- **THEN** the guard renders the requested page

#### Scenario: Unauthenticated user accesses protected route
- **WHEN** an unauthenticated user navigates to a protected route
- **THEN** the guard redirects to `/login`
- **AND** the original URL is preserved in state so the user can be redirected back after login

#### Scenario: Session expired while on a protected route
- **WHEN** the user's session expires while they are on a protected route
- **AND** the API returns a 401
- **THEN** the guard redirects to `/login`

### Requirement: PermissionGuard restricts routes by permission

The system SHALL provide a `PermissionGuard` component that accepts a required permission string and only renders content if the user has that permission.

#### Scenario: User has required permission
- **WHEN** a user with the required permission navigates to a protected route
- **THEN** the guard renders the requested page

#### Scenario: User lacks required permission
- **WHEN** a user without the required permission navigates to a protected route
- **THEN** the guard redirects to `/401`
- **OR** the guard renders a "Sin permisos suficientes" message

### Requirement: AppLayout provides sidebar and header

The system SHALL provide an `AppLayout` component with a sidebar navigation menu, a header bar, and a main content area (React Router Outlet).

#### Scenario: Sidebar renders menu items based on permissions
- **WHEN** a user with role ADMIN is logged in
- **THEN** the sidebar shows menu items for: Dashboard, Estructura Académica, Usuarios, Auditoría, plus any feature modules

#### Scenario: Sidebar renders only permitted items for PROFESOR
- **WHEN** a user with role PROFESOR is logged in
- **THEN** the sidebar shows only menu items the PROFESOR has access to (Comisiones, Calificaciones, Atrasados)

#### Scenario: Sidebar is collapsible
- **WHEN** the user clicks the collapse toggle on the sidebar
- **THEN** the sidebar collapses to icons-only mode
- **AND** the main content area expands accordingly

#### Scenario: Header shows user information
- **WHEN** a user is logged in
- **THEN** the header displays the user's name/email
- **AND** the header displays the user's roles
- **AND** the header has a logout button

#### Scenario: Header logout button triggers logout
- **WHEN** the logged-in user clicks the header logout button
- **THEN** the system executes the logout flow (auth-frontend spec)
- **AND** redirects to `/login`

### Requirement: Shared UI components are available

The system SHALL provide reusable UI components: Button, Input, Card, Spinner, Alert. Each component SHALL be a functional component with forwardRef support and className prop.

#### Scenario: Button renders with variants
- **WHEN** a Button is rendered with `variant="primary"`
- **THEN** it has primary color styles
- **WHEN** a Button is rendered with `variant="secondary"`
- **THEN** it has secondary color styles
- **WHEN** a Button is rendered with `variant="danger"`
- **THEN** it has danger/red color styles
- **WHEN** a Button is disabled
- **THEN** it is not clickable and has reduced opacity

#### Scenario: Input renders with label and error
- **WHEN** an Input is rendered with a `label` prop
- **THEN** the label is displayed above the input
- **WHEN** an Input has an `error` prop
- **THEN** the error message is displayed below the input
- **AND** the input border changes to error color

#### Scenario: Card renders with header, body, and footer
- **WHEN** a Card is rendered
- **THEN** it has a container with padding and shadow
- **AND** optional header, body, and footer sections

#### Scenario: Spinner shows loading state
- **WHEN** a Spinner is rendered
- **THEN** it displays an animated spinning indicator

#### Scenario: Alert renders with different types
- **WHEN** an Alert is rendered with `type="error"`
- **THEN** it shows a red/danger alert box
- **WHEN** an Alert is rendered with `type="success"`
- **THEN** it shows a green/success alert box
- **WHEN** an Alert is rendered with `type="warning"`
- **THEN** it shows a yellow/warning alert box
- **WHEN** an Alert is rendered with `type="info"`
- **THEN** it shows a blue/info alert box

### Requirement: Lazy loading for all pages

All feature pages SHALL be lazy-loaded using `React.lazy()` and wrapped in `<Suspense>` with a `<Spinner />` fallback.

#### Scenario: Page loads lazily
- **WHEN** a user navigates to a lazy-loaded page
- **THEN** the Spinner fallback is shown while the page chunk loads
- **AND** once loaded, the page renders normally
