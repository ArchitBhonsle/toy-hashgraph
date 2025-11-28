import config
import peers

def main():
  config.setup()
  config.log()

  peers.start_listener()
  peers.dial()

  peers.wait_for_all_channels()
  print("[MAIN] All channels established, peer communication ready!")

if __name__ == "__main__":
  main()
