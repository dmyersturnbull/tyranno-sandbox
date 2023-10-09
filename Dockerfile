# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to CICD
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/cicd
# SPDX-License-Identifier: Apache-2.0

# https://stackoverflow.com/questions/53835198/integrating-python-poetry-with-docker/54763270#54763270

# :tyranno: FROM python:${project.requires-python~.semver_max(@).semver_minor(@)~}
FROM python:3.12

# --------------------------------------
# ------------- Set labels -------------

# See https://github.com/opencontainers/image-spec/blob/master/annotations.md
# :tyranno: LABEL org.opencontainers.image.version="${project.version}"
LABEL org.opencontainers.image.version="0.0.1-alpha1"
# :tyranno: LABEL org.opencontainers.image.vendor="${tool.cicd.data.vendor}"
LABEL org.opencontainers.image.vendor="dmyersturnbull"
# :tyranno: LABEL org.opencontainers.image.title="${project.name}"
LABEL org.opencontainers.image.title="cicd"
# :tyranno: LABEL org.opencontainers.image.version="${project.version}"
LABEL org.opencontainers.image.version="0.0.1-alpha0"
# :tyranno: LABEL org.opencontainers.image.url="${project.urls.homepage}"
LABEL org.opencontainers.image.url="https://github.com/dmyersturnbull/cicd"
# :tyranno: LABEL org.opencontainers.image.documentation="${project.urls.docs}"
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

WORKDIR /app
COPY . /app/

RUN pip install .[api]

EXPOSE 80
EXPOSE 443
EXPOSE 4433

CMD hypercorn cicd.api:app --bind '[::]:80' --bind '[::]:443' --quic-bind '[::]:4433'
