import socket
import time

import config
import network

def run():
  initial_timestamp = int(time.time())
  initial_timestamp_msg = network.build_message({ "type": "initial_timestamp", "value": initial_timestamp })

  for peer in config.PEERS:
    config.NODES[peer].get("channel").sendall(initial_timestamp_msg)

  config.NODES["alpha"].get("channel").sendall(
    network.build_message({
      "type": "transaction",
      "txn_data": "A"
    })
  )

  time.sleep(600)

  for peer in config.PEERS:
    config.NODES[peer].get("channel").sendall(network.build_message({
      "type": "quit"
    }))