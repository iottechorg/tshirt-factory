#!/bin/bash

# Factory Simulation Environment Setup
# Simple setup that just prepares the environment

set -e  # Exit on any error

echo "🏭 Factory Simulation Environment Setup"
echo "========================================"

# Configuration
VENV_NAME="factory-sim"
PYTHON_VERSION="python3"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}[INFO]${NC} Checking Python..."
if ! command -v $PYTHON_VERSION &> /dev/null; then
    echo "Error: Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

echo -e "${BLUE}[INFO]${NC} Creating virtual environment..."
$PYTHON_VERSION -m venv $VENV_NAME

echo -e "${BLUE}[INFO]${NC} Activating virtual environment..."
source $VENV_NAME/bin/activate

echo -e "${BLUE}[INFO]${NC} Installing basic dependencies..."
pip install --upgrade pip
pip install pyyaml pydantic

echo -e "${GREEN}[SUCCESS]${NC} Environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the environment: ${BLUE}source $VENV_NAME/bin/activate${NC}"
echo "2. Generate a factory: ${BLUE}python tools/factory_generator.py factory-configs/tshirt-factory.json${NC}"
echo "3. Navigate to generated factory: ${BLUE}cd generated-factories/tshirt-factory-id${NC}"
echo "4. Start factory: ${BLUE}docker compose up --build${NC}"
echo ""
echo "Quick test: ${BLUE}python -c \"import yaml, pydantic; print('Dependencies OK!')\"${NC}"