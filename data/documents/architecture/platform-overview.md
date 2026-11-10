---
title: "Northstar Commerce Platform Overview"
license: "MIT"
---

# Northstar Commerce Platform Overview

Northstar Commerce is a fictional SaaS storefront used by the OpsLens demo. The platform runs on Kubernetes and exposes a browser frontend through the public API gateway. This document is original demonstration content and contains no production credentials or customer information.

## Request path

A normal purchase request moves through the frontend, cart service, checkout service, payment service, and order confirmation path. The checkout service also calls product catalog, currency, shipping, and email services. Calls between application services use gRPC. The public API gateway is the only component intended to receive traffic directly from the internet.

The checkout service owns orchestration of a purchase but does not charge a card itself. Payment authorization is owned by the payment service. This distinction matters during incidents: a checkout error can be caused by checkout capacity, an unavailable dependency, or a payment rejection.

## Reliability boundaries

Every deployment must define readiness and liveness probes. Readiness removes an unhealthy instance from service traffic. Liveness is reserved for processes that cannot recover without a restart; it must not fail merely because a downstream dependency is slow.

Services use bounded retries with exponential backoff and jitter. A request must never retry indefinitely. Retry budgets are configured per dependency, and non-idempotent payment operations require an idempotency key.

## Observability

Every request carries a trace ID from the gateway. Applications emit structured logs with service, environment, version, trace ID, severity, and error code. Alerts should describe customer impact and link to the owning runbook. Logs must not include card details, access tokens, or customer secrets.

## Environments

Production, staging, and development use separate namespaces, credentials, and data. Commands in these documents are diagnostic examples. Operators must confirm the active cluster and namespace before running any command.

