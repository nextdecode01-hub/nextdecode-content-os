# P0 Performance, Scalability, Capacity Planning & Cost-Control Specification

NEXTDECODE Content OS — Batch 24

Document class: Detailed architecture and operational specification candidate

Status: DRAFT FOR OWNER REVIEW • NOT A CONTRACT FREEZE • NOT IMPLEMENTATION AUTHORIZATION

Prepared: 1 November 2026

Scope: Performance and resource behaviour across the initial single-owner Creator Mode and the longer-term modular Content OS.

## Document control and authority

| Field | Value |
| --- | --- |
| Purpose | Define how performance, capacity, scaling and cost are measured, bounded, tested and governed before implementation. |
| Authority baseline | Accepted ADR-001–ADR-010 and CF-01–CF-24 as recorded; Artifact 08 reconciliation candidate v1.1 supplements but does not supersede v1.0. |
| Decision status | Architectural directions are preserved. Numerical targets, quotas, capacity limits, retention, provider choices and spend thresholds remain owner decisions unless explicitly accepted elsewhere. |
| Relationships | Complements Batch 21 Observability, Batch 22 Configuration/Release and Batch 23 Backup/DR; aligns with Batches 17–18 state and API/event contracts. |
| Non-goals | No benchmark claim, production capacity claim, SLA, cloud/provider selection, spend authorization, deployment or repository change. |

Interpretation rule: this document distinguishes accepted architectural constraints, candidate design guidance, illustrative examples and unresolved owner decisions. A proposed metric or worksheet is not an approved target. Missing data must be measured or decided; it must not be silently replaced with assumed production numbers.

## 1. Executive summary

Performance engineering must protect correctness, governance and recoverability before optimizing speed. The initial product is a single-owner, one-workspace Creator Mode using a modular architecture. The existing Shorts Studio remains the specialist Python/FFmpeg engine behind a bounded adapter. Logical domain ownership does not imply microservices.

The system must support interactive control-plane work, research, orchestration, local media rendering, artifact movement, quality checks, distribution preparation and analytics without allowing one workload to exhaust shared resources or bypass authorization. Work that cannot safely proceed must wait, degrade transparently or fail closed.

- Measure end-to-end user-visible latency separately from queue wait, worker execution, artifact transfer and external-provider time.

- Bound concurrency, retries, memory, disk use, transfer rates and expensive operations; apply admission control and backpressure.

- Preserve durable state and exact-version governance under load, worker loss, timeouts or uncertain external outcomes.

- Keep the initial cost posture local-first/free-first with a ₹0 initial spend target; no paid provider or service may be activated by this specification.

- Scale only in response to observed bottlenecks and approved workload growth; do not pre-emptively split the architecture into microservices.

- Treat capacity estimates as hypotheses until validated through representative load, stress, soak and recovery tests.

## 2. Scope, assumptions and invariants

| ID | Invariant / constraint | Performance implication |
| --- | --- | --- |
| PERF-I01 | Single owner, one initial workspace, NEXTDECODE brand. | Initial sizing is single-tenant; do not infer multi-tenant requirements. |
| PERF-I02 | Shorts Studio remains a specialist engine behind a bounded adapter. | Measure rendering separately from control-plane API latency. |
| PERF-I03 | Cloud control plane is long-term shared workflow authority; local workers handle local-only/heavy work when available. | Local worker absence must produce safe waiting/degraded behaviour, not hidden loss or unapproved cloud execution. |
| PERF-I04 | Local-first/free-first; ₹0 initial target. | No paid service, provider, GPU rental, storage tier or egress activation without explicit approval. |
| PERF-I05 | Human approval before critical publishing; automatic public publishing disabled pending separate policy. | Load cannot weaken review, rights, authorization or publishing gates. |
| PERF-I06 | Approval ≠ authorization ≠ execution ≠ confirmed outcome. | Timeouts/retries preserve distinct state and reconcile unknown external outcomes. |
| PERF-I07 | Fail closed on uncertain rights, authorization, integrity or security. | Overload cannot trigger permissive fallback. |
| PERF-I08 | At-least-once delivery with idempotency and traceable attempts. | Duplicate delivery is expected; duplicate side effects must be prevented or reconciled. |
| PERF-I09 | Immutable artifact versions; repair creates a new version. | Capacity reclamation cannot silently mutate or destroy referenced evidence. |
| PERF-I10 | No destructive repository/Git action without explicit approval. | Performance work cannot use cleanup/reset shortcuts that risk user work. |

## 3. Workload model across the 12 logical modules

