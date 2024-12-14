#!/bin/bash
set -euo pipefail

echo "Regenerating Cargo.lock file..."
docker run --rm -v "$(pwd)/backend:/app" rust:slim bash -c "cd /app && rm -f Cargo.lock && cargo generate-lockfile"
echo "Done!" 