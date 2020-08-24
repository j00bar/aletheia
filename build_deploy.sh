#!/bin/bash

set -exv

ALETHEIA_IMAGE="quay.io/cloudservices/aletheia"
IMAGE_TAG=$(git rev-parse --short=7 HEAD)

if [[ -z "$QUAY_USER" || -z "$QUAY_TOKEN" ]]; then
    echo "QUAY_USER and QUAY_TOKEN must be set"
    exit 1
fi

DOCKER_CONF="$PWD/.docker"
mkdir -p "$DOCKER_CONF"
docker --config="$DOCKER_CONF" login -u="$QUAY_USER" -p="$QUAY_TOKEN" quay.io

docker --config="$DOCKER_CONF" build -t "${ALETHEIA_IMAGE}:${IMAGE_TAG}" .

docker --config="$DOCKER_CONF" push "${ALETHEIA_IMAGE}:${IMAGE_TAG}"
