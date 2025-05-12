# Makefile for AgenticTrust project

# Default target
.DEFAULT_GOAL := dev

.PHONY: server platform dev opa-server
OPA_POLICY_DIR := $(shell pwd)/demo/policies

# Start the OPA server using Docker
opa-server:
	docker run --rm -v $(OPA_POLICY_DIR):/policies -p 8181:8181 openpolicyagent/opa run --server --log-level debug --addr=0.0.0.0:8181 /policies

# Start the FastAPI OAuth server
server:
	docker run --rm -v $(OPA_POLICY_DIR):/policies -p 8181:8181 openpolicyagent/opa run --server --log-level debug --addr=0.0.0.0:8181 /policies & \
	sleep 5 && poetry run uvicorn agentictrust.main:app --reload --host 127.0.0.1 --port 8000 --log-config configs/logging.yml

# Start the Next.js platform UI
platform:
	cd platform && npm run dev

# Start both backend and platform for development
dev:
	docker run --rm -v $(OPA_POLICY_DIR):/policies -p 8181:8181 openpolicyagent/opa run --server --log-level debug --addr=0.0.0.0:8181 /policies & \
	poetry run uvicorn agentictrust.main:app --reload --host 127.0.0.1 --port 8000 --log-config configs/logging.yml & \
	cd platform && npm run dev
