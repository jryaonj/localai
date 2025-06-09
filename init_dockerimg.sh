#!/bin/bash

# This script pulls Docker images from various registries (Docker Hub, GHCR, etc.)
# and optionally uses proxies for pulling and tagging the images.

# Initialize proxy variables with default values
DOCKERHUBPXY="_DOCKERHUBPXY_"
GHCRPXY="_GHCRPXY_"
QUAYPXY="_QUAYPXY_"

# If proxy variables contain default placeholder values, set them to empty
[[ "$DOCKERHUBPXY" == "_DOCKERHUBPXY_" ]] && DOCKERHUBPXY=""
[[ "$GHCRPXY" == "_GHCRPXY_" ]] && GHCRPXY=""
[[ "$QUAYPXY" == "_QUAYPXY_" ]] && QUAYPXY=""

# Define arrays for different registries
declare -A docker_images=(
    ["nginx:stable"]=""
    ["postgres:latest"]=""
    ["pgvector/pgvector:0.8.0-pg17"]=""
    ["ollama/ollama"]=""
    ["vllm/vllm-openai"]=""
    ["apache/tika:latest-full"]=""
    ["searxng/searxng"]=""
)

declare -A ghcr_images=(
    ["ghcr.io/open-webui/open-webui:main"]=""
)

# declare -A quay_images=(
#     ["quay.io/astronomer/ap-airflow:2.9.0-buster-onbuild"]=""
# )

declare -A direct_images=(
    ["mcr.microsoft.com/playwright:v1.52.0-noble"]=""
)

# Function to pull and tag images
pull_and_tag() {
    local pxy=$1
    local image=$2
    # Split image into components
    IFS='/' read -ra PARTS <<< "$image"
    if [ ${#PARTS[@]} -eq 1 ]; then
        # If no organization, assume it's a library image
        local name_tag=${PARTS[0]}
        if [ -n "$pxy" ]; then
            image="${pxy}/library/${name_tag}"
        fi
    elif [ -n "$pxy" ]; then
        # If organization exists, keep the full path
        image="${pxy}/${image}"
    fi
    echo "Processing: $image"
    if [ -n "$pxy" ]; then
        docker pull "${pxy}/${image}"
        docker tag "${pxy}/${image}" "${image}"
    else
        # Direct download without proxy
        docker pull "${image}"
    fi
}

# Process Docker Hub images
for image in "${!docker_images[@]}"; do
    pull_and_tag "$DOCKERHUBPXY" "$image"
done

# Process GHCR images
for image in "${!ghcr_images[@]}"; do
    pull_and_tag "$GHCRPXY" "$image"
done

# Process Quay images (commented out)
# for image in "${!quay_images[@]}"; do
#     pull_and_tag "$QUAYPXY" "$image" 
# done

# Process direct images (no proxy)
for image in "${!direct_images[@]}"; do
    pull_and_tag "" "$image"
done
