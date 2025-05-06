"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, ArrowLeft, Save } from "lucide-react";
import { UserAPI, ScopeAPI, PolicyAPI, type Scope, type Policy, type User, type UserRegistration } from "@/lib/api";

interface UserFormProps {
  id?: string;
  initialUser?: User;
  isNew?: boolean;
}

export const UserForm = ({ id, initialUser, isNew = false }: UserFormProps) => {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableScopes, setAvailableScopes] = useState<Scope[]>([]);
  const [availablePolicies, setAvailablePolicies] = useState<Policy[]>([]);

  const [formData, setFormData] = useState<UserRegistration>({
    username: initialUser?.username || "",
    email: initialUser?.email || "",
    full_name: initialUser?.full_name || "",
    is_external: initialUser?.is_external || false,
    is_active: initialUser?.is_active ?? true,
    department: initialUser?.department || "",
    job_title: initialUser?.job_title || "",
    level: initialUser?.level || "",
    scopes: initialUser?.scopes || [],
    policies: initialUser?.policies || [],
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [scopes, policies] = await Promise.all([
          ScopeAPI.getAll(),
          PolicyAPI.getAll(),
        ]);
        setAvailableScopes(scopes);
        setAvailablePolicies(policies);
      } catch (err) {
        console.error("Failed to fetch metadata:", err);
        toast.error("Failed to load scopes/policies");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleCheckboxChange = (
    listKey: "scopes" | "policies",
    id: string,
    checked: boolean
  ) => {
    setFormData((prev) => {
      const current = new Set(prev[listKey] || []);
      if (checked) {
        current.add(id);
      } else {
        current.delete(id);
      }
      return { ...prev, [listKey]: Array.from(current) } as UserRegistration;
    });
  };

  const handleExternalChange = (value: string) => {
    setFormData((prev) => ({
      ...prev,
      is_external: value === "external",
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      if (isNew) {
        await UserAPI.create(formData);
        toast.success("User created successfully");
        router.push("/dashboard?tab=users");
      } else if (id) {
        await UserAPI.update(id, formData);
        toast.success("User updated successfully");
        router.push(`/dashboard/users/${id}`);
      }
    } catch (err) {
      console.error("Failed to save user:", err);
      setError("Failed to save user. Please check your inputs and try again.");
      toast.error("Failed to save user");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="container py-6 flex justify-center items-center min-h-[200px]">
        Loading...
      </div>
    );
  }

  return (
    <div className="container py-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Button
            variant="ghost"
            // Navigate back to the Users tab regardless of create or edit mode
            onClick={() => router.push("/dashboard?tab=users")}
            className="mr-4"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <h1 className="text-3xl font-semibold">
            {isNew ? "New User" : "Edit User"}
          </h1>
        </div>
        <Button type="submit" form="user-form" disabled={isSubmitting}>
          <Save className="mr-2 h-4 w-4" />
          {isSubmitting ? "Saving..." : "Save"}
        </Button>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <form id="user-form" onSubmit={handleSubmit} className="grid gap-6 grid-cols-1 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>User Details</CardTitle>
            <CardDescription>Basic information about the user</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Username *</Label>
              <Input
                id="username"
                name="username"
                value={formData.username}
                onChange={handleInputChange}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email *</Label>
              <Input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleInputChange}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="full_name">Full Name</Label>
              <Input
                id="full_name"
                name="full_name"
                value={formData.full_name}
                onChange={handleInputChange}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="department">Department</Label>
              <Input
                id="department"
                name="department"
                value={formData.department || ""}
                onChange={handleInputChange}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="job_title">Job Title</Label>
              <Input
                id="job_title"
                name="job_title"
                value={formData.job_title || ""}
                onChange={handleInputChange}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="level">Level</Label>
              <Input
                id="level"
                name="level"
                value={formData.level || ""}
                onChange={handleInputChange}
              />
            </div>
            <div className="space-y-2">
              <Label>User Type</Label>
              <RadioGroup
                defaultValue={formData.is_external ? "external" : "internal"}
                onValueChange={handleExternalChange}
              >
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="internal" id="internal" />
                  <Label htmlFor="internal">Internal</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="external" id="external" />
                  <Label htmlFor="external">External</Label>
                </div>
              </RadioGroup>
            </div>
          </CardContent>
        </Card>

        {/* Permissions */}
        <Card>
          <CardHeader>
            <CardTitle>Permissions</CardTitle>
            <CardDescription>Assign scopes and policies</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-4 max-h-[400px] overflow-y-auto">
            <div>
              <h4 className="font-medium mb-2">Scopes</h4>
              <div className="space-y-2">
                {availableScopes.map((scope) => (
                  <div key={scope.scope_id} className="flex items-center gap-2">
                    <Checkbox
                      id={`scope-${scope.scope_id}`}
                      checked={(formData.scopes || []).includes(scope.scope_id)}
                      onCheckedChange={(c) => handleCheckboxChange("scopes", scope.scope_id, !!c)}
                    />
                    <Label htmlFor={`scope-${scope.scope_id}`}>{scope.name}</Label>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h4 className="font-medium mb-2">Policies</h4>
              <div className="space-y-2">
                {availablePolicies.map((policy) => (
                  <div key={policy.policy_id} className="flex items-center gap-2">
                    <Checkbox
                      id={`policy-${policy.policy_id}`}
                      checked={(formData.policies || []).includes(policy.policy_id)}
                      onCheckedChange={(c) => handleCheckboxChange("policies", policy.policy_id, !!c)}
                    />
                    <Label htmlFor={`policy-${policy.policy_id}`}>{policy.name}</Label>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  );
};
