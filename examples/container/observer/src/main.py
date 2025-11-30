import logging
import importlib

import config
import nodes
import util

def main():
  config.setup()

  nodes.start_listener()
  nodes.wait_for_all_channels()

  logging.info("All peers have connected")
  logging.info(f"Running test case {config.TESTCASE}")

  module_name = f"test{config.TESTCASE}"  # e.g. test1, test2, test42
  test_module = importlib.import_module(module_name)

  test_module.run()

  for peer in config.PEERS:
    util.send_message(config.NODES[peer].get("channel"), {
      "type": "quit"
    })

if __name__ == "__main__":
  main()
