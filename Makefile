# Makefile for AgenticTrust project

# Default target
.DEFAULT_GOAL := dev

.PHONY: server platform dev opa

# Start the FastAPI OAuth server
server:
	poetry run uvicorn agentictrust.main:app --reload --host 127.0.0.1 --port 8000 --log-config configs/logging.yml

# Start the Next.js platform UI
platform:
	cd platform && npm run dev

# Start both backend and platform for development
dev:
	poetry run uvicorn agentictrust.main:app --reload --host 127.0.0.1 --port 8000 --log-config configs/logging.yml & \
	cd platform && npm run dev

# Start OPA for demo
opa:
	docker compose -f demo/docker-compose.yml up -d opa
