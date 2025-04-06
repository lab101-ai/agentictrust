# Frontend Migration: Flask to Next.js + shadcn/ui

This document outlines the migration of the AgenticTrust frontend from Flask templates to a modern Next.js application with shadcn/ui components.

## Migration Overview

### What's Changed?

- **Frontend Architecture**: Moved from server-rendered Flask templates to a standalone Next.js application 
- **UI Framework**: Migrated from Bootstrap to Tailwind CSS with shadcn/ui components
- **Separation of Concerns**: Clear separation between frontend (Next.js) and backend (Flask API)
- **Enhanced Developer Experience**: TypeScript for type safety, modern React patterns, and component-based architecture

### Before & After

**Before**: Flask templates in `app/templates` and static assets in `app/static`
**After**: Modern Next.js application in `frontend/` with API integration

## Directory Structure

```
agentictrust_v1/
├── app/               # Flask backend
│   ├── routes/        # API routes
│   ├── models/        # Database models
│   └── ...
└── frontend/          # Next.js frontend (new)
    ├── src/
    │   ├── app/       # Next.js App Router pages
    │   ├── components/# React components
    │   └── lib/       # Utilities and API services
    └── ...
```

## How It Works

1. The Next.js frontend is a standalone application that communicates with the Flask backend via API calls
2. The Flask backend provides RESTful APIs for the frontend to consume
3. The frontend application can be developed and deployed independently of the backend

## API Integration

The Next.js frontend integrates with the Flask backend using:

1. **API Service Layer**: `frontend/src/lib/api.ts` contains typed functions for all API calls
2. **API Route Proxy**: `frontend/src/app/api/route.ts` provides a proxy to avoid CORS issues

## How to Run

### Development Mode

1. Start the Flask backend:
```bash
# From the project root
source venv/bin/activate
flask run
```

2. Start the Next.js development server:
```bash
# From the frontend directory
npm run dev
```

3. Access the application at http://localhost:3000

### Production

For production, you can:

1. Build the Next.js application:
```bash
# From the frontend directory
npm run build
```

2. Deploy the built application to a static hosting service or serve it with a Node.js server

## Next Steps

- [ ] Complete the API integration for all endpoints
- [ ] Add authentication flow
- [ ] Implement client-side form validation
- [ ] Add data fetching with SWR or React Query for better caching and re-fetch strategies
- [ ] Set up end-to-end testing with Cypress

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [shadcn/ui Components](https://ui.shadcn.com/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

## Notes for Developers

This migration allows for a more maintainable and scalable frontend architecture. The separation of frontend and backend enables:

1. Independent scaling of frontend and backend services
2. Different teams to work on each part without conflicts
3. Better performance through client-side rendering and API caching
4. Easier testing of UI components in isolation

The Flask backend remains responsible for:
- API endpoints
- Authentication & authorization
- Database operations
- Business logic

While the Next.js frontend handles:
- User interface
- Client-side state management
- Form validation
- User experience enhancements 