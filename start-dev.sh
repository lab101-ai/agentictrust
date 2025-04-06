#!/bin/bash

# Default: start both backend and frontend
START_BACKEND=true
START_FRONTEND=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -b|--backend-only)
      START_BACKEND=true
      START_FRONTEND=false
      shift
      ;;
    -f|--frontend-only)
      START_BACKEND=false
      START_FRONTEND=true
      shift
      ;;
    -h|--help)
      echo "Usage: ./start-dev.sh [OPTIONS]"
      echo "Options:"
      echo "  -b, --backend-only    Start only the Flask backend"
      echo "  -f, --frontend-only   Start only the Next.js frontend"
      echo "  -h, --help            Show this help message"
      echo "No options will start both backend and frontend"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use -h or --help to see available options"
      exit 1
      ;;
  esac
done

FLASK_PID=""
NEXTJS_PID=""

# Start the Flask backend if requested
if [ "$START_BACKEND" = true ]; then
  echo "Starting Flask backend..."
  # Check if Poetry is installed
  if command -v poetry &> /dev/null; then
    (cd . && poetry run python -m flask run --debug) &
    FLASK_PID=$!
  else
    # Fallback to venv if Poetry is not installed
    source .venv/bin/activate
    (cd . && FLASK_ENV=development flask run) &
    FLASK_PID=$!
  fi
  
  # Wait for Flask to start
  echo "Waiting for Flask to start..."
  sleep 3
fi

# Start the Next.js frontend if requested
if [ "$START_FRONTEND" = true ]; then
  echo "Starting Next.js frontend..."
  (cd frontend && npm run dev) &
  NEXTJS_PID=$!
fi

# Function to handle script exit
function cleanup {
  echo "Shutting down servers..."
  if [ -n "$FLASK_PID" ]; then
    kill $FLASK_PID 2>/dev/null || true
  fi
  if [ -n "$NEXTJS_PID" ]; then
    kill $NEXTJS_PID 2>/dev/null || true
  fi
  exit
}

# Register the cleanup function for script exit
trap cleanup SIGINT SIGTERM

# Keep the script running if at least one service is started
if [ -n "$FLASK_PID" ] || [ -n "$NEXTJS_PID" ]; then
  echo "Development environment running. Press Ctrl+C to stop."
  wait
else
  echo "No services started. Use -h or --help to see available options."
  exit 1
fi 