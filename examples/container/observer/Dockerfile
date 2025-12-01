FROM python:3.12-alpine

# 1. System dependencies for building Rust extensions
RUN apk update && apk add --no-cache cargo build-base libffi-dev

RUN pip install maturin
RUN pip install patchelf
RUN pip install cryptography
RUN pip install matplotlib

# 3. Set app home
ENV APP_HOME=/usr/hashgraph
WORKDIR ${APP_HOME}

# 4. Copy your project (must be inside build context)
COPY "../../../toy-hashgraph" ${APP_HOME}/toy-hashgraph
COPY "../../../toy-hashgraph-py" ${APP_HOME}/toy-hashgraph-py

# Build your wheel
RUN cd toy-hashgraph-py && maturin build --release

# Install it
RUN pip install toy-hashgraph-py/target/wheels/*.whl

RUN mkdir -p ${APP_HOME}/examples/container/observer/images
RUN mkdir -p ${APP_HOME}/examples/container/observer/src
COPY examples/container/observer/src ${APP_HOME}/examples/container/observer/src

# 6. Default command to run your Python example
ENTRYPOINT ["python", "examples/container/observer/src/main.py"]
