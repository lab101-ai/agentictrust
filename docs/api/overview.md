# API Documentation Overview

**Base URL:** `/api`

Welcome to the Agentic Trust API. This guide describes how to manage Agents and Tools via REST endpoints. All payloads use JSON and standard HTTP status codes.

## Authentication

- **Public Endpoints:** no authentication required
  - `POST /api/agents/register`
  - `POST /api/agents/activate`
- **Protected Endpoints:** (future) require bearer token
  - All other `/api/agents/*` and `/api/tools/*`

## Structure

- **Agents API:** `/api/agents` — detailed in `docs/api/agents.md`
- **Tools API:** `/api/tools` — detailed in `docs/api/tools.md`
- **OAuth API:** `/api/oauth` — detailed in `docs/api/oauth.md`

Each section includes endpoint definitions, request and response schemas, example payloads, and possible error codes.
