# EC Project Context

## Atlassian identity

- Jira project: `EC` — E-commerce
- Jira board: `EC board` (`67`)
- Site: `https://ellie-oliveira.atlassian.net`
- Connected-account observation on 2026-11-02: project visible, but Jira issue search returned no issues and no Confluence spaces were accessible. Re-run the snapshot before relying on this observation.

## Local repository identity

The local codebase is `event-commerce-platform`, an event-driven e-commerce showcase. It is the primary architecture and code-pattern source until EC Jira/Confluence contains more authoritative project decisions.

## Delivery context

Repository docs identify persistence migrations, RabbitMQ consumers/producers, outbox/inbox delivery, observability, and contract tests as next milestones. These are repository-stated milestones, not Jira commitments.

## Grounding rules

Cite the relevant local file or Jira/Confluence source. Mark assumptions. If a Jira issue contradicts this file, verify it, preserve its remote link, and update the knowledge.

## Session findings (2026-11-02)

- Jira `EC-10` is the story “Define product and category data model,” under epic `EC-1 Product Catalog`, with 5 story points and acceptance criteria for stable product data, category assignment, and tested schema constraints.
- The approved decisions were: model a current price, represent availability with stock quantity plus an availability state, use Testcontainers for PostgreSQL integration tests, and allow the product API response to evolve.
- The affected checkout is the independently registered `product-service` repository, not the parent workspace repository. Its origin is configured locally; the parent `event-commerce-platform` checkout has no remote and should not be used for PR delivery.
- EC-10 was committed as `42dd345` (`feat(product): implement EC-10 catalog persistence`) and published as PR [#1](https://github.com/Ellie-A-Oliveira/commerce-product-service/pull/1).
- Verification passed with `mvn test`: one Testcontainers PostgreSQL persistence test, Flyway migration applied, zero failures/errors. Docker Desktop is required.
- The local product-service repository initially lacked Maven wrapper files; system Maven 3.10.0 was installed through Homebrew for verification.
