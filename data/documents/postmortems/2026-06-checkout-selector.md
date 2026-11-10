---
title: "Postmortem: Checkout Service Selector Mismatch"
license: "MIT"
---

# Postmortem: Checkout Service Selector Mismatch

## Summary

On 3 June 2026, checkout returned HTTP 503 for eleven minutes after a deployment changed a Pod label without updating the Service selector. Checkout Pods were healthy, but the Service had no endpoints.

## Detection

The gateway's 503 alert fired two minutes after deployment. Pod health dashboards appeared green because container health and readiness passed. The service-endpoint dashboard showed zero ready endpoints but was not linked from the alert.

## Root cause

The deployment label changed from `app: checkout` to `app.kubernetes.io/name: checkoutservice`. The Service continued selecting `app: checkout`. CI validated the YAML schema but did not verify that selectors matched workload labels.

## Resolution

Responders compared the Service selector with Pod labels, restored the expected label, and confirmed endpoint population. They did not restart unrelated dependencies.

## Corrective actions

CI now renders manifests and asserts that every internal Service selects at least one workload. The checkout alert links to the 503 runbook and service-endpoint dashboard. Deployment verification includes a synthetic checkout request.

