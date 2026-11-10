---
title: "Postmortem: Payment Retry Storm"
license: "MIT"
---

# Postmortem: Payment Retry Storm

## Summary

On 14 April 2026, a payment provider latency increase caused retry amplification across checkout and payment services. Checkout success fell for twenty-seven minutes. No duplicate charges were confirmed.

## Timeline

At 10:02 UTC, provider p95 latency increased. At 10:05, payment retries rose. The gateway, checkout service, and payment service each retried timeouts, multiplying provider traffic. At 10:11, the payment queue saturated and checkout began returning HTTP 503. At 10:18, responders disabled retries at the gateway and checkout layers and reduced payment concurrency. The queue recovered at 10:29, and checkout success returned to baseline at 10:32.

## Root cause

Retry policy had no single owner. Three layers independently retried the same authorization path. Although each layer had a small retry limit, their combination produced multiplicative attempts. The payment service also used fixed delays without jitter, which synchronized retry bursts.

## What went well

Idempotency keys prevented duplicate financial operations. Trace IDs allowed responders to connect repeated attempts to the same checkout. The provider circuit breaker was available and was opened during mitigation.

## Corrective actions

The Payments team owns the authorization retry policy. Gateway and checkout retries are disabled for payment authorization. Payment retries use exponential backoff with jitter and a total time budget. A load test now asserts the maximum provider-attempt ratio. An alert compares payment authorization volume with checkout volume.

