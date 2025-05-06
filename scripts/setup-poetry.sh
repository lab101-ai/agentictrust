#!/bin/bash

# Setup Poetry script for AgenticTrust

echo "Setting up Poetry for AgenticTrust..."

# Check if Poetry is installed
if ! command -v poetry &> /dev/null
then
    echo "Poetry is not installed. Installing now..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# Check Poetry version
POETRY_VERSION=$(poetry --version | awk '{print $3}')
echo "Poetry version: $POETRY_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating new Poetry virtual environment..."
    poetry config virtualenvs.in-project true
    poetry env use python3
else
    echo "Poetry virtual environment already exists."
fi

# Install dependencies
echo "Installing dependencies from pyproject.toml..."
poetry install

# Create logs directory
mkdir -p logs

echo "Setup complete!"
echo "To activate the virtual environment, run: poetry shell"
echo "To run the application: poetry run python run.py" 