import base64
import json
import time

import config

def send_transaction(receiver, txn_data):
  config.NODES[receiver].get("channel").sendall(
    build_message({
      "type": "transaction",
      "txn_data": txn_data
    })
  )

def send_initial_timestamp():
  initial_timestamp = int(time.time())
  initial_timestamp_msg = build_message({ "type": "initial_timestamp", "value": initial_timestamp })

  for peer in config.PEERS:
    config.NODES[peer].get("channel").sendall(initial_timestamp_msg)

def collect_hashgraphs():
  hashgraphs = []

  for peer in config.PEERS:
    sock = config.NODES[peer].get("channel")

    sock.sendall(
      build_message({
        "type": "export_hashgraph"
      })
    )

    data = sock.recv(4096)
    if not data:
      raise ValueError(f"No data received from peer {peer}")

    msg = parse_message(data)
    if not msg or not msg["type"] or msg["type"] != "hashgraph":
      raise ValueError(f"Invalid export hashgraph response from peer {peer}")

    hashgraphs.append(base64.b64decode(msg["hashgraph"]))

  return hashgraphs

def collect_simulation_events():
  simulation_events = []

  for peer in config.PEERS:
    sock = config.NODES[peer].get("channel")

    sock.sendall(
      build_message({
        "type": "export_simulation_events"
      })
    )

    data = sock.recv(4096)
    if not data:
      raise ValueError(f"No data received from peer {peer}")

    msg = parse_message(data)
    if not msg or not msg["type"] or msg["type"] != "simulation_events":
      raise ValueError(f"Invalid export simulation events response from peer {peer}")

    simulation_events.append(msg["simulation_events"])

  return simulation_events

def build_message(payload: dict) -> bytes:
  """
  Build a JSON message from a dictionary and encode it to bytes.
  Example payload:
    {"type": "key_exchange", "key": "<public_key>"}
  """
  try:
    return json.dumps(payload).encode()
  except Exception as e:
    raise ValueError(f"Failed to build message: {e}")

def parse_message(data: bytes) -> dict | None:
  """
  Decode JSON bytes into a dictionary.
  Returns None if the data is not valid JSON.
  """
  try:
    return json.loads(data.decode())
  except Exception:
    return None