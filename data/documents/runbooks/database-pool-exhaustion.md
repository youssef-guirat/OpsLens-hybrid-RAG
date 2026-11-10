---
title: "Runbook: Database Connection Pool Exhaustion"
license: "MIT"
---

# Runbook: Database Connection Pool Exhaustion

## Symptoms

Applications log connection acquisition timeouts, request latency rises, and PostgreSQL active connections approach the configured limit. Pods may remain ready even though requests are failing. Scaling application replicas can make this failure worse because every replica opens another pool.

## Diagnosis

Identify which service and database role consume connections. Compare active, idle, and idle-in-transaction sessions. Check pool wait time, query latency, transaction duration, recent replica scaling, and deployment configuration. Look for leaked connections and transactions held open across network calls.

## Mitigation

Stop uncontrolled autoscaling and reduce per-replica pool size when aggregate pools exceed the database budget. Terminate only verified abandoned or idle-in-transaction sessions according to the database procedure. Roll back a deployment that introduced a connection leak. Do not increase the PostgreSQL connection limit without checking memory and workload capacity.

## Verification

Pool wait time should return to baseline, connection acquisition errors should stop, and active connection count should remain below the operational warning threshold. Verify application success rate and database p95 query latency for fifteen minutes.

## Prevention

Set an explicit global connection budget, enforce pool timeouts, close connections in all error paths, alert on pool wait time before exhaustion, and load-test replica scaling against the shared database limit.

