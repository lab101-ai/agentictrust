// API service for the application

// Helper function for making API requests

// Define options type
interface ApiRequestOptions {
  isDirect?: boolean;
}

export async function apiRequest<T>(
  endpoint: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
  body?: any,
  options?: ApiRequestOptions // Add options argument
): Promise<T> {
  // Determine URL based on options.isDirect
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || '';
  const url = options?.isDirect 
    ? `${baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}` 
    : `/api?endpoint=${encodeURIComponent(endpoint)}`;
  
  console.log(`Making API request${options?.isDirect ? ' directly' : ''} to: ${url}`); // Add logging

  try {
    const requestOptions: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };
    
    if (body && (method === 'POST' || method === 'PUT')) {
      requestOptions.body = JSON.stringify(body);
    }
    
    const response = await fetch(url, requestOptions);
    
    // Check if response is empty before parsing JSON
    const text = await response.text();
    
    const data = text.length ? JSON.parse(text) : {};
    
    if (!response.ok) {
      throw new Error(data.error || data.message || 'An error occurred');
    }
    
    return data as T;
  } catch (error) {
    console.error(`Error calling ${endpoint}:`, error);
    throw error;
  }
}

// Agent related API functions
export interface Agent {
  client_id: string;
  agent_name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  max_scope_level?: string;
  registration_token?: string;
  tools?: Tool[];
  tool_ids?: string[];
  allowed_tools?: string[];
  allowed_resources?: string[];
}

export interface AgentRegistration {
  agent_name: string;
  description?: string;
  allowed_resources?: string[];
  max_scope_level?: string;
  tool_ids?: string[];
}

export interface AgentCredentials {
  client_id: string;
  client_secret: string;
  registration_token: string;
}

export const AgentAPI = {
  getAll: () => apiRequest<{ agents: Agent[] }>('agents/list').then(data => data.agents),
  get: (clientId: string) => apiRequest<Agent>(`agents/${clientId}`),
  create: (agent: AgentRegistration) => 
    apiRequest<{ agent: Agent, credentials: AgentCredentials }>('agents/register', 'POST', agent)
      .then(data => ({ ...data.agent, credentials: data.credentials })),
  update: (clientId: string, agent: Partial<AgentRegistration>) => 
    apiRequest<{ message: string, agent: Agent }>(`agents/${clientId}`, 'PUT', agent)
      .then(data => data.agent),
  activate: (registrationToken: string) => 
    apiRequest<{ agent: Agent }>('agents/activate', 'POST', { registration_token: registrationToken })
      .then(data => data.agent),
  delete: (clientId: string) => 
    apiRequest<{ message: string }>(`agents/${clientId}`, 'DELETE'),
  getTools: (clientId: string) => 
    apiRequest<{ tools: Tool[] }>(`agents/${clientId}/tools`).then(data => data.tools),
  addTool: (clientId: string, toolId: string) => 
    apiRequest<{ agent: Agent }>(`agents/${clientId}/tools/${toolId}`, 'POST')
      .then(data => data.agent),
  removeTool: (clientId: string, toolId: string) => 
    apiRequest<{ agent: Agent }>(`agents/${clientId}/tools/${toolId}`, 'DELETE')
      .then(data => data.agent),
};

// Tool related API functions
export interface Tool {
  tool_id: string;
  name: string;
  description?: string;
  category?: string;
  is_active: boolean;
  permissions_required?: string[];
  parameters?: any[];
  inputSchema?: any[] | {
    type?: string;
    properties?: Record<string, any>;
    required?: string[];
    [key: string]: any;
  };
  created_at?: string;
  updated_at?: string;
}

export interface ToolRegistration {
  name: string;
  description?: string;
  category?: string;
  permissions_required?: string[];
  parameters?: any[];
  inputSchema?: any[] | {
    type?: string;
    properties?: Record<string, any>;
    required?: string[];
    [key: string]: any;
  };
}

