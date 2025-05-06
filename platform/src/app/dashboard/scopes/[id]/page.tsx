"use client";

import { useState, useEffect, use } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ScopeAPI, type Scope } from "@/lib/api";
import { ArrowLeft, AlertTriangle } from "lucide-react";
import { useRouter } from "next/navigation";
import { ScopeForm } from "@/components/dashboard/scope";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  // In client components with Next.js 15, we use React.use() to unwrap the Promise
  const { id } = use(params);
  const [scope, setScope] = useState<Scope | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const loadScope = async () => {
      try {
        setIsLoading(true);
        const scopeData = await ScopeAPI.get(id);
        setScope(scopeData);
      } catch (error) {
        setError((error as Error).message);
      } finally {
        setIsLoading(false);
      }
    };

    loadScope();
  }, [id]);

  if (isLoading) {
    return (
      <div className="container py-6">
        <div className="flex items-center mb-6">
          <Skeleton className="h-10 w-10 rounded-full mr-4" />
          <Skeleton className="h-10 w-[300px]" />
        </div>

        <div className="grid gap-6 grid-cols-1">
          <Skeleton className="h-[500px] w-full" />
        </div>
      </div>
    );
  }

  if (!scope || error) {
    return (
      <div className="container py-6">
        <div className="flex items-center mb-6">
          <Button variant="ghost" onClick={() => router.back()} className="mr-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <h1 className="text-3xl font-semibold">Scope Not Found</h1>
        </div>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col items-center justify-center py-12">
              <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
              <h2 className="text-xl font-semibold mb-2">Scope Not Found</h2>
              <p className="text-muted-foreground mb-6">
                {error || "The scope you are looking for does not exist or has been deleted."}
              </p>
              <Button onClick={() => router.push("/dashboard?tab=scopes")}>
                Return to Scopes
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return <ScopeForm id={id} initialScope={scope} />;
}
