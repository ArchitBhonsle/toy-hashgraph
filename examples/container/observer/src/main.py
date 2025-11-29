import logging
import importlib

import config
import nodes

def main():
  config.setup()

  nodes.start_listener()
  nodes.wait_for_all_channels()

  logging.info("All peers have connected")
  logging.info(f"Running test case {config.TESTCASE}")

  module_name = f"test{config.TESTCASE}"  # e.g. test1, test2, test42
  test_module = importlib.import_module(module_name)

  test_module.run()

if __name__ == "__main__":
  main()
