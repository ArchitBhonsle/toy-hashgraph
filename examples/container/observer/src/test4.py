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
  util.send_gossip_interval(5)
  util.send_initial_timestamp()

  simulation_duration = 30
  transaction_interval_seconds = 10

  transaction_counter = 0
  last_transaction_time = config.INITIAL_TIMESTAMP - 1

  cur_time = int(time.time())
  while cur_time < config.INITIAL_TIMESTAMP + simulation_duration:
    time.sleep(transaction_interval_seconds)

    cur_time = int(time.time())
    last_transaction_time = cur_time

    peer = random.choice(config.PEERS)
    transaction_counter += 1
    tx_data = f"tx_{transaction_counter}"
    util.send_transaction(peer, tx_data)

    logging.info(f"[{cur_time}s] Submitted transaction {tx_data} to peer {peer}")

  time.sleep(60 * 2)

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
    ordering = get_transactions_in_consensus_order(i, states[i]["graph"], graph_querier)
    ordered_transactions.append(ordering)

  logging.info("")
  logging.info("Transactions:")
  for i, ordering in enumerate(ordered_transactions):
    logging.info(f"Peer {config.PEERS[i]}: {ordering}")

  l = len(ordered_transactions[0])
  for i in range(1, len(states)):
    if len(ordered_transactions[i]) < l:
      l = len(ordered_transactions[i])

  if l == 0:
    logging.warn("One or more nodes have 0 commited transaction.")
    return

  logging.info("")
  logging.info(f"Conses achieved for {l} transactions!")

  for i in range(l):
    t = ordered_transactions[0][i]
    for j in range(1, len(states)):
      if t != ordered_transactions[j][i]:
        raise ValueError(f"Mismatching {i}th transaction")

def get_transactions_in_consensus_order(peer_i, data, graph):
  transactions = [(bytes.fromhex(h), e) for h, e in data["events"].items() if e["kind"] == "default" and e["transactions"]]

  commited_transactions = [transaction for transaction in transactions if graph.round_received(transaction[0]) is not None]
  logging.info(f"{len(commited_transactions)} out of {len(transactions)} transactions were commited by {config.PEERS[peer_i]}")

  commited_transactions.sort(key=cmp_to_key(lambda a, b: graph.consensus_ordering(a[0], b[0]) or 0))
  return [bytes.fromhex(commited_transaction[1]["transactions"]).decode() for commited_transaction in commited_transactions]
