# syntax=docker/dockerfile:1
# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

# Declare the core build args.
# These must exist outside of any stage and be declared before the first FROM.
ARG ALPINE_VERSION=""
# ::tyranno:: ARG PYTHON_VERSION="$<<."python-versions".default>>"
ARG PYTHON_VERSION="3.14"

#
# -------------------------- Base image and uv --------------------------------------------------- #

# Start the stage "builder", and download uv.
# Install Bash and use it.
FROM python:$PYTHON_VERSION-alpine$ALPINE_VERSION AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN apk add bash
SHELL ["/bin/bash", "-c"]

# Environment variables
# `/root/.local/bin` is defined by the XDG Base Directory Spec.
# `/root/.cargo/bin` is the default dir for Cargo-installed tools.
ENV PATH=/root/.cargo/bin/:/root/.local/bin:$PATH
# Any non-empty string ≠ 1 is taken as true for boolean UV and Python env vars.
# https://docs.python.org/3/using/cmdline.html#envvar-PYTHONFAULTHANDLER
ENV PYTHONFAULTHANDLER=1
# https://docs.python.org/3/using/cmdline.html#envvar-PYTHONUNBUFFERED
ENV PYTHONUNBUFFERED=1
# https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1

#
# -------------------------- Labels -------------------------------------------------------------- #

# These are standard opencontainer labels; see:
# https://github.com/opencontainers/image-spec/blob/master/annotations.md
# ::tyranno:: LABEL org.opencontainers.image.version="$<<project.version.pypa_ver(@).to_semver(@)>>"
LABEL org.opencontainers.image.version="0.0.1-alpha.0"
# ::tyranno:: LABEL org.opencontainers.image.vendor="$<<.vendor>>"
LABEL org.opencontainers.image.vendor="dmyersturnbull"
# ::tyranno:: LABEL org.opencontainers.image.title="$<<project.name>>"
LABEL org.opencontainers.image.title="tyranno-sandbox"
# ::tyranno:: LABEL org.opencontainers.image.url="$<<project.urls.Homepage>>"
LABEL org.opencontainers.image.url="https://github.com/dmyersturnbull/tyranno-sandbox"
# ::tyranno:: LABEL org.opencontainers.image.documentation="$<<project.urls.Documentation>>"
LABEL org.opencontainers.image.documentation="https://github.com/dmyersturnbull/tyranno-sandbox"
# ::tyranno:: LABEL org.opencontainers.image.licenses="$<<project.license.text>>"
LABEL org.opencontainers.image.licenses="Apache-2.0"

#
# -------------------------- Build and install --------------------------------------------------- #

# We'll install in 2 layers: (1) transitive dependencies and (2) project, as described in
# https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
# Then, we'll create a new stage containing only our installed package, as described in
# https://docs.astral.sh/uv/guides/integration/docker/#non-editable-installs

WORKDIR /var/app

# Install the dependencies in one layer.
RUN \
  --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  uv sync \
    --frozen \
    --no-build \
    --no-dev \
    --extra server \
    --no-editable \
    --no-install-project

# Copy the source, then build and install it in another layer.
COPY . /var/app/
RUN \
  --mount=type=cache,target=/root/.cache/uv \
  uv sync \
    --frozen \
    --no-dev \
    --inexact \
    --no-editable

# Start a new stage, copying over only the files we need.
# **IMPORTANT: Comment out while prototyping so tools remain available in the container.**
# FROM python:$PYTHON_VERSION:alpine$ALPINE_VERSION
# COPY --from=builder --chown=app:app /var/app/.venv /var/app/.venv

#
# -------------------------- Entrypoint: `__main__.py` ------------------------------------------- #

# For a command-line tool:
# ::tyranno:: # ENTRYPOINT ["/var/app/.venv/bin/$<<project.scripts.$<<project.name>>>>"]
# ENTRYPOINT ["/var/app/.venv/bin/tyranno-sandbox"]
# CMD ["--help"]

#
# -------------------------- Entrypoint: hypercorn + FastAPI ------------------------------------- #

# Expose HTTP 1.1 & 2.0 on TCP/80, HTTPS 1.1 & 2.0 on TCP/443, and HTTP/3 on UDP/443.
EXPOSE 80
EXPOSE 443
EXPOSE 443/udp

ARG N_WORKERS=1
ARG LOG_LEVEL=WARNING
ARG BACKLOG_SIZE=100

ENV N_WORKERS=$N_WORKERS
ENV LOG_LEVEL=$LOG_LEVEL
ENV BACKLOG_SIZE=$BACKLOG_SIZE

CMD exec \
  /var/app/.venv/bin/hypercorn tyranno_sandbox.api:api \
    --bind '[::]:80' \
    --bind '[::]:443' \
    --quic-bind '[::]:443' \
    --log-file - \
    --log-level $LOG_LEVEL \
    --workers $N_WORKERS \
    --backlog $BACKLOG_SIZE

# Declare a container healthcheck, which Docker Compose (used in CI) will use.
# We *could* instead define it in `compose.yaml`, but there's no downside to keeping it here.
# This is equivalent to our choice for K8s "liveness" probe.
# Alpine's `curl` doesn't support `--http3` yet, but HTTP/2 is fine.
# (`--http2-prior-knowledge` initiates an HTTP/2 request without a prior HTTP/1.1 request.)
HEALTHCHECK \
  --start-period=5s \
  --start-interval=2.5s \
  --timeout=10s \
  CMD curl --fail --http2-prior-knowledge http://localhost/ || exit 1
