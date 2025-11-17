#!/bin/bash

set -e  # Exit immediately if any command exits with a non-zero status


# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "AWS Credentials Setup for Docker Development"
echo "================================================"
echo ""

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Check if AWS CLI is installed
print_info "Checking for AWS CLI..."
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed, plz install the AWS CLI first, and then run this script again."
    print_info "Install AWS CLI:"
    print_info "  macOS:   brew install awscli"
    print_info "  Linux:   https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi
print_success "AWS CLI found: $(aws --version)"

# Check if credentials already exist
if [ -f "$HOME/.aws/credentials" ]; then
    print_info "Existing AWS credentials found"
    read -p "Do you want to reconfigure? (y/N): " reconfigure
    if [[ ! $reconfigure =~ ^[Yy]$ ]]; then
        echo ""
        print_info "Skipping credential configuration"
        existing_creds=true
    else
        existing_creds=false
    fi
else
    existing_creds=false
fi


# Configure AWS credentials
if [ "$existing_creds" = false ]; then
    echo ""
    print_info "Configuring AWS credentials..."
    echo ""
    echo "You'll need:"
    echo "  1. AWS Access Key ID"
    echo "  2. AWS Secret Access Key"
    echo "  3. Default region (e.g., us-west-1)"
    echo ""
    
    read -p "Enter AWS Access Key ID: " access_key
    read -p "Enter AWS Secret Access Key: " secret_key
    read -p "Enter default region [us-west-1]: " region
    region=${region:-us-west-1}
    
    # Use aws configure set to avoid credentials in history
    aws configure set aws_access_key_id "$access_key"
    aws configure set aws_secret_access_key "$secret_key"
    aws configure set region "$region"
    aws configure set output json
    
    print_success "AWS credentials configured"
fi

# Verify credentials work
echo ""
print_info "Verifying credentials..."
if aws sts get-caller-identity &> /dev/null; then
    print_success "Credentials verified successfully"
    aws sts get-caller-identity --output table
else
    print_error "Failed to verify credentials"
    echo "Please check your Access Key ID and Secret Access Key"
    exit 1
fi

print_info "Setup Lemonaid Docker environment"

# Override the .env file from s3 bucket
print_info "Overriding the .env file from s3 bucket..."
aws s3 cp s3://lemonaid-init-files-bucket/.env .env


print_info "Cleaning up previous Docker containers..."
docker-compose -f ./docker/docker-compose.yml down --remove-orphans --volumes 

print_info "Building Docker image..."
docker-compose -f ./docker/docker-compose.yml build --no-cache

print_info "Starting Docker containers (running in detached mode)..."
docker-compose -f ./docker/docker-compose.yml up --force-recreate

print_success "Setup complete!"
print_info " - Service URL: http://localhost:8000"