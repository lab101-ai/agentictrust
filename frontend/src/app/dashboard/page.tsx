import { StatsCard } from "@/components/dashboard/StatsCard";
import { RegisterAgentDialog } from "@/components/dashboard/RegisterAgentDialog";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

export default function DashboardPage() {
  // Mock data for demonstration
  const stats = {
    agentsCount: 5,
    toolsCount: 12,
    tokensCount: 25,
    activeTokensCount: 18
  };

  const agents = [
    { client_id: "agent-123", agent_name: "Calendar Assistant", is_active: true, created_at: "2023-04-01" },
    { client_id: "agent-456", agent_name: "Data Processor", is_active: true, created_at: "2023-03-15" },
    { client_id: "agent-789", agent_name: "Code Helper", is_active: false, created_at: "2023-02-28" },
  ];

  const tools = [
    { tool_id: "tool-123", name: "Calendar API", category: "API", is_active: true },
    { tool_id: "tool-456", name: "File Reader", category: "File Operations", is_active: true },
    { tool_id: "tool-789", name: "Data Analyzer", category: "AI/ML", is_active: false },
  ];

  const tokens = [
    { token_id: "token-123", client_id: "agent-123", task_id: "task-abc", issued_at: "2023-04-01 14:30", expires_at: "2023-04-01 15:30" },
    { token_id: "token-456", client_id: "agent-456", task_id: "task-def", issued_at: "2023-04-01 15:45", expires_at: "2023-04-01 16:45" },
  ];

  const logs = [
    { log_id: "log-123", timestamp: "2023-04-01 14:35", client_id: "agent-123", task_id: "task-abc", event_type: "API_CALL", status: "success" },
    { log_id: "log-456", timestamp: "2023-04-01 14:40", client_id: "agent-123", task_id: "task-abc", event_type: "TOKEN_VALIDATE", status: "success" },
    { log_id: "log-789", timestamp: "2023-04-01 15:50", client_id: "agent-456", task_id: "task-def", event_type: "API_CALL", status: "failed" },
  ];

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Admin Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatsCard value={stats.agentsCount} label="Registered Agents" />
        <StatsCard value={stats.toolsCount} label="Registered Tools" />
        <StatsCard value={stats.tokensCount} label="Total Tokens" />
        <StatsCard value={stats.activeTokensCount} label="Active Tokens" />
      </div>
      
      <Card id="agents">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Agents</CardTitle>
          <RegisterAgentDialog />
        </CardHeader>
        <CardContent>
          {agents.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Client ID</TableHead>
                  <TableHead>Agent Name</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {agents.map((agent) => (
                  <TableRow key={agent.client_id}>
                    <TableCell>{agent.client_id}</TableCell>
                    <TableCell>{agent.agent_name}</TableCell>
                    <TableCell>
                      <Badge variant={agent.is_active ? "default" : "secondary"}>
                        {agent.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell>{agent.created_at}</TableCell>
                    <TableCell className="space-x-2">
                      <Button variant="outline" size="sm">View</Button>
                      <Button variant="outline" size="sm">Tools</Button>
                      <Button variant="destructive" size="sm">Delete</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="bg-muted p-4 rounded-md text-center">
              No agents registered yet. Click "Register New Agent" to create one.
            </div>
          )}
        </CardContent>
      </Card>
      
      <Card id="tools">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Tools</CardTitle>
          <Button>Register New Tool</Button>
        </CardHeader>
        <CardContent>
          {tools.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tool ID</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tools.map((tool) => (
                  <TableRow key={tool.tool_id}>
                    <TableCell>{tool.tool_id}</TableCell>
                    <TableCell>{tool.name}</TableCell>
                    <TableCell>{tool.category || 'N/A'}</TableCell>
                    <TableCell>
                      <Badge variant={tool.is_active ? "default" : "secondary"}>
                        {tool.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="space-x-2">
                      <Button variant="outline" size="sm">View</Button>
                      <Button variant="outline" size="sm">Edit</Button>
                      <Button variant="destructive" size="sm">Delete</Button>
                      {tool.is_active ? (
                        <Button variant="secondary" size="sm">Deactivate</Button>
                      ) : (
                        <Button variant="default" size="sm">Activate</Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="bg-muted p-4 rounded-md text-center">
              No tools registered yet. Click "Register New Tool" to create one.
            </div>
          )}
        </CardContent>
      </Card>
      
      <Card id="tokens">
        <CardHeader>
          <CardTitle>Active Tokens</CardTitle>
        </CardHeader>
        <CardContent>
          {tokens.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Token ID</TableHead>
                  <TableHead>Client ID</TableHead>
                  <TableHead>Task ID</TableHead>
                  <TableHead>Issued At</TableHead>
                  <TableHead>Expires At</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tokens.map((token) => (
                  <TableRow key={token.token_id}>
                    <TableCell>{token.token_id}</TableCell>
                    <TableCell>{token.client_id}</TableCell>
                    <TableCell>{token.task_id}</TableCell>
                    <TableCell>{token.issued_at}</TableCell>
                    <TableCell>{token.expires_at}</TableCell>
                    <TableCell className="space-x-2">
                      <Button variant="outline" size="sm">View</Button>
                      <Button variant="destructive" size="sm">Revoke</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="bg-muted p-4 rounded-md text-center">
              No active tokens available.
            </div>
          )}
        </CardContent>
      </Card>
      
      <Card id="audit">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Recent Audit Logs</CardTitle>
          <Button variant="outline">View All Logs</Button>
        </CardHeader>
        <CardContent>
          {logs.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>Client ID</TableHead>
                  <TableHead>Task ID</TableHead>
                  <TableHead>Event Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((log) => (
                  <TableRow key={log.log_id}>
                    <TableCell>{log.timestamp}</TableCell>
                    <TableCell>{log.client_id}</TableCell>
                    <TableCell>{log.task_id}</TableCell>
                    <TableCell>{log.event_type}</TableCell>
                    <TableCell>
                      <Badge 
                        variant={
                          log.status === "success" ? "default" : 
                          log.status === "failed" ? "destructive" : 
                          "secondary"
                        }
                      >
                        {log.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="space-x-2">
                      <Button variant="outline" size="sm">Details</Button>
                      <Button variant="secondary" size="sm">Chain</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="bg-muted p-4 rounded-md text-center">
              No audit logs available yet.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
} 