# AgenticTrust Test Suite

This test suite provides end-to-end testing for the AgenticTrust platform, focusing on users, agents, and tools.

## Overview

The test suite is organized into several modules:

- `test_users.py`: Tests for user management functionality
- `test_agents.py`: Tests for agent management functionality
- `test_tools.py`: Tests for tool management functionality
- `test_integration.py`: Integration tests that verify the interactions between users, agents, and tools

## Running Tests

To run the tests, use the following command from the project root:

```bash
pytest
```

To run specific test files:

```bash
pytest tests/test_users.py
pytest tests/test_agents.py
pytest tests/test_tools.py
pytest tests/test_integration.py
```

To run tests with detailed output:

```bash
pytest -v
```

## Test Structure

The tests use fixtures defined in `conftest.py` to set up the test environment, including:

- An in-memory SQLite database for testing
- Sample entities (users, agents, tools, scopes, policies)
- Engine instances for managing the entities

Each test focuses on a specific functionality or workflow, with setup, verification, and cleanup steps.

## Adding New Tests

When adding new tests, follow these conventions:

1. Place tests in an appropriate file based on the component being tested
2. Follow the naming convention `test_*` for test functions
3. Use existing fixtures where possible, or create new ones in `conftest.py`
4. Include cleanup steps to restore the test environment to its original state
