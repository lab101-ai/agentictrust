"use client";

import { useState, useEffect } from "react";
import { Token, TokenAPI } from "@/lib/api";
import { toast } from "sonner";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
// Badge import removed as we're using specialized badge components
import { StatusBadge, SecurityBadge, TimeBadge } from "@/components/ui/icon-badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, Key, Check, Clock, ShieldOff } from "lucide-react";
import TokenActions from "@/components/dashboard/TokenActions";

// TokenActions component using links to dedicated token pages

import { formatTimeAgo } from "@/lib/utils";

export function TokensTab() {
  const [tokens, setTokens] = useState<Token[]>([]);
  const [filteredTokens, setFilteredTokens] = useState<Token[]>([]);
  const [activeFilter, setActiveFilter] = useState<'all' | 'active' | 'revoked'>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const fetchTokens = async () => {
    setLoading(true);
    setError(false);
    try {
      const data = await TokenAPI.getAll();
      setTokens(data);
      applyFilter(activeFilter, data);
    } catch (err) {
      setError(true);
      toast.error("Failed to load tokens");
    } finally {
      setLoading(false);
    }
  };

  const applyFilter = (filter: 'all' | 'active' | 'revoked', tokenData = tokens) => {
    setActiveFilter(filter);
    switch (filter) {
      case 'active':
        setFilteredTokens(tokenData.filter(token => !token.is_revoked));
        break;
      case 'revoked':
        setFilteredTokens(tokenData.filter(token => token.is_revoked));
        break;
      default:
        setFilteredTokens(tokenData);
    }
  };

  useEffect(() => {
    fetchTokens();
  }, []);

  return (
    <Card id="tokens">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>OAuth Tokens</CardTitle>
            <CardDescription>View and manage tokens</CardDescription>
          </div>
          <div className="flex gap-2">
            {/* No specific actions for tokens */}
          </div>
        </div>
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
              <>
                <div className="flex gap-2 mb-4">
                  <Button 
                    variant={activeFilter === 'all' ? 'default' : 'outline'} 
                    size="sm"
                    onClick={() => applyFilter('all')}
                  >
                    All
                  </Button>
                  <Button 
                    variant={activeFilter === 'active' ? 'default' : 'outline'} 
                    size="sm"
                    onClick={() => applyFilter('active')}
                  >
                    Active
                  </Button>
                  <Button 
                    variant={activeFilter === 'revoked' ? 'default' : 'outline'} 
                    size="sm"
                    onClick={() => applyFilter('revoked')}
                  >
                    Revoked
                  </Button>
                </div>
                <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Token ID</TableHead>
                    <TableHead>Client</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Expires</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredTokens.map((token) => (
                    <TableRow key={token.token_id}>
                      <TableCell className="font-mono text-xs">{token.token_id.substring(0, 12)}...</TableCell>
                      <TableCell className="font-mono text-xs">{token.client_id.substring(0, 8)}...</TableCell>
                      <TableCell>
                        {token.issued_at ? (
                          <span title={new Date(token.issued_at).toLocaleString()}>
                            {formatTimeAgo(token.issued_at)}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">Unknown</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {token.expires_at ? (
                          <span 
                            title={new Date(token.expires_at).toLocaleString()}
                            className={new Date(token.expires_at) < new Date() ? "text-destructive" : ""}
                          >
                            {formatTimeAgo(token.expires_at)}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">Unknown</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {token.is_revoked ? (
                          <SecurityBadge subtype="warning">Revoked</SecurityBadge>
                        ) : (token.expires_at && new Date(token.expires_at) < new Date()) ? (
                          <TimeBadge subtype="expired">Expired</TimeBadge>
                        ) : (
                          <StatusBadge subtype="success">Active</StatusBadge>
                        )}
                      </TableCell>
                      <TableCell>
                        <TokenActions token={token} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
                {activeFilter !== 'all' && filteredTokens.length === 0 && (
                  <div className="mt-4 p-4 bg-muted/50 rounded-md text-center">
                    <p className="text-muted-foreground">No {activeFilter} tokens found. Try a different filter.</p>
                  </div>
                )}
              </>
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
