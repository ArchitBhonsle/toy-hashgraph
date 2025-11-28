import logging
import argparse
import keys
from toy_hashgraph import Hashgraph

logging.basicConfig(
  level=logging.WARN,
  format='[%(levelname)s] %(asctime)s - %(message)s'
)

# System parameters
PEER_NAMES = ["alpha", "bravo", "charlie", "delta"]
NAME = None
PORT = 5000
PEERS = None
PUBLIC_KEY = None
PRIVATE_KEY = None
HASHGRAPH = None

def setup():
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

  PEERS = {
    name: { "id": i }
    for i, name in enumerate(PEER_NAMES)
  }

  NAME = PEER_NAMES[args.id]
  PRIVATE_KEY, PUBLIC_KEY = keys.generate()
  # TODO: Uncomment when Hashgraph initialization is ready
  # HASHGRAPH = Hashgraph(NAME, PRIVATE_KEY, {name: config.PEERS[name]["id"] for name in PEER_NAMES})

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