Workload classification informs metrics, isolation boundaries and test scenarios. This table does not assert that every module is implemented or active.

| Module | Representative work | Resource profile / concern | Primary protection |
| --- | --- | --- | --- |
| 1. Workspace & Control Center | Dashboard reads, settings, command submission | Low-latency API and DB reads; expensive synchronous aggregation. | Bound query time; safe read models. |
| 2. Content Graph | Entity/version lookup, relationship traversal | DB indexes, joins, graph-shaped reads and write contention. | Pagination; scoped indexes. |
| 3. Knowledge Management | Ingestion, parsing, indexing, retrieval | CPU, memory, disk and optional embedding/provider cost. | File-size limits; staged processing; provider gates. |
| 4. Research Intelligence | Search orchestration, collection, synthesis | External latency/rate limits, CPU and token/usage cost. | Timeouts; bounded fan-out; provenance. |
| 5. Brand Intelligence | Brand rules and consistency analysis | Reads plus CPU/LLM-bound optional analysis. | Versioned rules; bounded context. |
| 6. Strategy & Planning | Calendar, plans, dependency queries | Interactive DB reads/writes and calculations. | Short transactions; async bulk work. |
| 7. Content Quality Intelligence | Policy, claim, format and quality checks | CPU/LLM-bound mix; possible fan-out. | Hard limits; hard blockers remain hard blockers. |
| 8. Multiformat Creation Engine | Script, storyboard, render orchestration | CPU/GPU-optional, memory and disk-heavy operations. | Separate interactive control from render workers. |
| 9. Asset Management | Upload, checksum, preview, transcode, retrieval | Disk/network I/O, storage and bandwidth. | Streaming; checksums; quotas; immutable versions. |
| 10. Automation & Agent Orchestration | Workflow runs, task dispatch, heartbeats | Queue throughput, DB writes, worker slots, retries. | Leases; backpressure; idempotency; fairness. |
| 11. Distribution Studio | Package validation, upload preparation, platform calls | Network and external API latency; side-effect risk. | Central authorization; rate limits; outcome reconciliation. |
| 12. Analytics & Learning | Aggregation, reports, trend analysis | DB scans, CPU, memory and large result sets. | Async aggregation; bounded windows; read models. |

## 4. Performance dimensions and measurement model

| Dimension | Definition | Required segmentation |
| --- | --- | --- |
| User-visible latency | User action to useful response or durable acknowledgement. | Interactive query vs command; p50/p95/p99; cold/warm. |
| Queue wait | Durable enqueue to worker claim/start. | Queue, priority, task type, worker class. |
| Execution duration | Worker start to terminal attempt result. | Task type, engine/version, input size, hardware. |
| End-to-end workflow | Accepted command to completed/reviewable result. | Workflow version, stage, retries, external waits. |
| Artifact transfer | Bytes and elapsed time including checksum verification. | Source/destination, size band, protocol, retries. |
| Throughput | Completed valid units per time window. | Jobs, tasks, assets, API requests, events; accepted vs completed. |
| Concurrency | Simultaneous active requests/jobs/tasks/transfers/renders. | Resource pool and workload class. |
| Saturation | CPU, RAM, GPU, disk, DB connections, queue and network pressure. | Host/worker/pool; sustained and peak windows. |
| Reliability under load | Correctness/recovery under constrained resources. | Duplicate events, lease expiry, cancellation, timeout, restart. |
| Cost efficiency | Resource and operational cost per valid completed unit. | ₹ monetary cost plus compute/storage/bandwidth/engineering. |

Use monotonic clocks within processes and UTC timestamps for cross-system event records. Record wall-clock elapsed time and stage timings. Correlation IDs, workflow/run IDs, job/task IDs, attempt IDs, worker IDs and artifact version IDs should connect measurements where available.

## 5. Performance budgets — owner target worksheet

No production latency, throughput, concurrency, resource or SLO targets are approved by this document. Complete this worksheet after baseline measurements and representative workload definition.

