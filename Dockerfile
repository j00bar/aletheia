FROM centos:8
RUN mkdir /src && \
    yum install -y dnf-plugins-core && \
    yum config-manager --set-enabled PowerTools && \
    yum install -y python3 git pandoc python3-sphinx java-1.8.0-openjdk graphviz curl && \
    pip3 install -U --no-cache poetry setuptools pipenv && \
    curl -o /src/plantuml.jar -L http://sourceforge.net/projects/plantuml/files/plantuml.jar/download && \
    printf '#!/bin/sh\nexec java -jar /src/plantuml.jar "$@"' > /usr/bin/plantuml && \
    chmod +x /usr/bin/plantuml && \
    yum clean all
COPY . /src/aletheia
WORKDIR /src/aletheia
RUN poetry install
ENTRYPOINT ["poetry", "run"]
CMD ["aletheia"]