"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const pathname = usePathname();
  
  // Close mobile menu when route changes
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [pathname]);

  const isTabActive = (tabName: string | null) => {
    if (!tabName && pathname === "/dashboard") return true;
    return pathname.includes("/dashboard") && 
      new URLSearchParams(pathname.split('?')[1] || '').get('tab') === tabName;
  };

  return (
    <div className="flex min-h-screen bg-muted/30">
      {/* Mobile menu overlay */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm lg:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}
      
      {/* Mobile menu button */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed top-4 left-4 z-50 lg:hidden"
        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
      >
        {isMobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
      </Button>
      
      {/* Sidebar */}
      <aside 
        className={cn(
          "fixed inset-y-0 left-0 z-40 w-72 border-r bg-background transition-transform duration-300 ease-in-out",
          isMobileMenuOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div className="flex h-16 items-center border-b px-6">
          <Link href="/" className="font-bold text-xl">
            <span className="text-primary">AgenticTrust</span>
          </Link>
        </div>
        
        <nav className="flex flex-col gap-2 p-6">
          <Button 
            variant={isTabActive(null) ? "default" : "ghost"} 
            className="justify-start w-full" 
            asChild
          >
            <Link href="/dashboard">
              Dashboard
            </Link>
          </Button>
          <Button 
            variant={isTabActive("agents") ? "default" : "ghost"} 
            className="justify-start w-full" 
            asChild
          >
            <Link href="/dashboard?tab=agents">
              Agents
            </Link>
          </Button>
          <Button 
            variant={isTabActive("tools") ? "default" : "ghost"} 
            className="justify-start w-full" 
            asChild
          >
            <Link href="/dashboard?tab=tools">
              Tools
            </Link>
          </Button>
          <Button 
            variant={isTabActive("tokens") ? "default" : "ghost"} 
            className="justify-start w-full" 
            asChild
          >
            <Link href="/dashboard?tab=tokens">
              Tokens
            </Link>
          </Button>
          <Button 
            variant={isTabActive("audit") ? "default" : "ghost"} 
            className="justify-start w-full" 
            asChild
          >
            <Link href="/dashboard?tab=audit">
              Audit Logs
            </Link>
          </Button>
          <Button 
            variant={isTabActive("scopes") ? "default" : "ghost"} 
            className="justify-start w-full" 
            asChild
          >
            <Link href="/dashboard?tab=scopes">
              Scopes
            </Link>
          </Button>
        </nav>
      </aside>
      
      {/* Main content */}
      <main className="flex-1 lg:pl-72">
        <div className="container mx-auto p-6">
          {children}
        </div>
      </main>
    </div>
  );
} 