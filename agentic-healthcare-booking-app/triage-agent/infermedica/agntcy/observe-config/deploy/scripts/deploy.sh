#!/bin/bash
# ====================
# FILE: scripts/deploy.sh
# ====================

set -e  # Exit on any error

echo "Observability Stack Deployment"
echo "========================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo "Error: This script should not be run as root. Please run as a non-root user with sudo privileges."
    exit 1
fi

# Install Docker if not present
install_docker() {
    if ! command -v docker &> /dev/null; then
        echo "Installing Docker..."
        
        # Detect OS and install Docker
        if [ -f /etc/amazon-linux-release ]; then
            # Amazon Linux
            sudo yum update -y
            sudo yum install -y docker
            sudo systemctl start docker
            sudo systemctl enable docker
            sudo usermod -aG docker $USER || true # '|| true' to prevent exit if user already in group
        
        elif [ -f /etc/debian_version ]; then
            # Ubuntu/Debian
            sudo apt update
            sudo apt install -y docker.io
            sudo systemctl start docker
            sudo systemctl enable docker
            sudo usermod -aG docker $USER || true
            
        else
            echo "Attempting to install Docker via get.docker.com (generic Linux)..."
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER || true
            rm get-docker.sh
        fi
        
        echo "Docker installed. Please log out and back in, then run this script again to apply Docker group changes."
        exit 0
    else
        echo "Docker is already installed."
    fi
}

# Install Docker Compose
install_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        echo "Installing Docker Compose..."
        # Download Docker Compose from GitHub releases
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        echo "Docker Compose installed."
    else
        echo "Docker Compose is already installed."
    fi
}

# Create required directories
setup_directories() {
    echo "Setting up data directories for observability components..."
    sudo mkdir -p /opt/observability-stack/data/{clickhouse,grafana}
    # Ensure the current user owns the directories for write permissions
    sudo chown -R $USER:$USER /opt/observability-stack
    echo "Directories created and permissions set."
}

# Update configuration files with secure passwords
update_passwords() {
    echo "Generating secure passwords for services..."
    
    # Generate random passwords
    # Using openssl for robust random string generation
    CLICKHOUSE_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    GRAFANA_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    # Update .env file placeholders
    # Assumes .env file exists and contains placeholders like SecureClickHouse123!
    sed -i "s/StrongPassword!/$CLICKHOUSE_PASS/g" .env || { echo "Error: ClickHouse password placeholder not found in .env"; exit 1; }
    sed -i "s/StrongPassword!/$GRAFANA_PASS/g" .env || { echo "Error: Grafana password placeholder not found in .env"; exit 1; }
    
    # Update ClickHouse users.xml (assuming it's in a 'clickhouse' subdirectory)
    sed -i "s/StrongPassword!/$CLICKHOUSE_PASS/g" clickhouse/users.xml || { echo "Error: ClickHouse password placeholder not found in clickhouse/users.xml"; exit 1; }
    
    # Update Grafana datasource (assuming it's in 'grafana/provisioning/datasources/datasources.yml')
    sed -i "s/vStrongPassword!/$CLICKHOUSE_PASS/g" grafana/provisioning/datasources/datasources.yml || { echo "Error: ClickHouse password placeholder not found in grafana/provisioning/datasources/datasources.yml"; exit 1; }
    
    echo "Generated passwords:"
    echo "--------------------"
    echo "ClickHouse: $CLICKHOUSE_PASS"
    echo "Grafana:    $GRAFANA_PASS"
    echo "--------------------"
    echo "IMPORTANT: Save these passwords securely! They are also saved to ./.passwords file."
    
    # Save to file for later reference (hidden and restricted permissions)
    cat > .passwords <<EOF
ClickHouse Password: $CLICKHOUSE_PASS
Grafana Password: $GRAFANA_PASS
Generated on: $(date)
EOF
    chmod 600 .passwords # Restrict read/write access to owner only
}

# Deploy the stack
deploy_stack() {
    echo "Deploying observability stack services using Docker Compose..."
    
    # Pull latest images to ensure up-to-date versions
    docker-compose pull
    
    # Start services in detached mode
    docker-compose up -d
    
    echo "Docker Compose services started."
}