| Metric / service class | Measure | Baseline evidence | Candidate target | Hard limit / timeout | Owner decision |
| --- | --- | --- | --- | --- | --- |
| Interactive read API | p50/p95/p99 |  |  |  |  |
| Interactive command acknowledgement | p50/p95/p99 |  |  |  |  |
| Durable enqueue acknowledgement | p95/p99 |  |  |  |  |
| Queue wait — interactive priority | p50/p95/p99 |  |  |  |  |
| Queue wait — normal background | p50/p95/p99 |  |  |  |  |
| Research task duration | p50/p95/p99 by task |  |  |  |  |
| Quality-check duration | p50/p95/p99 by check |  |  |  |  |
| Short-form render duration | duration / media-minute ratio |  |  |  |  |
| Artifact transfer | throughput and time by size |  |  |  |  |
| Workflow completion | end-to-end by class |  |  |  |  |
| DB query/transaction | p95/p99 and slow-query count |  |  |  |  |
| Worker availability / lease | heartbeat, claim, expiry |  |  |  |  |
| Resource saturation | CPU/RAM/GPU/disk/network |  |  |  |  |
| Period spend | actual monetary spend |  |  |  |  |

Budget rules: define a user-visible objective and a hard safety limit separately; specify measurement window, percentile, workload class, exclusions, alert threshold, owner and remediation. A timeout is not proof that an external side effect did not occur.

## 6. Capacity planning model

### 6.1 Workload inputs

| Input | Required data | Estimation / validation |
| --- | --- | --- |
| Active workspaces/users | Initial active owner count, concurrent sessions, future expansion assumptions. | Current scope is one owner/one workspace; future multi-user load is separate. |
| Content demand | Items per day/week, variants per item, scheduled work. | Derive from observed editorial cadence. |
| Media profile | Duration, resolution, frame rate, codec, bitrate, audio tracks, output profiles. | Collect representative samples, including outliers and invalid inputs. |
| Asset profile | Count, average/max file size, versions, retention, derivative count. | Measure actual corpus and version growth. |
| Job arrivals | Arrival rate by class, bursts, dependency fan-out, scheduled peaks. | Capture traces; model normal, peak, burst and catch-up. |
| Worker supply | CPU/RAM/disk/GPU, online hours, competing desktop use. | Inventory actual machine; reserve interactive headroom. |
| External dependencies | Rate limits, latency, quotas, availability, pricing. | Do not activate providers; use documented limits only. |
| Database growth | Rows by entity/event/attempt, indexes, write rate, retention, backup overhead. | Measure growth; partition only with evidence. |
| Network | Upload/download bandwidth, latency, data caps, variability. | Measure sustained throughput and competing traffic. |

### 6.2 Capacity equations and planning heuristics

These equations are planning aids, not approved targets. Validate assumptions with measured traces and repeatable tests.

- Average concurrent work = arrival rate × average service time (Little’s Law), applied per workload class only when stable.

- Required worker slots ≈ peak arrival rate × average execution time ÷ target utilization. Define burst shape, failure reserve and local availability before adding headroom.

- Backlog drain time ≈ queued units × average service time ÷ effective parallel slots; adjust for dependencies, contention and retries.

- Storage growth ≈ source bytes + derivative bytes + immutable versions + manifests/metadata + temporary workspace + backup copies − eligible retention expiry.

- Network transfer lower bound ≈ payload bytes ÷ measured sustained throughput; include protocol overhead, retries, checksum and throttling.

- Render capacity should be expressed in jobs/hour and output-media-minutes per wall-clock hour, segmented by profile and hardware.

- DB capacity includes foreground queries, workflow/event writes, outbox/inbox, observability and backup/restore workloads.

Do not size from a single average when workloads are bursty or heavy-tailed. Include p95/p99 input sizes, largest permitted asset, retry amplification, worker loss and recovery backlog.

## 7. Local worker and media-engine resource model

| Resource | Risks / signals | Required controls |
| --- | --- | --- |
| CPU | FFmpeg filters, encoding, image/video analysis and transcodes compete with desktop use. | Per-worker caps; CPU headroom; priorities; cancellation; bounded process lifetime. |
| GPU / accelerator | Optional acceleration may be unavailable, unsupported or slower for some profiles. | Capability discovery; explicit profiles; no assumed GPU; fallback only if policy and quality permit. |
| RAM | Large frames, parallel decoders, model context and buffers cause swapping/OOM. | Input limits; streaming/chunking; per-task memory budget; isolation; graceful failure. |
| Disk capacity | Temporary renders, caches, source assets and logs fill volumes. | Scratch quotas; free-space preflight; bounded cache; safe cleanup only for unreferenced temporary files. |
| Disk I/O | Decode/encode, checksum, copies and DB activity contend. | Measure throughput/queue depth; avoid redundant copies. |
| Network | Sync/uploads compete with interactive work and can be interrupted. | Transfer concurrency/bandwidth caps; resumable transfer where supported; checksum. |
| Thermal / power | Sustained renders throttle or stop on laptops/desktops. | Observe throttling; pause/reduce concurrency; do not assume always-on workers. |

