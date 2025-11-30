import base64
import json
import time
import struct

import config

def send_message(sock, payload: dict):
  """
  Send a length-prefixed JSON message over a socket.
  Format: [4-byte length (big-endian)] [JSON data]
  """
  try:
    json_data = json.dumps(payload).encode()
    length = len(json_data)
    msg = length.to_bytes(4, byteorder='big') + json_data
    sock.sendall(msg)
  except Exception as e:
    raise ValueError(f"Failed to send message: {e}")

def recv_message(sock) -> dict | None:
  """
  Receive a complete length-prefixed message from a socket.
  Handles fragmentation by reading until we get the full message.

  Returns the parsed JSON dict, or None if there's an error.
  """
  try:
    # Read the 4-byte length header
    length_data = b""
    while len(length_data) < 4:
      chunk = sock.recv(4 - len(length_data))
      if not chunk:
        return None  # Connection closed
      length_data += chunk

    msg_length = int.from_bytes(length_data, byteorder='big')

    # Read the actual message
    msg_data = b""
    while len(msg_data) < msg_length:
      chunk = sock.recv(min(4096, msg_length - len(msg_data)))
      if not chunk:
        return None  # Connection closed prematurely
      msg_data += chunk

    return json.loads(msg_data.decode())
  except Exception as e:
    print(f"[ERROR] recv_message failed: {e}")
    return None

def send_transaction(receiver, txn_data):
  send_message(config.NODES[receiver].get("channel"), {
    "type": "transaction",
    "txn_data": txn_data
  })

def send_initial_timestamp():
  initial_timestamp = int(time.time())

  for peer in config.PEERS:
    send_message(config.NODES[peer].get("channel"), {
      "type": "initial_timestamp",
      "value": initial_timestamp
    })

def collect_hashgraphs():
  hashgraphs = []

  for peer in config.PEERS:
    sock = config.NODES[peer].get("channel")

    send_message(sock, {
      "type": "export_hashgraph"
    })

    msg = recv_message(sock)
    if not msg or msg.get("type") != "hashgraph":
      raise ValueError(f"Invalid export hashgraph response from peer {peer}")

    hashgraphs.append(msg["hashgraph"])

  return hashgraphs

def collect_simulation_events():
  simulation_events = []

  for peer in config.PEERS:
    sock = config.NODES[peer].get("channel")

    send_message(sock, {
      "type": "export_simulation_events"
    })

    msg = recv_message(sock)
    if not msg or msg.get("type") != "simulation_events":
      raise ValueError(f"Invalid export simulation events response from peer {peer}")

    simulation_events.append(msg["simulation_events"])

  return simulation_events