# Wait for services to be ready
wait_for_services() {
    echo "Waiting for observability services to become ready..."
    
    # Wait for ClickHouse
    echo "Waiting for ClickHouse (max 5 minutes)..."
    for i in {1..60}; do # 60 attempts * 5 seconds = 300 seconds (5 minutes)
        if docker-compose exec -T clickhouse clickhouse-client --query "SELECT 1" &>/dev/null; then
            echo "ClickHouse is ready."
            break
        fi
        sleep 5
        echo "Waiting for ClickHouse... ($i/60)"
        if [ $i -eq 60 ]; then echo "ClickHouse did not become ready in time."; exit 1; fi
    done
    
    # Wait for OTEL Collector (assuming it exposes a health endpoint)
    echo "Waiting for OpenTelemetry Collector (max 2.5 minutes)..."
    for i in {1..30}; do # 30 attempts * 5 seconds = 150 seconds (2.5 minutes)
        # Check a common health endpoint for OTel Collector
        if curl -sf http://localhost:13133/ &>/dev/null; then
            echo "OpenTelemetry Collector is ready."
            break
        fi
        sleep 5
        echo "Waiting for OpenTelemetry Collector... ($i/30)"
        if [ $i -eq 30 ]; then echo "OpenTelemetry Collector did not become ready in time."; exit 1; fi
    done
    
    # Wait for Grafana
    echo "Waiting for Grafana (max 2.5 minutes)..."
    for i in {1..30}; do # 30 attempts * 5 seconds = 150 seconds (2.5 minutes)
        # Check Grafana's health API endpoint
        if curl -sf http://localhost:3000/api/health &>/dev/null; then
            echo "Grafana is ready."
            break
        fi
        sleep 5
        echo "Waiting for Grafana... ($i/30)"
        if [ $i -eq 30 ]; then echo "Grafana did not become ready in time."; exit 1; fi
    done
    echo "All core observability services are up and running."
}

# Display final information
show_completion() {
    # Attempt to get public IP, useful for cloud deployments
    local PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")
    
    echo ""
    echo "Deployment completed successfully!"
    echo "================================="
    echo ""
    echo "Service Access Information:"
    echo "  Grafana Dashboard: http://$PUBLIC_IP:3000"
    echo "  OpenTelemetry HTTP Endpoint (for traces/logs): http://$PUBLIC_IP:4318/v1/traces and http://$PUBLIC_IP:4318/v1/logs"
    echo "  OpenTelemetry gRPC Endpoint (for metrics): grpc://$PUBLIC_IP:4317"
    echo "  OpenTelemetry Collector Health Check: http://$PUBLIC_IP:13133/"
    echo ""
    echo "Login Credentials:"
    echo "  Grafana Username: admin"
    echo "  Grafana Password: (see ./.passwords file for the generated password)"
    echo ""
    echo "Container Status:"
    docker-compose ps
    echo ""
    echo "Next Steps:"
    echo "1. Configure your application's OTLP_HTTP_ENDPOINT to: http://$PUBLIC_IP:4318"
    echo "   (or http://localhost:4318 if running locally and accessing from host)"
    echo "2. Open Grafana at http://$PUBLIC_IP:3000 and log in with the provided credentials."
    echo "3. Run your application to start sending telemetry data."
    echo "4. Explore the pre-configured dashboards in Grafana or create your own."
    echo ""
    echo "Useful Commands:"
    echo "  View service logs: docker-compose logs -f [service-name]"
    echo "  Stop all services: docker-compose down"
    echo "  Restart all services: docker-compose restart"
    echo "  Access ClickHouse CLI: docker-compose exec clickhouse clickhouse-client"
    echo ""
}

# Main deployment function
main() {
    echo "Starting observability stack deployment process..."
    
    install_docker
    install_docker_compose
    setup_directories
    update_passwords
    deploy_stack
    wait_for_services
    show_completion
    
    echo "Observability stack deployment finished!"
}

# Run main function
main "$@"