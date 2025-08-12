# APRA Compliance Monitoring Application

A comprehensive compliance monitoring system built following SOLID, DRY, KISS principles with Behavior-Driven Development (BDD) implementation.

## Architecture Overview

This application implements a microservices architecture with:
- **Frontend**: React.js with Material-UI for responsive dashboard
- **Backend**: Python FastAPI web services
- **Database**: MySQL for transaction tracking and compliance data
- **Containerization**: Docker containers for AWS EKS deployment
- **Testing**: BDD with pytest-bdd and comprehensive unit tests

## Key Features

- Real-time transaction monitoring
- APRA compliance rule engine
- Automated violation detection
- Interactive compliance dashboard
- Comprehensive audit trails
- RESTful API services
- Docker containerization ready for EKS

## Project Structure

```
compliance-monitoring-app/
├── backend/                    # Python FastAPI services
│   ├── app/
│   │   ├── api/               # API endpoints
│   │   ├── core/              # Core business logic
│   │   ├── models/            # Database models
│   │   ├── services/          # Business services
│   │   └── tests/             # BDD and unit tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # React.js dashboard
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API services
│   │   └── tests/             # Frontend tests
│   ├── Dockerfile
│   └── package.json
├── database/                   # MySQL schema and migrations
├── docker-compose.yml          # Local development
├── k8s/                       # Kubernetes manifests for EKS
└── docs/                      # Documentation
```

## Getting Started

1. Clone the repository
2. Run with Docker Compose: `docker-compose up`
3. Access dashboard at: http://localhost:3000
4. API documentation at: http://localhost:8000/docs

## Testing

- BDD tests: `pytest backend/app/tests/bdd/`
- Unit tests: `pytest backend/app/tests/unit/`
- Frontend tests: `npm test`

## Deployment

Deploy to AWS EKS using the provided Kubernetes manifests in the `k8s/` directory.
