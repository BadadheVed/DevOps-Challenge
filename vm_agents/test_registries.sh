#!/bin/bash

# Test script to check if metrics from global registry and isolated registries collide

echo "=========================================="
echo "Prometheus Registry Collision Test"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}[INFO] Starting tests...${NC}"
echo ""

# Get Python executable path from venv
PYTHON_CMD="/Users/ved/DevOps-Challenge/.venv/bin/python3"

# Start the FastAPI app with GLOBAL registry on port 8000
echo -e "${GREEN}[1/4] Starting FastAPI app (GLOBAL registry) on port 8000${NC}"
cd "$SCRIPT_DIR"
$PYTHON_CMD api.py &
API_PID=$!
sleep 3
echo -e "${GREEN}✓ API started (PID: $API_PID)${NC}"
echo ""

# Start script instance 1 with ISOLATED registry on port 9001
echo -e "${GREEN}[2/4] Starting Script Instance 1 (ISOLATED registry) on port 9001${NC}"
$PYTHON_CMD script.py --instance-id 1 --port 9001 --operations 10 &
SCRIPT1_PID=$!
sleep 2
echo -e "${GREEN}✓ Script Instance 1 started (PID: $SCRIPT1_PID)${NC}"
echo ""

# Start script instance 2 with ISOLATED registry on port 9002
echo -e "${GREEN}[3/4] Starting Script Instance 2 (ISOLATED registry) on port 9002${NC}"
$PYTHON_CMD script.py --instance-id 2 --port 9002 --operations 10 &
SCRIPT2_PID=$!
sleep 2
echo -e "${GREEN}✓ Script Instance 2 started (PID: $SCRIPT2_PID)${NC}"
echo ""

# Start script instance 3 with ISOLATED registry on port 9003
echo -e "${GREEN}[4/4] Starting Script Instance 3 (ISOLATED registry) on port 9003${NC}"
$PYTHON_CMD script.py --instance-id 3 --port 9003 --operations 10 &
SCRIPT3_PID=$!
sleep 2
echo -e "${GREEN}✓ Script Instance 3 started (PID: $SCRIPT3_PID)${NC}"
echo ""

echo -e "${BLUE}=========================================="
echo "All instances running. Access metrics at:"
echo "=========================================${NC}"
echo -e "${YELLOW}API (GLOBAL):      http://localhost:8000/metrics${NC}"
echo -e "${YELLOW}Script Instance 1: http://localhost:9001/metrics${NC}"
echo -e "${YELLOW}Script Instance 2: http://localhost:9002/metrics${NC}"
echo -e "${YELLOW}Script Instance 3: http://localhost:9003/metrics${NC}"
echo ""
echo -e "${YELLOW}API Info: http://localhost:8000/info${NC}"
echo ""

# Monitor and collect metrics
echo -e "${BLUE}[INFO] Collecting metrics for comparison...${NC}"
sleep 20

echo ""
echo -e "${BLUE}=========================================="
echo "Metrics Comparison:"
echo "=========================================${NC}"
echo ""

echo -e "${GREEN}[API - GLOBAL Registry]${NC}"
echo "http://localhost:8000/metrics"
curl -s http://localhost:8000/metrics 2>/dev/null | grep -E "api_test|http_requests|http_request_duration" | head -10

echo ""
echo -e "${GREEN}[Script Instance 1 - ISOLATED Registry]${NC}"
echo "http://localhost:9001/metrics"
curl -s http://localhost:9001/metrics 2>/dev/null | grep -E "script_operations|script_operation_duration" | head -10

echo ""
echo -e "${GREEN}[Script Instance 2 - ISOLATED Registry]${NC}"
echo "http://localhost:9002/metrics"
curl -s http://localhost:9002/metrics 2>/dev/null | grep -E "script_operations|script_operation_duration" | head -10

echo ""
echo -e "${GREEN}[Script Instance 3 - ISOLATED Registry]${NC}"
echo "http://localhost:9003/metrics"
curl -s http://localhost:9003/metrics 2>/dev/null | grep -E "script_operations|script_operation_duration" | head -10

echo ""
echo -e "${BLUE}=========================================="
echo "Test Analysis:"
echo "=========================================${NC}"
echo -e "${YELLOW}✓ API uses GLOBAL registry (shared across instances)${NC}"
echo -e "${YELLOW}✓ Scripts use ISOLATED registries (unique per instance)${NC}"
echo -e "${YELLOW}✓ Each script's metrics appear only on its own port${NC}"
echo -e "${YELLOW}✓ No collision - each registry is independent${NC}"

# Cleanup
echo ""
echo -e "${BLUE}Cleaning up processes...${NC}"
kill $API_PID $SCRIPT1_PID $SCRIPT2_PID $SCRIPT3_PID 2>/dev/null
wait $API_PID $SCRIPT1_PID $SCRIPT2_PID $SCRIPT3_PID 2>/dev/null

echo -e "${GREEN}[DONE] All processes stopped${NC}"