export const ToolAPI = {
  getAll: () => apiRequest<{ tools: Tool[] }>('tools').then(data => data.tools),
  get: (toolId: string) => apiRequest<Tool>(`tools/${toolId}`),
  create: (tool: ToolRegistration) => 
    apiRequest<{ message: string, tool: Tool }>('tools', 'POST', tool).then(data => data.tool),
  update: (toolId: string, tool: Partial<ToolRegistration>) => 
    apiRequest<{ message: string, tool: Tool }>(`tools/${toolId}`, 'PUT', tool).then(data => data.tool),
  delete: (toolId: string) => 
    apiRequest<{ message: string }>(`tools/${toolId}`, 'DELETE'),
  activate: (toolId: string) => 
    apiRequest<{ message: string, tool: Tool }>(`tools/${toolId}/activate`, 'POST').then(data => data.tool),
  deactivate: (toolId: string) => 
    apiRequest<{ message: string, tool: Tool }>(`tools/${toolId}/deactivate`, 'POST').then(data => data.tool),
};

// Token related API functions
export interface Token {
  token_id: string; // Corresponds to JTI
  client_id: string;
  active?: boolean; // Only from introspection
  scope: string; // Space-separated string
  token_type?: string; // Typically Bearer
  exp: number; // Expiration timestamp
  iat: number; // Issued at timestamp
  sub: string; // Subject - Should be agent_instance_id for OIDC-A
  aud: string; // Audience
  iss: string; // Issuer
  // OIDC-A Claims
  agent_instance_id: string;
  agent_type?: string | null;
  agent_model?: string | null;
  agent_version?: string | null;
  agent_provider?: string | null;
  delegator_sub?: string | null;
  delegation_chain?: any[] | null; // Parsed JSON
  delegation_purpose?: string | null;
  delegation_constraints?: Record<string, any> | null; // Parsed JSON
  agent_capabilities?: string[] | null; // Parsed JSON
  agent_trust_level?: string | null;
  agent_attestation?: Record<string, any> | null; // Parsed JSON
  agent_context_id?: string | null;
  // Custom Claims (Optional)
  task_id?: string | null;
  parent_task_id?: string | null;
  parent_token_id?: string | null; // Maybe available in some contexts
  granted_tools?: string[] | null; // Parsed from space-separated string
  granted_resources?: string[] | null; // Parsed from space-separated string
  scope_inheritance_type?: string | null;
  task_description?: string | null;
  // Fields below might only be present in admin/DB views
  is_revoked?: boolean;
  issued_at?: string; // ISO string format from DB potentially
  expires_at?: string; // ISO string format from DB potentially
  revoked_at?: string | null;
  revocation_reason?: string | null;
}

export interface TokenRequest {
  grant_type: 'client_credentials' | 'refresh_token';
  client_id: string;
  client_secret?: string; // Required for client_credentials
  refresh_token?: string; // Required for refresh_token
  scope?: string; // Space-separated string
  // OIDC-A Claims (Primarily for client_credentials)
  agent_instance_id?: string; // Required for client_credentials
  agent_type?: string;
  agent_model?: string;
  agent_provider?: string;
  agent_version?: string; // This might come from Agent record usually
  delegator_sub?: string;
  delegation_chain?: any[]; // Send as array, backend expects JSON string
  delegation_purpose?: string;
  delegation_constraints?: Record<string, any>; // Send as object
  agent_capabilities?: string[]; // Send as array
  agent_trust_level?: string;
  agent_attestation?: Record<string, any>; // Send as object
  agent_context_id?: string;
  // Custom Claims (Optional)
  task_id?: string;
  task_description?: string;
  required_tools?: string[]; // May not be standard, specific to app
  required_resources?: string[]; // May not be standard, specific to app
  parent_task_id?: string;
  parent_token?: string; // May not be standard, specific to app
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string; // e.g., Bearer
  expires_in: number;
  scope: string; // Space-separated string
  token_id: string; // JTI
  id_token?: string; // Optional ID Token JWT string
  // Custom fields (Optional)
  task_id?: string;
  parent_task_id?: string;
  parent_token_id?: string;
  granted_tools?: string; // Backend sends space-separated string
  granted_resources?: string; // Backend sends space-separated string
}

