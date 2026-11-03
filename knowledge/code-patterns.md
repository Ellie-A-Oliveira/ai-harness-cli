# Code Patterns and Working Agreements

Source: local repository inspection, 2026-11-02.

- Health endpoints return `{ "service": "...", "status": "ok" }`.
- Resource routes use plural nouns: `/orders`, `/products`, `/reservations`.
- Prototype IDs use domain prefixes: `ord_`, `res_`, `sku_`.
- Inventory returns HTTP 409 for insufficient stock and HTTP 404 for missing reservations.
- Java services use Spring Boot controllers and records; Python inventory uses FastAPI and Pydantic; the gateway uses NestJS with strict TypeScript.
- Every event includes `eventId`, `occurredAt`, and `correlationId`.
- Event changes should remain additive and backward compatible; breaking changes require a new version or coordinated migration.
- Keep orchestration in `order-service`, state ownership in the owning service, and compatibility rules in `event-contracts`.
- Add contract tests with event changes and document infrastructure startup changes.

Prototype caveat: in-memory maps/lists, demo products, simulated payment failure, and development RabbitMQ credentials are not production patterns.
