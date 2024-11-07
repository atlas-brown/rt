#!/bin/bash


set -euo pipefail

docker run --rm "${DOCKER_IMAGE}:${TAG}" bash --version
docker run --rm "${DOCKER_IMAGE}:${TAG}" sudo --version
docker run --rm "${DOCKER_IMAGE}:${TAG}" visudo -c
docker run --rm "${DOCKER_IMAGE}:${TAG}" bash -c 'sudo microdnf install sudo'

docker run --rm -eDOCKER_CLI_EXPERIMENTAL=enabled "${DOCKER_IMAGE}:${TAG}" docker buildx version
docker run --rm "${DOCKER_IMAGE}:${TAG}" docker --version
docker run --rm "${DOCKER_IMAGE}:${TAG}" git --version
docker run --rm "${DOCKER_IMAGE}:${TAG}" which --version
docker run --rm "${DOCKER_IMAGE}:${TAG}" which git

docker run --rm "${DOCKER_IMAGE}:${TAG}" bash -c 'date | grep -E "CES?T"'
docker run --rm "${DOCKER_IMAGE}:${TAG}" bash -c 'locale | grep -E LC_ALL=.+\.UTF-8'


docker run --rm "${DOCKER_IMAGE}:${TAG}" bash --version

docker run --rm "${DOCKER_IMAGE}:${TAG}" java -version
docker run --rm "${DOCKER_IMAGE}:${TAG}" mvn --version
docker run --rm "${DOCKER_IMAGE}:${TAG}" bash -c 'java -XshowSettings:properties -version |& grep "file.encoding = UTF-8"'

# Test Maven
docker run --rm -v "$(git rev-parse --show-toplevel)/test-applications/java/example-app/":/opt/app-root/src:cached "${DOCKER_IMAGE}:${TAG}" mvn -q --batch-mode clean package
docker run --rm -eSPRING_MAIN_BANNER-MODE=off -e JAVA_OPTS="-Dspring.mandatory-file-encoding=UTF-8" -v "$(git rev-parse --show-toplevel)/test-applications/java/example-app/target/dockerhub-pipeline-images-test-jar.jar":/opt/app-root/src/app.jar "${DOCKER_IMAGE}:${TAG}"

docker run --rm "${DOCKER_IMAGE}:${TAG}" bash -c 'java -version 2>&1 | grep -q "build 1\.8"'


docker run --rm "${DOCKER_IMAGE}:${TAG}" gcc --version
docker run --rm "${DOCKER_IMAGE}:${TAG}" node --version
docker run --rm "${DOCKER_IMAGE}:${TAG}" npm --version
docker run --rm "${DOCKER_IMAGE}:${TAG}" yarn --version

# Test node package managers
docker run --rm "${DOCKER_IMAGE}:${TAG}" npm install iconv
docker run --rm "${DOCKER_IMAGE}:${TAG}" yarn add iconv

# Test Headless chrome
docker run --rm "${DOCKER_IMAGE}:${TAG}" bash -c 'npm install puppeteer && ldd ./node_modules/puppeteer/.local-chromium/linux-*/chrome-linux/chrome | grep -vz "=> not found"'
docker run --rm "${DOCKER_IMAGE}:${TAG}" bash -c 'npm install puppeteer && ./node_modules/puppeteer/.local-chromium/linux-*/chrome-linux/chrome --version'

# Test Headless firefox
docker run --rm "${DOCKER_IMAGE}:${TAG}" bash -c 'PUPPETEER_PRODUCT=firefox npm install puppeteer && ./node_modules/puppeteer/.local-firefox/linux-*/firefox/firefox --version'

# Test Headless chrome via angular
docker run --rm -eCI=1 -v "$(git rev-parse --show-toplevel)/test-applications/js/example-app/":/opt/app-root/src/:cached "${DOCKER_IMAGE}:${TAG}" bash -c 'npm ci && npx ng test --watch=false --code-coverage --browsers ChromeHeadlessNoSandbox'
docker run --rm -eCI=1 -ePUPPETEER_PRODUCT=firefox --shm-size 2g  -v "$(git rev-parse --show-toplevel)/test-applications/js/example-app/":/opt/app-root/src/:cached "${DOCKER_IMAGE}:${TAG}" bash -c 'npm ci && npx ng test --watch=false --code-coverage --browsers FirefoxHeadless'

docker run --rm "${DOCKER_IMAGE}:${TAG}" bash -c 'node --version | grep -q "v12"'

