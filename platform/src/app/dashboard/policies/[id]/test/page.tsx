"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { IconBadge } from "@/components/ui/icon-badge";
import { 
  PolicyAPI, 
  type Policy, 
  type PolicyEvaluationRequest, 
  type PolicyEvaluationResponse 
} from "@/lib/api";
import { 
  ArrowLeft, 
  Play, 
  CheckCircle2, 
  XCircle, 
  FlaskConical, 
  AlertCircle, 
  User, 
  FileText, 
  Activity
} from "lucide-react";

// Example context templates
const CONTEXT_TEMPLATES = {
  basic: {
    agent: {
      id: "agent-123",
      name: "Example Agent",
      authenticated: true,
      role: "user"
    },
    resource: {
      id: "resource-456",
      type: "document",
      owner_id: "agent-123"
    },
    action: {
      type: "read"
    },
    environment: {
      time: {
        hour: 14,
        is_business_hours: true,
        is_weekend: false
      },
      network: {
        ip: "192.168.1.100"
      }
    }
  },
  adminAccess: {
    agent: {
      id: "admin-789",
      name: "Admin User",
      authenticated: true,
      role: "admin"
    },
    resource: {
      id: "resource-456",
      type: "document",
      owner_id: "agent-123"
    },
    action: {
      type: "write"
    },
    environment: {
      time: {
        hour: 10,
        is_business_hours: true,
        is_weekend: false
      }
    }
  },
  outsideBusinessHours: {
    agent: {
      id: "agent-123",
      name: "Example Agent",
      authenticated: true,
      role: "user"
    },
    resource: {
      id: "resource-456",
      type: "document",
      owner_id: "agent-123"
    },
    action: {
      type: "read"
    },
    environment: {
      time: {
        hour: 22,
        is_business_hours: false,
        is_weekend: false
      }
    }
  }
};

