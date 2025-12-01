import logging
import time
import random

import config
import util
import visualization
import util

def run():
  util.send_initial_timestamp()

  simulation_duration = 60 * 10 # 10 Minutes
  transaction_interval_seconds = 20

  transaction_counter = 0
  last_transaction_time = config.INITIAL_TIMESTAMP - 1

  cur_time = int(time.time())
  while cur_time < config.INITIAL_TIMESTAMP + simulation_duration:
    time.sleep(transaction_interval_seconds)

    cur_time = int(time.time())
    last_transaction_time = cur_time

    if random.choice([True, False]):
      peer = random.choice(config.PEERS)
      transaction_counter += 1
      tx_data = f"tx_{transaction_counter}"
      util.send_transaction(peer, tx_data)

      logging.info(f"[{cur_time}s] Submitted transaction {tx_data} to peer {peer}")

  hashgraphs = util.collect_hashgraphs()

  # Visualize results
  visualization.visualize_hashgraphs(
    hashgraphs,
    [i for i, peer in enumerate(config.PEERS)]
  )
