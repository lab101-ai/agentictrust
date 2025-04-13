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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useState, useEffect } from "react";
import { toast } from "sonner";
import { MoreHorizontal, Pencil, Trash, AlertCircle, Check, X } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Scope, ScopeAPI } from "@/lib/api";

// Using the Scope interface from api.ts

// Ensure all required properties are present before passing to component
export default function ScopeActions({ scope, onUpdate }: { scope: Scope; onUpdate: () => void }) {
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [scopeCategories, setScopeCategories] = useState<string[]>(["read", "write", "admin", "tool"]);
  const [formData, setFormData] = useState<Scope>({ ...scope });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Fetch available categories on mount
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch("/api?endpoint=scopes/categories");
        if (!response.ok) {
          throw new Error("Failed to fetch scope categories");
        }
        const data = await response.json();
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
  
  // Update form data when scope changes
  useEffect(() => {
    setFormData({ ...scope });
  }, [scope]);
  
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
  
  const handleUpdate = async () => {
    setIsSubmitting(true);
    setError(null);
    
    try {
      await ScopeAPI.update(scope.scope_id, formData);
      
      toast.success(`Scope "${formData.name}" updated successfully`);
      setIsEditDialogOpen(false);
      onUpdate();
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unknown error occurred");
      toast.error("Failed to update scope");
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const handleDelete = async () => {
    setIsSubmitting(true);
    
    try {
      await ScopeAPI.delete(scope.scope_id);
      
      toast.success(`Scope "${scope.name}" deleted successfully`);
      setIsDeleteDialogOpen(false);
      onUpdate();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to delete scope");
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="h-8 w-8 p-0">
            <span className="sr-only">Open menu</span>
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuLabel>Actions</DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => setIsEditDialogOpen(true)}>
            <Pencil className="mr-2 h-4 w-4" />
            Edit
          </DropdownMenuItem>
          <DropdownMenuItem 
            onClick={() => setIsDeleteDialogOpen(true)}
            className="text-destructive"
          >
            <Trash className="mr-2 h-4 w-4" />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      
      {/* Edit Scope Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Edit Scope</DialogTitle>
            <DialogDescription>
              Update the details and permissions for this scope
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
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
              
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_active"
                  checked={formData.is_active === undefined ? true : !!formData.is_active}
                  onCheckedChange={(checked) => 
                    handleCheckboxChange("is_active", checked === true)
                  }
                />
                <Label htmlFor="is_active" className="text-sm font-normal">
                  Active (scope can be used in token requests)
                </Label>
              </div>
            </div>
            
            <DialogFooter>
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => setIsEditDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button 
                type="button" 
                onClick={handleUpdate}
                disabled={isSubmitting}
              >
                {isSubmitting ? "Updating..." : "Update Scope"}
              </Button>
            </DialogFooter>
          </div>
        </DialogContent>
      </Dialog>
      
      {/* Delete Confirmation Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Confirm Deletion</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete the scope "{scope.name}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <div className="pt-4">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Warning</AlertTitle>
              <AlertDescription>
                Deleting this scope may break existing tokens that use it. Ensure there are no active dependencies before proceeding.
              </AlertDescription>
            </Alert>
          </div>
          <DialogFooter>
            <Button 
              type="button" 
              variant="outline" 
              onClick={() => setIsDeleteDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button 
              type="button" 
              variant="destructive"
              onClick={handleDelete}
              disabled={isSubmitting}
            >
              {isSubmitting ? "Deleting..." : "Delete Scope"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