export default function PolicyTestPage({ params }: { params: { id: string } }) {
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isTesting, setIsTesting] = useState(false);
  const [activeTemplate, setActiveTemplate] = useState("basic");
  const [contextJson, setContextJson] = useState("");
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<PolicyEvaluationResponse | null>(null);
  const router = useRouter();

  useEffect(() => {
    const loadPolicy = async () => {
      try {
        setIsLoading(true);
        const policyData = await PolicyAPI.get(params.id);
        setPolicy(policyData);
        // Set initial context
        setContextJson(JSON.stringify(CONTEXT_TEMPLATES.basic, null, 2));
      } catch (error) {
        toast.error(`Failed to load policy: ${(error as Error).message}`);
      } finally {
        setIsLoading(false);
      }
    };

    loadPolicy();
  }, [params.id]);

  const handleTemplateChange = (template: string) => {
    setActiveTemplate(template);
    setContextJson(JSON.stringify(CONTEXT_TEMPLATES[template as keyof typeof CONTEXT_TEMPLATES], null, 2));
    setJsonError(null);
    setTestResult(null);
  };

  const handleContextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setContextJson(e.target.value);
    try {
      JSON.parse(e.target.value);
      setJsonError(null);
    } catch (error) {
      setJsonError("Invalid JSON format");
    }
  };

  const handleTest = async () => {
    if (jsonError) {
      toast.error("Please fix the JSON format before testing");
      return;
    }

    if (!policy) {
      toast.error("Policy not available for testing");
      return;
    }

    try {
      setIsTesting(true);
      const context = JSON.parse(contextJson);
      
      const request: PolicyEvaluationRequest = {
        context
      };

      // For testing an existing policy
      const result = await PolicyAPI.test(
        {
          name: policy.name,
          description: policy.description,
          effect: policy.effect,
          conditions: policy.conditions,
          priority: policy.priority
        },
        context
      );
      
      setTestResult(result);
      
      if (result.access) {
        toast.success("Policy evaluation granted access");
      } else {
        toast.error("Policy evaluation denied access");
      }
    } catch (error) {
      toast.error(`Test failed: ${(error as Error).message}`);
    } finally {
      setIsTesting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="container py-6">
        <div className="flex items-center mb-6">
          <Skeleton className="h-10 w-10 rounded-full mr-4" />
          <Skeleton className="h-10 w-[300px]" />
        </div>

        <div className="grid gap-6 grid-cols-1 md:grid-cols-2">
          <Skeleton className="h-[600px] w-full" />
          <Skeleton className="h-[600px] w-full" />
        </div>
      </div>
    );
  }

  if (!policy) {
    return (
      <div className="container py-6">
        <div className="flex items-center mb-6">
          <Button variant="ghost" onClick={() => router.back()} className="mr-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <h1 className="text-3xl font-semibold">Policy Not Found</h1>
        </div>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col items-center justify-center py-12">
              <AlertCircle className="h-12 w-12 text-destructive mb-4" />
              <h2 className="text-xl font-semibold mb-2">Policy Not Found</h2>
              <p className="text-muted-foreground mb-6">
                The policy you are looking for does not exist or has been deleted.
              </p>
              <Button onClick={() => router.push("/dashboard?tab=policies")}>
                Return to Policies
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container py-6">
      <div className="flex items-center mb-6">
        <Button variant="ghost" onClick={() => router.back()} className="mr-4">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <h1 className="text-3xl font-semibold">Test Policy</h1>
      </div>

      <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle className="flex items-center">
                  <span>Policy Details</span>
                  <IconBadge
                    variant={policy.effect === 'allow' ? 'default' : 'destructive'}
                    className="ml-2"
                    icon={policy.effect === 'allow' ? CheckCircle2 : XCircle}
                  />
                </CardTitle>
                <CardDescription>
                  {policy.description || "No description provided"}
                </CardDescription>
              </div>
              {!policy.is_active && (
                <Badge variant="outline">Inactive</Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h3 className="text-sm font-medium mb-1">Name</h3>
              <p>{policy.name}</p>
            </div>
            
            <div>
              <h3 className="text-sm font-medium mb-1">Effect</h3>
              <Badge variant={policy.effect === 'allow' ? 'default' : 'destructive'}>
                {policy.effect.toUpperCase()}
              </Badge>
            </div>
            
            <div>
              <h3 className="text-sm font-medium mb-1">Priority</h3>
              <p>{policy.priority}</p>
            </div>
            
            <div>
              <h3 className="text-sm font-medium mb-1">Conditions</h3>
              <pre className="bg-muted p-4 rounded-md text-xs overflow-x-auto max-h-48">
                {JSON.stringify(policy.conditions, null, 2)}
              </pre>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle className="flex items-center">
                  <FlaskConical className="mr-2 h-5 w-5" />
                  Test Environment
                </CardTitle>
                <CardDescription>
                  Configure a context to test this policy
                </CardDescription>
              </div>
              <Button 
                variant="default"
                size="sm"
                onClick={handleTest}
                disabled={isTesting || !!jsonError}
              >
                {isTesting ? (
                  <>
                    <div className="h-4 w-4 mr-2 animate-spin rounded-full border-2 border-current border-t-transparent" />
                    Testing
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Test Policy
                  </>
                )}
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <Tabs value={activeTemplate} onValueChange={handleTemplateChange}>
              <TabsList className="grid grid-cols-3 mb-2">
                <TabsTrigger value="basic">
                  <User className="mr-2 h-4 w-4" />
                  Basic
                </TabsTrigger>
                <TabsTrigger value="adminAccess">
                  <FileText className="mr-2 h-4 w-4" />
                  Admin
                </TabsTrigger>
                <TabsTrigger value="outsideBusinessHours">
                  <Activity className="mr-2 h-4 w-4" />
                  After Hours
                </TabsTrigger>
              </TabsList>
            </Tabs>

            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm font-medium">Context JSON</span>
                {jsonError && (
                  <span className="text-destructive text-sm">
                    {jsonError}
                  </span>
                )}
              </div>
              <Textarea
                className="font-mono h-[300px]"
                value={contextJson}
                onChange={handleContextChange}
              />
            </div>

            {testResult && (
              <Card>
                <CardHeader className="py-3">
                  <CardTitle className="text-base flex items-center">
                    <span>Test Result</span>
                    <IconBadge
                      variant={testResult.access ? 'default' : 'destructive'}
                      className="ml-2"
                      icon={testResult.access ? CheckCircle2 : XCircle}
                    />
                  </CardTitle>
                </CardHeader>
                <CardContent className="py-2">
                  <div className="space-y-2">
                    <div className="flex items-center">
                      <span className="font-medium">Access:</span>
                      <Badge 
                        variant={testResult.access ? 'default' : 'destructive'} 
                        className="ml-2"
                      >
                        {testResult.access ? 'ALLOWED' : 'DENIED'}
                      </Badge>
                    </div>
                    <div>
                      <span className="font-medium">Reason:</span>
                      <p className="text-sm mt-1">{testResult.reason}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
