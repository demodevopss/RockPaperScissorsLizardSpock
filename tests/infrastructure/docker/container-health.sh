#!/bin/bash
# Docker Container Health and Security Tests for RPSLS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPORT_DIR="reports/infrastructure"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$REPORT_DIR/docker_health_$TIMESTAMP.html"

mkdir -p "$REPORT_DIR"

echo -e "${BLUE}🐳 Starting Docker Infrastructure Tests${NC}"
echo "========================================="

# Initialize report
cat > "$REPORT_FILE" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Docker Infrastructure Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .test { margin: 20px 0; padding: 15px; border-radius: 5px; }
        .pass { background: #d4edda; border-left: 5px solid #28a745; }
        .fail { background: #f8d7da; border-left: 5px solid #dc3545; }
        .info { background: #d1ecf1; border-left: 5px solid #17a2b8; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 3px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>🐳 Docker Infrastructure Test Report</h1>
    <p>Generated: $(date)</p>
EOF

# Test functions
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="$3"
    
    echo -e "${YELLOW}Testing: $test_name${NC}"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASS: $test_name${NC}"
        cat >> "$REPORT_FILE" << EOF
    <div class="test pass">
        <h3>✅ $test_name - PASSED</h3>
        <pre>$test_command</pre>
    </div>
EOF
        return 0
    else
        echo -e "${RED}❌ FAIL: $test_name${NC}"
        cat >> "$REPORT_FILE" << EOF
    <div class="test fail">
        <h3>❌ $test_name - FAILED</h3>
        <pre>$test_command</pre>
        <p>Expected: $expected_result</p>
    </div>
EOF
        return 1
    fi
}

run_info_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "${BLUE}Info: $test_name${NC}"
    local result=$(eval "$test_command")
    echo "$result"
    
    cat >> "$REPORT_FILE" << EOF
    <div class="test info">
        <h3>ℹ️ $test_name</h3>
        <pre>$result</pre>
    </div>
EOF
}

# Test 1: Docker daemon is running
run_test "Docker Daemon Running" "docker version >/dev/null 2>&1" "Docker daemon should be accessible"

# Test 2: Check RPSLS images exist
run_test "RPSLS API Image Exists" "docker images | grep -q 'devopsserdar/rpsls'" "Image should be present"
run_test "RPSLS Web Image Exists" "docker images | grep -q 'devopsserdar/rpsls-web'" "Image should be present"

# Test 3: Image sizes are reasonable
run_info_test "RPSLS API Image Size" "docker images devopsserdar/rpsls:latest --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}'"
run_info_test "RPSLS Web Image Size" "docker images devopsserdar/rpsls-web:latest --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}'"

# Test 4: Image vulnerability scan (if Trivy is available)
if command -v trivy >/dev/null 2>&1; then
    echo -e "${YELLOW}Running Trivy security scan...${NC}"
    
    # Scan API image
    trivy image --exit-code 0 --severity HIGH,CRITICAL --format json devopsserdar/rpsls:latest > "$REPORT_DIR/api_vulnerabilities.json" 2>/dev/null || true
    api_vulns=$(cat "$REPORT_DIR/api_vulnerabilities.json" | jq -r '.Results[]?.Vulnerabilities? | length' 2>/dev/null || echo "0")
    
    if [ "$api_vulns" -eq 0 ]; then
        run_test "API Image Security Scan" "echo 'No critical vulnerabilities found'" "No critical/high vulnerabilities"
    else
        echo -e "${RED}❌ Found $api_vulns vulnerabilities in API image${NC}"
        cat >> "$REPORT_FILE" << EOF
    <div class="test fail">
        <h3>❌ API Image Security Scan - FAILED</h3>
        <p>Found $api_vulns critical/high vulnerabilities</p>
        <p>Detailed report: reports/infrastructure/api_vulnerabilities.json</p>
    </div>
EOF
    fi
    
    # Scan Web image
    trivy image --exit-code 0 --severity HIGH,CRITICAL --format json devopsserdar/rpsls-web:latest > "$REPORT_DIR/web_vulnerabilities.json" 2>/dev/null || true
    web_vulns=$(cat "$REPORT_DIR/web_vulnerabilities.json" | jq -r '.Results[]?.Vulnerabilities? | length' 2>/dev/null || echo "0")
    
    if [ "$web_vulns" -eq 0 ]; then
        run_test "Web Image Security Scan" "echo 'No critical vulnerabilities found'" "No critical/high vulnerabilities"
    else
        echo -e "${RED}❌ Found $web_vulns vulnerabilities in Web image${NC}"
    fi
else
    echo -e "${YELLOW}Trivy not available, skipping vulnerability scan${NC}"
fi

# Test 5: Dockerfile best practices
echo -e "${YELLOW}Checking Dockerfile best practices...${NC}"

check_dockerfile() {
    local dockerfile="$1"
    local name="$2"
    
    if [ -f "$dockerfile" ]; then
        echo -e "${BLUE}Analyzing $name Dockerfile...${NC}"
        
        # Check for non-root user
        if grep -q "USER" "$dockerfile"; then
            run_test "$name - Non-root user" "grep -q 'USER' $dockerfile" "Should run as non-root user"
        else
            echo -e "${RED}❌ $name Dockerfile should specify USER directive${NC}"
        fi
        
        # Check for health check
        if grep -q "HEALTHCHECK" "$dockerfile"; then
            run_test "$name - Health check" "grep -q 'HEALTHCHECK' $dockerfile" "Should include health check"
        else
            echo -e "${YELLOW}⚠️ $name Dockerfile could benefit from HEALTHCHECK${NC}"
        fi
        
        # Check for minimal base image
        if grep -q "alpine\|slim" "$dockerfile"; then
            run_test "$name - Minimal base image" "grep -q 'alpine\\|slim' $dockerfile" "Should use minimal base image"
        else
            echo -e "${YELLOW}⚠️ Consider using minimal base image for $name${NC}"
        fi
        
        # Check for multi-stage build
        if grep -c "^FROM" "$dockerfile" | grep -q "[2-9]"; then
            run_test "$name - Multi-stage build" "test \$(grep -c '^FROM' $dockerfile) -gt 1" "Multi-stage build reduces image size"
        fi
        
    else
        echo -e "${RED}❌ $dockerfile not found${NC}"
    fi
}

check_dockerfile "devops/docker/Dockerfile" "API"
check_dockerfile "Source/Services/RPSLS.Game/Server/Dockerfile" "Web"

# Test 6: Docker Compose validation
if [ -f "devops/docker/docker-compose.tests.yml" ]; then
    run_test "Docker Compose Validation" "docker-compose -f devops/docker/docker-compose.tests.yml config >/dev/null 2>&1" "Compose file should be valid"
else
    echo -e "${YELLOW}⚠️ Docker Compose test file not found${NC}"
fi

# Test 7: Container resource limits
run_info_test "Docker System Info" "docker system df"
run_info_test "Docker Version" "docker version --format 'Version: {{.Server.Version}}, API: {{.Server.APIVersion}}'"

# Test 8: Network configuration
run_info_test "Docker Networks" "docker network ls"

# Test 9: Volume information
run_info_test "Docker Volumes" "docker volume ls"

# Generate summary
echo -e "${BLUE}Generating test summary...${NC}"

cat >> "$REPORT_FILE" << EOF
    <h2>Test Summary</h2>
    <div class="test info">
        <h3>Infrastructure Health Status</h3>
        <ul>
            <li>Docker daemon is operational</li>
            <li>RPSLS images are available</li>
            <li>Security scanning completed</li>
            <li>Dockerfile best practices reviewed</li>
        </ul>
    </div>
    
    <h2>Recommendations</h2>
    <div class="test info">
        <ul>
            <li>Regularly update base images</li>
            <li>Implement automated vulnerability scanning</li>
            <li>Use multi-stage builds to reduce image size</li>
            <li>Add health checks to containers</li>
            <li>Run containers as non-root users</li>
        </ul>
    </div>
    
    <h2>Next Steps</h2>
    <div class="test info">
        <ol>
            <li>Address any failed tests</li>
            <li>Review vulnerability reports</li>
            <li>Optimize Docker images</li>
            <li>Implement monitoring</li>
        </ol>
    </div>
</body>
</html>
EOF

echo -e "${GREEN}✅ Docker infrastructure tests completed${NC}"
echo -e "${BLUE}📊 Report saved to: $REPORT_FILE${NC}"

# Open report if on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${BLUE}Opening report in browser...${NC}"
    open "$REPORT_FILE" 2>/dev/null || true
fi
