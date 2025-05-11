# AgenticTrust Frontend

This is the frontend for the AgenticTrust platform, built with Next.js and shadcn/ui.

## Features

- Modern UI with Next.js App Router and TypeScript
- Beautiful, accessible components with shadcn/ui
- Seamless integration with the AgenticTrust backend API
- Responsive dashboard for managing agents, tools, tokens, and audit logs

## Getting Started

### Prerequisites

- Node.js 18.17 or later
- npm or yarn

### Installation

The frontend is part of the main AgenticTrust repository. Once you have cloned the main repository, navigate to the frontend directory:

```bash
cd frontend
```

Then install dependencies:

```bash
npm install
# or
yarn install
```

3. Configure environment variables:

Create a `.env.local` file in the frontend directory with the following content:

```
NEXT_PUBLIC_API_URL=http://localhost:5000/api
```

Adjust the URL if your backend is running on a different host or port.

### Development

Run the development server:

```bash
npm run dev
# or
yarn dev
```

The app will be available at [http://localhost:3000](http://localhost:3000).

### Building for Production

Build the application for production:

```bash
npm run build
# or
yarn build
```

Start the production server:

```bash
npm run start
# or
yarn start
```

## Project Structure

- `src/app/` - Next.js App Router pages and layouts
- `src/components/` - Reusable React components
  - `src/components/ui/` - shadcn/ui components
  - `src/components/dashboard/` - Dashboard-specific components
- `src/lib/` - Utilities and API services

## API Integration

The API service functions are defined in `src/lib/api.ts` and provide typed functions for interacting with the backend API.

## Available APIs

- `AgentAPI` - Functions for managing agents
- `ToolAPI` - Functions for managing tools
- `TokenAPI` - Functions for managing tokens
- `AuditAPI` - Functions for viewing audit logs
- `StatsAPI` - Functions for getting dashboard statistics

## UI Components

The UI is built with shadcn/ui, a collection of re-usable components built on top of Tailwind CSS and Radix UI. The components are fully accessible and customizable.
