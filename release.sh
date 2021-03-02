#!/bin/bash
IMAGE_DOMAIN=${BUILD_IMAGE_DOMAIN:-docker.io}
IMAGE_NAMESPACE=${BUILD_IMAGE_NAMESPACE:-rainbond}
DOMESTIC_BASE_NAME=${DOMESTIC_BASE_NAME:-'registry.cn-hangzhou.aliyuncs.com'}
DOMESTIC_NAMESPACE=${DOMESTIC_NAMESPACE:-'goodrain'}

if [ -z "$VERSION" ]; then
  if [ -z "$TRAVIS_TAG" ]; then
    VERSION=$TRAVIS_BRANCH-dev
  else
    VERSION=$TRAVIS_TAG
  fi
fi

function release() {
  git_commit=$(git log -n 1 --pretty --format=%h)
  buildTime=$(date +%F-%H)
  release_desc=${VERSION}-${git_commit}-${buildTime}
  image_name="rbd-app-ui"
  docker build --network=host --build-arg VERSION="${VERSION}" --build-arg RELEASE_DESC="${release_desc}" -t "${IMAGE_DOMAIN}/${IMAGE_NAMESPACE}/${image_name}:${VERSION}" -f Dockerfile.release .
  if [ $? -ne 0 ]; then
    exit 1
  fi
  if [ "$TRAVIS_PULL_REQUEST" == "false" ]; then
    docker login "${IMAGE_DOMAIN}" -u "$DOCKER_USERNAME" -p "$DOCKER_PASSWORD"
    docker push "${IMAGE_DOMAIN}/${IMAGE_NAMESPACE}/${image_name}:${VERSION}"
    if [ ${DOMESTIC_BASE_NAME} ]; then
      docker tag "${IMAGE_DOMAIN}/${IMAGE_NAMESPACE}/${image_name}:${VERSION}" "${DOMESTIC_BASE_NAME}/${DOMESTIC_NAMESPACE}/${image_name}:${VERSION}"
      docker login -u "$DOMESTIC_DOCKER_USERNAME" -p "$DOMESTIC_DOCKER_PASSWORD" "${DOMESTIC_BASE_NAME}"
      docker push "${DOMESTIC_BASE_NAME}/${DOMESTIC_NAMESPACE}/${image_name}:${VERSION}"
    fi
  fi
}
case $1 in
*)
  release
  ;;
esac
