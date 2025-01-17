# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

# https://stackoverflow.com/questions/53835198/integrating-python-poetry-with-docker/54763270#54763270

# :tyranno: FROM python:${.default-python-version.vr_minor(@)}
FROM python:3.13

# --------------------------------------
# ------------- Set labels -------------

# See https://github.com/opencontainers/image-spec/blob/master/annotations.md
# :tyranno: LABEL org.opencontainers.image.version="${project.version}"
LABEL org.opencontainers.image.version="0.0.1-alpha0"
# :tyranno: LABEL org.opencontainers.image.vendor="${.vendor}"
LABEL org.opencontainers.image.vendor="dmyersturnbull"
# :tyranno: LABEL org.opencontainers.image.title="${project.name}"
LABEL org.opencontainers.image.title="cicd"
# :tyranno: LABEL org.opencontainers.image.url="${project.urls.Homepage}"
LABEL org.opencontainers.image.url="https://github.com/dmyersturnbull/cicd"
# :tyranno: LABEL org.opencontainers.image.documentation="${project.urls.Documentation}"
LABEL org.opencontainers.image.documentation="https://github.com/dmyersturnbull/cicd"

# --------------------------------------
# ---------- Copy and install ----------

# ENV no longer adds a layer in new Docker versions,
# so we don't need to chain these in a single line
ENV PYTHONFAULTHANDLER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=120
ENV PATH="/root/.cargo/bin/:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh

WORKDIR /app
COPY . /app/

#RUN uv install .
RUN uv sync --frozen

EXPOSE 80
EXPOSE 443

CMD hypercorn cicd.api:app --bind '[::]:80' --bind '[::]:443' --quic-bind '[::]:443'
