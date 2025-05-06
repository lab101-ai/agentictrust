# Gap Analysis Checklist – OAuth 2.0 ABAC for LLM Agents

This document compares the AgenticTrust codebase to the requirements described in the white-paper "OAuth 2.0 ABAC for LLM Agents".

Legend: ✅ implemented   🟡 partial / PoC   🔲 missing

---

## 1 · OAuth 2.0 Fundamentals
| Area | Status | Notes |
|------|--------|-------|
| Client-Credentials grant | ✅ | `/api/oauth/token` implemented & audited |
| Refresh-Token grant | ✅ | auto-revokes used refresh token |
| Authorization Code (PKCE) | 🟡 | Back-end ready (`AuthorizationCode`, `/api/oauth/authorize`, `OAuthEngine.exchange_code_for_token`) — **missing consent UI & HITL flow** |
| Introspection endpoint | ✅ | `/api/oauth/introspect` |
| Revocation endpoint | ✅ | cascades to child tokens |
| JWKS discovery | ✅ | JWKS served at discovery route |
| OIDC meta discovery | ✅ | `.well-known/openid-configuration` |
| Device Authorization grant | 🔲 | not started |
| CIBA (back-channel) | 🔲 | not started |
| Delegation Grant support | ✅ | `/api/delegations` router, `DelegationEngine`, delegation audits |

## 2 · Attribute-Based Access Control (ABAC)
| Area | Status | Notes |
|------|--------|-------|
| Policy DB model | ✅ | CRUD via `/api/policies` |
| PolicyEngine compile/evaluate | ✅ | `core/policy/engine.py`, `evaluator.py` |
| Enforcement on token issuance | 🟡 | engine invoked; custom rule set still limited – expand condition DSL & coverage |
| Enforcement on resource access | 🔲 | middleware still missing |
| Policy hot-reload | 🟡 | YAML reload supported, no watcher |

## 3 · Granular Scopes & RAR
| Area | Status | Notes |
|------|--------|-------|
| Scope model & CRUD | ✅ | ScopeEngine |
| Implied-scope expansion | ✅ | `expand_implied_scopes` |
| Rich Authorization Requests (RAR) | 🔲 | groundwork planned; schema outlines under review |
| Registry UI | 🔲 | dashboard page missing |

## 4 · Task-Aware OAuth Extensions
| Area | Status | Notes |
|------|--------|-------|
| `task_id` / lineage persisted | ✅ | columns in `IssuedToken` + audits |
| Parent–child validation | ✅ | verified in `/token` when parent_token provided |
| Scope inheritance check | 🟡 | subset validation performed; needs advanced narrowing + expansion policy checks |
| Mandatory lineage headers middleware | 🔲 | not implemented |
| Task-chain visualisation | 🟡 | JSON API ready; UI pending |
| Delegated-token issuance & audit | ✅ | OAuthEngine consumes `grant_id`, DelegationAuditLog records events |

## 5 · Agent Lifecycle & Identity
| Area | Status | Notes |
|------|--------|-------|
| Agent register / activate | ✅ | `/api/agents/*` |
| Client-secret hashing | ✅ | PBKDF2 |
| Secret rotation | 🔲 | no endpoint/cron |
| Agent roles attribute | 🔲 | column not present |
| Watch-mode / HITL | 🔲 | future work |

## 6 · Token Security Enhancements
| Area | Status | Notes |
|------|--------|-------|
| mTLS binding | 🔲 | — |
| DPoP proof | 🔲 | — |
| Token Exchange | 🔲 | — |
| Expiry configuration | ✅ | configurable in `Config` |
| Automated key rotation | 🔲 | PoC script drafted; scheduler integration pending |
| Rate limiting / cost caps | 🔲 | none |
| Anomalous IP detection | 🔲 | none |

## 7 · Logging, Audit & Monitoring
| Area | Status | Notes |
|------|--------|-------|
| Structured JSON logs | ✅ | `utils.logger` |
| Task audit log | ✅ | `TaskAuditLog` model writes |
| Domain / IP block-list | 🔲 | table not present |
| Prompt-injection moderation | 🔲 | — |

## 8 · Federation & Third-Party Integration
| Area | Status | Notes |
|------|--------|-------|
| OIDC ID-token support | ✅ | issued when `openid` scope present |
| Token Exchange to SaaS | 🔲 | not started |
| Ephemeral credential injection | 🔲 | — |

## 9 · Documentation & DX
| Area | Status | Notes |
|------|--------|-------|
| Swagger docs | ✅ | FastAPI `/docs` |
| Getting-started guide | 🔲 | missing |
| Policy authoring cookbook | 🔲 | missing |
| Architecture diagram | 🔲 | missing |

---

### Suggested Next-Sprint Backlog
1. Finish Auth-Code + PKCE flow.
2. Middleware to enforce task lineage headers.
3. ABAC enforcement on resource endpoints.
4. Add Rich Authorization Request (`authorization_details`).
5. Secret/key rotation & rate-limiting jobs.
6. Policy hot-reload watcher.
7. Admin UI widgets for task-chain visual.
8. Delegation grant management UI & max-depth enforcement visualiser.
9. Begin mTLS / DPoP research. 