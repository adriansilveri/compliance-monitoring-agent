#!/bin/bash

# APRA Compliance Monitoring Application Deployment Script
# Following SOLID principles and best practices

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_REGISTRY=${DOCKER_REGISTRY:-"your-registry.amazonaws.com"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
NAMESPACE="compliance-monitoring"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

build_images() {
    log_info "Building Docker images..."
    
    # Build backend image
    log_info "Building backend image..."
    docker build -t ${DOCKER_REGISTRY}/compliance-backend:${IMAGE_TAG} ./backend
    
    # Build frontend image
    log_info "Building frontend image..."
    docker build -t ${DOCKER_REGISTRY}/compliance-frontend:${IMAGE_TAG} ./frontend
    
    log_success "Docker images built successfully"
}

push_images() {
    log_info "Pushing Docker images to registry..."
    
    # Login to ECR (if using AWS ECR)
    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${DOCKER_REGISTRY}
    
    # Push backend image
    docker push ${DOCKER_REGISTRY}/compliance-backend:${IMAGE_TAG}
    
    # Push frontend image
    docker push ${DOCKER_REGISTRY}/compliance-frontend:${IMAGE_TAG}
    
    log_success "Docker images pushed successfully"
}

deploy_to_kubernetes() {
    log_info "Deploying to Kubernetes..."
    
    # Create namespace
    kubectl apply -f k8s/namespace.yaml
    
    # Apply secrets and config maps
    kubectl apply -f k8s/secrets.yaml
    
    # Update image tags in deployment files
    sed -i.bak "s|compliance-backend:latest|${DOCKER_REGISTRY}/compliance-backend:${IMAGE_TAG}|g" k8s/backend-deployment.yaml
    sed -i.bak "s|compliance-frontend:latest|${DOCKER_REGISTRY}/compliance-frontend:${IMAGE_TAG}|g" k8s/frontend-deployment.yaml
    
    # Deploy backend
    kubectl apply -f k8s/backend-deployment.yaml
    
    # Deploy frontend
    kubectl apply -f k8s/frontend-deployment.yaml
    
    # Deploy ingress
    kubectl apply -f k8s/ingress.yaml
    
    # Deploy HPA
    kubectl apply -f k8s/hpa.yaml
    
    # Restore original deployment files
    mv k8s/backend-deployment.yaml.bak k8s/backend-deployment.yaml
    mv k8s/frontend-deployment.yaml.bak k8s/frontend-deployment.yaml
    
    log_success "Kubernetes deployment completed"
}

wait_for_deployment() {
    log_info "Waiting for deployment to be ready..."
    
    # Wait for backend deployment
    kubectl rollout status deployment/compliance-backend -n ${NAMESPACE} --timeout=300s
    
    # Wait for frontend deployment
    kubectl rollout status deployment/compliance-frontend -n ${NAMESPACE} --timeout=300s
    
    log_success "Deployment is ready"
}

run_tests() {
    log_info "Running tests..."
    
    # Run backend tests
    log_info "Running backend tests..."
    cd backend
    python -m pytest app/tests/ -v --cov=app --cov-report=term-missing
    cd ..
    
    # Run frontend tests (if available)
    if [ -f "frontend/package.json" ]; then
        log_info "Running frontend tests..."
        cd frontend
        npm test -- --coverage --watchAll=false
        cd ..
    fi
    
    log_success "Tests completed"
}

show_deployment_info() {
    log_info "Deployment Information:"
    echo "=========================="
    
    # Get service information
    kubectl get services -n ${NAMESPACE}
    
    # Get pod information
    kubectl get pods -n ${NAMESPACE}
    
    # Get ingress information
    kubectl get ingress -n ${NAMESPACE}
    
    log_info "Application URLs:"
    INGRESS_HOST=$(kubectl get ingress compliance-ingress -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    if [ ! -z "$INGRESS_HOST" ]; then
        echo "Frontend: https://${INGRESS_HOST}"
        echo "API: https://${INGRESS_HOST}/api/v1/docs"
    else
        log_warning "Ingress not ready yet. Check again in a few minutes."
    fi
}

cleanup() {
    log_info "Cleaning up..."
    
    # Remove temporary files
    rm -f k8s/*.bak
    
    log_success "Cleanup completed"
}

# Main deployment function
main() {
    log_info "Starting APRA Compliance Monitoring Application Deployment"
    
    case "${1:-deploy}" in
        "build")
            check_prerequisites
            build_images
            ;;
        "push")
            check_prerequisites
            push_images
            ;;
        "deploy")
            check_prerequisites
            build_images
            push_images
            deploy_to_kubernetes
            wait_for_deployment
            show_deployment_info
            ;;
        "test")
            run_tests
            ;;
        "local")
            log_info "Starting local development environment..."
            docker-compose up -d
            log_success "Local environment started. Access at http://localhost:3000"
            ;;
        "local-down")
            log_info "Stopping local development environment..."
            docker-compose down
            log_success "Local environment stopped"
            ;;
        "status")
            show_deployment_info
            ;;
        "cleanup")
            cleanup
            ;;
        *)
            echo "Usage: $0 {build|push|deploy|test|local|local-down|status|cleanup}"
            echo ""
            echo "Commands:"
            echo "  build      - Build Docker images"
            echo "  push       - Push Docker images to registry"
            echo "  deploy     - Full deployment to Kubernetes"
            echo "  test       - Run tests"
            echo "  local      - Start local development environment"
            echo "  local-down - Stop local development environment"
            echo "  status     - Show deployment status"
            echo "  cleanup    - Clean up temporary files"
            exit 1
            ;;
    esac
    
    cleanup
    log_success "Operation completed successfully!"
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# Run main function
main "$@"
