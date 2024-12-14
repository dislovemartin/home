# AI Model Platform

A modern, high-performance platform for discovering, managing, and interacting with AI models.

## Features

- Browse and discover AI models
- Detailed model information and metrics
- User authentication and authorization
- Model search and filtering
- Performance tracking and analytics

## Tech Stack

### Backend
- Rust with Axum framework
- PostgreSQL database
- Redis for caching
- JWT for authentication

### Frontend
- React with TypeScript
- Material-UI components
- Redux Toolkit for state management
- React Query for data fetching

## Project Structure

```
.
├── backend/           # Rust backend service
├── frontend/         # React frontend application
├── docker/           # Docker configuration files
├── docs/            # Documentation
└── scripts/         # Development and deployment scripts
```

## Development Setup

### Prerequisites
- Rust (latest stable)
- Node.js (v18+)
- PostgreSQL
- Docker and Docker Compose
- Git

### Getting Started

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-model-platform
```

2. Set up the backend:
```bash
cd backend
cargo build
```

3. Set up the frontend:
```bash
cd frontend
npm install
```

4. Start the development environment:
```bash
docker-compose up -d  # Starts PostgreSQL and Redis
cd backend && cargo run
cd frontend && npm start
```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 