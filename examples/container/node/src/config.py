import logging
import argparse
import threading

import keys

logging.basicConfig(
  level=logging.INFO,
  format='[%(levelname)s] %(asctime)s - %(message)s'
)

# System parameters
ID = None
OBSERVER = {
  "hostname": "observer"
}
PEER_NAMES = ["alpha", "bravo", "charlie", "delta"]
NAME = None
PORT = 5000
PEERS = None
PUBLIC_KEY = None
PRIVATE_KEY = None

# Hashgraph paramters
INITIAL_TIMESTAMP = None
HASHGRAPH = None

keys_ready_cond = threading.Condition()

def setup():
  global ID
  global NAME
  global PEERS
  global PUBLIC_KEY
  global PRIVATE_KEY
  global HASHGRAPH

  args = parse()

  if args.id is None:
    raise ValueError("Invalid or missing id")

  if args.id >= len(PEER_NAMES):
    raise ValueError("Invalid id")

  ID = args.id
  PEERS = {
    name: { "id": i }
    for i, name in enumerate(PEER_NAMES)
  }

  NAME = PEER_NAMES[ID]
  PRIVATE_KEY, PUBLIC_KEY = keys.generate()
  PEERS[NAME]["public_key"] = PUBLIC_KEY

def parse():
  parser = argparse.ArgumentParser()
  parser.add_argument("-id", type=int, help="Node id")

  return parser.parse_args()

def log():
  logging.debug("=== Node Configuration ===")
  logging.debug(f"PEER_NAMES:  {PEER_NAMES}")
  logging.debug(f"NAME:        {NAME}")
  logging.debug(f"PORT:        {PORT}")
  logging.debug(f"PEERS:       {PEERS}")
  logging.debug(f"PRIVATE_KEY: {PRIVATE_KEY}")
  logging.debug(f"PUBLIC_KEY:  {PUBLIC_KEY}")
  logging.debug("==========================")
