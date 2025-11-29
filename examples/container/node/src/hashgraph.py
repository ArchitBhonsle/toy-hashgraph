import logging
import time

from toy_hashgraph import Hashgraph
import config

def handle_transaction(msg: dict):
  if config.HASHGRAPH is None:
    logging.info("Hashgraph hasn't been initialized")
    return

  tx_data = msg.get("txn_data").encode()
  config.HASHGRAPH.append_transaction(tx_data)

  logging.info(f"[{int(time.time())}s] Appended transaction: {msg.get("txn_data")}")

def handle_initial_timestamp(msg: dict):
  config.INITIAL_TIMESTAMP = msg.get("value")

  config.HASHGRAPH = Hashgraph(
    config.ID,
    config.INITIAL_TIMESTAMP,
    config.PRIVATE_KEY,
    {
      i: config.PEERS[peer]["public_key"]
      for i, peer in enumerate(config.PEERS)
    }
  )

  logging.info(f"Initialized hashgraph with timestamp {config.INITIAL_TIMESTAMP}")
