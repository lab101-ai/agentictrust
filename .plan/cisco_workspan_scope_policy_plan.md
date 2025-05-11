## Cisco × WorkSpan ‑ OAuth / Scope / Policy Plan  
*(Initial draft – version 0.1)*

---

### 1  Authorisation dimensions
1. **Company ID** – e.g. `cisco`, `ibm`
2. **Department / Role** – `sales_rep`, `sales_exec`, `engineering`, …
3. **Data Grain** – `own-row`, `company-wide`, `aggregate-cross-company`
4. **Action** – `read` / `write`

---

### 2  Scope taxonomy
Format `<verb>:<dataset>:<grain>`

| Scope String | Description |
|--------------|-------------|
| `read:sales:own` | Sales-rep; row-level access to their own deals |
| `read:sales:company` | Exec; company-level view of all Cisco sales |
| `read:sales:aggregate` | Exec; aggregated cross-company metrics (anonymised) |
| `write:sales:own` | Optional; reps updating their own pipeline |

Hierarchy: `read:sales:own` ⊂ `read:sales:company` ⊂ `read:sales:aggregate`

> Scopes stay short – dynamic values (e.g. company_id) are delegated to **RAR** / custom claims.

---

### 3  Rich Authorisation Requests (RAR)
Example attached to `/oauth/token` request:
```json
{
  "type": "read:sales:company",
  "locations": ["https://api.workspan.com"],
  "dataclass": "sales",
  "identifier": {
    "company_id": "cisco"
  }
}
```

---

### 4  Policy Engine rules (Rego sketch)
```rego
package sales_access

default allow = false

# 1. Sales execs – company + aggregate access
allow {
    input.scope in {"read:sales:company", "read:sales:aggregate"}
    input.claims.role == "sales_exec"
    input.rars[_].identifier.company_id == input.claims.company_id
}

# 2. Sales reps – own deals only
allow {
    input.scope == "read:sales:own"
    input.claims.role == "sales_rep"
    input.resource.owner_id == input.claims.user_id
}
```

---

### 5  Persona → Token mapping
| Persona | Scopes | Claims |
|---------|--------|--------|
| Cisco Sales Rep "Alice" | `read:sales:own` | `{ role:"sales_rep", company_id:"cisco" }` |
| Cisco Sales Exec "Bob" | `read:sales:company read:sales:aggregate` | `{ role:"sales_exec", company_id:"cisco" }` |
| Cisco Engineer "Carol" | _(none – request fails)_ | `{ role:"engineering" }` |

---

### 6  Token issuance snippet (Python SDK)
```python
client = AgenticTrustClient(api_base="https://auth.agentictrust.com")

token = client.token.request(
    client_id=BOB_CLIENT_ID,
    client_secret=BOB_SECRET,
    scope=["read:sales:company", "read:sales:aggregate"],
    task_description="WorkSpan dashboard load",
    required_tools=["workspan_sales_api"],
    agent_type="human",
    additional_claims={
        "role": "sales_exec",
        "company_id": "cisco",
    },
)
```

---

### 7  Aggregated-only API endpoint proposal
```
GET /sales/aggregate?metric=revenue   # requires scope: read:sales:aggregate
```
Returns anonymised cross-company statistics.

---

### 8  Integration into Demo Agents
1. Register WorkSpan tool:  
   `register_tool_with_client(client, local_tool=WorkSpanSalesAPI)`
2. Decorate agent:  
   `@secure_agent(client=client, max_scope_level="restricted")`
3. AgenticTrust handles token issuance, lineage, audit automatically.

---

### 9  PRD compliance checklist
- [x] Granular scopes
- [x] RAR binding to company_id
- [x] Short-lived tokens + refresh
- [x] Task lineage (task_id, parent_task_id)
- [x] Policy enforcement & audit trail 