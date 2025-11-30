import logging
import selectors
import socket
import threading
import json
import time
import base64
import copy

import config
import hashgraph
import network

def handle_export_hashgraph(msg: dict):
  if not config.HASHGRAPH:
    hashgraph_data = None
  else:
    with config.HASHGRAPH_LOCK:
      hashgraph_data = config.HASHGRAPH.as_json()

  network.send_message(config.OBSERVER.get("channel"), {
    "type": "hashgraph",
    "hashgraph": hashgraph_data
  })

def handle_export_simulation_events(msg: dict):
  with config.SIMULATION_EVENTS_LOCK:
    simulation_events = copy.deepcopy(config.SIMULATION_EVENTS)

  network.send_message(config.OBSERVER.get("channel"), {
    "type": "simulation_events",
    "simulation_events": simulation_events
  })

def handle_echo(msg: dict):
  """
  Example for other message types.
  """
  logging.info(f"[RECV] Echo from {config.OBSERVER.get("hostname")}: {msg.get('text')}")

MESSAGE_HANDLERS = {
  "echo": handle_echo,
  "initial_timestamp": hashgraph.handle_initial_timestamp,
  "transaction": hashgraph.handle_transaction,
  "export_hashgraph": handle_export_hashgraph,
  "export_simulation_events": handle_export_simulation_events
  # Add new message types here
}

def dial(retries=10, backoff=0.5):
  attempt = 0
  while attempt < retries:
    try:
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.settimeout(2.0)
      s.connect((config.OBSERVER["hostname"], config.PORT))
      # success
      config.OBSERVER["channel"] = s
      logging.debug(f"dial: Connected to {config.OBSERVER["hostname"]}:{config.PORT}")
      break
    except Exception as e:
      attempt += 1
      logging.debug(f"dial: Failed to connect to {config.OBSERVER["hostname"]} (attempt {attempt}/{retries}): {e}")
      time.sleep(backoff)
  else:
    logging.warning(f"dial: Giving up connecting to {config.OBSERVER["hostname"]} after {retries} attempts")

sel = selectors.DefaultSelector()

def register():
  sock = config.OBSERVER.get("channel")
  sel.register(sock, selectors.EVENT_READ, data=config.OBSERVER.get("hostname"))
  logging.debug(f"Registered {config.OBSERVER.get("hostname")} for polling")

def poll():
  while True:
    events = sel.select(timeout=None)
    for key, mask in events:
      sock = key.fileobj
      peer_name = key.data
      try:
        msg = network.recv_message(sock)
        if not msg:
          logging.info(f"[RECV] {peer_name} disconnected")
          sel.unregister(sock)
          sock.close()
          config.OBSERVER["channel"] = None
          return

        msg_type = msg.get("type")
        if msg_type == "quit":
          logging.info("Quitting")
          return

        handler = MESSAGE_HANDLERS.get(msg_type)
        if handler:
          handler(msg)
        else:
          logging.warning(f"[RECV] Unknown message type '{msg_type}' from {peer_name}")

      except Exception as e:
        logging.error(f"[RECV] Error reading from {peer_name}: {e}")
        sel.unregister(sock)
        sock.close()
        config.OBSERVER["channel"] = None

def start_polling_thread():
  t = threading.Thread(target=poll, daemon=True)
  t.start()
  return t
