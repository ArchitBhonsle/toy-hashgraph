import logging
import time
import threading

from toy_hashgraph import Hashgraph
import config
import gossip

def handle_transaction(msg: dict):
  if config.HASHGRAPH is None:
    logging.info("Hashgraph hasn't been initialized")
    return

  tx_data = msg.get("txn_data").encode()

  with config.HASHGRAPH_LOCK:
    timestamp = int(time.time())
    config.HASHGRAPH.append_transaction(tx_data)

  with config.SIMULATION_EVENTS_LOCK:
    config.SIMULATION_EVENTS.append({
      'type': 'transaction',
      'peer': config.ID,
      'transaction': msg.get("txn_data"),
      'time': timestamp
    })

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

  threading.Thread(target=gossip.gossip, args=(), daemon=True).start()

  logging.info("Started gossip thread")
