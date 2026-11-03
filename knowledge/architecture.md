# Event Commerce Platform Architecture

Source: local `event-commerce-platform` repository, inspected 2026-11-02. This is an implementation snapshot, not a production design authority.

## System shape

- `api-gateway`: NestJS edge service; currently exposes `/health`. Intended boundary for route proxies, auth, rate limiting, and correlation middleware.
- `product-service`: Spring Boot 3.3 / Java 21 catalog API with `GET /products` and `GET /products/{id}`; current data is demo data.
- `order-service`: Spring Boot 3.3 / Java 21 order API and intended Saga owner. Current endpoints are `POST /orders` and `GET /orders/{id}`; state is in memory.
- `inventory-service`: FastAPI reservation API with health, reserve, and release endpoints.
- `event-contracts`: compatibility boundary for JSON event schemas.
- `storefront`: Vite + React + TypeScript operations dashboard mock.
- `infra`: Docker Compose for PostgreSQL, RabbitMQ, and Redis.

## Core flow

The first vertical slice is `POST /orders` → inventory reservation → simulated payment → order confirmation, with inventory release on failure. Event names include `inventory.reservation.requested`, `inventory.reserved`, `inventory.released`, `payment.authorized`, `payment.failed`, and `order.confirmed`.

## Current gaps

Persistence, migrations, RabbitMQ publishing/listeners, outbox/inbox delivery, observability, auth, gateway routing, and contract tests are documented as future work. Do not claim they are implemented without new source evidence.
