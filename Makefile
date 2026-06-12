
# VERSION=$(shell git describe | sed 's/^v//')

VERSION=0.0.0

DOCKER=podman

all: containers

# Not used
wheels:
	pip3 wheel --no-deps --wheel-dir dist graphit/
	pip3 wheel --no-deps --wheel-dir dist graphit-base/
	pip3 wheel --no-deps --wheel-dir dist graphit-flow/
	pip3 wheel --no-deps --wheel-dir dist graphit-vertexai/
	pip3 wheel --no-deps --wheel-dir dist graphit-bedrock/
	pip3 wheel --no-deps --wheel-dir dist graphit-embeddings-hf/
	pip3 wheel --no-deps --wheel-dir dist graphit-cli/
	pip3 wheel --no-deps --wheel-dir dist graphit-ocr/
	pip3 wheel --no-deps --wheel-dir dist graphit-unstructured/
	pip3 wheel --no-deps --wheel-dir dist graphit-mcp/

packages: update-package-versions
	rm -rf dist/
	cd graphit && python -m build --sdist --outdir ../dist/
	cd graphit-base && python -m build --sdist --outdir ../dist/
	cd graphit-flow && python -m build --sdist --outdir ../dist/
	cd graphit-vertexai && python -m build --sdist --outdir ../dist/
	cd graphit-bedrock && python -m build --sdist --outdir ../dist/
	cd graphit-embeddings-hf && python -m build --sdist --outdir ../dist/
	cd graphit-cli && python -m build --sdist --outdir ../dist/
	cd graphit-ocr && python -m build --sdist --outdir ../dist/
	cd graphit-unstructured && python -m build --sdist --outdir ../dist/
	cd graphit-mcp && python -m build --sdist --outdir ../dist/

pypi-upload:
	twine upload dist/*-${VERSION}.*

CONTAINER_BASE=docker.io/graphit

update-package-versions:
	mkdir -p graphit-cli/graphit
	mkdir -p graphit/graphit
	echo __version__ = \"${VERSION}\" > graphit-base/graphit/base_version.py
	echo __version__ = \"${VERSION}\" > graphit-flow/graphit/flow_version.py
	echo __version__ = \"${VERSION}\" > graphit-vertexai/graphit/vertexai_version.py
	echo __version__ = \"${VERSION}\" > graphit-bedrock/graphit/bedrock_version.py
	echo __version__ = \"${VERSION}\" > graphit-embeddings-hf/graphit/embeddings_hf_version.py
	echo __version__ = \"${VERSION}\" > graphit-cli/graphit/cli_version.py
	echo __version__ = \"${VERSION}\" > graphit-ocr/graphit/ocr_version.py
	echo __version__ = \"${VERSION}\" > graphit-unstructured/graphit/unstructured_version.py
	echo __version__ = \"${VERSION}\" > graphit/graphit/graphit_version.py
	echo __version__ = \"${VERSION}\" > graphit-mcp/graphit/mcp_version.py

containers: container-base container-flow \
container-bedrock container-vertexai \
container-hf container-ocr \
container-unstructured container-mcp

some-containers: container-base container-flow container-unstructured

push:
	${DOCKER} push ${CONTAINER_BASE}/graphit-base:${VERSION}
	${DOCKER} push ${CONTAINER_BASE}/graphit-flow:${VERSION}
	${DOCKER} push ${CONTAINER_BASE}/graphit-bedrock:${VERSION}
	${DOCKER} push ${CONTAINER_BASE}/graphit-vertexai:${VERSION}
	${DOCKER} push ${CONTAINER_BASE}/graphit-hf:${VERSION}
	${DOCKER} push ${CONTAINER_BASE}/graphit-ocr:${VERSION}
	${DOCKER} push ${CONTAINER_BASE}/graphit-unstructured:${VERSION}
	${DOCKER} push ${CONTAINER_BASE}/graphit-mcp:${VERSION}

# Individual container build targets
container-%: update-package-versions
	${DOCKER} build \
	    -f containers/Containerfile.${@:container-%=%} \
	    -t ${CONTAINER_BASE}/graphit-${@:container-%=%}:${VERSION} .

# Multi-arch: build both platforms sequentially into one manifest (local use)
manifest-%: update-package-versions
	-@${DOCKER} manifest rm \
	    ${CONTAINER_BASE}/graphit-${@:manifest-%=%}:${VERSION}
	${DOCKER} build --platform linux/amd64,linux/arm64 \
	    -f containers/Containerfile.${@:manifest-%=%} \
	    --manifest \
	    ${CONTAINER_BASE}/graphit-${@:manifest-%=%}:${VERSION} .

# Multi-arch: build a single platform image (for parallel CI)
platform-%-amd64: update-package-versions
	${DOCKER} build --platform linux/amd64 \
	    -f containers/Containerfile.${@:platform-%-amd64=%} \
	    -t ${CONTAINER_BASE}/graphit-${@:platform-%-amd64=%}:${VERSION}-amd64 .

platform-%-arm64: update-package-versions
	${DOCKER} build --platform linux/arm64 \
	    -f containers/Containerfile.${@:platform-%-arm64=%} \
	    -t ${CONTAINER_BASE}/graphit-${@:platform-%-arm64=%}:${VERSION}-arm64 .

# Push a single platform image
push-platform-%-amd64:
	${DOCKER} push \
	    ${CONTAINER_BASE}/graphit-${@:push-platform-%-amd64=%}:${VERSION}-amd64

push-platform-%-arm64:
	${DOCKER} push \
	    ${CONTAINER_BASE}/graphit-${@:push-platform-%-arm64=%}:${VERSION}-arm64

# Combine per-platform images into a multi-arch manifest
combine-manifest-%:
	-@${DOCKER} manifest rm \
	    ${CONTAINER_BASE}/graphit-${@:combine-manifest-%=%}:${VERSION}
	${DOCKER} manifest create \
	    ${CONTAINER_BASE}/graphit-${@:combine-manifest-%=%}:${VERSION} \
	    docker://${CONTAINER_BASE}/graphit-${@:combine-manifest-%=%}:${VERSION}-amd64 \
	    docker://${CONTAINER_BASE}/graphit-${@:combine-manifest-%=%}:${VERSION}-arm64
	${DOCKER} manifest push \
	    ${CONTAINER_BASE}/graphit-${@:combine-manifest-%=%}:${VERSION}

# Push a container
push-container-%:
	${DOCKER} push \
	    ${CONTAINER_BASE}/graphit-${@:push-container-%=%}:${VERSION}

# Push a manifest (from local multi-arch build)
push-manifest-%:
	${DOCKER} manifest push \
	    ${CONTAINER_BASE}/graphit-${@:push-manifest-%=%}:${VERSION}

clean:
	rm -rf wheels/

set-version:
	echo '"${VERSION}"' > templates/values/version.jsonnet

docker-hub-login:
	cat docker-token.txt | \
	    ${DOCKER} login -u graphit --password-stdin registry-1.docker.io

