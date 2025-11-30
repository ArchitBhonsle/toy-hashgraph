import socket
import time

import config
import util
import visualization
import util

def run():
  util.send_initial_timestamp()

  util.send_transaction("alpha", "A")

  time.sleep(30) # 30s

  hashgraphs = util.collect_hashgraphs()
  simulation_events = util.collect_simulation_events()

  # Verify results

  # Visualize results
  visualization.visualize_hashgraphs(
    hashgraphs,
    [i for i, peer in enumerate(config.PEERS)]
  )

  for peer in config.PEERS:
    util.send_message(config.NODES[peer].get("channel"), {
      "type": "quit"
    })
