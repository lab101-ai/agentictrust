# Granular OAuth Scope Strategy for LLM Agents

## 1. Introduction

### 1.1 Problem Statement

Traditional OAuth 2.0 scope practices, often relying on broad permissions, are insufficient for securely managing the capabilities of LLM-based agents. Agents require fine-grained access control aligned with the principle of least privilege to mitigate risks associated with their potential autonomy and broad interaction capabilities. Overly permissive scopes grant excessive access, increasing the potential impact of compromised agents or unintended actions.

### 1.2 Goals

This document outlines a strategy for defining and implementing granular OAuth scopes tailored for LLM agents. The goals are to:

*   **Enhance Security:** Limit agent permissions to the minimum required for specific tasks.
*   **Improve Control:** Provide users and administrators with finer control over agent capabilities.
*   **Increase Transparency:** Make agent permissions clearer to users during consent and for auditing.
*   **Promote Consistency:** Establish a standard approach for defining scopes across different APIs and services used by agents.
*   **Enable Least Privilege:** Ensure agents operate with only the necessary permissions for their authorized functions.

### 1.3 Scope

This strategy covers the definition, structure, naming, hierarchy, implementation, and documentation of granular OAuth scopes specifically for LLM agents interacting with APIs.

## 2. Scope Naming Convention

A consistent, hierarchical naming convention is adopted using colons (`:`) as separators:

`{resource}:{action}:{qualifier(s)}`

*   **`{resource}` (Required):** Lowercase, singular noun identifying the primary resource (e.g., `email`, `calendar`, `file`, `repo`).
*   **`{action}` (Required):** Lowercase verb specifying the action (e.g., `read`, `create`, `update`, `delete`, `send`, `list`, `admin`). Prefer specific verbs over generic `write` where applicable.
*   **`{qualifier(s)}` (Optional):** Lowercase term(s) providing further refinement (e.g., `content`, `metadata`, `status`, `comment`, `basic`, `full`). Multiple qualifiers allowed, separated by colons.

*(Reference: `scope_naming_convention.md`)*

## 3. Scope Hierarchy and Structure

A principle of implied permissions provides structure:

*   **Qualifier Implication:** Broader scopes (less specific) generally imply the permissions of their more specific, qualified counterparts (e.g., `email:read` implies `email:read:content`).
*   **Action Implication:** The `admin` action scope implies corresponding `read` and `write` actions for that resource (e.g., `repo:admin:hooks` implies `repo:read:hooks` and `repo:write:hooks`).
*   **Documentation is Key:** All implications MUST be explicitly documented for each scope. Do not rely solely on convention for security decisions.

Scopes are logically grouped by resource for documentation and potential consent screen presentation.

*(Reference: `scope_hierarchy_structure.md`)*

## 4. Analysis of Agent Actions & Proposed Scopes

Analysis of potential agent actions (reading, writing, deleting, interacting across resources like email, calendar, files, code repositories, etc.) informed the scope design. Key proposed scopes based on the naming convention include:

*   **Email:** `email:read`, `email:read:list`, `email:read:content`, `email:send`, `email:create:draft`, `email:delete`
*   **Calendar:** `calendar:read`, `calendar:read:freebusy`, `calendar:create:event`, `calendar:update:event`, `calendar:delete:event`
*   **File:** `file:list`, `file:read:content`, `file:read:metadata`, `file:create`, `file:update`, `file:delete`, `file:admin:share`
*   **Repository:** `repo:read:code`, `repo:read:issues`, `repo:write:commit`, `repo:create:pr`, `repo:admin:hooks`
*   **Profile:** `profile:read:basic`, `profile:read:email`, `profile:write`

*(Reference: `agent_action_scope_analysis.md`, `scope_naming_convention.md`)*

## 5. Guidelines for API Developers

API developers MUST adhere to the following when implementing the scope strategy:

1.  **Define Scopes:** Follow the naming convention and documentation requirements when creating new scopes.
2.  **Map Endpoints:** Map each API endpoint/operation to the most specific required scope(s).
3.  **Enforce Checks:** Implement scope checks within the API, validating the token's granted scopes against required scopes (considering hierarchy) before processing requests.
4.  **Reject Unauthorized Requests:** Return HTTP `403 Forbidden` with `WWW-Authenticate` header indicating `insufficient_scope` and the required scope(s).
5.  **Document Thoroughly:** Maintain a central scope registry and document required scopes in API references.
6.  **Manage Evolution:** Follow best practices for adding, modifying (discouraged), and deprecating scopes.

