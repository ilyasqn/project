#!/bin/bash

# Deploy microservices to Kubernetes
# Usage: ./scripts/deploy.sh [--context CONTEXT] [--build]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
K8S_DIR="$PROJECT_ROOT/k8s"

# Default values
CONTEXT=""
BUILD=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --context)
            CONTEXT="$2"
            shift 2
            ;;
        --build)
            BUILD=true
            shift
            ;;
        --delete)
            DELETE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set kubectl context if specified
if [ -n "$CONTEXT" ]; then
    echo "Using kubectl context: $CONTEXT"
    kubectl config use-context "$CONTEXT"
fi

# Build images if requested
if [ "$BUILD" = true ]; then
    echo "Building Docker images..."
    # Use minikube image build if minikube is available
    if command -v minikube &> /dev/null && minikube status &> /dev/null; then
        "$SCRIPT_DIR/build-all.sh" --minikube
    else
        "$SCRIPT_DIR/build-all.sh"
    fi
    echo ""
fi

# Delete resources if requested
if [ "$DELETE" = true ]; then
    echo "Deleting all resources..."
    kubectl delete namespace microservices --ignore-not-found
    echo "Resources deleted."
    exit 0
fi

echo "Deploying microservices to Kubernetes..."
echo ""

# Apply namespace first
echo "Creating namespace..."
kubectl apply -f "$K8S_DIR/namespace.yaml"

# Apply config and secrets
echo "Applying ConfigMap and Secrets..."
kubectl apply -f "$K8S_DIR/configmap.yaml"
kubectl apply -f "$K8S_DIR/secrets.yaml"

# Deploy PostgreSQL
echo "Deploying PostgreSQL..."
kubectl apply -f "$K8S_DIR/postgres/pvc.yaml"
kubectl apply -f "$K8S_DIR/postgres/deployment.yaml"
kubectl apply -f "$K8S_DIR/postgres/service.yaml"

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n microservices --timeout=120s

# Deploy RabbitMQ
echo "Deploying RabbitMQ..."
kubectl apply -f "$K8S_DIR/rabbitmq/deployment.yaml"
kubectl apply -f "$K8S_DIR/rabbitmq/service.yaml"

# Wait for RabbitMQ to be ready
echo "Waiting for RabbitMQ to be ready..."
kubectl wait --for=condition=ready pod -l app=rabbitmq -n microservices --timeout=120s

# Deploy MongoDB
echo "Deploying MongoDB..."
kubectl apply -f "$K8S_DIR/mongodb/pvc.yaml"
kubectl apply -f "$K8S_DIR/mongodb/deployment.yaml"
kubectl apply -f "$K8S_DIR/mongodb/service.yaml"

# Wait for MongoDB to be ready
echo "Waiting for MongoDB to be ready..."
kubectl wait --for=condition=ready pod -l app=mongodb -n microservices --timeout=180s

# Deploy Redis
echo "Deploying Redis..."
kubectl apply -f "$K8S_DIR/redis/deployment.yaml"
kubectl apply -f "$K8S_DIR/redis/service.yaml"

# Wait for Redis to be ready
echo "Waiting for Redis to be ready..."
kubectl wait --for=condition=ready pod -l app=redis -n microservices --timeout=120s

# Deploy application services
echo "Deploying User Service..."
kubectl apply -f "$K8S_DIR/user/deployment.yaml"
kubectl apply -f "$K8S_DIR/user/service.yaml"

echo "Deploying Product Service..."
kubectl apply -f "$K8S_DIR/product/deployment.yaml"
kubectl apply -f "$K8S_DIR/product/service.yaml"

echo "Deploying Notification Service..."
kubectl apply -f "$K8S_DIR/notification/deployment.yaml"
kubectl apply -f "$K8S_DIR/notification/service.yaml"

echo "Deploying AI Service..."
kubectl apply -f "$K8S_DIR/ai/deployment.yaml"
kubectl apply -f "$K8S_DIR/ai/service.yaml"

# Deploy Monitoring Stack
echo "Deploying Monitoring Stack (Prometheus, Loki, Promtail, Grafana)..."
kubectl apply -f "$K8S_DIR/monitoring/prometheus.yaml"
kubectl apply -f "$K8S_DIR/monitoring/loki.yaml"
kubectl apply -f "$K8S_DIR/monitoring/promtail.yaml"
kubectl apply -f "$K8S_DIR/monitoring/grafana.yaml"

# Wait for all application services to be ready
echo "Waiting for services to be ready..."
kubectl wait --for=condition=ready pod -l app=user-service -n microservices --timeout=120s
kubectl wait --for=condition=ready pod -l app=product-service -n microservices --timeout=120s
kubectl wait --for=condition=ready pod -l app=notification-service -n microservices --timeout=120s
kubectl wait --for=condition=ready pod -l app=ai-service -n microservices --timeout=120s

echo ""
echo "================================================"
echo "Deployment complete!"
echo "================================================"
echo ""

# Get minikube IP for NodePort access
MINIKUBE_IP=$(minikube ip 2>/dev/null || echo "localhost")

echo "Application Services:"
echo ""
echo "  User Service:         http://${MINIKUBE_IP}:30001/docs"
echo "  Product Service:      http://${MINIKUBE_IP}:30002/docs"
echo "  Notification Service: http://${MINIKUBE_IP}:30003/docs"
echo "  AI Service:           http://${MINIKUBE_IP}:30004/docs"
echo ""
echo "Infrastructure Services:"
echo ""
echo "  PostgreSQL:           ${MINIKUBE_IP}:30432"
echo "  RabbitMQ AMQP:        ${MINIKUBE_IP}:30672"
echo "  RabbitMQ Management:  http://${MINIKUBE_IP}:31672 (guest/guest)"
echo "  MongoDB:              ${MINIKUBE_IP}:30017"
echo "  Redis:                ${MINIKUBE_IP}:30379"
echo ""
echo "Monitoring:"
echo ""
echo "  Grafana:              http://${MINIKUBE_IP}:30300 (admin/admin)"
echo "  Prometheus:           http://${MINIKUBE_IP}:30090"
echo ""
echo "Health checks:"
echo "  curl http://${MINIKUBE_IP}:30001/health"
echo "  curl http://${MINIKUBE_IP}:30002/health"
echo "  curl http://${MINIKUBE_IP}:30003/health"
echo "  curl http://${MINIKUBE_IP}:30004/health"
echo ""
echo "To check pod status:"
echo "  kubectl get pods -n microservices"
echo ""
echo "To view logs:"
echo "  kubectl logs -f deployment/user-service -n microservices"
echo ""
echo "To delete all resources:"
echo "  $0 --delete"
