#!/bin/bash
#
# build-container.sh - Build the kube-broadcast container
#
# This script builds the kube-broadcast container image using podman/docker.
# The build includes running all tests - build will fail if tests fail.

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="${IMAGE_NAME:-kube-broadcast}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
CONTAINERFILE="containerfiles/kube-broadcast"

# Detect container engine
if command -v podman &> /dev/null; then
    CONTAINER_ENGINE="podman"
elif command -v docker &> /dev/null; then
    CONTAINER_ENGINE="docker"
else
    echo -e "${RED}Error: Neither podman nor docker found${NC}"
    echo "Please install podman or docker to build containers"
    exit 1
fi

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}kube-broadcast Container Build${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
echo -e "Container Engine: ${GREEN}${CONTAINER_ENGINE}${NC}"
echo -e "Image Name:       ${GREEN}${IMAGE_NAME}:${IMAGE_TAG}${NC}"
echo -e "Containerfile:    ${GREEN}${CONTAINERFILE}${NC}"
echo ""

# Check if containerfile exists
if [ ! -f "$CONTAINERFILE" ]; then
    echo -e "${RED}Error: Containerfile not found: $CONTAINERFILE${NC}"
    exit 1
fi

# Check if source directory exists
if [ ! -d "src" ]; then
    echo -e "${RED}Error: Source directory 'src' not found${NC}"
    echo "Please run this script from the kube-broadcast project root"
    exit 1
fi

# Build the container
echo -e "${YELLOW}Starting build...${NC}"
echo ""

BUILD_START=$(date +%s)

if $CONTAINER_ENGINE build \
    -f "$CONTAINERFILE" \
    -t "${IMAGE_NAME}:${IMAGE_TAG}" \
    . ; then

    BUILD_END=$(date +%s)
    BUILD_TIME=$((BUILD_END - BUILD_START))

    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}✓ Build Successful!${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo -e "Image: ${GREEN}${IMAGE_NAME}:${IMAGE_TAG}${NC}"
    echo -e "Build time: ${GREEN}${BUILD_TIME}s${NC}"
    echo ""

    # Show image info
    echo -e "${BLUE}Image Information:${NC}"
    $CONTAINER_ENGINE images "${IMAGE_NAME}:${IMAGE_TAG}"
    echo ""

    # Suggest next steps
    echo -e "${BLUE}Next Steps:${NC}"
    echo ""
    echo "Run the container:"
    echo -e "  ${YELLOW}$CONTAINER_ENGINE run -p 8000:8000 ${IMAGE_NAME}:${IMAGE_TAG}${NC}"
    echo ""
    echo "Run with configuration:"
    echo -e "  ${YELLOW}$CONTAINER_ENGINE run -p 8000:8000 \\${NC}"
    echo -e "    ${YELLOW}-e KUBE_TOKEN=\"your-token\" \\${NC}"
    echo -e "    ${YELLOW}${IMAGE_NAME}:${IMAGE_TAG}${NC}"
    echo ""
    echo "Check health:"
    echo -e "  ${YELLOW}curl http://localhost:8000/health${NC}"
    echo ""

else
    BUILD_END=$(date +%s)
    BUILD_TIME=$((BUILD_END - BUILD_START))

    echo ""
    echo -e "${RED}================================${NC}"
    echo -e "${RED}✗ Build Failed!${NC}"
    echo -e "${RED}================================${NC}"
    echo ""
    echo -e "Build time: ${RED}${BUILD_TIME}s${NC}"
    echo ""
    echo -e "${YELLOW}Common Issues:${NC}"
    echo "1. Tests failed - check test output above"
    echo "2. Dependencies missing - verify pyproject.toml"
    echo "3. Source files missing - check src/ directory"
    echo ""
    echo "Run tests locally to debug:"
    echo -e "  ${YELLOW}./test.sh${NC}"
    echo ""
    exit 1
fi
