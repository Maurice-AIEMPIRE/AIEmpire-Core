# Services

This directory contains backend services and APIs.

## Structure

```
services/
├── api/              # REST API
├── worker/           # Background workers
├── webhook-handler/  # Webhook processor
└── scheduler/        # Cron jobs & scheduled tasks
```

## Guidelines

- Each service should be independently deployable
- Use Docker Compose for local development
- Document API endpoints
- Include health check endpoints

## Service Template

```
services/my-service/
├── src/              # Source code
├── tests/            # Tests
├── Dockerfile        # Container definition
├── requirements.txt  # Python deps
├── package.json      # Node deps
└── README.md         # Service docs
```

## Adding New Services

1. Create service directory
2. Add Dockerfile
3. Add to docker-compose in /infra
4. Document in service README
5. Add CI/CD pipeline
