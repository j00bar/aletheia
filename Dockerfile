FROM centos:8
RUN mkdir /src && \
    yum install -y dnf-plugins-core && \
    yum config-manager --set-enabled PowerTools && \
    yum install -y python3 git pandoc python3-sphinx java-1.8.0-openjdk graphviz curl libpq-devel gcc python3-devel make && \
    pip3 install -U --no-cache poetry setuptools pipenv && \
    curl -o /src/plantuml.jar -L http://sourceforge.net/projects/plantuml/files/plantuml.jar/download && \
    printf '#!/bin/sh\nexec java -jar /src/plantuml.jar "$@"' > /usr/bin/plantuml && \
    chmod +x /usr/bin/plantuml && \
    yum clean all && \
    mkdir -p /etc/aletheia && \
    git config --system credential.helper 'store --file /etc/aletheia/git-credentials' && \
    git config --system user.email "aletheia@redhat.com" && \
    git config --system user.name "Aletheia Docs Builder"
COPY poetry.lock pyproject.toml /src/aletheia/
WORKDIR /src/aletheia
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=off PIPENV_VENV_IN_PROJECT=1
RUN poetry config virtualenvs.create false && poetry install
COPY . /src/aletheia/
RUN python3 setup.py install
CMD ["aletheia"]