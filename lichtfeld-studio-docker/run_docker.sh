#!/bin/bash

usage() {
    echo "Usage: $0 [-bnu] [CUDA_VERSION]"
    echo "  -b       Build with cache"
    echo "  -n       Build without cache"
    echo "  -u       Start docker-compose and enter container"
    echo "  -c       Stop and clean up"
    echo "  -h       Show this help message"
    echo
    echo "If a CUDA version is passed as a final positional argument (e.g. 12.8.0), it overrides auto-detection."
    echo "Set CUDA_OS (default: ubuntu22.04) to choose the CUDA base image OS tag."
}

# --- Default: auto-detect CUDA version
detected_cuda=$(nvidia-smi | grep -oP 'CUDA Version: \K[0-9]+\.[0-9]+')
if [[ -n "$detected_cuda" ]]; then
    CUDA_VERSION="${detected_cuda}.0" # Needed because nvcc returns version without patch
else
    CUDA_VERSION="12.8.0"
fi

# --- Flags
COMPOSE_FILE="lichtfeld-studio-docker/docker-compose.yml"
CUDA_OS="${CUDA_OS:-ubuntu22.04}"
BUILD=false
BUILD_ARGS=""
COMPOSEUP=false

# --- Parse short options
while getopts "bnuch" opt; do
    case ${opt} in
        b ) BUILD=true ;;
        n ) BUILD=true; BUILD_ARGS="--no-cache" ;;
        u ) COMPOSEUP=true ;;
        c ) docker compose -f "$COMPOSE_FILE" down --remove-orphans; exit 0 ;;
        h ) usage; exit 0 ;;
        * ) usage; exit 1 ;;
    esac
done

shift $((OPTIND - 1))

# --- CUDA override (no validation)
if [[ $# -gt 0 ]]; then
    CUDA_VERSION="$1"
fi

echo "Using CUDA version: $CUDA_VERSION"
echo "Using CUDA OS tag: $CUDA_OS"

# --- Export env vars for docker-compose
export USER_UID=$(id -u)
export USER_GID=$(id -g)
export USERNAME=$(id -un)
export USER_PASSWORD=${USERNAME}
export HOSTNAME=$(hostname)
export HOME=$HOME
export DISPLAY=$DISPLAY
export XAUTHORITY=$XAUTHORITY
export SSH_AUTH_SOCK=$SSH_AUTH_SOCK
export CUDA_VERSION
export CUDA_OS

# --- Build step
if [ "$BUILD" = true ]; then
    echo "Building docker image with CUDA $CUDA_VERSION..."
    DOCKER_BUILDKIT=1 docker compose -f "$COMPOSE_FILE" build $BUILD_ARGS
    if [ "$?" -ne 0 ]; then
        echo "Docker build failed!"
        exit 1
    fi
fi

# --- Run container
if [ "$COMPOSEUP" = true ]; then
    echo "Starting docker container..."
    docker compose -f "$COMPOSE_FILE" up -d
    if [ "$?" -ne 0 ]; then
        echo "Docker compose up failed!"
        exit 1
    fi
    docker compose -f "$COMPOSE_FILE" exec lichtfeld-studio bash
fi
