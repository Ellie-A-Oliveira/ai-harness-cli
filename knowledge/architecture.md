# Event Commerce Platform Architecture

Source: local `event-commerce-platform` repository, inspected 2026-11-02. This is an implementation snapshot, not a production design authority.

## System shape

- `api-gateway`: NestJS edge service; currently exposes `/health`. Intended boundary for route proxies, auth, rate limiting, and correlation middleware.
- `product-service`: Spring Boot 3.3 / Java 21 catalog API with `GET /products` and `GET /products/{id}`. EC-10 adds PostgreSQL persistence using Spring Data JPA and Flyway for products, categories, current prices, and availability.
- `order-service`: Spring Boot 3.3 / Java 21 order API and intended Saga owner. Current endpoints are `POST /orders` and `GET /orders/{id}`; state is in memory.
- `inventory-service`: FastAPI reservation API with health, reserve, and release endpoints.
- `event-contracts`: compatibility boundary for JSON event schemas.
- `storefront`: Vite + React + TypeScript operations dashboard mock.
- `infra`: Docker Compose for PostgreSQL, RabbitMQ, and Redis.

## Core flow

The first vertical slice is `POST /orders` → inventory reservation → simulated payment → order confirmation, with inventory release on failure. Event names include `inventory.reservation.requested`, `inventory.reserved`, `inventory.released`, `payment.authorized`, `payment.failed`, and `order.confirmed`.

## Current gaps

RabbitMQ publishing/listeners, outbox/inbox delivery, observability, auth, gateway routing, and contract tests remain documented as future work. Product persistence and its first migration are now implemented in the product-service repository; do not generalize that implementation to the other services without source evidence.

## Product-service persistence boundary

- `products` owns stable product IDs, names, descriptions, and active status.
- `categories` and `product_categories` model category assignment.
- `product_prices` stores the current integer price in cents.
- `product_availability` stores non-negative stock quantity and an availability flag.
- Flyway migration `V1__create_catalog_schema.sql` is validated by Hibernate with `ddl-auto=validate`.
- The persistence test uses PostgreSQL 16 through Testcontainers and is the current migration smoke test.
