#!/bin/bash
#
# test.sh - Run all tests for kube-broadcast
#
# This script runs both data layer tests and integration tests.
# Can be run from anywhere in the project.

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
SRC_DIR="$PROJECT_ROOT/app/src"
TESTS_DIR="$PROJECT_ROOT/app/tests"

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}kube-broadcast Test Suite${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest not installed${NC}"
    echo "Install with: pip install pytest pytest-cov"
    exit 1
fi

# Track test results
FAILED=0

# Function to run tests and track failures
run_test() {
    local test_name="$1"
    local test_cmd="$2"

    echo -e "${YELLOW}Running: $test_name${NC}"
    echo "Command: $test_cmd"
    echo ""

    if eval "$test_cmd"; then
        echo -e "${GREEN}✓ $test_name passed${NC}"
        echo ""
    else
        echo -e "${RED}✗ $test_name failed${NC}"
        echo ""
        FAILED=$((FAILED + 1))
    fi
}

# 1. Data layer tests (fast only)
echo -e "${GREEN}1. Data Layer Tests (fast)${NC}"
echo "----------------------------"
cd "$SRC_DIR"
run_test "Data layer (fast)" \
    "python -m pytest ${TESTS_DIR}/ -v -m 'not slow' --tb=short -q"

# Summary
echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Test Summary${NC}"
echo -e "${GREEN}================================${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All test suites passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ $FAILED test suite(s) failed${NC}"
    exit 1
fi
