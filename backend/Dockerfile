# Build stage
FROM rust:slim AS build

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y pkg-config libssl-dev && \
    rm -rf /var/lib/apt/lists/*

# Create new empty project
RUN cargo new --bin backend

# Copy manifests
COPY Cargo.toml Cargo.lock ./backend/

# Set working directory
WORKDIR /app/backend

# Build dependencies only (this layer will be cached if dependencies don't change)
RUN cargo build --release

# Remove the dummy source code
RUN rm src/*.rs

# Copy actual source code and SQLx data
COPY src ./src
COPY migrations ./migrations
COPY .sqlx ./.sqlx

# Build application in offline mode
ENV SQLX_OFFLINE=true
RUN cargo build --release

# Production stage
FROM debian:bookworm-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y ca-certificates libssl3 netcat-traditional && \
    rm -rf /var/lib/apt/lists/*

# Copy binary and migrations from builder
COPY --from=build /app/backend/target/release/backend ./backend
COPY --from=build /app/backend/migrations ./migrations

# Create non-root user
RUN useradd -m -U -s /bin/bash app && \
    chown -R app:app /app

# Create start script
RUN echo '#!/bin/bash\nset -ex\n\necho "Starting backend service..."\n\n# Wait for the database to be ready\necho "Waiting for database..."\nuntil nc -z db 5432; do\n  echo "Database not ready, waiting..."\n  sleep 2\ndone\n\necho "Database is ready!"\necho "Running migrations..."\n./backend migrate\necho "Migrations completed!"\necho "Starting server..."\nexec ./backend' > /app/start.sh && \
    chmod +x /app/start.sh

USER app

CMD ["/app/start.sh"] 