# Briefing example (code mode)

A made-up review showing the Step 8 layout end to end: the input, then the output. The repo, PR and story are fictional; follow the shape, not the content.

## Input

**PR #142, "feat [sc-1234]: retry failed webhook deliveries"**

> Retries a delivery on 5xx or timeout, five attempts with exponential backoff, then dead-letters it. Also retries 429 and honours `Retry-After`, which ADR-012 says not to; I think it should. Customers aren't told about dead-lettered deliveries yet. Open question for product.

```
 src/Delivery/DeliveryWorker.cs          | 64 +++++++++----
 src/Delivery/BackoffPolicy.cs           | 38 ++++++++
 src/Delivery/DeadLetterSink.cs          | 22 +++++
 src/Delivery/DeliveryOptions.cs         |  6 +-
 tests/Delivery/DeliveryWorkerTests.cs   | 91 ++++++++++++++++++
 tests/Delivery/BackoffPolicyTests.cs    | 30 ++++++
```

**Story sc-1234 (retry failed webhook deliveries), acceptance criteria:**
- A 5xx response is retried with backoff.
- Delivery gives up after five attempts and dead-letters the message.
- A timeout counts as a failure.

Also found: #139 (rate-limit outbound webhooks) is open and touches `DeliveryWorker.cs`; the reviewer approved it earlier. CI green.

## Output: the briefing

**What it achieves.** A webhook delivery that fails with a 5xx or a timeout is retried up to five times with backoff, instead of being dropped. It implements sc-1234 (retry failed webhook deliveries).

**How it works.**

```
before:  publish ──► POST endpoint ──► 5xx ──► logged, dropped

after:   publish ──► POST endpoint ──► 5xx ──► retry queue
                                                 │  1s, 4s, 16s, 64s, 256s
                                                 ▼
                                           POST endpoint ──► 2xx ──► done
                                                 │
                                                 └─ 5th failure ──► dead-letter
```

**Where it sits.**
- Implements ADR-012 (outbound delivery is at-least-once). Departs from it on one point: ADR-012 says 4xx is never retried, but this PR retries `429`. The PR description says so.
- #139 (rate-limit outbound webhooks) touches `DeliveryWorker.cs` too, but only the constructor. That overlap is textual, not real. Your last review on #139 was an approval, and nothing here withdraws it.

**What needs you.**
1. *Technical*: retry `429`, which departs from ADR-012?
   - **a.** (author's) Retry `429` and honour `Retry-After`.
   - **b.** Treat `429` like any other 4xx: never retry.
2. *Product*: once the five retries are exhausted, does the customer get told?
   - **a.** (author's) Dead-letter only, visible in logs.
   - **b.** Also mark the delivery as failed in the API, so it shows in the customer's delivery log.

Coverage 6/6 files; 1 approval (CI bot); CI green.
**Not raised:** naming of `BackoffPolicy` (taste); a subagent's "missing cancellation token" (it is passed at `DeliveryWorker.cs:31`).

**Tests.**

| AC | Test | |
|---|---|---|
| 5xx is retried with backoff | `DeliveryWorkerTests.Retries_on_5xx` | ✅ |
| Gives up after five attempts | `DeliveryWorkerTests.Dead_letters_after_five` | ✅ |
| Timeout counts as a failure | none | ⚠️ unit-level only via `HttpClient` mock; no integration test against the real endpoint stub |

*Stop here and wait for answers.*

The reviewer answers: "1 a, 2 b, but that one goes to product".

## Output: the draft

> Thanks, the before/after in the description made this quick to follow.
>
> **Blocking:** what ends the loop at `DeliveryWorker.cs:58` when the queue is empty?
>
> ```
> while (!queue.TryDequeue(out var item)) { continue; }
> ```
>
> As written it spins until the host stops it.
>
> Retrying `429` with `Retry-After` makes sense to me. Could the PR add a line to ADR-012 recording the departure?
>
> Whether customers should see exhausted deliveries in the API is a product question. I've taken it to product; it doesn't need to block this PR.
>
> Could a timeout get an integration test against the endpoint stub? The mock covers the unit case but not the real `HttpClient` timeout path.
>
> For everything except the blocking point, you choose: fix it here or file follow-ups.

*Shown in full; posted only after the reviewer says yes.*

## Output: the ledger

Posted request-changes on #142 (link). Re-requested: none. Filed: none. Worktrees removed. Open: the product question on exhausted deliveries, with product.
