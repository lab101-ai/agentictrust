"use client";

import { Button } from "@/components/ui/button";
import { useState } from "react";
import { toast } from "sonner";
import { Pencil, Trash2 } from "lucide-react";
import { Scope, ScopeAPI } from "@/lib/api";
import { useRouter } from "next/navigation";

// Using the Scope interface from api.ts

// Ensure all required properties are present before passing to component
export default function ScopeActions({ scope, onUpdate }: { scope: Scope; onUpdate: () => void }) {
  const router = useRouter();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const handleEditScope = () => {
    router.push(`/dashboard/scopes/${scope.scope_id}`);
  };
  
  const handleDelete = async () => {
    if (confirm(`Are you sure you want to delete this scope: ${scope.name}?`)) {
      setIsSubmitting(true);
      try {
        await ScopeAPI.delete(scope.scope_id);
        toast.success(`Scope ${scope.name} deleted successfully`);
        onUpdate();
      } catch (error) {
        // Error handled by toast
        toast.error("Failed to delete scope");
      } finally {
        setIsSubmitting(false);
      }
    }
  };
  
  return (
    <>
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={handleEditScope}
          title="Edit scope"
        >
          <Pencil className="h-4 w-4" />
          <span className="sr-only">Edit</span>
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-destructive bg-destructive/10 hover:text-destructive hover:bg-destructive/20"
          onClick={handleDelete}
          disabled={isSubmitting}
          title="Delete scope"
        >
          <Trash2 className="h-4 w-4" />
          <span className="sr-only">{isSubmitting ? "Deleting..." : "Delete"}</span>
        </Button>
      </div>

    </>
  );
}
