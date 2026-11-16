# Google Forward Deployed Engineer (FDE) Intern — Interview Notes

These notes distill the core architectural decisions, engineering tradeoffs, and technical talking points across the 8 phases of **SprintMate**.

---

## 1. Quick Project Elevator Pitch

> *"SprintMate is an AI sprint risk copilot for engineering managers that investigates delivery bottlenecks by correlating Jira-style issue tracking with GitHub pull requests, CI test step failures, and developer capacity. Rather than letting LLMs hallucinate risk metrics, risk scoring is 100% deterministic Python rules. The LLM agents—orchestrated via Google ADK and communicating with custom tools over the Model Context Protocol (MCP)—investigate root causes, explain correlations, and propose rebalancing. All actions follow strict human-in-the-loop governance: AI can only create pending proposals, and approval requires manager role authorization, an atomic state re-check, and an append-only audit trail."*

---

## 2. Phase-by-Phase Technical Concepts

### Phase 0: Project Scaffolding & CI
1. **Clean Separation of Concerns**: Strict monorepo architecture with pure Python in `backend/` and pure React/TypeScript in `frontend/`. No leaky node dependencies in backend or vice versa.
2. **Deterministic CI Environment**: Fast unit tests execute with zero database dependency in milliseconds. Integration tests run against an isolated `postgres:16-alpine` service container with applied migrations and loaded seed data.
3. **Reproducibility**: Parameterized environment variables with `.env.example`, Docker Compose port mapping (5433 to avoid host port collisions), and non-root execution.

### Phase 1: Data Modeling & Tracker Adapters
1. **Polymorphic Tracker Adapters**: Created `BaseTrackerAdapter` and `BaseVcsAdapter` interfaces. The system works transparently with synthetic DevCore PostgreSQL tables or live GitHub REST APIs via environment variable toggle (`DATA_MODE=demo|live`).
2. **Rich Synthetic Ground Truth**: Seeded 3 teams, 12 developers, 60 issues, 30 PRs, 30 CI runs, and 5 postmortems featuring deliberate anomalies (e.g. `PAY-142` blocked by overdue `PAY-139`, `PR #211` failing `test_pool_saturation`, `David Kim` at 200% load).
3. **Database Sequence Synchronization**: Handled PostgreSQL explicit primary key vs serial sequence desynchronization after bulk-loading seed data using `setval(pg_get_serial_sequence(...))` to prevent dynamic insert collisions.

### Phase 2: Deterministic Risk Engine
1. **Explainable Deterministic Rules**: 7 mathematical rules calculate sprint risk without LLM guesswork. Each rule outputs structured `RiskFinding` dataclasses with severity, weight, affected keys, and machine-readable metadata.
2. **Workload & Capacity Math**: Developer capacity modeling ($Assigned / Capacity$) flags overload at $> 120\%$ load and finds reassignment candidates matching both skill tags and free points.
3. **Dependency Graph Traversal**: Detects transitive dependency chains where an overdue bug blocks an intermediate ticket that blocks a sprint goal deliverable (`PAY-139` -> `PAY-142` -> `PAY-150`).

### Phase 3: Model Context Protocol (MCP) Server
1. **Open Standard Tool Protocol**: Built a standalone MCP server using the official Python `mcp` SDK running over `stdio`. Decoupled from the web framework so any MCP client can consume it.
2. **Defensive Mutation Design**: The MCP tool `propose_reassignment` intentionally *never* mutates issues directly. It only creates a `PENDING` proposal, upholding the principle of least privilege.
3. **Tool Parameter Typing**: Strict type schemas on tools (`get_issue(key: str)`, `get_ci_status(pr_number: int)`, `search_issues(...)`) preventing prompt injection through malformed tool calls.

### Phase 4: Google ADK Multi-Agent Architecture
1. **Constrained 2-Agent Topology**: Supervisor root agent handles user dialogue, intent parsing, and markdown evidence grounding. Investigator sub-agent handles MCP tool execution via Google ADK's `McpToolset`.
2. **Token & Latency Telemetry**: Custom observability logger measures p50/p95 latency and token counts, calculating estimated inference cost per query using Gemini API pricing.
3. **Sub-2s Response Times**: Optimized with `gemini-3.5-flash-lite`, delivering reliable multi-step tool investigations in ~1.8 seconds.

