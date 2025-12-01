ROOT := ../..

build-node:
	cd $(ROOT) && docker build -t hashgraph-node -f examples/container/node/Dockerfile .

build-observer:
	cd $(ROOT) && docker build -t hashgraph-observer -f examples/container/observer/Dockerfile .

build: build-node build-observer