Workers advertise actual capabilities and resource availability; orchestration must not dispatch based only on nominal labels. A local worker going offline is normal and must not silently move local-only work to an unapproved provider.

## 8. Admission control, concurrency and backpressure

| Control | Candidate behaviour | Safety requirement |
| --- | --- | --- |
| Admission limits | Bound active workflows, queued jobs, fan-out, payload size and concurrent transfers. | Reject/defer with clear reason; preserve durable command outcome. |
| Concurrency pools | Separate interactive API, research, render, quality, transfer, analytics and distribution pools where useful. | Bulk work cannot starve control-plane or security checks. |
| Priority classes | Interactive/control, deadline-aware editorial, normal background, bulk/maintenance. | No bypass of rights/QA/approval/authorization; prevent starvation with aging/fairness. |
| Backpressure | Slow producers when queue depth, DB pressure, disk headroom or worker slots cross approved thresholds. | Expose delay; avoid unbounded in-memory queues. |
| Retry budget | Cap attempts and elapsed retry window; exponential backoff with jitter; dead-letter/manual review. | Idempotency required; uncertain external side effects need reconciliation. |
| Fan-out limits | Bound research sources, derivative generation and child tasks. | Record partial results; prevent unbounded task trees. |
| Cancellation | Cooperative cancellation and safe subprocess termination. | Cancellation does not roll back completed external side effects. |
| Resource quotas | Per-job memory, CPU time, scratch disk, output size and network limits. | Quota breach fails safely and leaves recoverable evidence. |

## 9. Scaling strategy and architecture boundaries

- Start with accepted modular architecture and explicit domain ownership. Logical modules do not require separate deployables or databases.

- Prefer vertical tuning and bounded worker pools while measured demand and operational simplicity justify it.

- Scale worker capacity independently from control-plane API capacity where boundaries permit.

- Consider horizontal worker replication only when tasks are safely claimable, idempotent, capability-routed and observable.

- Keep database authoritative state and transactional outbox/inbox semantics; an in-memory queue is not a durable substitute.

- Do not split services solely to solve a local bottleneck; first identify query/task profile, isolation need and operational cost.

- Cloud control plane and local worker responsibilities remain accepted direction; no provider, hosting topology or deployment target is selected.

- Scale-down respects active leases, heartbeats, in-flight subprocesses, artifact writes and external-operation uncertainty.

## 10. Database performance and data growth

| Area | Guidance | Evidence before change |
| --- | --- | --- |
| Query shape | Bound result sizes; paginate; avoid N+1; separate interactive reads from analytical scans. | Query plans, rows examined/returned, latency. |
| Indexes | Index scoped lookup, ownership, lifecycle and queue-claim paths based on actual patterns. | EXPLAIN plans, write amplification, index size/use. |
| Connections | Bound pools and transaction timeouts; account for API, workers and maintenance. | Peak connections, wait time, pool saturation. |
| Transactions | Keep short; never hold DB transactions during rendering or external calls. | Duration, lock waits, deadlocks. |
| Hot rows | Avoid single frequently updated counter/state rows where independent records suffice. | Lock contention and write throughput. |
| Outbox/inbox | Batch safely; monitor lag; preserve transactional consistency. | Outbox age/depth and delivery attempts. |
| Event/history growth | Retention/archive only after owner decision and evidence needs review. | Growth rate, restore impact, retention decision. |
| Partitioning | Defer until measured table size/query patterns justify it. | Before/after plans, operational complexity, migration/restore test. |

Analytics should not run unbounded scans on the primary interactive path. Use bounded windows, pre-aggregations or read models only when correctness, freshness and ownership are specified.

## 11. Queue, workflow and worker throughput

- Queue depth alone is insufficient: track oldest age, enqueue/claim/completion rates, retries and dead-letter count by task class.

- Lease duration and heartbeat interval must account for task duration and worker pauses; values require owner-approved configuration.

- Expired leases may cause redelivery. Attempt records and idempotency keys distinguish delivery attempts from logical work.

- Use bounded claim batches and prevent one worker monopolizing the queue.

- Measure dispatch, startup, execution, artifact commit and final state transition separately.

- Retries must not amplify an outage; apply backoff, jitter, retry budgets, circuit/pause controls and idempotency.

- Include recovery backlog in capacity planning; steady-state throughput does not prove outage recovery capacity.

- Represent long-running FFmpeg work as durable task state with progress/heartbeat evidence, not a request thread held open.

