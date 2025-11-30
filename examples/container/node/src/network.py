import logging
import selectors
import socket
import threading
import json

import config
import handlers

sel = selectors.DefaultSelector()

def register_peers():
  """Register all current recv_channel sockets with the selector."""
  for peer_name, peer_info in config.PEERS.items():
    sock = peer_info.get("recv_channel")
    if sock is not None:
      try:
        sel.register(sock, selectors.EVENT_READ, data=peer_name)
        logging.debug(f"Registered {peer_name} for polling")
      except KeyError:
        # Already registered, ignore
        pass

def poll_peers():
  while True:
    events = sel.select(timeout=None)
    for key, mask in events:
      sock = key.fileobj
      peer_name = key.data
      try:
        msg = recv_message(sock)
        if not msg:
          logging.info(f"[RECV] {peer_name} disconnected")
          sel.unregister(sock)
          sock.close()
          config.PEERS[peer_name]["recv_channel"] = None
          continue

        msg_type = msg.get("type")
        handler = handlers.MESSAGE_HANDLERS.get(msg_type)
        if handler:
          handler(peer_name, msg)
        else:
          logging.warning(f"[RECV] Unknown message type '{msg_type}' from {peer_name}")

      except Exception as e:
        logging.error(f"[RECV] Error reading from {peer_name}: {e}")
        sel.unregister(sock)
        sock.close()
        config.PEERS[peer_name]["recv_channel"] = None

def start_polling_thread():
  t = threading.Thread(target=poll_peers, daemon=True)
  t.start()
  return t

def build_message(payload: dict) -> bytes:
  """
  Build a length-prefixed JSON message.
  Format: [4-byte length (big-endian)] [JSON data]

  This ensures we can reliably receive large messages that may arrive
  fragmented across multiple TCP packets.
  """
  try:
    json_data = json.dumps(payload).encode()
    # Prepend 4-byte length header (big-endian unsigned int)
    length = len(json_data)
    return length.to_bytes(4, byteorder='big') + json_data
  except Exception as e:
    raise ValueError(f"Failed to build message: {e}")

def send_message(sock: socket.socket, payload: dict) -> None:
  """
  Send a complete length-prefixed JSON message over a socket.
  """
  try:
    msg = build_message(payload)
    sock.sendall(msg)
  except Exception as e:
    logging.error(f"send_message error: {e}")
    raise

def recv_message(sock: socket.socket) -> dict | None:
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
    logging.error(f"recv_message error: {e}")
    return None

def parse_message(data: bytes) -> dict | None:
  """
  Decode JSON bytes into a dictionary (legacy/fallback).
  Returns None if the data is not valid JSON.

  Note: This is kept for backwards compatibility but should not be used
  for messages that may be fragmented. Use recv_message() instead.
  """
  try:
    return json.loads(data.decode())
  except Exception:
    return None
