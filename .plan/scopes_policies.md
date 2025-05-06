## A. Fine‑grained Scope Catalogue

*Naming convention: `<domain>.<resource>.<action>[.<qualifier>]`*

| Domain                | Example Resources                 | Typical Actions (`read`, `create`, `update`, `delete`, `invoke`, `exchange`, `admin`) | Representative Scopes                                                        |
| --------------------- | --------------------------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| **Partner Metrics**   | adoption\_score, usage\_telemetry | read                                                                                  | `partner.adoption_score.read`, `partner.usage_telemetry.read`                |
| **Deals & Pipeline**  | deal, opportunity, quote          | read, create, update, delete, export                                                  | `deals.read`, `deals.create`, `deals.update`, `deals.delete`, `deals.export` |
| **LCI Telemetry**     | lci\_raw, lci\_summary            | read, write                                                                           | `lci.raw.read`, `lci.summary.read`, `lci.raw.write`                          |
| **Partner Directory** | partner\_profile, partner\_user   | read, update, invite                                                                  | `partner.profile.read`, `partner.profile.update`, `partner.user.invite`      |
| **Agent Registry**    | agent\_record                     | read, register, update, suspend                                                       | `agent.registry.read`, `agent.registry.register`, `agent.registry.suspend`   |
| **Token Services**    | token                             | exchange, introspect, revoke                                                          | `token.exchange`, `token.introspect`, `token.revoke`                         |
| **Workflow Engine**   | workflow\_instance                | launch, pause, resume, cancel                                                         | `workflow.launch`, `workflow.pause`, `workflow.cancel`                       |
| **File/Object Store** | object                            | read:\<obj‑id\*> ¹, write:\<obj‑id\*>                                                 | `object.read:12345`, `object.write:12345`                                    |
| **Observability**     | audit\_log, metrics               | read, export                                                                          | `audit_log.read`, `metrics.export`                                           |
| **Admin / Config**    | env\_config, secrets\_vault       | read, update                                                                          | `config.read`, `config.update`, `vault.read`                                 |

¹ Path‑scoped or tag‑scoped object claims prevent “bucket‑wide” access.

---

## B. Policy Modules

*Implemented in OPA/Rego, Cedar, or equivalent PDP language.*

| Policy Layer                    | Core Decision Logic                                                                                                            |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **Registration Policy**         | *Who* can register an agent, permissible default scopes, required attestations (signing key, mTLS cert, security‑review flag). |
| **Scope Assignment**            | Maps actor‑type **(user‑int, user‑ext, agent‑int, agent‑ext, system)** and partner/tenant to an **allowable‑scope set**.       |
| **Delegation / Token‑Exchange** | • Parent token must include `delegable=true` claim.<br>• Child scopes ⊆ parent scopes.<br>• Hop‑limit (`hop_count ≤ 3`).       |
| **Tenant Isolation**            | Reject if `partnerId` claim ≠ request parameter.<br>Block cross‑tenant resource IDs.                                           |
| **Time / Risk‑Based Access**    | Business‑hours only, or step‑up MFA for `*.export`, or deny high‑risk IP ranges.                                               |
| **Data Sensitivity Tiering**    | `dataSensitivity` claim drives stronger token binding (e.g., require `cnf` + mTLS for *highly‑restricted*).                    |
| **Rate & Concurrency Limits**   | Quotas on `token.exchange` and API calls per actor‑type.                                                                       |
| **Revocation & Logout**         | Fan‑out invalidation—any token descended from a revoked parent introspects as `revoked=true`.                                  |
| **Emergency Break‑Glass**       | Privileged auditor role can obtain `audit_log.read` via 4‑eyes approval; logs immutable.                                       |

*Compile unit tests so every positive scenario hits an **allow** clause, every negative scenario trips an **explicit deny**.*
