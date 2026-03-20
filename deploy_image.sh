#!/bin/bash

SERVICE_NAME="$1"

if [ -z "$SERVICE_NAME" ]; then
    echo "Error: parameter required."
    echo "Usage: $0 <service_name>"
    exit 1
fi

COMPOSE_FILE="docker-compose-${SERVICE_NAME}.yml"
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "Error: compose file not found: $COMPOSE_FILE"
    exit 1
fi

remove_containers() {
    local filter="$1"
    local container_ids
    container_ids=$(docker ps -a --filter "$filter" -q)
    if [ "$container_ids" != "" ]; then
        docker stop $container_ids
        docker rm $container_ids
    fi
}

if [ "$SERVICE_NAME" = "n8n" ]; then
    remove_containers "name=^/n8n$"
    remove_containers "name=^/n8n_main$"
    remove_containers "name=^/n8n_worker$"
    remove_containers "name=^/n8n_redis$"
elif [ "$SERVICE_NAME" = "db" ]; then
    remove_containers "name=^/n8n_db$"
    remove_containers "name=^/n8n_db_migrate$"
elif [ "$SERVICE_NAME" = "api" ]; then
    remove_containers "name=^/fastapi_server$"
elif [ "$SERVICE_NAME" = "ollama" ]; then
    remove_containers "name=^/ollama$"
else
    remove_containers "name=^/n8n_${SERVICE_NAME}"
fi

docker-compose -f "$COMPOSE_FILE" up --build -d

if [ "$SERVICE_NAME" = "ollama" ]; then
    echo "Waiting for ollama server..."
    for i in {1..30}; do
        if docker exec ollama ollama ps >/dev/null 2>&1; then
            break
        fi
        sleep 2
    done

    if ! docker exec ollama ollama ps >/dev/null 2>&1; then
        echo "Error: ollama server is not ready."
        exit 1
    fi

    echo "Pulling model: llama3:latest"
    docker exec ollama ollama pull llama3:latest
fi
