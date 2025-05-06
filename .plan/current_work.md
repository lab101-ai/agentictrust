# Current Work

Here's a high-level walkthrough of everything under `app/` and the major end-to-end flows it enables:

---

## 1. app/config.py
Holds your `Config` class:
- Reads env-vars (secret key, DB URL, OIDC issuer, key paths, CORS origins, scope policy)
- Ensures local SQLite folder exists
- Defines token lifetimes (access/refresh) & default scopes

## 2. app/main.py
Bootstraps the FastAPI app:
- Loads or generates JWKS keys (`app.utils.keys`)
- Lifespan: init DB (`app.db.init_db`) & seed data (`app.utils.initial_data`)
- CORS, logging middleware, exception handlers
- Includes routers: agents, tools, scopes, policies, oauth, admin, users, discovery
- Exposes `/` health-check & `/api/routes`

## 3. app/db/
### 3.1 models/
SQLAlchemy models + helpers:
- **agent.py** → `Agent` clients
- **user.py** → resource-owners
- **token.py** → `IssuedToken` (access/refresh, expiry, revoked, parent/child)
- **tool.py** → `Tool` definitions
- **scope.py** → atomic OAuth scopes
- **policy.py** → `Policy` rules for scope/tool access
- **audit/** → comprehensive audit tables (`TaskAuditLog`, `ScopeAuditLog`, `PolicyAuditLog`, `TokenAuditLog`, `ResourceAuditLog`, `AgentAuditLog`, `DelegationAuditLog`) capturing every security-relevant event
- **authorization_code.py** → `AuthorizationCode` rows for PKCE Authorization Code flow
- **delegation_grant.py** → `DelegationGrant` rows representing principal → agent delegation approvals

### 3.2 migrations/
Alembic scripts for schema evolution
- `versions/` directory contains auto-generated revision files for each DB change.

## 4. app/core/
Core business logic & engines:
- **registry.py** → lazy-singleton getters (`get_scope_engine`, `get_policy_engine`) and `initialize_core_engines()` that the FastAPI lifespan hook calls so engines are ready once the DB is up.

### 4.1 High-level service modules
- **admin.py** → dashboard metrics, audit queries, token listing / revoke helpers.
- **agents.py** → CRUD + activation for `Agent` clients, tool association, and audit logging.
- **users.py** → CRUD for platform users.
- **tools.py** → CRUD tools & parameter schema handling.
- **oauth.py** → (legacy) thin helpers kept for backward-compat.
- **delegation/** → `engine.py` that manages `DelegationGrant` lifecycle (create, revoke, validate) & emits audit rows.
- **oauth/** → `engine.py` (token issuance, refresh, introspection, PKCE), `utils.py` (JWT + lineage checks) – centralised OAuth business logic used across routers.

### 4.2 Scope engine (`core/scope/`)
- **engine.py** → loads default scopes from `data/scopes.yml`, exposes `create_scope`, `expand`, `registry`, etc. Persists to DB.
- **operations.py** → functional helpers (e.g., implied-scope expansion rules).
- **utils.py / enum.py** → validation helpers & enums for scope categories.

### 4.3 Policy engine (`core/policy/`)
- **engine.py** → ABAC/OPA-style `PolicyEngine` that compiles YAML/JSON rules and caches them.
- **evaluator.py** → runtime evaluator that checks whether a given token / scope set satisfies a policy.
- **operations.py** → low-level logical operations (AND/OR, attribute matching).
- **loader.py** → YAML/JSON loader that supports hot-reloading.

### 4.4 OAuth engine (`core/oauth/`)
- **engine.py** → `OAuthEngine` façade that unifies Client Credentials, Refresh Token, and Authorization Code (PKCE) flows; handles policy evaluation, audit logging, and persistent token lineage.
- **utils.py** → shared crypto helpers for PKCE verification, JWT validation, scope-inheritance, and task-lineage checks.
- **__init__.py** exports `get_oauth_engine()` convenience loader.

### 4.5 Delegation engine (`core/delegation/`)
- **engine.py** → `DelegationEngine` providing principal → agent delegation CRUD, depth/constraint validation, and audit hooks.

These engines are used internally by routers and other cores via the singleton getters in `registry.py`.

## 5. app/routers/
HTTP ↔ core:
- `/api/agents`, `/api/tools`, `/api/scopes`, `/api/policies`, `/api/users`, `/api/delegations`
- `/api/oauth`:
   - `POST /token` (client credentials & refresh grants)
   - `POST /introspect` (validate & enrich token details)
   - `POST /revoke` (revoke token + children)
   - `GET  /authorize` (PKCE Authorization Code endpoint powered by OAuthEngine)
   - `GET  /agentinfo`, `POST /check_token_access`, `POST /audit/task` (diagnostics & audit helpers)
- `/api/admin` → dashboard stats, audit logs, token management
- `/api/discovery` → OIDC discovery docs & JWKS

### 5.1 Route reference (HTTP → Core)

#### Agents (`/api/agents`)
- **POST** `/register` – register a new agent and return a one-time `registration_token`.
- **POST** `/activate` – activate the agent using the `registration_token`.
- **GET**  `/list` – list all registered agents.
- **GET**  `/{client_id}` – retrieve a single agent.
- **PUT**  `/{client_id}` – update agent metadata & scopes.
- **DELETE** `/{client_id}` – delete/revoke an agent.
- **GET**  `/me` – placeholder for token-based self-lookup (not yet implemented).
- **GET**  `/{client_id}/tools` – list the tools assigned to an agent.
- **POST** `/{client_id}/tools/{tool_id}` – grant a tool to an agent.
- **DELETE** `/{client_id}/tools/{tool_id}` – remove a tool from an agent.

#### Tools (`/api/tools`)
- **POST** `/` – create a tool.
- **GET**  `/` – list tools (filterable by `category`/`is_active`).
- **GET**  `/{tool_id}` – read a single tool record.
- **PUT**  `/{tool_id}` – update a tool definition.
- **DELETE** `/{tool_id}` – delete a tool.
- **POST** `/{tool_id}/activate` – mark tool active.
- **POST** `/{tool_id}/deactivate` – mark tool inactive.

#### Scopes (`/api/scopes`)
- **POST** `/` – create scope.
- **GET**  `/` – list scopes.
- **GET**  `/{scope_id}` – get scope.
- **PUT**  `/{scope_id}` – update scope.
- **DELETE** `/{scope_id}` – delete scope.
- **POST** `/expand` – expand scopes & implied permissions.
- **GET**  `/registry` – flattened registry export.

#### Policies (`/api/policies`)
- CRUD endpoints identical to scopes above: **POST**, **GET**, **GET/{id}**, **PUT/{id}**, **DELETE/{id}**.

#### Users (`/api/users`)
- **POST** `/` – create user.
- **GET**  `/` – list users.
- **GET**  `/{user_id}` – get user.
- **PUT**  `/{user_id}` – update user.
- **DELETE** `/{user_id}` – delete user.

#### Delegations (`/api/delegations`)
- **POST** `/` – create delegation grant.
- **DELETE** `/{grant_id}` – revoke grant.
- **GET**  `/{grant_id}` – read grant.
- **GET**  `/principal/{principal_id}` – list grants for a principal.

#### OAuth (`/api/oauth`)
- **POST** `/token` – client_credentials, refresh_token & authorization_code exchange.
- **POST** `/introspect` – RFC 7662 introspection.
- **POST** `/revoke` – RFC 7009 revocation (+children).
- **POST** `/verify` – token & lineage verification helper.
- **POST** `/verify-tool-access` – tool-access check helper.
- **GET**  `/agentinfo` – returns agent claims for bearer token.
- **POST** `/check_token_access` – legacy helper alias.
- **GET**  `/authorize` – PKCE authorization-code endpoint.

#### Admin (`/api/admin`)
- **GET**  `/dashboard`, `/stats/dashboard` – summary stats.
- **GET**  `/audit/logs` – paginated audit feed.
- **GET**  `/tokens` – list tokens (filters).
- **GET**  `/tokens/{token_id}` – inspect token.
- **POST** `/tokens/{token_id}/revoke` – revoke token (+children optional).
- **POST** `/tokens/introspect` – introspect via OAuthEngine.
- **GET**  `/audit/task/{task_id}` – full task history.
- **GET**  `/audit/task-chain/{task_id}` – related task chain.

#### Discovery (`app/routers/discovery.py`)
- **GET** `/api/.well-known/openid-configuration`
- **GET** `/api/.well-known/jwks.json`

## 6. app/schemas/
Pydantic models powering request/response validation:
- **oauth.py** → `TokenRequest`, `IntrospectRequest`, `RevokeRequest`, plus rich enums for delegation chain, attestation, capabilities.
- **agents.py**, **tools.py**, **scopes.py**, **policies.py**, **users.py**, **admin.py** → typed DTOs for each resource.

## 7. app/utils/
Shared helpers & infra glue:
- **config.py** → YAML loader with env-override support.
- **initial_data.py** → loads YAML/JSON fixtures for agents, scopes, tools, policies and seeds DB if missing.
- **keys.py** → RSA keypair generation & JWKS exposure.
- **logger.py** → structured logging wrapper (STDOUT console, JSON log mode, bindable context for tasks & tokens).
- **oauth.py** → JWT encode/decode, PKCE verifier, token hashing utilities.

---

# Core workflows

1. **Server startup**
   - Run DB migrations & init tables.
   - Pre-load scopes (ScopeEngine) & seed config (initial_data).

2. **Agent management**
   - Register → Activate agents (`/api/agents/register → /activate`).
   - Rotate client secrets, manage tool bindings.

3. **OAuth2/OIDC flows**
   - Client Credentials → `POST /token` (returns access + refresh + optional ID Token).
   - Refresh Token → `POST /token` with `grant_type=refresh_token`.
   - Introspect / Revoke for downstream services.
   - Authorization Code (PKCE) implemented via `AuthorizationCode` model & `OAuthEngine.exchange_code_for_token()`.

   **How OAuth tokens are issued (engine internals)**
   **Client Credentials Grant**
   1. Client sends `POST /api/oauth/token` with `grant_type=client_credentials`, `client_id`, `client_secret`, and optional `scope`.
   2. `OAuthEngine.issue_client_credentials()` validates the `Agent`, optionally processes delegation, and checks PolicyEngine/ScopeEngine.
   3. `IssuedToken.create()` persists the token row (access & refresh) and writes `TokenAuditLog`/`TaskAuditLog`.
   4. JSON response `{access_token, refresh_token, token_type="Bearer", expires_in, scope, token_id, task_id}` is returned.

   **Refresh Token Grant**
   1. Client sends `POST /api/oauth/token` with `grant_type=refresh_token` and `refresh_token` value.
   2. `OAuthEngine.refresh_token()` validates the refresh token (expiry, revocation, scope subset).
   3. A fresh access (and optional refresh) token is minted, lineage fields (`parent_token_id`) are set, and audit rows are recorded.

   **Authorization Code + PKCE Grant**
   a) **Authorization request** – `GET /api/oauth/authorize` with `response_type=code`, `client_id`, `redirect_uri`, `scope`, `code_challenge`, etc.  `OAuthEngine.create_authorization_code()` stores the hashed code & PKCE challenge and immediately auto-approves (MVP).
   b) **Token exchange** – `POST /api/oauth/token` with `grant_type=authorization_code`, `code`, `client_id`, `code_verifier`, `redirect_uri`. `OAuthEngine.exchange_code_for_token()` verifies the code + PKCE, then issues tokens via `IssuedToken.create()`.

   **Introspection & Revocation**
   - `POST /api/oauth/introspect` → `OAuthEngine.introspect()` decodes the JWT and returns the associated DB row.
   - `POST /api/oauth/revoke` → `OAuthEngine.revoke()` marks the token (and, optionally, its children) as revoked.

   **Lineage & Audit**
   - Every token carries `task_id`, `parent_task_id`, and optional `delegation_grant_id` to construct a verifiable chain.
   - `TaskAuditLog`, `TokenAuditLog`, and `DelegationAuditLog` capture issuance, validation, and revocation events for end-to-end traceability.

4. **Task-level OAuth verification** (NEW)
   - Every issued token stores `task_id`, `parent_task_id`, and hashes of parent tokens.
   - Routers & utils enforce scope inheritance, lineage validation, and audit chain.

5. **Granular scopes & policies**
   - ScopeEngine expands implied scopes.
   - PolicyEngine enforces RAR-style constraints during token issuance & access checks.

6. **Tool management & audit**
   - CRUD tools, associate with scopes.
   - TaskAuditLog logs every call with timestamp, client_id, scope, task lineage.

7. **Admin dashboard & auditing**
   - `/api/admin/dashboard`, `/api/admin/audit`, `/api/admin/tokens`.
   - Bulk revoke & visualise task chains.

8. **OIDC discovery**
   - `/.well-known/openid-configuration`, `/.well-known/jwks.json` expose metadata for federated clients.

9. **Delegation flows** (NEW)
   - Principals (users/agents) can create delegation grants for downstream agents via `/api/delegations`.
   - DelegationEngine enforces scope subset, max_depth, expiry.
   - OAuthEngine consumes valid `grant_id` during token issuance to mint child tokens bound to the delegation.
   - DelegationAuditLog records grant lifecycle and delegated-token issuance events.

*This file captures the up-to-date work overview.*