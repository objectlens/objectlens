compose := if `which podman 2>/dev/null` != "" { "podman compose" } else { "docker compose" }

set dotenv-load := true
set dotenv-filename := ".env"

install:
    cd backend && uv sync
    cd frontend && npm install

backend:
    mkdir -p example/development/data/objectlens/providers example/development/data/objectlens/users
    cp -n backend/data/providers/* example/development/data/objectlens/providers/ 2>/dev/null || true
    cd backend && OBJECTLENS_DATABASE_URL="sqlite:///../example/development/data/objectlens/objectlens.db" OBJECTLENS_PROVIDERS_CONFIG_DIR="../example/development/data/objectlens/providers" OBJECTLENS_USERS_CONFIG_DIR="../example/development/data/objectlens/users" uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
    cd frontend && npm run dev

dev:
    @echo "Starting ObjectLens backend and frontend"
    @trap 'kill 0' INT TERM EXIT; just backend & just frontend & wait

lint:
    cd backend && uv run ruff check .
    cd frontend && npm run lint

format:
    cd backend && uv run ruff format .

test:
    cd backend && uv run pytest

clean:
    rm -rf backend/.venv frontend/node_modules frontend/.nuxt frontend/.output .pytest_cache .ruff_cache

docker-up:
    mkdir -p example/development/data/objectlens/providers example/development/data/objectlens/users
    cp -n backend/data/providers/* example/development/data/objectlens/providers/ 2>/dev/null || true
    {{compose}} -f example/development/docker-compose.yaml up --build

docker-down:
    {{compose}} -f example/development/docker-compose.yaml down

docker-garage-up:
    {{compose}} -f example/garage/docker-compose.yaml up --build

init-garage:
    #!/bin/sh
    NODE_ID=$({{compose}} -f example/garage/docker-compose.yaml exec garage /garage status 2>&1 | grep -oE "[0-9a-f]{16}" | head -n 1 | tr -d '\r' | tr -d '\n'); \
    echo "Discovered Garage Node ID: $NODE_ID"; \
    if [ -n "$NODE_ID" ]; then \
        echo "Assigning node $NODE_ID to local zone..."; \
        {{compose}} -f example/garage/docker-compose.yaml exec garage /garage layout assign $NODE_ID -z local -c 10G || true; \
        echo "Applying layout change..."; \
        {{compose}} -f example/garage/docker-compose.yaml exec garage /garage layout apply --version 1 || true; \
    fi
    echo "Importing custom S3 credentials..."
    {{compose}} -f example/garage/docker-compose.yaml exec garage /garage key import my-custom-user my-custom-secret-key --yes || true
    echo "Creating default S3 bucket..."
    {{compose}} -f example/garage/docker-compose.yaml exec garage /garage bucket create objectlens-demo || true
    echo "Authorizing imported S3 key..."
    {{compose}} -f example/garage/docker-compose.yaml exec garage /garage bucket allow objectlens-demo --read --write --key my-custom-user || true
    echo "S3 Garage initialization completed successfully!"
