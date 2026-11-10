---
title: "Service Ownership Directory"
license: "MIT"
---

# Service Ownership Directory

## Checkout

The Checkout team owns `checkoutservice`, cart-to-order orchestration, calls to shipping and payment, and the checkout success rate objective. Its primary alert is `CheckoutSuccessRateLow`. Checkout incidents are escalated through `#oncall-checkout`.

## Payments

The Payments team owns `paymentservice`, authorization idempotency, provider integration, retry policy, and payment error classification. Its primary alerts are `PaymentAuthorizationFailureHigh` and `PaymentRetryRateHigh`. Payment incidents are escalated through `#oncall-payments`. Suspected duplicate charges are always treated as severity P1 until disproved.

## Identity

The Identity team owns user sessions, service certificates, workload identities, and authentication middleware. Its primary alerts are `AuthenticationFailureHigh` and `CertificateExpirySoon`. Security Operations joins any incident involving credential exposure or unauthorized access.

## Platform

The Platform team owns Kubernetes clusters, ingress, service discovery, deployment tooling, observability, and shared PostgreSQL infrastructure. Application teams still own the behavior and capacity of their services.

## Incident leadership

The first responding team may declare an incident. For P1 and P2 incidents, the incident commander coordinates work and the technical lead directs diagnosis. The communications lead posts updates. The incident commander should not be the person executing every mitigation.

