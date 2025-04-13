// API service for the application

// Helper function for making API requests
async function apiRequest<T>(
  endpoint: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
  body?: any
): Promise<T> {
  const url = `/api?endpoint=${encodeURIComponent(endpoint)}`;
  
  try {
    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };
    
    if (body && (method === 'POST' || method === 'PUT')) {
      options.body = JSON.stringify(body);
    }
    
    const response = await fetch(url, options);
    
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
  token_id: string;
  client_id: string;
  task_id?: string;
  parent_task_id?: string;
  parent_token_id?: string;
  issued_at: string;
  expires_at: string;
  is_revoked: boolean;
  scope: string[];
  granted_tools?: string[];
  granted_resources?: string[];
  scope_inheritance_type?: string;
  task_description?: string;
  revoked_at?: string;
  revocation_reason?: string;
}

export interface TokenRequest {
  client_id: string;
  client_secret: string;
  scope?: string[] | string;
  task_id?: string;
  task_description?: string;
  required_tools?: string[];
  required_resources?: string[];
  parent_task_id?: string;
  parent_token?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  scope: string;
  task_id: string;
  granted_tools: string[];
  granted_resources: string[];
  parent_task_id?: string;
  parent_token_id?: string;
}

export const TokenAPI = {
  getAll: () => apiRequest<{ tokens: Token[] }>('admin/tokens').then(data => data.tokens),
  get: (tokenId: string) => apiRequest<Token>(`admin/tokens/${tokenId}`),
  revoke: (tokenId: string, reason?: string) => 
    apiRequest<{ revoked: boolean, token_id: string }>(`admin/tokens/${tokenId}/revoke`, 'POST', 
      reason ? { reason } : undefined),
  search: (params: { client_id?: string, task_id?: string, is_valid?: boolean, is_revoked?: boolean }) => 
    apiRequest<{ tokens: Token[] }>(`admin/tokens/search?${new URLSearchParams(params as any)}`).then(data => data.tokens),
  issue: (tokenRequest: TokenRequest) => 
    apiRequest<TokenResponse>('oauth/token', 'POST', tokenRequest),
  verify: (token: string, taskId?: string, parentTaskId?: string, parentToken?: string) => 
    apiRequest<{ is_valid: boolean, token_info: Token }>('oauth/verify', 'POST', {
      token,
      task_id: taskId,
      parent_task_id: parentTaskId,
      parent_token: parentToken
    }),
  introspect: (token: string, includeTaskHistory: boolean = false, includeChildren: boolean = false) => 
    apiRequest<{ active: boolean, token_info: Token, task_history?: any[], task_chain?: string[] }>('oauth/introspect', 'POST', {
      token,
      include_task_history: includeTaskHistory,
      include_children: includeChildren
    }),
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
  status: 'success' | 'failed' | 'pending';
  details?: any;
  source_ip?: string;
}

export const AuditAPI = {
  getAll: (limit: number = 20) => 
    apiRequest<{ logs: AuditLog[] }>(`admin/audit/logs?limit=${limit}`).then(data => data.logs),
  search: (params: {
    client_id?: string,
    token_id?: string,
    task_id?: string,
    event_type?: string,
    status?: string,
    limit?: number
  }) => 
    apiRequest<{ logs: AuditLog[] }>(`admin/audit/logs?${new URLSearchParams(params as any)}`).then(data => data.logs),
  getTaskHistory: (taskId: string) => 
    apiRequest<{ history: AuditLog[] }>(`admin/audit/task/${taskId}`).then(data => data.history),
  getTaskChain: (taskId: string) => 
    apiRequest<{ task_chain: string[], task_details: any[] }>(`admin/audit/task-chain/${taskId}`),
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

// Stats API functions
export interface DashboardStats {
  agents_count: number;
  tools_count: number;
  tokens_count: number;
  active_tokens_count: number;
}

export const StatsAPI = {
  getDashboardStats: () => apiRequest<DashboardStats>('admin/stats/dashboard'),
};