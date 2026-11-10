---
title: "Runbook: Service Certificate Expiry"
license: "MIT"
---

# Runbook: Service Certificate Expiry

## Symptoms

Requests fail with TLS handshake or certificate validation errors. `CertificateExpirySoon` should warn before expiration; `AuthenticationFailureHigh` may fire after expiration. Multiple services can fail at once when they share a trust chain.

## Diagnosis

Inspect the presented certificate's subject, issuer, validity interval, and subject alternative names. Confirm which secret or certificate resource is mounted by the workload. Compare the certificate stored in Kubernetes with the certificate presented on the failing connection. Check certificate-controller events and renewal permissions.

## Mitigation

Use the approved certificate automation to issue and deploy a replacement. Do not disable TLS verification, copy a private key into chat, or create an untracked self-signed production certificate. Restart or roll workloads only when they do not reload renewed certificates automatically. Coordinate trust-bundle changes with both client and server owners.

## Verification

Confirm the new certificate is presented, all expected names validate, the complete chain is trusted, authentication error rate returns to baseline, and the expiration monitor reports the new date. Record the failed renewal mechanism as a corrective action.

