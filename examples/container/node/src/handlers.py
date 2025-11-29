import logging
import base64
import time

import config

def handle_gossip(peer_name: str, msg: dict):
  if config.HASHGRAPH is None:
    logging.info("Recieved gossip, but hashgraph wasn't initialized")
    return

  data = base64.b64decode(msg["hashgraph"])
  with config.HASHGRAPH_LOCK:
    config.HASHGRAPH.receive(data, int(time.time()))

  logging.debug(f"handle_gossip: Handled gossip from peer f{peer_name}")

def handle_key_exchange(peer_name: str, msg: dict):
  """
  Handles 'key_exchange' messages.
  Decodes the base64 key back to bytes and stores in config.PEERS.
  """
  key_b64 = msg["key"]
  key_bytes = base64.b64decode(key_b64)
  config.PEERS[peer_name]["public_key"] = key_bytes
  logging.debug(f"[RECV] Received public key from {peer_name}")

  with config.keys_ready_cond:
    config.keys_ready_cond.notify_all()

def handle_echo(peer_name: str, msg: dict):
  """
  Example for other message types.
  """
  logging.info(f"[RECV] Echo from {peer_name}: {msg.get('text')}")

# Map message types to functions
MESSAGE_HANDLERS = {
  "key_exchange": handle_key_exchange,
  "echo": handle_echo,
  "gossip": handle_gossip
  # Add new message types here
}
