"use client";

import { useEffect, useState, use } from "react";
import { toast } from "sonner";
import { UserForm } from "@/components/dashboard/user/user-form";
import { UserAPI, type User } from "@/lib/api";
import { AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface EditUserPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default function EditUserPage({ params }: EditUserPageProps) {
  const { id } = use(params);
  const userId = id;

  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUserData = async () => {
      setLoading(true);
      setError(null);
      try {
        const userData = await UserAPI.get(userId);
        setUser(userData);
      } catch (err) {
        console.error("Failed to fetch user:", err);
        setError("Failed to load user data. Please try again.");
        toast.error("Failed to load user data");
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, [userId]);

  if (loading) {
    return (
      <div className="container py-6">
        <div className="flex justify-center items-center min-h-[300px]">
          <div className="text-center">
            <div className="animate-spin h-8 w-8 border-t-2 border-primary rounded-full mx-auto mb-4"></div>
            <p>Loading user data...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="container py-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error || "Failed to load user data. Please try again."}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return <UserForm id={userId} initialUser={user} />;
}
