import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { IconBadge, PolicyBadge } from "@/components/ui/icon-badge";
import { PolicyAPI, type Policy } from "@/lib/api";
import { PolicyActions } from "@/components/dashboard/PolicyActions";
import { useRouter } from 'next/navigation';
import { Plus, RefreshCw, FileCode, BarChart3, Check, Shield, ShieldX, Power, PowerOff } from 'lucide-react';
import { formatTimeAgo } from "@/lib/utils";

export const PoliciesTab = () => {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const router = useRouter();

  const loadPolicies = async () => {
    try {
      setIsLoading(true);
      const data = await PolicyAPI.getAll();
      setPolicies(data);
    } catch (error) {
      toast.error(`Failed to load policies: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadPolicies();

    // Listen for refresh events from parent
    const handleRefresh = () => {
      loadPolicies();
    };

    window.addEventListener('dashboard:refresh', handleRefresh);
    return () => {
      window.removeEventListener('dashboard:refresh', handleRefresh);
    };
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadPolicies();
    setIsRefreshing(false);
  };

  const handleDelete = (policyId: string) => {
    setPolicies(policies.filter(p => p.policy_id !== policyId));
  };

  const handleEdit = (policy: Policy) => {
    router.push(`/dashboard/policies/${policy.policy_id}`);
  };



  const handleCreateNew = () => {
    router.push('/dashboard/policies/new');
  };



  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Access Control Policies</CardTitle>
            <CardDescription>
              Manage attribute-based access control (ABAC) policies
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button 
              onClick={() => router.push('/dashboard/policies/templates')} 
              variant="outline"
              size="icon"
              className="h-8 w-8"
              title="Policy Templates"
            >
              <FileCode className="h-4 w-4" />
            </Button>
            <Button 
              onClick={() => router.push('/dashboard/policies/metrics')} 
              variant="outline"
              size="icon"
              className="h-8 w-8"
              title="Policy Metrics"
            >
              <BarChart3 className="h-4 w-4" />
            </Button>
            <Button onClick={handleCreateNew} size="sm">
              <Plus className="h-4 w-4 mr-2" />
              New Policy
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex justify-center my-8">
            <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
          </div>
        ) : policies.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <p>No policies found. Create your first policy to get started.</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead>Effect</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {policies.map((policy) => (
                <TableRow key={policy.policy_id}>
                  <TableCell className="font-medium">
                    <div>
                      {policy.name}
                      {policy.description && (
                        <p className="text-xs text-muted-foreground truncate max-w-md">
                          {policy.description}
                        </p>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>{policy.priority}</TableCell>
                  <TableCell>
                    <PolicyBadge subtype={policy.effect === 'allow' ? 'allow' : 'deny'}>
                      {policy.effect === 'allow' ? 'Allow' : 'Deny'}
                    </PolicyBadge>
                  </TableCell>
                  <TableCell>
                    <PolicyBadge subtype={policy.is_active ? 'active' : 'inactive'}>
                      {policy.is_active ? 'Active' : 'Inactive'}
                    </PolicyBadge>
                  </TableCell>
                  <TableCell>{policy.created_at && formatTimeAgo(policy.created_at)}</TableCell>
                  <TableCell className="text-right">
                    <PolicyActions
                      policy={policy}
                      onDelete={handleDelete}
                      onEdit={handleEdit}
                      onRefresh={handleRefresh}
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
      <CardFooter className="text-sm text-muted-foreground">
        {policies.length > 0 && (
          <p>Total: {policies.length} policies</p>
        )}
      </CardFooter>
    </Card>
  );
};