## 12. Artifact storage, transfer and integrity cost

| Concern | Specification candidate | Open dependency |
| --- | --- | --- |
| Immutable versions | Preserve exact artifact identity/version; repair/transformation creates a new version. | Canonical metadata and retention. |
| Integrity | Checksum on ingest/transfer and verify before use; distinguish mismatch from transient failure. | Approved algorithms and cadence. |
| Temporary storage | Bound scratch; record owner/expiry for temporary files. | Safe cleanup eligibility and retention. |
| Deduplication | May reduce storage only where identity and rights/ownership semantics permit. | Cross-scope policy and privacy implications. |
| Transfer | Stream large files, cap concurrency, support resumability where supported, verify bytes/checksum. | Protocol and provider choice. |
| Derivatives | Generate only required derivatives; track lineage and version. | Derivative catalogue and retention. |
| Backups | Include metadata and binaries consistently; coordinate with Batch 23 recovery groups. | RPO/RTO and backup target remain unapproved. |
| Deletion/legal hold | Do not reclaim referenced or legally held evidence due to capacity pressure. | Retention, legal hold and deletion authority. |

## 13. Cost-control framework

Cost is broader than invoices. The initial monetary target remains ₹0. Local electricity, hardware wear, storage, bandwidth, maintenance and engineering time are real costs. This specification authorizes no paid service or provider activation.

| Cost category | Measure | Control / approval boundary |
| --- | --- | --- |
| Monetary services | Hosting, DB, object storage, egress, API/LLM usage, GPU, monitoring, domains, subscriptions. | Hard stop before paid activation; owner approves provider, budget, account and ceiling. |
| Local compute | CPU/GPU time, electricity estimate, hardware wear, machine availability. | Concurrency caps; schedule heavy work; protect desktop responsiveness. |
| Storage | Source, derivative, cache, temporary, metadata, logs and backup bytes. | Quota and retention review; never delete evidence without authority. |
| Bandwidth | Uploads, downloads, sync, retries and external egress. | Transfer limits, compression where suitable, resumability and retry caps. |
| Operational | Monitoring, incidents, credential maintenance, restore drills and support burden. | Prefer understandable components; avoid premature distributed complexity. |
| Engineering | Implementation, tests, migrations, security and maintenance effort. | Measure total complexity; do not shift unbounded manual work to owner. |

### 13.1 Spend guardrails

1. Keep paid integrations, usage-based APIs, cloud resources and automatic upgrades disabled/unconfigured by default.

1. Require explicit owner approval before account creation, payment details, billing, paid tier provisioning or chargeable API calls.

1. Before activation record provider, purpose, pricing basis, free-tier conditions, quota, alert threshold, hard cap, billing owner and disable procedure.

1. Usage alerts are not hard caps unless provider enforcement is confirmed.

1. A free trial is not approval for paid continuation; define expiry and disable behaviour.

1. On quota exhaustion or uncertain billing state, fail closed for the paid capability and preserve local work where possible.

1. Reconcile invoices/usage against recorded operations; investigate unexpected usage before resuming.

## 14. Autoscaling, scheduling and safe scale-down

Autoscaling is a candidate future capability, not an approved deployment decision. Any controller must be bounded, observable, reversible and unable to weaken authorization.

| Trigger signal | Possible action | Guard / exit condition |
| --- | --- | --- |
| Sustained queue age above approved threshold | Add eligible worker slots or reduce producer intake. | Capability, budget, credentials and concurrency cap verified. |
| CPU/RAM pressure on local worker | Pause low-priority work or reduce render concurrency. | Do not kill active work without cancellation/recovery protocol. |
| Disk headroom below threshold | Stop new render/transfer admission; alert owner. | Never auto-delete referenced artifacts or evidence. |
| DB connection saturation | Apply backpressure and reduce worker claim rate. | Preserve control-plane and recovery access. |
| Provider rate limiting | Reduce fan-out and apply backoff. | Do not bypass limits or switch to unapproved provider. |
| Low queue demand | Scale down idle workers. | No active lease, subprocess, artifact commit or uncertain external operation. |

## 15. Performance observability and dashboards

Batch 21 is the observability baseline. This batch adds capacity-focused views; it does not replace Batch 21 logging, metrics, tracing, health checks, alerts, dashboards or runbooks.

