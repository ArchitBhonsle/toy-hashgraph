import logging
import threading
import time
import random
import base64

import config
import network

def gossip():
  if config.HASHGRAPH is None:
    raise ValueError("Hashgraph has not been initialized")

  logging.debug(f"Gossipping with an interval {config.GOSSIP_INTERVAL}")

  while True:
    time.sleep(config.GOSSIP_INTERVAL)

    with config.HASHGRAPH_LOCK:
      timestamp = int(time.time())
      data = config.HASHGRAPH.send()

    receiver = random.choice(config.PEER_NAMES)

    # Ignore if ourself.
    if receiver == config.NAME:
      continue

    with config.SIMULATION_EVENTS_LOCK:
      network.send_message(config.PEERS[receiver]["send_channel"], {
        "type": "gossip",
        "hashgraph": base64.b64encode(data).decode()
      })

      config.SIMULATION_EVENTS.append({
        'type': 'gossip',
        'sender': config.ID,
        'receiver': config.PEER_NAMES.index(receiver),
        'time': timestamp
      })

    logging.debug(f"Gossiped to {receiver}")
