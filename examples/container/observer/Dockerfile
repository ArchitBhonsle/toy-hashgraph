FROM python:3.12-alpine

# 3. Set app home
ENV APP_HOME=/usr/hashgraph-observer
WORKDIR ${APP_HOME}

RUN mkdir -p ${APP_HOME}/src
COPY src ${APP_HOME}/src

# 6. Default command to run your Python example
ENTRYPOINT ["python", "src/main.py"]