### Phase 5: Human-in-the-Loop Governance & Concurrency
1. **Role-Based Access Control (RBAC)**: Enforced via FastAPI dependencies (`require_role("manager")`). Developers can query the assistant and browse proposals but receive `403 Forbidden` if attempting approval.
2. **Atomic State Re-check Pattern**: When a manager approves a proposal, the executor atomically verifies `issue.assignee_id == proposal.current_assignee_id`. If another engineer reassigned the issue concurrently, the proposal is marked `STALE` and the mutation safely aborts.
3. **Immutable Audit Trail**: Append-only `audit_log` records before/after JSON states, actor identity, role, timestamp, and outcome.

### Phase 6: Frontend Experience
1. **Centralized Typed API Client**: All network traffic flows through `src/api/client.ts` with zero scattered `fetch` calls in UI components. Reads base URL from `VITE_API_BASE_URL`.
2. **Clickable Evidence Grounding**: Chat answers include interactive evidence pills (`PAY-142`, `PR #211`). Clicking an evidence pill immediately slides out the Issue Drawer showing full history and blockers.
3. **Interactive Role Switcher**: Instant switching between Manager and Developer roles in the navbar, demonstrating real-time UI permission state and approval action locking.

### Phase 7: Evaluation Suite & Ground Truth Benchmarks
1. **Empirical Measurement**: 16 scenarios testing risk identification, tool selection, reassignment recommendation, and security defense.
2. **100% Precision & Recall**: Deterministic rules detected 8/8 anomalies against `ground_truth.json` with 0 false positives.
3. **Security Invariant Verification**: Programmatic tests prove that developer approvals are blocked, stale proposals are rejected, and prompt injection strings are neutralized.

---

## 3. Anticipated Interview Questions & Strong Answers

#### Q: "Why didn't you use LangChain or LlamaIndex?"
> *"LangChain and LlamaIndex introduce deep abstraction layers that make debugging multi-step failures opaque in production systems. For an enterprise engineering assistant, I wanted clean, direct control over agent communication and tool execution. By using the official Google ADK alongside the official Model Context Protocol (MCP) Python SDK, the architecture remains lightweight, explicit, and easy to explain. Tools communicate over standardized stdio streams, and agent transitions are predictable without hidden prompt bloat."*

#### Q: "Why make risk scoring deterministic if you're building an AI tool?"
> *"In forward-deployed environments, engineering leaders need numbers they can trust in executive reviews. If an LLM calculates a sprint health score of 72 today and 61 tomorrow on the exact same data due to sampling variance, managers lose trust. In SprintMate, risk scoring is 100% deterministic Python rules: 4 days blocked is always 4 days blocked. The LLM's role is what generative AI is best at: synthesizing complex cross-system narratives, discovering non-obvious correlations (like a failing CI test on a PR blocking a critical path issue), and formulating actionable reassignment proposals."*

#### Q: "How does your system handle race conditions when two managers act at once?"
> *"We implement an atomic state re-check pattern. When the Investigator agent proposes a reassignment, it records the issue's current assignee at proposal creation time. When a manager clicks 'Approve', the executor begins a database transaction, re-reads the target issue directly from PostgreSQL, and verifies that `issue.assignee_id == proposal.current_assignee_id`. If another manager or developer changed the assignee in the interim, the state check detects the discrepancy, transitions the proposal to `STALE`, logs the failed attempt in the audit trail, and aborts without mutating the issue."*

#### Q: "How do you protect the system against prompt injection?"
> *"Prompt injection is defended at three architectural boundaries: First, the database and MCP tools are strictly read-only for agents; agents cannot mutate tables even if commanded to by malicious issue descriptions. Second, tool selection is validated against rigid Pydantic schemas. Third, state mutations can only be executed through an authenticated human manager via dedicated REST endpoints with RBAC validation and state re-checks."*
