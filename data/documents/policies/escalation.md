---
title: "Incident Escalation and Communication Policy"
license: "MIT"
---

# Incident Escalation and Communication Policy

## Declaring an incident

Any responder may declare an incident. Record the start time, customer impact, current severity, affected services, and available evidence. Create a shared timeline before making several simultaneous changes.

## Required roles

P1 and P2 incidents require an incident commander and technical lead. P1 also requires a communications lead. The incident commander maintains priorities, requests additional responders, and approves major risk decisions. The technical lead coordinates diagnosis and mitigation. The communications lead publishes clear impact-based updates.

## Escalation triggers

Escalate when customer impact crosses a severity threshold, the owner is unknown, a mitigation fails twice, financial duplication is possible, sensitive data may be exposed, or fifteen minutes pass without a credible diagnosis. Security Operations must join suspected credential or data exposure. Payments leadership joins suspected duplicate charges.

## Human approval

Bulk replay of payment operations, disabling authentication checks, destructive database commands, and permanent deletion of production data require explicit approval from the incident commander and the relevant service owner. The system must preserve an audit record of the request, approver, time, and result.

## Closure

Close the incident only after user impact has ended, primary metrics are stable, temporary changes are recorded, and follow-up owners exist. P1 and P2 incidents require a blameless postmortem.