| Dashboard | Minimum panels / signals | Operational question |
| --- | --- | --- |
| System overview | API latency/errors, queue age, active jobs, worker availability, DB health, disk headroom. | Is system healthy and where is pressure? |
| Workload throughput | Arrivals/completions/retries by task class; backlog age and drain rate. | Can system keep up and recover from bursts? |
| Worker/local engine | CPU/RAM/GPU/disk/network, slots, lease age, render duration, offline time. | Are workers correctly sized and responsive? |
| Database | Query latency, slow queries, pool, locks, transactions, outbox lag. | Is persistence the bottleneck? |
| Artifact pipeline | Bytes, transfer time, checksum failures, retries, scratch use, version growth. | Are storage and transfer constrained? |
| Cost and quota | Authorized paid usage, local resource estimates, storage growth, quota remaining. | Are financial/resource boundaries respected? |
| Reliability under load | Timeouts, duplicate deliveries, lease expiry, dead-letter, unknown outcomes. | Is pressure affecting correctness/governance? |

Avoid high-cardinality metric labels such as arbitrary content IDs. Put identifiers in access-controlled, redacted logs/traces. Alert thresholds and retention are owner-approved values.

## 16. Performance and capacity test strategy

| Test class | Purpose | Required conditions / evidence |
| --- | --- | --- |
| Baseline | Establish normal latency/throughput for representative workloads. | Known machine/software versions, representative corpus, repeatable run, raw measurements. |
| Load | Validate defined steady-state demand. | Arrival profile, concurrency, percentiles, errors, queue stability. |
| Stress | Find saturation and safe failure boundaries. | Gradual increase; identify bottleneck and fail-safe behaviour. |
| Spike | Test sudden bursts and scheduled peaks. | Burst arrival, admission control, durable queue, recovery to baseline. |
| Soak | Detect leaks, disk growth, stale leases and drift. | Long run with resource samples and periodic workflow checks. |
| Concurrency/race | Validate idempotency, state versions and contention. | Duplicate delivery, simultaneous commands, stale writes, competing claims. |
| Worker-loss | Validate disconnect/restart during work. | Lease expiry, partial artifacts, retry/resume, no false completion. |
| Dependency outage | Validate DB, network, provider or storage degradation. | Backpressure, bounded retries, pause and operator visibility. |
| Artifact stress | Validate large files, checksum, interrupted transfer and disk pressure. | Maximum approved size, slow network, insufficient disk, integrity checks. |
| Recovery load | Validate restore and backlog drain after outage. | Batch 23 recovery sequence, consistency and no duplicate protected side effects. |

## 17. Acceptance matrix

| ID | Scenario | Pass condition / oracle | Evidence |
| --- | --- | --- | --- |
| CAP-01 | Interactive API at agreed baseline | Approved latency/error objectives met; control plane remains responsive. | Load report, traces, dashboard. |
| CAP-02 | Background render saturation | Interactive and governance paths remain within budgets or degrade explicitly. | Resource samples and traces. |
| CAP-03 | Queue burst | Durable backlog remains bounded; no silent loss; backlog drains at measured rate. | Queue metrics and reconciliation. |
| CAP-04 | Local worker unavailable | Local-only tasks wait/defer; no unauthorized cloud execution. | State history and dispatch logs. |
| CAP-05 | Worker killed during render | Lease/attempt recovery correct; incomplete output not complete. | Attempt records and artifact inspection. |
| CAP-06 | Duplicate task delivery | Idempotency prevents duplicate logical effects; attempts traceable. | Duplicate-injection report. |
| CAP-07 | Provider throttling | Backoff prevents retry storm; no unapproved fallback. | Rate-limit traces and counters. |
| CAP-08 | DB pool saturation | Backpressure works; no unbounded connections or lost durable commands. | DB metrics and command reconciliation. |
| CAP-09 | Disk nearly full | New heavy work safely deferred/rejected; referenced artifacts intact. | Disk telemetry and manifest check. |
| CAP-10 | Interrupted large transfer | Partial artifact never becomes usable; resume/retry verifies checksum. | Transfer logs and checksum. |
| CAP-11 | Outbox backlog | Events delivered/retried without breaking source transaction state. | Outbox lag and reconciliation. |
| CAP-12 | Heavy analytics query | Interactive workloads protected; report scope bounded. | Query plans and API latency. |
| CAP-13 | Long soak | No unbounded memory, disk, queue, lease or log growth beyond approved bounds. | Time-series report and analysis. |
| CAP-14 | Scale-down with active lease | Worker not terminated unsafely; work completes or follows recovery. | Worker lifecycle and attempt evidence. |
| CAP-15 | Paid quota exhausted | Paid capability stops safely; no surprise charge or unapproved fallback. | Usage ledger and configuration. |
| CAP-16 | Governance under overload | Rights/QA/approval/authorization remain enforced; BLOCKED cannot be bypassed. | Negative tests and audit. |
| CAP-17 | Unknown external outcome | Reconcile before retry; no duplicate publish or false success. | External-operation record. |
| CAP-18 | Recovery after outage | Batch 23 invariants hold during backlog replay/drain. | Restore report and consistency evidence. |

