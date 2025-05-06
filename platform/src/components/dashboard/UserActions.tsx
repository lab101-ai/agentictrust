"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Pencil, Trash2, Check, Ban } from "lucide-react";
import { toast } from "sonner";
import { User, UserAPI } from "@/lib/api";

interface UserActionsProps {
  user: User;
  onUpdate?: () => Promise<void> | void;
}

export default function UserActions({ user, onUpdate }: UserActionsProps) {
  const router = useRouter();
  const [isToggling, setIsToggling] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleToggleActive = async () => {
    setIsToggling(true);
    try {
      await UserAPI.update(user.user_id, { is_active: !user.is_active });
      toast.success(
        `User ${user.username} ${user.is_active ? "deactivated" : "activated"} successfully`
      );
      if (onUpdate) await onUpdate();
    } catch (error) {
      toast.error("Failed to update user status");
    } finally {
      setIsToggling(false);
    }
  };

  const handleDelete = async () => {
    if (
      !confirm(`Are you sure you want to delete this user: ${user.username}?`)
    ) {
      return;
    }

    setIsDeleting(true);
    try {
      await UserAPI.delete(user.user_id);
      toast.success(`User ${user.username} deleted successfully`);
      if (onUpdate) await onUpdate();
    } catch (error) {
      toast.error("Failed to delete user");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8"
        onClick={() => router.push(`/dashboard/users/${user.user_id}`)}
        title="Edit user"
      >
        <Pencil className="h-4 w-4" />
        <span className="sr-only">Edit</span>
      </Button>

      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8 text-destructive bg-destructive/10 hover:text-destructive hover:bg-destructive/20"
        onClick={handleDelete}
        disabled={isDeleting}
        title="Delete user"
      >
        <Trash2 className="h-4 w-4" />
        <span className="sr-only">{isDeleting ? "Deleting..." : "Delete"}</span>
      </Button>

      <Button
        variant="ghost"
        size="icon"
        className={`h-8 w-8 ${
          user.is_active
            ? "text-destructive bg-destructive/10 hover:bg-destructive/20"
            : "text-emerald-600 bg-emerald-50 hover:bg-emerald-100"
        }`}
        onClick={handleToggleActive}
        disabled={isToggling}
        title={user.is_active ? "Deactivate user" : "Activate user"}
      >
        {user.is_active ? (
          <Ban className="h-4 w-4" />
        ) : (
          <Check className="h-4 w-4" />
        )}
        <span className="sr-only">
          {isToggling ? "Updating..." : user.is_active ? "Deactivate" : "Activate"}
        </span>
      </Button>
    </div>
  );
}
