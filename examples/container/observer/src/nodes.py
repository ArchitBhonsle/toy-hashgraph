import logging
import socket
import threading

import config

ready_lock = threading.Lock()
ready_cond = threading.Condition(ready_lock)

def handle_connection(conn, addr):
  ip, port = addr
  logging.debug(f"handle_connection: Incoming connection from {ip}:{port}")

  try:
    hostname = socket.gethostbyaddr(ip)[0]
  except socket.herror:
    hostname = ip  # fallback if no reverse DNS

  logging.debug(f"handle_connection: Resolved hostname: {hostname}")

  peer_name = extract_peer_name(hostname)

  with ready_cond:
    config.NODES[peer_name]["channel"] = conn
    ready_cond.notify_all()

def listen():
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.bind(("0.0.0.0", config.PORT))
  server.listen()

  logging.debug(f"Listening for peers on port {config.PORT}...")

  while True:
    channels = sum(ch.get("channel") is not None for ch in config.NODES.values())
    if channels == len(config.PEERS):
      break

    conn, addr = server.accept()
    t = threading.Thread(target=handle_connection, args=(conn, addr), daemon=True)
    t.start()

def start_listener():
  t = threading.Thread(target=listen, daemon=True)
  t.start()

def wait_for_all_channels():
  expected = len(config.PEERS)
  with ready_cond:
    while True:
      channels = sum(ch.get("channel") is not None for ch in config.NODES.values())
      if channels == expected:
        break
      ready_cond.wait()

def extract_peer_name(hostname: str) -> str:
  try:
    return hostname.split('.')[0].split('-')[1]
  except Exception:
    return hostname