import socket
import time

import config
import util

def run():
  util.send_initial_timestamp()

  util.send_transaction("alpha", "A")

  time.sleep(30) # 30s

  hashgraphs_raw = util.collect_hashgraphs()
  simulation_events = util.collect_simulation_events()

  # Verify results

  for peer in config.PEERS:
    config.NODES[peer].get("channel").sendall(util.build_message({
      "type": "quit"
    }))
