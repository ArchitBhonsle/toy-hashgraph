import argparse
import logging

PEERS = ["alpha", "bravo", "charlie", "delta"]
NODES = {
  peer: { "id": i }
  for i, peer in enumerate(PEERS)
}
TESTCASE = None
PORT = 5000

# Visualization
OUTPUT_DIR = "/usr/hashgraph-observer/images"
PEER_VIEWS_FILENAME = "/usr/hashgraph-observer/images/hashgraph_peer_views.png"
TIMELINE_FILENAME = "/usr/hashgraph-observer/images/hashgraph_timeline.png"
MERGED_GRAPH_FILENAME = "/usr/hashgraph-observer/images/hashgraph_merged.png"
DPI = 150

def setup():
  global TESTCASE

  logging.basicConfig(
    level=logging.DEBUG,
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