## 18. SLO, SLA and readiness distinction

An SLI is a measured indicator (latency, availability, error rate or queue age). An SLO is an internally approved objective over a defined window. An SLA is an externally committed service agreement with obligations/remedies. This document defines candidate SLIs and a target-setting process only; it establishes no SLO, SLA, uptime promise or customer-facing commitment.

- Do not publish availability percentages until scope, denominator, exclusions, dependency boundaries and evidence are agreed.

- Do not treat unit tests or a short load test as proof of production capacity.

- Do not use render throughput as a substitute for workflow quality or governance correctness.

- Performance objectives cannot override data integrity, rights, approval, authorization, privacy or recovery.

## 19. Capacity review cadence and scaling triggers

| Review point | Activity | Output |
| --- | --- | --- |
| Before each milestone | Update workload assumptions, input corpus, target worksheet and constraints. | Versioned capacity assumptions and owner decisions. |
| Before release candidate | Run baseline/load/stress tests for changed paths and compare evidence. | Regression report and release-gate recommendation. |
| After material workload change | Recalculate arrivals, storage growth, media profile and worker supply. | Updated model and quota proposal. |
| Operational review | Review queue age, saturation, failure/retry, storage and cost trends. | Corrective actions with owner and due date. |
| Before paid expansion | Present measured bottleneck, free/local alternatives, full cost, cap and exit plan. | Explicit owner approval or rejection. |

Trigger values must derive from approved budgets and observed baseline. A dashboard threshold is not automatically a scaling authorization.

## 20. Risks and failure modes

| Risk | Impact | Mitigation / evidence |
| --- | --- | --- |
| Unmeasured assumptions | Wrong sizing and misleading claims. | Representative corpus and trace-based model. |
| Heavy jobs starve interactive work | Control plane unusable during renders/analysis. | Separate pools, admission control and fairness. |
| Retry amplification | Outage becomes larger outage and cost spike. | Retry budgets, jitter, pause controls and idempotency. |
| Unbounded temporary files | Disk exhaustion and failed renders/evidence risk. | Scratch quotas, safe cleanup, disk preflight. |
| Premature microservices | Operational complexity, latency and cost. | Preserve modular architecture until evidence justifies extraction. |
| Free-tier surprise billing | Unapproved charges. | No billing activation without approval; caps and disable procedure. |
| Autoscaling runaway | Resource/cost escalation. | Maximum slots, budget guard and owner pause. |
| Misleading averages | Tail latency and burst failures hidden. | Percentiles, workload segmentation and stress tests. |
| Governance bypass under pressure | Unauthorized external side effect. | Central gates; overload fails closed. |
| Recovery overload | Restored system cannot drain backlog safely. | Recovery-load testing and bounded drain rate. |

## 21. Open owner decisions

| ID | Decision required | Why it matters | Status |
| --- | --- | --- | --- |
| PCD-01 | Approve interactive API/command latency objectives. | Defines user experience and budget. | OPEN |
| PCD-02 | Approve queue wait objectives by priority. | Defines scheduling/backlog expectations. | OPEN |
| PCD-03 | Approve workload arrival/content/media profile. | Required for meaningful capacity sizing. | OPEN |
| PCD-04 | Approve maximum source/output media profile and asset size. | Bounds memory, disk, transfer and render demand. | OPEN |
| PCD-05 | Approve local worker resource reservation and concurrency caps. | Protects desktop responsiveness. | OPEN |
| PCD-06 | Approve priority classes and starvation/fairness policy. | Determines scheduling. | OPEN |
| PCD-07 | Approve queue, retry, lease and heartbeat numeric values. | Needed for durable execution/recovery. | OPEN |
| PCD-08 | Approve scratch, cache, log and artifact quotas. | Prevents disk exhaustion/evidence loss. | OPEN |
| PCD-09 | Approve retention, archival and deletion policy with legal/evidence review. | Determines storage growth and deletion authority. | OPEN |
| PCD-10 | Approve SLI/SLO scope, windows and thresholds. | Enables objective readiness. | OPEN |
| PCD-11 | Approve test environment and representative corpus. | Ensures repeatability and realism. | OPEN |
| PCD-12 | Approve future provider, paid service, billing account or spend cap separately. | Required before chargeable use. | OPEN |
| PCD-13 | Approve autoscaling eligibility, maximum capacity and shutdown rules. | Prevents uncontrolled scaling/unsafe termination. | OPEN |
| PCD-14 | Approve analytics/read-model freshness requirements. | Balances load and correctness. | OPEN |
| PCD-15 | Approve multi-user/workspace assumptions if scope changes. | Initial model is single-owner only. | OPEN |
| PCD-16 | Approve operational capacity review owner and cadence. | Keeps assumptions current. | OPEN |