export interface IntrospectionResponse extends Token {
  active: boolean;
}

export interface AgentInfoResponse extends Token {}

export const TokenAPI = {
  getAll: () => apiRequest<{ tokens: Token[] }>('admin/tokens').then(data => data.tokens),
  get: (tokenId: string) => apiRequest<Token>(`admin/tokens/${tokenId}`),
  revoke: (tokenId: string, reason?: string) => 
    apiRequest<{ message: string }>(`oauth/revoke`, 'POST', { 
      token: tokenId, 
      reason: reason 
      // TODO: Add client auth if needed by backend 
    }).then(data => data.message === 'Token revoked successfully'),
  search: (params: { client_id?: string, task_id?: string, is_valid?: boolean, is_revoked?: boolean }) => 
    apiRequest<{ tokens: Token[] }>(`admin/tokens/search?${new URLSearchParams(params as any)}`).then(data => data.tokens),
  
  issue: (tokenRequest: TokenRequest) => {
    // Prepare body, converting complex types if backend expects JSON strings
    const body: any = { ...tokenRequest };
    if (body.delegation_chain) {
      body.delegation_chain = JSON.stringify(body.delegation_chain);
    }
    if (body.delegation_constraints) {
      body.delegation_constraints = JSON.stringify(body.delegation_constraints);
    }
    if (body.agent_capabilities) {
      body.agent_capabilities = JSON.stringify(body.agent_capabilities);
    }
    if (body.agent_attestation) {
      body.agent_attestation = JSON.stringify(body.agent_attestation);
    }
    // Remove client_secret if grant_type is refresh_token
    if (body.grant_type === 'refresh_token') {
        delete body.client_secret;
        delete body.agent_instance_id; // Not needed/used for refresh
    } else {
        delete body.refresh_token;
    }

    return apiRequest<TokenResponse>('oauth/token', 'POST', body);
  },

  verify: (token: string, taskId?: string, parentTaskId?: string, parentToken?: string) => 
    apiRequest<{ is_valid: boolean, token_info: Token }>('oauth/verify', 'POST', { // Endpoint likely custom
      token,
      task_id: taskId,
      parent_task_id: parentTaskId,
      parent_token_id: parentToken // Assuming this maps to parent_token_id if needed
    }).then(data => data.is_valid && data.token_info ? data.token_info : null),
  
  introspect: (token: string) => 
    apiRequest<IntrospectionResponse>('oauth/introspect', 'POST', { token }),
    
  agentinfo: (accessToken: string) => 
    // agentinfo typically uses Authorization header, apiRequest needs modification
    // Temporary workaround: pass token via query/body if backend proxy allows
    // Proper fix: modify apiRequest to handle Auth headers or use a different fetch mechanism
    apiRequest<AgentInfoResponse>(`oauth/agentinfo?token=${accessToken}`, 'GET'), // Or POST if needed by proxy
    // Example using fetch directly with header:
    /*
    async (accessToken: string): Promise<AgentInfoResponse> => {
      const response = await fetch('/api?endpoint=oauth/agentinfo', { // Assuming proxy endpoint
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });
      const text = await response.text();
      const data = text.length ? JSON.parse(text) : {};
      if (!response.ok) {
        throw new Error(data.error || data.message || 'AgentInfo request failed');
      }
      return data as AgentInfoResponse;
    }
    */
};

// Audit log related API functions
export interface AuditLog {
  log_id: string;
  timestamp: string;
  client_id: string;
  task_id?: string;
  parent_task_id?: string;
  token_id?: string;
  event_type: string;
  status: string;
  details?: any;
  source_ip?: string;
}

export interface AuditSearchParams {
  taskId?: string;
  clientId?: string;
  tokenId?: string;
  eventType?: string;
  status?: string;
  fromDate?: string;
  toDate?: string;
  limit?: number;
}

