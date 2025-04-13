"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useState, useEffect } from "react";
import { toast } from "sonner";
import { AlertCircle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ScopeRegistration, ScopeAPI } from "@/lib/api";

interface ScopeCategories {
  categories: string[];
}

export function RegisterScopeDialog({ onScopeAdded }: { onScopeAdded?: () => void }) {
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState<ScopeRegistration>({
    name: "",
    description: "",
    category: "read",
    is_sensitive: false,
    requires_approval: false,
    is_default: false,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scopeCategories, setScopeCategories] = useState<string[]>(["read", "write", "admin", "tool"]);
  
  // Fetch available categories on mount
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch("/api?endpoint=scopes/categories");
        if (!response.ok) {
          throw new Error("Failed to fetch scope categories");
        }
        const data: ScopeCategories = await response.json();
        if (data.categories && data.categories.length > 0) {
          setScopeCategories(data.categories);
        }
      } catch (err) {
        console.error("Error fetching scope categories:", err);
        // Fall back to default categories
      }
    };
    
    fetchCategories();
  }, []);
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };
  
  const handleSelectChange = (value: string) => {
    setFormData((prev) => ({ ...prev, category: value }));
  };
  
  const handleCheckboxChange = (name: string, checked: boolean) => {
    setFormData((prev) => ({ ...prev, [name]: checked }));
  };
  
  const handleRegister = async () => {
    setIsSubmitting(true);
    setError(null);
    
    try {
      // Validate required fields
      if (!formData.name || !formData.description) {
        throw new Error("Name and description are required");
      }
      
      await ScopeAPI.create(formData);
      
      toast.success(`Scope "${formData.name}" registered successfully`);
      setOpen(false);
      setFormData({
        name: "",
        description: "",
        category: "read",
        is_sensitive: false,
        requires_approval: false,
        is_default: false,
      });
      
      // Notify parent component to refresh scopes list
      if (onScopeAdded) {
        onScopeAdded();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unknown error occurred");
      toast.error("Failed to create scope");
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Register New Scope</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Register New Scope</DialogTitle>
          <DialogDescription>
            Create a new OAuth scope for agent permissions
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={(e) => { e.preventDefault(); handleRegister(); }} className="space-y-4 py-4">
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          
          <div className="grid gap-2">
            <Label htmlFor="name">Scope Name</Label>
            <Input
              id="name"
              name="name"
              placeholder="e.g., read:profile"
              value={formData.name}
              onChange={handleInputChange}
              required
            />
            <p className="text-sm text-muted-foreground">
              Use a descriptive name with namespace (e.g., read:profile, write:data)
            </p>
          </div>
          
          <div className="grid gap-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              name="description"
              placeholder="Describe what this scope allows"
              value={formData.description}
              onChange={handleInputChange}
              className="min-h-[80px]"
              required
            />
          </div>
          
          <div className="grid gap-2">
            <Label htmlFor="category">Category</Label>
            <Select
              value={formData.category}
              onValueChange={handleSelectChange}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a category" />
              </SelectTrigger>
              <SelectContent>
                {scopeCategories.map((category) => (
                  <SelectItem key={category} value={category}>
                    {category.charAt(0).toUpperCase() + category.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          <div className="flex flex-col gap-3">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_sensitive"
                checked={formData.is_sensitive}
                onCheckedChange={(checked) => 
                  handleCheckboxChange("is_sensitive", checked === true)
                }
              />
              <Label htmlFor="is_sensitive" className="text-sm font-normal">
                Mark as sensitive (requires special handling and approval)
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox
                id="requires_approval"
                checked={formData.requires_approval}
                onCheckedChange={(checked) => 
                  handleCheckboxChange("requires_approval", checked === true)
                }
              />
              <Label htmlFor="requires_approval" className="text-sm font-normal">
                Requires explicit approval before being granted
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_default"
                checked={formData.is_default}
                onCheckedChange={(checked) => 
                  handleCheckboxChange("is_default", checked === true)
                }
              />
              <Label htmlFor="is_default" className="text-sm font-normal">
                Add to default scope set for new agents
              </Label>
            </div>
          </div>
          
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Creating..." : "Create Scope"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
