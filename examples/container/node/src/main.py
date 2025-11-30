import logging
import base64
import time

import config
import peers
import network
import observer
from toy_hashgraph import Hashgraph

def main():
  config.setup()
  config.log()

  peers.start_listener()
  peers.dial()

  peers.wait_for_all_channels()
  logging.info("All channels established, peer communication ready!")

  network.register_peers() # Sets up the list of sockets to poll.
  network.start_polling_thread()

  send_keys_to_all_peers()
  logging.info("Sent public keys to all peers")

  wait_for_other_keys()
  logging.info("Received public keeys from all peers")

  observer.dial()
  observer.register()
  observer.poll()

def send_keys_to_all_peers():
  for peer_name in config.PEERS:
    if peer_name == config.NAME:
      continue
    send_public_key(peer_name)

def send_public_key(peer_name: str):
  sock = config.PEERS[peer_name].get("send_channel")
  if sock is None:
    return

  # Convert bytes to base64 string for JSON
  key_b64 = base64.b64encode(config.PUBLIC_KEY).decode()

  try:
    network.send_message(sock, {"type": "key_exchange", "key": key_b64})
    logging.debug(f"[SEND] Sent public key to {peer_name}")
  except Exception as e:
    logging.error(f"[SEND] Failed to send public key to {peer_name}: {e}")

def wait_for_other_keys():
  """
  Blocks until all other peers have sent their public keys.
  """
  expected_peers = [p for p in config.PEERS if p != config.NAME]

  with config.keys_ready_cond:
    while True:
      # Count peers that have sent their keys
      received_keys = [
        p for p in expected_peers
        if config.PEERS[p].get("public_key") is not None
      ]

      if len(received_keys) >= len(expected_peers):
        break  # All keys received

      # Wait until notified that a key might have arrived
      config.keys_ready_cond.wait(timeout=1)

if __name__ == "__main__":
  main()