*(Reference: `api_developer_scope_guidelines.md`)*

## 6. Handling Resource Identifiers

This scope strategy focuses on permissions related to *types* of resources and actions (e.g., `file:read:content`). Access control for *specific* resource instances (e.g., file ID `123`) is the responsibility of the Resource Server's authorization logic. This logic can use information from the token (e.g., `sub`, `delegator_sub`, custom claims) or other contextual data, but resource IDs should not be embedded in scope strings.

## 7. Consent Screen Considerations

While scopes are granular, the user consent screen should aim for clarity:

*   **Group Related Scopes:** Group scopes by resource (e.g., "Access your Email", "Manage your Calendar").
*   **Use User-Friendly Descriptions:** Display the documented user-facing description for each scope or group.
*   **Highlight Sensitive Permissions:** Clearly indicate scopes granting write, delete, admin, or access to sensitive data.
*   **Allow Granular Consent (Optional):** Consider allowing users to selectively grant/deny specific granular scopes within a group, though this adds complexity.

## 8. Relationship to Agent Capabilities and Intent

OAuth scopes define *permissions* granted to the agent (the client application acting on behalf of the user). They represent *what* the agent *can* do.

This is distinct from:

*   **Agent Capabilities:** The inherent functions the agent model/instance *is able* to perform (potentially represented by claims like `agent_capabilities` in an OIDC-A context).
*   **Delegation Intent/Purpose:** The specific reason *why* a user delegated authority to the agent (potentially represented by claims like `delegation_purpose`).

Authorization decisions at the Resource Server should consider both the granted OAuth scopes *and* potentially other factors like agent capabilities, delegation context, and specific resource policies (ABAC).

## 9. Scope Evolution

The scope definitions should be treated as a living standard. A process for proposing, reviewing, and approving new scopes or modifications should be established, involving API owners and security teams. Changes must be versioned and communicated clearly.

## 10. Conclusion

This granular OAuth scope strategy, based on the `{resource}:{action}:{qualifier(s)}` naming convention and associated guidelines, provides a robust framework for applying the principle of least privilege to LLM agents. Consistent implementation across APIs is key to enhancing security and control in agent-driven ecosystems.



## 11. Implementation Examples

This section provides practical examples illustrating how the granular OAuth scope strategy would be implemented and used in various parts of the OAuth 2.0 flow.

### Example Scenario

An LLM agent client application ("Agent Assist") wants to read a user's calendar to find free time slots and draft an email reply based on that information.

**Required Permissions:**

*   Read calendar free/busy status.
*   Create draft emails.

**Corresponding Scopes:**

*   `calendar:read:freebusy`
*   `email:create:draft`

### 11.1 Client Authorization Request

The "Agent Assist" client initiates the OAuth 2.0 Authorization Code flow by redirecting the user to the Authorization Server (AS) with the required scopes:

```http
GET /authorize?response_type=code
  &client_id=agent_assist_client
  &redirect_uri=https://client.example.com/callback
  &scope=openid%20calendar:read:freebusy%20email:create:draft
  &state=xyz789
  &code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM
  &code_challenge_method=S256
```

*Key Point:* The client requests the *specific, granular* scopes it needs (`calendar:read:freebusy`, `email:create:draft`) along with `openid` for authentication.

### 11.2 Authorization Server: Consent Screen (Conceptual)

The Authorization Server authenticates the user and presents a consent screen based on the requested scopes and their documented user-facing descriptions:

```text
Allow "Agent Assist" to access your account?

Agent Assist is requesting permission to:

[ ] Access your Profile (Required)
    - View your basic profile information

[X] Access your Calendar
    [X] View your free/busy status

[X] Access your Email
    [X] Create draft emails

By allowing access, Agent Assist will be able to perform these actions on your behalf.

[ Allow ] [ Deny ]
```

*Key Points:*
*   Scopes are grouped by resource (`Calendar`, `Email`).
*   User-friendly descriptions are shown.
*   The granularity allows the user (in theory, if the UI supports it) to potentially deny specific permissions, although here both requested permissions are checked by default.

