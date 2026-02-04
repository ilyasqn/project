# Microservices Project

A cloud-native microservices architecture with event-driven communication, AI-powered features, and comprehensive monitoring.

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ User Service │     │Product Service│    │  AI Service  │     │ Notification │
│   :30001     │     │    :30002    │     │    :30004    │     │   :30003     │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │                    │
       └────────────────────┴────────────────────┴────────────────────┘
                                    │
                            ┌───────▼───────┐
                            │   RabbitMQ    │
                            │  (Event Bus)  │
                            └───────────────┘
                                    │
       ┌────────────────────────────┼────────────────────────────┐
       │                            │                            │
┌──────▼──────┐            ┌────────▼────────┐          ┌────────▼────────┐
│ PostgreSQL  │            │     MongoDB     │          │      Redis      │
│   :30432    │            │     :30017      │          │     :30379      │
└─────────────┘            └─────────────────┘          └─────────────────┘
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| User Service | 30001 | User management (CRUD, authentication) |
| Product Service | 30002 | Product catalog management |
| Notification Service | 30003 | Email and Telegram notifications |
| AI Service | 30004 | AI-powered description generation |

## Infrastructure

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 30432 | Primary database for users and products |
| MongoDB | 30017 | Document store for AI history and notification logs |
| Redis | 30379 | Caching layer for products and AI descriptions |
| RabbitMQ | 30672 | Message broker for event-driven communication |
| RabbitMQ UI | 31672 | Management interface (guest/guest) |

## Monitoring

| Service | Port | Description |
|---------|------|-------------|
| Grafana | 30300 | Dashboards and visualization (admin/admin) |
| Loki | - | Log aggregation (internal) |
| Promtail | - | Log collection agent (internal) |

## Quick Start

### Prerequisites

- [Minikube](https://minikube.sigs.k8s.io/docs/start/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Docker](https://docs.docker.com/get-docker/)

### One-Command Deployment

```bash
# Clone the repository
git clone <repository-url>
cd project

# Start minikube (if not running)
minikube start

# Deploy everything
./scripts/deploy.sh --build
```

This will:
1. Build all Docker images inside minikube
2. Deploy all infrastructure (PostgreSQL, RabbitMQ, MongoDB, Redis)
3. Deploy all application services
4. Deploy monitoring stack (Grafana, Loki, Promtail)
5. Display all service URLs

### Access Services

After deployment, get the minikube IP:
```bash
minikube ip
```

Then access services at:

**Application APIs (Swagger UI):**
- User Service: `http://<MINIKUBE_IP>:30001/docs`
- Product Service: `http://<MINIKUBE_IP>:30002/docs`
- Notification Service: `http://<MINIKUBE_IP>:30003/docs`
- AI Service: `http://<MINIKUBE_IP>:30004/docs`

**Infrastructure:**
- RabbitMQ Management: `http://<MINIKUBE_IP>:31672` (guest/guest)
- Grafana: `http://<MINIKUBE_IP>:30300` (admin/admin)

**Database Connections:**
- PostgreSQL: `<MINIKUBE_IP>:30432`
- MongoDB: `<MINIKUBE_IP>:30017`
- Redis: `<MINIKUBE_IP>:30379`

## Scripts

| Script | Description |
|--------|-------------|
| `./scripts/deploy.sh --build` | Build and deploy everything |
| `./scripts/deploy.sh` | Deploy without rebuilding images |
| `./scripts/deploy.sh --delete` | Delete all resources |
| `./scripts/build-all.sh --minikube` | Build images only |

## Event Flow

```
1. Product Created (without description)
   └─► product.created event published to RabbitMQ
       ├─► AI Service receives event
       │   └─► Generates description using LLM
       │   └─► Publishes ai.description.generated
       └─► Notification Service receives event
           └─► Sends Telegram notification

2. AI Description Generated
   └─► ai.description.generated event published
       ├─► Product Service receives event
       │   └─► Updates product with description
       │   └─► Invalidates Redis cache
       └─► Notification Service receives event
           └─► Sends Telegram notification
```

## Environment Variables

### Application Services

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `RABBITMQ_URL` | RabbitMQ connection string |
| `REDIS_URL` | Redis connection string |
| `MONGODB_URL` | MongoDB connection string |
| `OPENAI_API_KEY` | OpenAI API key (AI Service) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token (Notification Service) |
| `TELEGRAM_CHAT_ID` | Telegram chat ID (Notification Service) |

## Testing

Run tests for each service:

```bash
# AI Service tests
python3 -m pytest services/ai

# Product Service tests
python3 -m pytest services/product

# Notification Service tests
python3 -m pytest services/notification

# Integration tests
python3 -m pytest tests/
```

## Useful Commands

```bash
# Check pod status
kubectl get pods -n microservices

# View logs
kubectl logs -f deployment/user-service -n microservices
kubectl logs -f deployment/ai-service -n microservices

# Restart a deployment
kubectl rollout restart deployment/user-service -n microservices

# Scale a deployment
kubectl scale deployment/user-service --replicas=3 -n microservices

# Port forward (alternative access method)
kubectl port-forward svc/grafana 3000:3000 -n microservices
```

## API Examples

### Create User
```bash
curl -X POST http://<MINIKUBE_IP>:30001/users/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "testuser", "password": "secret123"}'
```

### Create Product (triggers AI description generation)
```bash
curl -X POST http://<MINIKUBE_IP>:30002/products/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Wireless Headphones", "price": 99.99, "sku": "WH-001", "category": "Electronics"}'
```

### Generate AI Text
```bash
curl -X POST http://<MINIKUBE_IP>:30004/ai/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a product description for wireless headphones", "max_tokens": 100}'
```

## Project Structure

```
project/
├── services/
│   ├── user/           # User Service
│   ├── product/        # Product Service
│   ├── notification/   # Notification Service
│   └── ai/             # AI Service
├── shared/             # Shared utilities (RabbitMQ client)
├── k8s/                # Kubernetes manifests
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml
│   ├── postgres/
│   ├── rabbitmq/
│   ├── mongodb/
│   ├── redis/
│   ├── user/
│   ├── product/
│   ├── notification/
│   ├── ai/
│   └── monitoring/
├── scripts/
│   ├── deploy.sh       # Deployment script
│   └── build-all.sh    # Build script
└── docker-compose.yml  # Local development
```

## Troubleshooting

### Pods not starting
```bash
# Check pod status
kubectl describe pod <pod-name> -n microservices

# Check events
kubectl get events -n microservices --sort-by='.lastTimestamp'
```

### Service not accessible
```bash
# Verify service is NodePort
kubectl get svc -n microservices

# Check endpoints
kubectl get endpoints -n microservices
```

### View Grafana logs
```bash
# In Grafana, go to Explore > Select Loki > Run query:
{namespace="microservices", app="user-service"}
```
