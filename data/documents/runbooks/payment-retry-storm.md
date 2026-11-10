---
title: "Runbook: Payment Retry Storm"
license: "MIT"
---

# Runbook: Payment Retry Storm

## Trigger

Use this runbook when `PaymentRetryRateHigh` fires, payment provider latency rises, or traces show repeated authorization attempts for the same checkout. A retry storm can amplify a small provider slowdown into payment and checkout saturation.

## Diagnosis

Group authorization attempts by idempotency key and trace ID. Compare original requests with retries and confirm whether retry backoff and jitter are present. Check provider latency, timeout rate, payment worker concurrency, queue depth, and connection-pool usage. Determine whether retries originate in the gateway, checkout service, payment service, or client.

## Immediate mitigation

Reduce payment retry concurrency before increasing upstream timeouts. Disable retries at duplicate layers so one component owns the policy. Keep exponential backoff and jitter enabled. Preserve idempotency checks and never bypass them to increase throughput. If the provider is degraded, open the circuit breaker and return a clear temporary failure instead of continuing an unbounded retry loop.

Do not replay failed authorization requests in bulk until duplicate-charge risk has been reviewed. Any evidence of duplicate authorization or charge elevates the incident to P1 and requires the Payments lead and incident commander.

## Recovery validation

Retry rate and queue depth must trend downward while successful authorization rate recovers. Confirm that a repeated idempotency key produces one financial operation. Compare provider request volume with checkout volume; it should return close to one authorization sequence per checkout. Monitor for thirty minutes after restoring normal concurrency.

## Escalation

Page `#oncall-payments` immediately for duplicate-charge risk, provider-wide failure, or more than ten minutes of material checkout impact. Notify Customer Support when user-visible payment failures cross the P1 threshold.

