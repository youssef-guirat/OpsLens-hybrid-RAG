---
title: "Runbook: Checkout HTTP 503 Errors"
license: "MIT"
---

# Runbook: Checkout HTTP 503 Errors

## Symptoms

Customers cannot complete purchases and the gateway returns HTTP 503. The `CheckoutSuccessRateLow` alert fires, or traces show unavailable gRPC calls from the frontend to `checkoutservice`.

## Immediate checks

Confirm the environment and namespace. Check the checkout Deployment's available replicas, recent rollouts, Pod restarts, readiness status, and Kubernetes events. Compare the first failure time with deployments or configuration changes. Inspect checkout logs by trace ID, then identify whether failures originate in checkout or one of its dependencies.

If endpoints are empty while Pods are running, compare the Service selector with Pod labels and check readiness probe failures. If endpoints exist, test service DNS and connectivity from a diagnostic Pod. Do not restart every service before collecting events, logs, and deployment versions.

## Dependency isolation

Inspect calls to payment, product catalog, currency, and shipping separately. High checkout latency with payment timeouts follows the payment timeout runbook. Connection acquisition errors follow the database pool exhaustion runbook. A single unavailable dependency should not be misdiagnosed as checkout capacity.

## Safe mitigation

Roll back the most recent checkout deployment when the timing and error signature match. If healthy Pods exist but readiness is too strict, do not remove the probe; correct the underlying dependency or probe design. Scale checkout only when CPU, memory, or concurrency evidence shows saturation. Record every change and its result in the incident timeline.

## Verification

Verify that checkout success rate, p95 latency, 503 rate, and dependency error rates return to their normal ranges for at least fifteen minutes. Run one synthetic purchase and confirm that no duplicate payment was created.