export const AuditAPI = {
  getAll: (limit: number = 20) => 
    apiRequest<{ logs: AuditLog[] }>(`admin/audit/logs?limit=${limit}`).then(data => data.logs),
  get: (logId: string) =>
    apiRequest<AuditLog>(`admin/audit/logs/${logId}`),
  search: (params: AuditSearchParams) => {
    const queryParams = new URLSearchParams();
    
    // Map the frontend params to API params
    const paramMap: Record<string, string> = {
      taskId: 'task_id',
      clientId: 'client_id',
      tokenId: 'token_id',
      eventType: 'event_type',
      status: 'status',
      fromDate: 'from_date',
      toDate: 'to_date',
      limit: 'limit'
    };
    
    // Build query parameters
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        const apiKey = paramMap[key] || key;
        queryParams.append(apiKey, value.toString());
      }
    });
    
    return apiRequest<{ logs: AuditLog[] }>(`admin/audit/logs?${queryParams}`).then(data => data.logs);
  },
  getTaskHistory: (taskId: string) => 
    apiRequest<{ history: AuditLog[] }>(`admin/audit/task/${taskId}`).then(data => data.history),
  // Define interface for task chain response
  getTaskChain: (taskId: string) => 
    apiRequest<{ 
      task_chain: string[], 
      task_details: any[], 
      root_task_id: string 
    }>(`admin/audit/task-chain/${taskId}`)
      .catch(error => {
        console.error(`Error fetching task chain for ${taskId}:`, error);
        throw error;
      }),
};

