# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

# Set the labels.
# These are standard opencontainer labels; see:
# https://github.com/opencontainers/image-spec/blob/master/annotations.md
# :tyranno: LABEL org.opencontainers.image.version="${{project.version}}"
LABEL org.opencontainers.image.version="0.0.1-alpha0"
# :tyranno: LABEL org.opencontainers.image.vendor="${{.vendor}}"
LABEL org.opencontainers.image.vendor="dmyersturnbull"
# :tyranno: LABEL org.opencontainers.image.title="${{project.name}}"
LABEL org.opencontainers.image.title="tyranno-sandbox"
# :tyranno: LABEL org.opencontainers.image.url="${{project.urls.Homepage}}"
LABEL org.opencontainers.image.url="https://github.com/dmyersturnbull/tyranno-sandbox"
# :tyranno: LABEL org.opencontainers.image.documentation="${{project.urls.Documentation}}"
LABEL org.opencontainers.image.documentation="https://github.com/dmyersturnbull/tyranno-sandbox"

# Declare the core build args.
# These must exist outside of any stage and be declared before the first FROM.
ARG ALPINE_VERSION=""
# :tyranno: ARG PYTHON_VERSION="${{.cicd-python.pep440_str_minor(@)}}"
ARG PYTHON_VERSION="3.13"

# -------------------- Download uv and set vars --------------------

# Start the stage "builder", and download uv.
FROM python:$PYTHON_VERSION:alpine$ALPINE_VERSION as builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
SHELL ["/bin/bash", "-c"]

# Environment variables
ENV PATH=/root/.cargo/bin/:/root/.local/bin:$PATH
# Any non-empty string is taken as true for boolean UV and Python env vars.
# https://docs.python.org/3/using/cmdline.html#envvar-PYTHONFAULTHANDLER
ENV PYTHONFAULTHANDLER=yes
# https://docs.python.org/3/using/cmdline.html#envvar-PYTHONUNBUFFERED
ENV PYTHONUNBUFFERED=yes
# https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_LINK_MODE=copy
# https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_COMPILE_BYTECODE=yes
# Alternative we're not using:
# ENV UV_NO_CACHE=yes

# -------------------- Install the project --------------------

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
  uv sync --locked --no-dev --no-editable --no-install-project

# Copy the source and build/install it in another layer.
COPY . /var/app/
RUN \
  --mount=type=cache,target=/root/.cache/uv \
  uv sync --locked --no-dev --no-editable

# ******************** In production only! ************************
#
# -------------------- Run in a fresh stage --------------------
# Make a new stage that contains only the final venv.
# FROM python:$PYTHON_VERSION:alpine$ALPINE_VERSION
# COPY --from=builder --chown=app:app /var/app/.venv /var/app/.venv
# *****************************************************************

ENTRYPOINT [
"/var/app/.venv/tyranno"
]
CMD [
"--version"
]

# -------------------------------------------------------------------------------------------------

# An example of starting a hypercorn server.

# Expose HTTP 1.1 & 2.0 on TCP/80, HTTPS 1.1 & 2.0 on TCP/443, and HTTP/3 on UDP/443.
# EXPOSE 80
# EXPOSE 443
# EXPOSE 443/udp

# ENTRYPOINT [
# "/var/app/.venv/bin/hypercorn",
# "tyranno_sandbox.api:app"
# ]
# CMD [
# "--bind",
# "[::]:80",
# "--bind",
# "[::]:443",
# "--quic-bind",
# "[::]:443"
# ]

# ARG HEALTHCHECK_INTERVAL=5m
# ARG HEALTHCHECK_TIMEOUT=3s
# ARG HEALTHCHECK_START_PERIOD=5s

# Ubuntu curl doesn't support --http3 yet
# HEALTHCHECK \
#   --interval=$HEALTHCHECK_INTERVAL \
#   --timeout=$HEALTHCHECK_TIMEOUT \
#   --start-period=$HEALTHCHECK_START_PERIOD \
#   CMD curl --fail --http2-prior-knowledge http://localhost/ || exit 1
