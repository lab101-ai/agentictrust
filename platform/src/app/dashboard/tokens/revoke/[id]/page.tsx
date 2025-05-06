"use client";

import { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ShieldOff, AlertCircle, Shield } from "lucide-react";
import { Token, TokenAPI } from "@/lib/api";
import { toast } from "sonner";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { SecurityBadge, StatusBadge, TimeBadge } from "@/components/ui/icon-badge";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { TokenDetailsCard } from "@/components/dashboard/token/token-details-card";
import { TokenPermissionsCard } from "@/components/dashboard/token/token-permissions-card";

interface RevokeTokenPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default function RevokeTokenPage({ params }: RevokeTokenPageProps) {
  const { id } = use(params);
  const tokenId = id;
  const router = useRouter();
  
  const [token, setToken] = useState<Token | null>(null);
  const [loading, setLoading] = useState(true);
  const [isRevoking, setIsRevoking] = useState(false);
  const [revocationReason, setRevocationReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Fetch token data
  useEffect(() => {
    const fetchTokenData = async () => {
      setLoading(true);
      setError(null);
      try {
        const tokenData = await TokenAPI.get(tokenId);
        
        // Check if token is already revoked
        if (tokenData.is_revoked) {
          setError("This token has already been revoked.");
        }
        
        setToken(tokenData);
      } catch (err) {
        console.error("Failed to fetch token:", err);
        setError("Failed to load token data. Please try again.");
        toast.error("Failed to load token data");
      } finally {
        setLoading(false);
      }
    };
    
    fetchTokenData();
  }, [tokenId]);
  
  const handleBack = () => {
    router.push("/dashboard?tab=tokens");
  };

  const handleRevoke = async () => {
    setIsRevoking(true);
    try {
      await TokenAPI.revoke(tokenId, revocationReason || "Manually revoked from admin panel");
      toast.success(`Token ${tokenId} revoked successfully`);
      // Navigate back to tokens dashboard
      router.push("/dashboard?tab=tokens");
    } catch (error) {
      toast.error("Failed to revoke token");
      setError("Failed to revoke token. Please try again.");
    } finally {
      setIsRevoking(false);
    }
  };

  if (loading) {
    return (
      <div className="container py-6">
        <div className="flex items-center mb-6">
          <Button variant="ghost" onClick={handleBack} className="mr-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <h1 className="text-3xl font-semibold">Revoke Token</h1>
        </div>
        <Card>
          <CardContent className="p-8 flex justify-center items-center">
            <div className="text-center">
              <div className="animate-spin h-8 w-8 border-t-2 border-primary rounded-full mx-auto mb-4"></div>
              <p>Loading token data...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !token) {
    return (
      <div className="container py-6">
        <div className="flex items-center mb-6">
          <Button variant="ghost" onClick={handleBack} className="mr-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <h1 className="text-3xl font-semibold">Revoke Token</h1>
        </div>
        <Card>
          <CardContent className="p-8">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {error || "Failed to load token data. Please try again."}
              </AlertDescription>
            </Alert>
            <Button className="mt-4" onClick={handleBack}>
              Return to Token Details
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container py-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Button variant="ghost" onClick={handleBack} className="mr-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <h1 className="text-3xl font-semibold">Revoke Token</h1>
        </div>
      </div>
      
      <Alert className="mb-6 bg-amber-50 border-amber-200">
        <AlertCircle className="h-4 w-4 text-amber-600" />
        <AlertDescription className="text-amber-800">
          Warning: Revoking a token is permanent and cannot be undone. Any applications or services using this token will lose access immediately.
        </AlertDescription>
      </Alert>
      
      <div className="grid gap-6 grid-cols-1 md:grid-cols-2 mb-6">
        <TokenDetailsCard token={token} />
        <TokenPermissionsCard token={token} />
      </div>
      
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <ShieldOff className="h-5 w-5 text-destructive" />
            <div>
              <CardTitle>Revocation Details</CardTitle>
              <CardDescription>
                Please provide a reason for revoking this token
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <Label htmlFor="revocation-reason">Revocation Reason</Label>
            <Textarea
              id="revocation-reason"
              placeholder="Enter a reason for revoking this token..."
              value={revocationReason}
              onChange={(e) => setRevocationReason(e.target.value)}
              className="min-h-24"
            />
            <p className="text-sm text-muted-foreground">
              Providing a reason helps with audit logs and tracking token lifecycle.
            </p>
          </div>
        </CardContent>
        
        <CardFooter className="flex justify-end gap-3 pt-2">
          <Button variant="outline" onClick={handleBack}>
            Cancel
          </Button>
          <Button 
            variant="destructive" 
            onClick={handleRevoke}
            disabled={isRevoking || token.is_revoked}
            className="flex items-center gap-2"
          >
            <ShieldOff className="h-4 w-4" />
            {isRevoking ? "Revoking..." : "Revoke Token"}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
