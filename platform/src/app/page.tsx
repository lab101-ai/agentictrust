import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-primary/10 to-primary/5">
      <div className="container flex flex-col items-center justify-center gap-12 px-4 py-16 text-center">
        <h1 className="text-5xl font-extrabold tracking-tight">
          Welcome to <span className="text-primary">AgenticTrust</span>
        </h1>
        <p className="max-w-2xl text-lg">
          Secure OAuth Framework for LLM-Based Agents - Ensuring authentication, authorization, 
          and audit capabilities for your AI agents.
        </p>
        <div className="flex gap-4">
          <Button asChild>
            <Link href="/dashboard">
              Go to Dashboard
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <a href="https://github.com/yourusername/agentictrust" target="_blank" rel="noopener noreferrer">
              View on GitHub
            </a>
          </Button>
        </div>
      </div>
    </div>
  );
}
