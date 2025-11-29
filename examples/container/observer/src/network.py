import logging
import selectors
import socket
import threading
import json

import config

sel = selectors.DefaultSelector()

# def register_peers():
#   """Register all current recv_channel sockets with the selector."""
#   for peer_name, peer_info in config.PEERS.items():
#     sock = peer_info.get("recv_channel")
#     if sock is not None:
#       try:
#         sel.register(sock, selectors.EVENT_READ, data=peer_name)
#         logging.debug(f"Registered {peer_name} for polling")
#       except KeyError:
#         # Already registered, ignore
#         pass

# def poll_peers():
#   while True:
#     events = sel.select(timeout=None)
#     for key, mask in events:
#       sock = key.fileobj
#       peer_name = key.data
#       try:
#         data = sock.recv(4096)
#         if not data:
#           logging.info(f"[RECV] {peer_name} disconnected")
#           sel.unregister(sock)
#           sock.close()
#           config.PEERS[peer_name]["recv_channel"] = None
#           continue

#         msg = parse_message(data)
#         if not msg:
#           logging.warning(f"[RECV] Invalid message from {peer_name}")
#           continue

#         msg_type = msg.get("type")
#         handler = handlers.MESSAGE_HANDLERS.get(msg_type)
#         if handler:
#           handler(peer_name, msg)
#         else:
#           logging.warning(f"[RECV] Unknown message type '{msg_type}' from {peer_name}")

#       except Exception as e:
#         logging.error(f"[RECV] Error reading from {peer_name}: {e}")
#         sel.unregister(sock)
#         sock.close()
#         config.PEERS[peer_name]["recv_channel"] = None

# def start_polling_thread():
  # t = threading.Thread(target=poll_peers, daemon=True)
  # t.start()
  # return t

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
