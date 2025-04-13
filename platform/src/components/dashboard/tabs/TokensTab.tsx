"use client";

import { useState, useEffect } from "react";
import { Token, TokenAPI } from "@/lib/api";
import { toast } from "sonner";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import TokenActions from "@/components/dashboard/TokenActions";

export function TokensTab() {
  const [tokens, setTokens] = useState<Token[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const fetchTokens = async () => {
    setLoading(true);
    setError(false);
    try {
      const data = await TokenAPI.getAll();
      setTokens(data);
    } catch (err) {
      setError(true);
      toast.error("Failed to load tokens");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTokens();
  }, []);

  return (
    <Card id="tokens">
      <CardHeader>
        <CardTitle>OAuth Tokens</CardTitle>
        <CardDescription>View and manage tokens</CardDescription>
      </CardHeader>
      <CardContent>
        {error ? (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error loading tokens</AlertTitle>
            <AlertDescription>There was a problem fetching the token data.</AlertDescription>
          </Alert>
        ) : loading ? (
          <div className="space-y-4">
            {Array(4).fill(0).map((_, i) => (
              <Skeleton key={`token-skeleton-${i}`} className="h-12 w-full" />
            ))}
          </div>
        ) : (
          <>
            {tokens.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Token ID</TableHead>
                    <TableHead>Client</TableHead>
                    <TableHead>Issued At</TableHead>
                    <TableHead>Expires</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tokens.map((token) => (
                    <TableRow key={token.token_id}>
                      <TableCell className="font-mono text-xs">{token.token_id.substring(0, 12)}...</TableCell>
                      <TableCell className="font-mono text-xs">{token.client_id.substring(0, 8)}...</TableCell>
                      <TableCell>{new Date(token.issued_at).toLocaleString()}</TableCell>
                      <TableCell>{new Date(token.expires_at).toLocaleString()}</TableCell>
                      <TableCell>
                        <Badge variant={token.is_revoked ? "secondary" : "default"}>
                          {token.is_revoked ? "Revoked" : "Active"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <TokenActions token={token} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="bg-muted p-4 rounded-md text-center">
                No active tokens available.
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
