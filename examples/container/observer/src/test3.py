import logging
import time
import random
import json

import config
import util
import visualization
import util
from toy_hashgraph import GraphQuerier
from functools import cmp_to_key

def run():
  util.send_initial_timestamp()

  simulation_duration = 30 # 1 Minutes
  transaction_interval_seconds = 10

  transaction_counter = 0
  last_transaction_time = config.INITIAL_TIMESTAMP - 1

  cur_time = int(time.time())
  while cur_time < config.INITIAL_TIMESTAMP + simulation_duration:
    time.sleep(transaction_interval_seconds)

    cur_time = int(time.time())
    last_transaction_time = cur_time

    # if random.choice([True, False]):
    peer = random.choice(config.PEERS)
    transaction_counter += 1
    tx_data = f"tx_{transaction_counter}"
    util.send_transaction(peer, tx_data)

    logging.info(f"[{cur_time}s] Submitted transaction {tx_data} to peer {peer}")

  time.sleep(30)

  states_json = util.collect_hashgraphs()

  # Visualize results
  visualization.visualize_hashgraphs(
    states_json,
    [i for i, peer in enumerate(config.PEERS)]
  )

  try:
    test_total_order(states_json)
  except Exception as e:
    logging.info(f"Test failed: {e}")
    return

  logging.info("Test passed!")

def test_total_order(states_json):
  if len(states_json) == 0:
    raise ValueError("No states")

  states = [json.loads(state_json) for state_json in states_json]
  graph_queriers = [GraphQuerier.from_json(json.dumps(state["graph"])) for state in states]
  ordered_transactions = []

  for i, graph_querier in enumerate(graph_queriers):
    ordering = get_transactions_in_consensus_order(states[i]["graph"], graph_querier)
    ordered_transactions.append(ordering)

  for ordering in ordered_transactions:
    logging.info(ordering)

  l = len(ordered_transactions[0])
  for i in range(1, len(states)):
    if len(ordered_transactions[i]) != l:
      raise ValueError("Not all nodes have the same number of commited transactions")

  if l == 0:
    logging.warn("System has 0 transactions")
    return

  for i in range(l):
    t = ordered_transactions[0][i]
    for j in range(1, len(states)):
      if t != ordered_transactions[j][i]:
        raise ValueError(f"Mismatching {i}th transaction")

def get_transactions_in_consensus_order(data, graph):
  transactions = [(bytes.fromhex(h), e) for h, e in data["events"].items() if e["kind"] == "default" and e["transactions"]]
  logging.info(f"Found {len(transactions)} transactions")

  commited_transactions = [transaction for transaction in transactions if graph.round_received(transaction[0]) is not None]
  logging.info(f"{len(commited_transactions)} were commited")

  commited_transactions.sort(key=cmp_to_key(lambda a, b: graph.consensus_ordering(a[0], b[0]) or 0))
  return [bytes.fromhex(commited_transaction["transactions"]).decode for commited_transaction in commited_transactions]
