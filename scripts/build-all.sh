#!/bin/bash

# Build all Docker images for the microservices
# Usage: ./scripts/build-all.sh [--push] [--registry REGISTRY]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
PUSH=false
REGISTRY=""
TAG="latest"
MINIKUBE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --push)
            PUSH=true
            shift
            ;;
        --registry)
            REGISTRY="$2/"
            shift 2
            ;;
        --tag)
            TAG="$2"
            shift 2
            ;;
        --minikube)
            MINIKUBE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Building microservices Docker images..."
echo "Project root: $PROJECT_ROOT"
echo "Registry: ${REGISTRY:-local}"
echo "Tag: $TAG"
echo ""

# Services to build
SERVICES=("user" "product" "notification" "ai")

cd "$PROJECT_ROOT"

for SERVICE in "${SERVICES[@]}"; do
    IMAGE_NAME="${REGISTRY}${SERVICE}-service:${TAG}"
    DOCKERFILE="services/${SERVICE}/Dockerfile.dev"

    echo "================================================"
    echo "Building ${SERVICE}-service..."
    echo "Image: $IMAGE_NAME"
    echo "================================================"

    if [ "$MINIKUBE" = true ]; then
        minikube image build -t "$IMAGE_NAME" -f "$DOCKERFILE" .
    else
        docker build -t "$IMAGE_NAME" -f "$DOCKERFILE" .

        if [ "$PUSH" = true ]; then
            echo "Pushing $IMAGE_NAME..."
            docker push "$IMAGE_NAME"
        fi
    fi

    echo ""
done

echo "================================================"
echo "All images built successfully!"
echo "================================================"
echo ""
echo "Images created:"
for SERVICE in "${SERVICES[@]}"; do
    echo "  - ${REGISTRY}${SERVICE}-service:${TAG}"
done
echo ""

if [ "$PUSH" = false ]; then
    echo "To push images, run with --push flag:"
    echo "  $0 --push --registry your-registry.com"
fi
