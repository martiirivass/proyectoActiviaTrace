## ADDED Requirements

### Requirement: Rate limit login attempts by IP and email
The system SHALL limit login attempts to 5 requests per 60 seconds per unique combination of IP address and email. Exceeding this limit SHALL return HTTP 429. The counter SHALL use a sliding window and reset after 60 seconds of no requests from that combination. The rate limiter SHALL operate in-memory (for now) and does not persist across application restarts.

#### Scenario: Under rate limit
- **WHEN** user submits fewer than 5 login requests per 60 seconds for the same IP+email combination
- **THEN** system processes the login request normally (200 or 401 depending on credentials)

#### Scenario: Exceeds rate limit
- **WHEN** user submits 6 or more login requests within 60 seconds for the same IP+email combination
- **THEN** system returns HTTP 429 with `Retry-After` header and error detail "Too many login attempts. Try again in {seconds} seconds."

#### Scenario: Rate limit resets after window
- **WHEN** a user exceeded the rate limit and waits 60+ seconds without further attempts
- **THEN** the counter resets and the next login request is processed normally
