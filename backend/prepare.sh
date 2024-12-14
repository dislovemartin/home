#!/bin/bash
set -e

echo "Installing sqlx-cli..."
cargo install sqlx-cli --no-default-features --features native-tls,postgres

echo "Starting PostgreSQL container..."
docker run --name temp-postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=aimodels -d -p 5432:5432 postgres:14-alpine

echo "Waiting for PostgreSQL to be ready..."
until docker exec temp-postgres pg_isready -U postgres > /dev/null 2>&1; do
  echo "Waiting for database..."
  sleep 1
done

echo "Running migrations..."
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/aimodels cargo sqlx migrate run

echo "Creating SQLx offline data..."
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/aimodels cargo sqlx prepare --workspace

echo "Cleaning up..."
docker stop temp-postgres
docker rm temp-postgres

echo "Done! SQLx query data has been generated." 