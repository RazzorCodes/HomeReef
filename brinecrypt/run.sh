#!/bin/bash
#
# run.sh - Start kube-broadcast server
#
# This script starts the kube-broadcast server and accepts the same
# parameters as kube_broadcast.py. Can be run from anywhere.
#
# Usage:
#   ./run.sh [options]
#   ./run.sh --config config.toml
#   ./run.sh --token TOKEN --ssh-admin KEY --ssh-agent KEY
#   ./run.sh --help

# Exit on error
set -e

# Get script directory (absolute path)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
SRC_DIR="$PROJECT_ROOT/app/src"
CONFIG_PATH="$SCRIPT_DIR/config/default-config.toml"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}Error: Python not found${NC}"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD=$(command -v python3 2>/dev/null || command -v python)

# Check if src directory exists
if [ ! -d "$SRC_DIR" ]; then
    echo -e "${RED}Error: Source directory not found: $SRC_DIR${NC}"
    exit 1
fi

# Check if kube_broadcast.py exists
if [ ! -f "$SRC_DIR/kube_broadcast.py" ]; then
    echo -e "${RED}Error: kube_broadcast.py not found in $SRC_DIR${NC}"
    exit 1
fi

# Print banner
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}kube-broadcast Server${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Starting from: $SRC_DIR"
echo "Python: $PYTHON_CMD"
echo ""

# Change to src directory
cd "$SRC_DIR"

# dummy server
while true; do printf "HTTP/1.1 200 OK\r\nContent-Length: 17\r\n\r\nSOME-REMOTE-DATA\n" | nc -l 127.0.0.1 9000; done &
server_pid=$!

# Start the server with all passed arguments
echo -e "${GREEN}Starting server...${NC}"
echo "Arguments: $@"
echo ""

# Run the application
exec $PYTHON_CMD -m kube_broadcast  --config $CONFIG_PATH "$@"
kill "$server_pid"
