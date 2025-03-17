#!/bin/bash
# Script to run integration tests for Cyberon API

# Set colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Running Cyberon API Integration Tests${NC}"
echo -e "${BLUE}===========================================${NC}"

# Check if a specific test is provided
if [ "$1" ]; then
    echo -e "${BLUE}Running specific test: $1${NC}"
    pytest -m integration app/tests/$1 -v
else
    # Run all integration tests
    echo -e "${BLUE}Running all integration tests...${NC}"
    pytest -m integration -v
fi

# Capture the exit code
result=$?

# Display the result
if [ $result -eq 0 ]; then
    echo -e "${GREEN}All integration tests passed!${NC}"
else
    echo -e "${RED}Integration tests failed with exit code $result${NC}"
fi

exit $result