// Scope related API functions
export interface Scope {
  scope_id: string;
  name: string;
  description: string;
  category: string;
  is_sensitive?: boolean;
  requires_approval?: boolean;
  is_default?: boolean;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ScopeRegistration {
  name: string;
  description: string;
  category: string;
  is_sensitive?: boolean;
  requires_approval?: boolean;
  is_default?: boolean;
  is_active?: boolean;
}

export const ScopeAPI = {
  getAll: () => apiRequest<{ scopes: Scope[] }>('scopes').then(data => data.scopes),
  get: (scopeId: string) => apiRequest<Scope>(`scopes/${scopeId}`),
  create: (scope: ScopeRegistration) => 
    apiRequest<Scope>('scopes', 'POST', scope),
  update: (scopeId: string, scope: Partial<ScopeRegistration>) => 
    apiRequest<Scope>(`scopes/${scopeId}`, 'PUT', scope),
  delete: (scopeId: string) => 
    apiRequest<{ message: string }>(`scopes/${scopeId}`, 'DELETE'),
  activate: (scopeId: string) => 
    apiRequest<Scope>(`scopes/${scopeId}/activate`, 'POST'),
  deactivate: (scopeId: string) => 
    apiRequest<Scope>(`scopes/${scopeId}/deactivate`, 'POST'),
  getDefault: () => 
    apiRequest<{ scopes: Scope[] }>('scopes/default', 'GET').then(data => data.scopes),
  addDefault: () => 
    apiRequest<{ message: string }>('scopes/default', 'POST'),
};

// Policy related API functions
export interface Policy {
  policy_id: string;
  name: string;
  description?: string;
  effect: 'allow' | 'deny';
  conditions: any; // JSON structure of condition rules
  scopes?: string[];
  priority: number;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface PolicyRegistration {
  name: string;
  description?: string;
  effect: 'allow' | 'deny';
  conditions: any; // JSON structure or string
  scopes?: string[];
  priority?: number;
  is_active?: boolean;
}

export interface PolicyEvaluationRequest {
  context: {
    agent?: any;
    resource?: any;
    action?: any;
    environment?: any;
  };
  scope?: string;
}

export interface PolicyEvaluationResponse {
  access: boolean;
  reason: string;
  policy?: Policy;
}

export const PolicyAPI = {
  getAll: () => apiRequest<{ policies: Policy[] }>('policies').then(data => data.policies),
  get: (policyId: string) => apiRequest<Policy>(`policies/${policyId}`),
  create: (policy: PolicyRegistration) => apiRequest<Policy>('policies', 'POST', policy),
  update: (policyId: string, policy: Partial<PolicyRegistration>) => 
    apiRequest<Policy>(`policies/${policyId}`, 'PUT', policy),
  delete: (policyId: string) => 
    apiRequest<{message: string}>(`policies/${policyId}`, 'DELETE'),
  activate: (policyId: string) => 
    apiRequest<Policy>(`policies/${policyId}/activate`, 'PUT'),
  deactivate: (policyId: string) => 
    apiRequest<Policy>(`policies/${policyId}/deactivate`, 'PUT'),
  evaluate: (request: PolicyEvaluationRequest) => 
    apiRequest<PolicyEvaluationResponse>('policies/evaluate', 'POST', request),
  test: (policy: PolicyRegistration, context: any) => 
    apiRequest<PolicyEvaluationResponse>('policies/test', 'POST', { policy, context }),
  getMetrics: () => apiRequest<{
    evaluations: {
      total: number;
      allowed: number;
      denied: number;
      byDay: number[];
    };
    policies: {
      total: number;
      active: number;
      allow: number;
      deny: number;
    };
    topDenied: Array<{name: string; count: number}>;
    topAllowed: Array<{name: string; count: number}>;
  }>('policies/metrics')
};

// User related API functions
export interface User {
  user_id: string;
  username: string;
  email: string;
  full_name?: string;
  department?: string;
  job_title?: string;
  level?: string;
  is_active: boolean;
  is_external?: boolean;
  scopes?: string[];
  policies?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface UserRegistration {
  username: string;
  email: string;
  full_name?: string;
  hashed_password?: string;
  department?: string;
  job_title?: string;
  level?: string;
  is_external?: boolean;
  scopes?: string[];
  policies?: string[];
  is_active?: boolean;
}

export const UserAPI = {
  getAll: () => apiRequest<{ users: User[] }>('users').then(data => data.users),
  get: (userId: string) => apiRequest<User>(`users/${userId}`),
  create: (user: UserRegistration) =>
    apiRequest<{ message: string; user: User }>('users', 'POST', user).then(d => d.user),
  update: (userId: string, user: Partial<UserRegistration>) =>
    apiRequest<{ message: string; user: User }>(`users/${userId}`, 'PUT', user).then(d => d.user),
  delete: (userId: string) => apiRequest<{ message: string }>(`users/${userId}`, 'DELETE'),
};

// Stats API functions
export interface DashboardStats {
  agents_count: number;
  tools_count: number;
  tokens_count: number;
  active_tokens_count: number;
  policies_count?: number;
  users_count?: number;
}

export const StatsAPI = {
  getDashboardStats: () => apiRequest<DashboardStats>('admin/stats/dashboard'),
};

// Discovery related API functions
export interface OIDCConfiguration {
  issuer: string;
  jwks_uri: string;
  token_endpoint: string;
  revocation_endpoint: string;
  introspection_endpoint: string;
  response_types_supported: string[];
  subject_types_supported: string[];
  id_token_signing_alg_values_supported: string[];
  scopes_supported: string[];
  token_endpoint_auth_methods_supported: string[];
  claims_supported: string[];
  grant_types_supported: string[];
  agent_claims_supported: string[];
  attestation_formats_supported: string[];
  code_challenge_methods_supported: string[];
}

export interface JWKS {
  keys: Array<{
    kid: string;
    kty: string;
    use: string;
    alg: string;
    n: string;
    e: string;
  }>;
}

export const DiscoveryAPI = {
  getOIDCConfiguration: () => 
    // Use the new API route for discovery endpoints 
    fetch('/api/discovery?endpoint=.well-known/openid-configuration')
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      }),
  getJWKS: () => 
    // Use the new API route for discovery endpoints
    fetch('/api/discovery?endpoint=.well-known/jwks.json')
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      }),
};