## 22. Freeze checklist and implementation boundary

- Reconcile this document against Artifact 08 v1.0, reconciliation candidate v1.1 and accepted standards.

- Approve workload model and representative test corpus; record source/date for every measured assumption.

- Approve numeric budgets, quotas, concurrency, retry and storage limits; silence or a generic “next” is not approval.

- Map Batch 21 observability and Batch 22 configuration controls to approved budgets.

- Ensure Batch 23 backup/recovery includes capacity for backups, restore and post-restore backlog drain.

- Approve test environment, load method, safety boundaries and evidence retention.

- Preserve ₹0 initial target; separately approve any paid provider/service before activation.

- Review security, privacy, rights and governance implications of telemetry/test data.

- Record detailed contract freeze separately from implementation authorization.

Implementation boundary: documentation/specification only. This does not authorize repository edits, agent coding, migrations, load against production, provider/account creation, billing activation, cloud deployment, production generation, upload or publishing. No performance benchmark or production readiness is claimed.

## 23. Traceability to the P0 baseline

| Baseline source / batch | Relationship |
| --- | --- |
| Artifact 08 accepted decisions v1.0 | Preserves architecture, owner authority, local-first/free-first, human approval, publishing restrictions and no-paid-services boundary. |
| Artifact 08 reconciliation candidate v1.1 | Retains open freeze items and distinctions around rights, approval, authorization, QA and provider decisions. |
| Canonical Data Dictionary & Entity Ownership Registry 1.0 | Metrics retain entity ownership and avoid ambiguous status fields. |
| API & Event Contract Standard 1.0 | Commands, events, durable acknowledgement, idempotency and correlation underpin throughput/retry measurement. |
| Unified Lifecycle State & Transition Standard 1.0 | Performance does not collapse lifecycle, execution or external-operation outcomes. |
| Batch 17 State-Machine Catalogue | Uses accepted QA, rights and approval vocabularies; no performance shortcut bypasses transitions. |
| Batch 18 API/Event/Schema Pack | Aligns queue, worker, idempotency, errors, outbox/inbox and external side-effect reconciliation. |
| Batch 21 Observability | Provides logging, metrics, tracing, health, alerts, dashboards and runbooks. |
| Batch 22 Configuration/Environment/Release | Budgets, quotas and concurrency limits require versioned configuration and release controls. |
| Batch 23 Backup/DR/Continuity | Capacity includes backup/restore load, recovery ordering and backlog drain. |

## 24. Glossary

| Term | Meaning |
| --- | --- |
| Admission control | Decision to accept, defer or reject work based on approved capacity and safety constraints. |
| Backpressure | Mechanism slowing/stopping producers when downstream resources are constrained. |
| Capacity headroom | Reserved resource margin for bursts, failure recovery and variability. |
| Concurrency | Number of operations active at once within a defined resource pool. |
| Idempotency | Repeated delivery of the same logical operation does not create duplicate logical effects. |
| Queue age | Elapsed time since a queued item became eligible for processing. |
| SLI / SLO / SLA | Service Level Indicator / Objective / Agreement; distinct measurement, internal target and external commitment. |
| Throughput | Rate of completed valid work, distinguished from accepted or enqueued work. |
| Unknown external outcome | External operation may have occurred but confirmation is unavailable; reconcile before retry. |

## 25. Final status

Batch 24 establishes a performance, capacity and cost-control design framework for owner review. Actual capacity, performance targets, resource quotas, SLOs, scaling thresholds and future spend remain unapproved until measured and explicitly decided. The document preserves the current architecture and safety invariants; it does not claim implementation, benchmark results, production readiness or authorization.

END OF BATCH 24


## Source document metadata (preserved from DOCX)

- **Header:** NEXTDECODE CONTENT OS  |  P0 SPECIFICATION SERIES
- **Footer:** Batch 24 • Candidate specification • Owner freeze and implementation authorization remain separate