### 11.3 Authorization Server: Issuing Tokens

Assuming the user clicks "Allow", the AS redirects back to the client with an authorization code. The client exchanges the code for tokens.

The AS issues an Access Token (e.g., JWT) and potentially an ID Token. The Access Token contains the granted scopes.

**Example JWT Access Token Payload:**

```json
{
  "iss": "https://auth.example.com",
  "sub": "user_123",
  "aud": "https://api.example.com",
  "exp": 1714482000,
  "iat": 1714478400,
  "jti": "abc123def456",
  "client_id": "agent_assist_client",
  "scope": "openid calendar:read:freebusy email:create:draft" 
}
```

*Key Point:* The `scope` claim contains the exact scopes granted by the user.

### 11.4 API Endpoint Definition & Documentation

The Calendar API and Email API document the scopes required for their endpoints:

**Calendar API Documentation:**

*   **Endpoint:** `GET /v1/me/freebusy`
*   **Description:** Retrieves the free/busy status for the authenticated user.
*   **Required Scope:** `calendar:read:freebusy` OR `calendar:read`

**Email API Documentation:**

*   **Endpoint:** `POST /v1/me/emails/drafts`
*   **Description:** Creates a new draft email.
*   **Required Scope:** `email:create:draft` OR `email:write`

*Key Point:* Documentation clearly states the minimum required scope(s) and potentially broader scopes that also grant access (due to hierarchy).

### 11.5 API Endpoint: Scope Enforcement Logic (Pseudocode)

When "Agent Assist" calls the API using the access token:

**Request:**

```http
GET /v1/me/freebusy HTTP/1.1
Host: api.example.com
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

**API Enforcement Logic (Simplified Pseudocode):**

```python
def handle_get_freebusy(request):
  # 1. Validate Access Token (signature, expiry, audience, issuer)
  access_token = validate_token(request.headers['Authorization'])
  if not access_token:
    return 401 Unauthorized

  # 2. Get Granted Scopes from Token
  granted_scopes = access_token.get('scope', '').split(' ')

  # 3. Define Required Scopes for this endpoint
  required_scopes = ['calendar:read:freebusy', 'calendar:read'] 

  # 4. Check if any required scope is granted
  has_sufficient_scope = False
  for req_scope in required_scopes:
    if req_scope in granted_scopes:
      has_sufficient_scope = True
      break
      
  # Consider hierarchy: If 'calendar:read' is granted, it implies 'calendar:read:freebusy'
  # (This logic might be more complex, potentially checking a scope definition service)
  if 'calendar:read' in granted_scopes:
      has_sufficient_scope = True 

  # 5. Enforce Decision
  if not has_sufficient_scope:
    return 403 Forbidden (error='insufficient_scope', required_scope='calendar:read:freebusy')

  # 6. Proceed with API logic if scope check passes
  data = get_freebusy_data(access_token['sub'])
  return 200 OK (data)

```

*Key Points:*
*   Token validation occurs first.
*   Granted scopes are extracted.
*   Required scopes for the specific endpoint are checked against granted scopes.
*   Hierarchy rules are applied (e.g., granting `calendar:read` allows access to endpoint requiring `calendar:read:freebusy`).
*   `403 Forbidden` with `insufficient_scope` error is returned if access is denied.

### 11.6 API Endpoint: Insufficient Scope Response

If "Agent Assist" tries to call an endpoint for which it lacks the required scope (e.g., tries to send an email using the token from step 3):

**Request:**

```http
POST /v1/me/emails/send HTTP/1.1
Host: api.example.com
Authorization: Bearer <JWT_ACCESS_TOKEN>
Content-Type: application/json

{ ... email data ... }
```

**API Response:**

```http
HTTP/1.1 403 Forbidden
WWW-Authenticate: Bearer error="insufficient_scope", error_description="The request requires 'email:send' scope.", scope="email:send"
Content-Type: application/json

{
  "error": "insufficient_scope",
  "error_description": "The request requires 'email:send' scope."
}
```

*Key Point:* The API clearly indicates *why* access was denied and *which* scope was missing.

These examples illustrate the flow from client request through user consent, token issuance, and API enforcement, demonstrating how the granular scope strategy operates in practice.
