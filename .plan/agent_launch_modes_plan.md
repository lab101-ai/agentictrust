# Agent Launch Modes & Token Issuance – Detailed Implementation Plan

Date: 2025-05-04
Author: GPT assistant (generated)

---

## 1. Goals
* Restrict *who/what* may start an Agent and obtain a token.
* Capture **launch metadata** in every token so PolicyEngine can allow/deny based on
  – `launch_reason`
  – `launched_by` (user or agent id)
* Ensure all code paths (App + SDK) supply the correct launch context.
* Maintain backwards-compatibility for existing clients (deprecate free-form
  `launch_reason`).

## 2. Canonical Launch Modes
| Mode | `launch_reason` | Who triggers? | Typical grant | Notes |
|------|-----------------|---------------|---------------|-------|
| **Interactive User** | `user_interactive` | Registered user via UI/API | `client_credentials` (user-bound scopes) | Must present user JWT or session cookie. |
| **System / Cron** | `system_job` | Internal scheduler, cron, webhook | `client_credentials` (machine scopes) | Allowed client_ids listed in `Config.SYSTEM_CLIENT_IDS`. |
| **Agent Delegated** | `agent_delegated` | Another agent already holding a parent token | `delegated_child` (inherits scopes/tools) | Requires `parent_token` + `parent_task_id`. |

> Any other value must be rejected (`invalid_launch_reason`).

## 3. Schema Changes (app/schemas/oauth.py)
1. Replace free-text `launch_reason: str = "interactive"` with an *enum*:
   ```python
   LaunchReason = Literal["user_interactive", "system_job", "agent_delegated"]
   launch_reason: LaunchReason = "user_interactive"
   ```
2. Add `launched_by: Optional[str]` – holds **user_id** or **client_id** (for cron)
   automatically set by server when possible.
3. Update all three request models (`TokenRequestClientCredentials`,
   `TokenRequestRefreshToken`, `TokenRequestAuthorizationCode`).

## 4. DB Model Changes (app/db/models/token.py)
* Add columns:
  ```python
  launch_reason = Column(String(32), nullable=False)
  launched_by   = Column(String(64), nullable=True)  # FK to user.id or agent.client_id
  ```
* Alembic migration: populate existing rows with `"user_interactive"` and
  `launched_by = client_id` for history.

## 5. Router Adjustments (app/routers/oauth.py)
* Pass `data.launch_reason` downstream **and** compute `launched_by`:
  ```python
  launched_by = request.state.user_id or client_id  # user extracted by auth middleware
  return engine.issue_client_credentials(..., launch_reason=data.launch_reason, launched_by=launched_by)
  ```
* Same for refresh & auth-code exchanges.
* Reject unknown `launch_reason` early (`400 invalid_request`).

## 6. OAuthEngine Updates (app/core/oauth/engine.py)
* Extend public methods:
  ```python
  def issue_client_credentials(..., launch_reason: LaunchReason, launched_by: str, ...)
  def refresh_token(..., launch_reason: LaunchReason, launched_by: str, ...)
  def exchange_code_for_token(..., launch_reason: LaunchReason, launched_by: str, ...)
  ```
* Store the values in the created/rotated `IssuedToken` rows.
* Enforce *Agent Delegated* rules:
  * If `launch_reason == "agent_delegated"` → **require** `parent_token` & `parent_task_id`.
  * Scope/tool set must be subset of parent (reuse existing inheritance logic).
* Enforce *System Job* rules:
  * Only allow `client_id` in `settings.SYSTEM_CLIENT_IDS`.
  * Bypass user login.

## 7. PolicyEngine Enhancements
* Allow policies to target `token.launch_reason` & `token.launched_by`.
  Example YAML:
  ```yaml
  - when:
      launch_reason: system_job
    allow:
      scopes: [internal.db.read]
  ```

## 8. SDK / demo Updates
### sdk/security/agent_security.py
* `fetch_token()` gains `launch_reason: str = "agent_delegated"` param – passed through.
* `secure_agent` wrapper auto-injects `launch_reason="agent_delegated"` when it calls `fetch_token` for child tasks.

### demo/ scripts
* User-driven flows: pass `launch_reason="user_interactive"` explicitly.
* Cron examples: add `--launch-reason system_job` CLI flag.

## 9. Audit & Monitoring
* **TaskAuditLog** – include `launch_reason`, `launched_by` in every `token_created|token_refresh` event.
* **PolicyAuditLog** – include decision context with launch values.
* Grafana/ELK: add dashboard filter by `launch_reason`.

## 10. Migration / Roll-out Steps
1. Create Alembic revision for DB changes.
2. Update schemas & regenerate OpenAPI docs.
3. Deploy server.
4. Release SDK v0.x → note breaking change for `launch_reason` enum.
5. Update cron jobs & existing agents to send the new field.
6. Gradually tighten PolicyEngine defaults: after 2 weeks, reject any token
   without one of the allowed reasons (feature-flag **STRICT_LAUNCH_REASON**).

## 11. Testing Matrix
| Case | Expected | Covered by |
|------|----------|------------|
| User gets token w/ `user_interactive` | 200 | `tests/oauth/test_client_credentials.py::test_user_interactive` |
| Unknown launch reason | 400 | `tests/oauth/test_invalid_launch_reason.py` |
| Cron without whitelisted client_id | 403 | `tests/oauth/test_system_job_blocked.py` |
| Delegated launch missing parent token | 400 | `tests/oauth/test_delegated_missing_parent.py` |
| Delegated child exceeds parent scopes | 403 | existing scope-inherit tests |

## 12. Timeline (engineering days)
| Task | Owner | d1 | d2 | d3 | d4 |
|------|-------|----|----|----|----|
| Schema + Enum | BE | ● | | | |
| Alembic migration | BE | ● | | | |
| OAuthEngine + Routers | BE | | ● | ● | |
| SDK + secure_agent | SDK | | ● | ● | |
| PolicyEngine | BE | | | ● | |
| Audit + Dashboards | DevOps | | | ● | |
| Tests | QA | | ● | ● | |
| Docs & Release notes | PM | | | | ● |

---

## 13. Open Questions
1. Should `launched_by` for *user_interactive* be `user_id` (resource owner) or the
   agent `client_id` acting on their behalf? _Proposal_: user_id; agent is still
   in `client_id` field.
2. For **system_job**, do we require mTLS or IP allow-list as extra defence?
3. Should refresh-token rotation inherit original `launch_reason` or allow change?
   _Proposal_: inherit to maintain provenance.

---
_End of plan_
