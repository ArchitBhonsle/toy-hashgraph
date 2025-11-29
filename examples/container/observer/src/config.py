import argparse
import logging

PEERS = ["alpha", "bravo", "charlie", "delta"]
NODES = {
  peer: { "id": i }
  for i, peer in enumerate(PEERS)
}
TESTCASE = None
PORT = 5000

def setup():
  global TESTCASE

  logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s'
  )

  args = parse()

  if args.id is None:
    raise ValueError("Invalid testcase id")

  TESTCASE = args.id


def parse():
  parser = argparse.ArgumentParser()
  parser.add_argument("-id", type=int, help="Test id")

  return parser.parse_args()
