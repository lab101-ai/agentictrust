"use client";

import { useState, useEffect, use } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { PolicyAPI, type Policy } from "@/lib/api";
import { ArrowLeft, AlertTriangle } from "lucide-react";
import { useRouter } from "next/navigation";
import { PolicyForm } from "@/components/dashboard/policy";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  // In client components with Next.js 15, we use React.use() to unwrap the Promise
  const { id } = use(params);
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const loadPolicy = async () => {
      try {
        setIsLoading(true);
        const policyData = await PolicyAPI.get(id);
        setPolicy(policyData);
      } catch (error) {
        setError((error as Error).message);
      } finally {
        setIsLoading(false);
      }
    };

    loadPolicy();
  }, [id]);

  if (isLoading) {
    return (
      <div className="container py-6">
        <div className="flex items-center mb-6">
          <Skeleton className="h-10 w-10 rounded-full mr-4" />
          <Skeleton className="h-10 w-[300px]" />
        </div>

        <div className="grid gap-6 grid-cols-1 md:grid-cols-2">
          <Skeleton className="h-[500px] w-full" />
          <Skeleton className="h-[500px] w-full" />
        </div>
      </div>
    );
  }

  if (!policy || error) {
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
              <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
              <h2 className="text-xl font-semibold mb-2">Policy Not Found</h2>
              <p className="text-muted-foreground mb-6">
                {error || "The policy you are looking for does not exist or has been deleted."}
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

  return <PolicyForm id={id} initialPolicy={policy} />;
}
