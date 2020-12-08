FROM centos:8


RUN mkdir /src && \
    yum install -y dnf-plugins-core && \
    yum config-manager --set-enabled powertools && \
    yum install -y python3 git pandoc python3-sphinx java-1.8.0-openjdk graphviz curl libpq-devel gcc python3-devel make && \
    yum clean all

RUN python3 -m venv /opt/aletheia_venv

ENV PATH="/opt/aletheia_venv/bin:$PATH" \
    HOME="/src/aletheia"

RUN curl -o /src/plantuml.jar -L http://sourceforge.net/projects/plantuml/files/plantuml.jar/download && \
    printf '#!/bin/sh\nexec java -jar /src/plantuml.jar "$@"' > /usr/bin/plantuml && \
    chmod +x /usr/bin/plantuml && \
    mkdir -p /etc/aletheia && \
    git config --system credential.helper 'store --file /etc/aletheia/git-credentials' && \
    git config --system user.email "aletheia@redhat.com" && \
    git config --system user.name "Aletheia Docs Builder"

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=off PIPENV_VENV_IN_PROJECT=1
RUN /opt/aletheia_venv/bin/pip install -U --no-cache pip setuptools poetry pipenv
COPY poetry.lock pyproject.toml /src/aletheia/
WORKDIR /src/aletheia
RUN source /opt/aletheia_venv/bin/activate && poetry install
COPY . /src/aletheia
RUN pip install --no-deps .  # deps already installed via poetry
CMD ["aletheia"]
