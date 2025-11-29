ROOT := ../..

build-node:
	cd $(ROOT) && docker build -t hashgraph-node -f examples/container/node/Dockerfile .

build-observer:
	docker build observer -t hashgraph-observer

build: build-node build-observer
